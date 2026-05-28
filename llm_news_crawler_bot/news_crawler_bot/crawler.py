import json
import logging
import asyncio
import uuid
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import quote_plus

from playwright.async_api import Page, async_playwright

from .agent import (
    choose_navigation_from_links,
    decompose_collection_goals,
    extract_article,
    plan_crawl,
    plan_login,
    select_targets_from_html,
)
from .config import OUTPUT_DIR, PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT_MS
from .models import ArticleMetadata, CrawlItem, CrawlResult

logger = logging.getLogger("news_crawler.crawler")


class NewsCrawlerBot:
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir

    async def crawl(
        self,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        instruction: Optional[str] = None,
        browser_mode: str = "bundled",
        cdp_url: Optional[str] = None,
        headless: Optional[bool] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        job_id: Optional[str] = None,
    ) -> CrawlResult:
        job_id = job_id or str(uuid.uuid4())
        job_dir = self.output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = job_dir / "screenshot.png"
        html_path = job_dir / "page.html"
        article_path = job_dir / "article.txt"
        metadata_path = job_dir / "metadata.json"
        items_root = job_dir / "items"
        items_root.mkdir(parents=True, exist_ok=True)

        def emit(message: str) -> None:
            logger.info(message)
            if log_callback:
                log_callback(message)

        async with async_playwright() as p:
            emit(f"Starting browser mode: {browser_mode}")
            browser = await self._launch_browser(p, browser_mode, cdp_url, headless)
            use_existing_context = browser_mode == "cdp" and bool(browser.contexts)
            context = browser.contexts[0] if use_existing_context else await browser.new_context(
                viewport={"width": 1366, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            context.set_default_timeout(PLAYWRIGHT_TIMEOUT_MS)
            page = await context.new_page()
            try:
                emit(f"Opening URL: {url}")
                await page.goto(url, wait_until="domcontentloaded")
                await self._wait_for_page_settle(page, emit)
                emit(f"Loaded page: {page.url}")

                if username and password:
                    emit("Credentials provided. Checking login flow.")
                    await self._login_if_needed(page, url, username, password, emit)
                else:
                    emit("No credentials provided. Skipping login.")

                targets = await self._prepare_targets(page, instruction, emit)
                emit(f"Prepared {len(targets)} target item(s) for extraction.")

                items: list[CrawlItem] = []
                for idx, target_url in enumerate(targets, start=1):
                    item_dir = items_root / f"item_{idx:03d}"
                    item_dir.mkdir(parents=True, exist_ok=True)
                    item_screenshot_path = item_dir / "screenshot.png"
                    item_html_path = item_dir / "page.html"
                    item_article_path = item_dir / "content.txt"
                    item_metadata_path = item_dir / "metadata.json"

                    try:
                        emit(f"[item {idx}/{len(targets)}] Opening target: {target_url}")
                        if page.url != target_url:
                            await self._goto_for_item(page, target_url, emit, idx, len(targets))

                        emit(f"[item {idx}/{len(targets)}] Capturing screenshot.")
                        await page.screenshot(path=str(item_screenshot_path), full_page=True, timeout=30000)
                        html = await page.content()
                        item_html_path.write_text(html, encoding="utf-8")

                        emit(f"[item {idx}/{len(targets)}] Sending content to LLM.")
                        metadata = await extract_article(
                            url=url,
                            final_url=page.url,
                            html=html,
                            screenshot_path=str(item_screenshot_path),
                            instruction=instruction,
                        )
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        logger.exception("Item extraction failed")
                        emit(f"[item {idx}/{len(targets)}] Failed, saving error metadata and continuing: {exc}")
                        metadata = await self._write_failed_item(
                            source_url=url,
                            target_url=target_url,
                            page=page,
                            screenshot_path=item_screenshot_path,
                            html_path=item_html_path,
                            error=exc,
                        )

                    self._write_outputs(metadata, item_metadata_path, item_article_path)
                    items.append(CrawlItem(
                        item_index=idx,
                        output_dir=str(item_dir),
                        metadata_path=str(item_metadata_path),
                        screenshot_path=str(item_screenshot_path),
                        article_path=str(item_article_path),
                        html_path=str(item_html_path),
                        metadata=metadata,
                    ))
                    emit(f"[item {idx}/{len(targets)}] Saved metadata, screenshot, content, and HTML.")

                    if idx == 1:
                        screenshot_path.write_bytes(item_screenshot_path.read_bytes())
                        html_path.write_text(html, encoding="utf-8")
                        article_path.write_text(metadata.content, encoding="utf-8")

                self._write_manifest(items, metadata_path)
                emit(f"Saved aggregate metadata list with {len(items)} item(s).")

                first_item = items[0] if items else None

                return CrawlResult(
                    job_id=job_id,
                    status="completed" if items else "failed",
                    output_dir=str(job_dir),
                    metadata_path=str(metadata_path),
                    screenshot_path=first_item.screenshot_path if first_item else None,
                    article_path=first_item.article_path if first_item else None,
                    metadata=first_item.metadata if first_item else None,
                    items=items,
                )
            except asyncio.CancelledError:
                emit("Stop requested. Cancelling crawl job.")
                try:
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                except Exception:
                    pass
                raise
            except Exception as exc:
                logger.exception("Crawl failed")
                emit(f"Crawl failed: {exc}")
                try:
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                except Exception:
                    pass
                return CrawlResult(
                    job_id=job_id,
                    status="failed",
                    output_dir=str(job_dir),
                    screenshot_path=str(screenshot_path) if screenshot_path.exists() else None,
                    error=str(exc),
                )
            finally:
                try:
                    await page.close()
                except Exception:
                    pass
                if not use_existing_context:
                    await context.close()
                if browser_mode != "cdp":
                    await browser.close()

    async def _goto_for_item(
        self,
        page: Page,
        target_url: str,
        emit: Callable[[str], None],
        idx: int,
        total: int,
    ) -> None:
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
            await self._wait_for_page_settle(page, emit)
            return
        except Exception as first_exc:
            emit(f"[item {idx}/{total}] First navigation attempt failed: {first_exc}")

        try:
            emit(f"[item {idx}/{total}] Retrying navigation with commit-only wait.")
            await page.goto(target_url, wait_until="commit", timeout=30000)
            await page.wait_for_timeout(3000)
            return
        except Exception as second_exc:
            raise RuntimeError(f"Navigation failed after retry: {second_exc}") from second_exc

    async def _write_failed_item(
        self,
        source_url: str,
        target_url: str,
        page: Page,
        screenshot_path: Path,
        html_path: Path,
        error: Exception,
    ) -> ArticleMetadata:
        try:
            await page.screenshot(path=str(screenshot_path), full_page=True, timeout=15000)
        except Exception:
            pass
        try:
            html = await page.content()
        except Exception:
            html = f"<html><body>Failed to load {target_url}</body></html>"
        html_path.write_text(html, encoding="utf-8")
        error_text = str(error) or repr(error)
        return ArticleMetadata(
            source_url=source_url,
            final_url=target_url,
            title="Extraction failed",
            author=None,
            published_at=None,
            category="error",
            summary=f"Could not extract this item: {error_text[:300]}",
            tags=["error"],
            content=f"Target URL: {target_url}\nError: {error_text}",
            language=None,
            screenshot_path=str(screenshot_path),
        )

    async def _launch_browser(
        self,
        playwright,
        browser_mode: str,
        cdp_url: Optional[str],
        headless: Optional[bool],
    ):
        args = ["--no-sandbox", "--disable-dev-shm-usage"]
        effective_headless = PLAYWRIGHT_HEADLESS if headless is None else headless
        if browser_mode == "cdp":
            if not cdp_url:
                raise ValueError("CDP mode requires cdp_url, for example http://127.0.0.1:9222")
            return await playwright.chromium.connect_over_cdp(cdp_url)
        if browser_mode == "chrome":
            return await playwright.chromium.launch(
                headless=effective_headless,
                channel="chrome",
                args=args,
            )
        try:
            return await playwright.chromium.launch(headless=effective_headless, args=args)
        except Exception:
            logger.warning("Bundled Chromium failed, trying system Chrome")
            return await playwright.chromium.launch(
                headless=effective_headless,
                channel="chrome",
                args=args,
            )

    async def _login_if_needed(
        self,
        page: Page,
        url: str,
        username: str,
        password: str,
        emit: Callable[[str], None],
    ) -> None:
        html = await page.content()
        plan = await plan_login(url, html)
        emit(f"Login plan: {plan.reasoning}")

        has_password_input = await page.locator("input[type='password']").count() > 0
        if not plan.requires_login and not has_password_input:
            emit("Login not required.")
            return

        if plan.login_url and plan.login_url != page.url:
            emit(f"Navigating to login URL: {plan.login_url}")
            await page.goto(plan.login_url, wait_until="domcontentloaded")
            await self._wait_for_page_settle(page, emit)

        if plan.pre_click_selector:
            emit(f"Clicking pre-login selector: {plan.pre_click_selector}")
            await self._try_click(page, plan.pre_click_selector)

        username_selectors = self._selector_candidates(
            plan.username_selector,
            [
                "#email",
                "input[name='email']",
                "input[type='email']",
                "input[autocomplete='username']",
                "input[name*='user']",
                "input[name*='email']",
                "input[id*='user']",
                "input[id*='email']",
                "input[type='text']",
            ],
        )
        password_selectors = self._selector_candidates(
            plan.password_selector,
            [
                "#pass",
                "input[name='pass']",
                "input[type='password']",
                "input[autocomplete='current-password']",
            ],
        )
        submit_selectors = self._selector_candidates(
            plan.submit_selector,
            [
                "button[name='login']",
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Log in')",
                "button:has-text('Login')",
                "button:has-text('Đăng nhập')",
                "button:has-text('Dang nhap')",
                "button:has-text('Sign in')",
            ],
        )

        if "facebook.com" in page.url.lower() and not await self._has_any_selector(page, username_selectors + password_selectors):
            emit("Facebook login inputs not visible; navigating to /login/ fallback.")
            await page.goto("https://www.facebook.com/login/", wait_until="domcontentloaded")
            await self._wait_for_page_settle(page, emit)

        username_selector = await self._fill_first_visible(page, username_selectors, username, "username", emit)
        password_selector = await self._fill_first_visible(page, password_selectors, password, "password", emit)
        emit(f"Login filled using username={username_selector}, password={password_selector}")
        try:
            submit_selector = await self._click_first_visible(page, submit_selectors, "login submit", emit)
            emit(f"Submitted login using selector: {submit_selector}")
        except Exception as exc:
            emit(f"Login submit click failed; pressing Enter in password field. ({exc})")
            await page.locator(password_selector).first.press("Enter", timeout=7000)
        try:
            await page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT_MS)
        except Exception:
            await page.wait_for_timeout(3000)

        if plan.success_indicator_selector:
            try:
                emit(f"Waiting for success indicator: {plan.success_indicator_selector}")
                await page.wait_for_selector(plan.success_indicator_selector, timeout=10000)
            except Exception:
                logger.warning("Success indicator was not found after login")
                emit("Success indicator was not found after login.")

        if page.url != url and plan.login_url:
            emit("Returning to target article URL after login.")
            await page.goto(url, wait_until="domcontentloaded")
            await self._wait_for_page_settle(page, emit)

    async def _try_click(self, page: Page, selector: str) -> None:
        locator = page.locator(selector).first
        await locator.wait_for(state="visible", timeout=10000)
        await locator.click()

    def _selector_candidates(self, preferred: Optional[str], fallbacks: list[str]) -> list[str]:
        selectors: list[str] = []
        if preferred:
            selectors.append(preferred)
        for selector in fallbacks:
            if selector not in selectors:
                selectors.append(selector)
        return selectors

    async def _has_any_selector(self, page: Page, selectors: list[str]) -> bool:
        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    return True
            except Exception:
                continue
        return False

    async def _fill_first_visible(
        self,
        page: Page,
        selectors: list[str],
        value: str,
        label: str,
        emit: Callable[[str], None],
    ) -> str:
        last_error: Exception | None = None
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count() == 0:
                    continue
                emit(f"Filling {label} selector: {selector}")
                await locator.fill(value, timeout=7000)
                return selector
            except Exception as exc:
                last_error = exc
                emit(f"{label} selector failed: {selector} ({exc})")
        raise RuntimeError(f"No usable {label} selector found. Last error: {last_error}")

    async def _click_first_visible(
        self,
        page: Page,
        selectors: list[str],
        label: str,
        emit: Callable[[str], None],
    ) -> str:
        last_error: Exception | None = None
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count() == 0:
                    continue
                emit(f"Clicking {label} selector: {selector}")
                await locator.click(timeout=7000)
                return selector
            except Exception as exc:
                last_error = exc
                emit(f"{label} selector failed: {selector} ({exc})")
        raise RuntimeError(f"No usable {label} selector found. Last error: {last_error}")

    async def _prepare_targets(
        self,
        page: Page,
        instruction: Optional[str],
        emit: Callable[[str], None],
    ) -> list[str]:
        if not instruction or not instruction.strip():
            emit("No detailed instruction to execute before extraction.")
            return [page.url]

        text = instruction.strip()
        text_lower = text.lower()
        emit(f"Instruction: {text}")

        emit("[step 1] Observe current page HTML for LLM planner.")
        current_html = await page.content()
        emit(f"[step 1] Current URL={page.url}; HTML chars={len(current_html)}")

        emit("[step 1b] Calling LLM goal decomposer for multi-topic/quota commands.")
        goal_plan = await decompose_collection_goals(page.url, text, current_html)
        if len(goal_plan.goals) > 1:
            start_url = page.url
            emit(
                f"[step 1b] Decomposed into {len(goal_plan.goals)} independent goal(s). "
                f"Reason: {goal_plan.reasoning}"
            )
            all_targets: list[str] = []
            for goal_idx, goal in enumerate(goal_plan.goals, start=1):
                if page.url != start_url:
                    emit(f"[goal {goal_idx}/{len(goal_plan.goals)}] Returning to start URL: {start_url}")
                    await page.goto(start_url, wait_until="domcontentloaded")
                    await self._wait_for_page_settle(page, emit)

                goal_instruction = goal.instruction.strip() or (
                    f"Collect {goal.target_count} {goal.target_type} item(s)"
                    + (f" about {goal.query}" if goal.query else "")
                )
                emit(
                    f"[goal {goal_idx}/{len(goal_plan.goals)}] "
                    f"count={goal.target_count}, type={goal.target_type}, "
                    f"query={goal.query!r}, navigation_url={goal.navigation_url!r}, "
                    f"instruction={goal_instruction!r}"
                )
                goal_targets = await self._prepare_targets(page, goal_instruction, emit)
                all_targets.extend(goal_targets[: goal.target_count])

            deduped_targets = self._dedupe_keep_order(all_targets)
            emit(
                f"[step 1b] Multi-goal target merge: "
                f"{len(deduped_targets)} unique target URL(s) from {len(all_targets)} collected URL(s)."
            )
            return deduped_targets

        emit("[step 2] Calling LLM planner via 9Router with instruction + current HTML.")
        plan = await plan_crawl(page.url, text, current_html)
        emit(
            "[step 2] LLM plan: "
            f"needs_search={plan.needs_search}, "
            f"navigation_url={plan.navigation_url!r}, "
            f"query={plan.search_query!r}, "
            f"count={plan.target_count}, "
            f"type={plan.target_type}, "
            f"platform={plan.platform_hint}, "
            f"open_each={plan.open_each_result}, "
            f"search_selector={plan.search_box_selector!r}, "
            f"result_selector={plan.result_link_selector!r}. "
            f"Reason: {plan.reasoning}"
        )

        query = plan.search_query if plan.needs_search else None
        requested_count = plan.target_count
        wants_first = any(token in text_lower for token in ("đầu tiên", "dau tien", "first", "top 1", "kết quả 1", "ket qua 1"))
        target_type = (plan.target_type or "").lower()
        platform_hint = (plan.platform_hint or "").lower()
        wants_video = any(token in text_lower for token in ("video", "youtube", "clip", "bài hát", "bai hat", "song", "music", "nhạc", "nhac"))
        wants_video = wants_video or any(token in target_type for token in ("video", "song", "music")) or platform_hint == "youtube"

        if plan.navigation_url and plan.navigation_url != page.url:
            emit(f"[step 3] Navigating to LLM requested URL: {plan.navigation_url}")
            await page.goto(plan.navigation_url, wait_until="domcontentloaded")
            await self._wait_for_page_settle(page, emit)

        if query:
            emit(f"Detected search query: {query}")
            emit(f"Requested item count: {requested_count}")
            if "youtube.com" in page.url.lower() or platform_hint == "youtube":
                search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
                emit(f"[step 3] Opening YouTube search results: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")
                await self._wait_for_page_settle(page, emit)
                targets = await self._select_targets_with_llm(
                    page,
                    text,
                    requested_count,
                    target_type,
                    platform_hint,
                    emit,
                )
                if targets:
                    return targets
                if any(token in target_type for token in ("channel", "profile", "creator", "account")):
                    targets = await self._collect_youtube_channel_urls(page, requested_count, emit)
                    if targets:
                        return targets
                    emit("No YouTube channel targets found; falling back to generic result URLs.")
                    targets = await self._collect_generic_result_urls(page, requested_count, emit)
                    if targets:
                        return targets
                    return [page.url]
                targets = await self._collect_youtube_video_urls(page, requested_count, emit)
                if targets:
                    return targets
                if wants_first or wants_video:
                    await self._open_first_youtube_video(page, emit)
                return [page.url]

            emit("[step 3] Trying to search on current page.")
            if await self._search_current_page(page, query, emit, plan.search_box_selector):
                targets = await self._select_targets_with_llm(
                    page,
                    text,
                    requested_count,
                    target_type,
                    platform_hint,
                    emit,
                )
                if targets:
                    return targets
                targets = await self._collect_generic_result_urls(page, requested_count, emit)
                if targets:
                    return targets
                if wants_first:
                    await self._open_first_generic_result(page, emit)

            emit("[step 3] Search box failed or produced no targets; asking LLM to choose a category/listing link.")
            if await self._open_relevant_navigation_link(page, text, query, emit):
                targets = await self._select_targets_with_llm(
                    page,
                    text,
                    requested_count,
                    target_type,
                    platform_hint,
                    emit,
                )
                if targets:
                    return targets

            if await self._open_direct_search_url(page, query, emit):
                targets = await self._select_targets_with_llm(
                    page,
                    text,
                    requested_count,
                    target_type,
                    platform_hint,
                    emit,
                )
                if targets:
                    return targets
            return [page.url]

        if requested_count > 1 or any(token in target_type for token in ("post", "article", "item", "product", "video")):
            emit("Planner decided no search is needed; selecting target items from current page.")
            targets = await self._select_targets_with_llm(
                page,
                text,
                requested_count,
                target_type,
                platform_hint,
                emit,
            )
            if targets:
                return targets

        emit("Planner decided no search is needed; extracting current page.")
        return [page.url]

    def _dedupe_keep_order(self, urls: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for url in urls:
            if not url or url in seen:
                continue
            seen.add(url)
            out.append(url)
        return out

    async def _select_targets_with_llm(
        self,
        page: Page,
        instruction: str,
        count: int,
        target_type: str,
        platform_hint: str,
        emit: Callable[[str], None],
    ) -> list[str]:
        emit("[step 4] Observe result/list page HTML for LLM target selection.")
        html = await page.content()
        emit(f"[step 4] Result URL={page.url}; HTML chars={len(html)}")
        emit("[step 5] Sending result/list HTML to LLM target selector.")
        selection = await select_targets_from_html(
            url=page.url,
            instruction=instruction,
            html=html,
            target_count=count,
            target_type=target_type,
            platform_hint=platform_hint,
        )
        emit(
            "[step 5] LLM target selection: "
            f"urls={len(selection.target_urls)}, "
            f"selector={selection.result_link_selector!r}, "
            f"open_each={selection.should_open_each}. "
            f"Reason: {selection.reasoning}"
        )

        urls = self._normalize_target_urls(selection.target_urls, page.url, count)
        if selection.result_link_selector:
            selector_urls = await self._collect_urls_by_selector(page, selection.result_link_selector, count, emit)
            urls = self._normalize_target_urls(urls + selector_urls, page.url, count)
            if selector_urls:
                emit(f"[step 5] Added URLs via LLM selector; total target URLs now {len(urls)}/{count}.")

        if len(urls) < count and platform_hint == "youtube":
            if any(token in target_type for token in ("channel", "profile", "creator", "account")):
                fallback_urls = await self._collect_youtube_channel_urls(page, count, emit)
            else:
                fallback_urls = await self._collect_youtube_video_urls(page, count, emit)
            urls = self._normalize_target_urls(urls + fallback_urls, page.url, count)
            if fallback_urls:
                emit(f"[step 5] Supplemented with YouTube DOM URLs; total target URLs now {len(urls)}/{count}.")

        if len(urls) < count and platform_hint == "facebook":
            fallback_urls = await self._collect_facebook_post_urls(page, count, emit)
            urls = self._normalize_target_urls(urls + fallback_urls, page.url, count)
            if fallback_urls:
                emit(f"[step 5] Supplemented with Facebook DOM post URLs; total target URLs now {len(urls)}/{count}.")

        if platform_hint == "facebook" and any(token in target_type for token in ("post", "article")):
            if urls:
                emit(f"[step 5] Facebook post mode: using {len(urls)} verified post URL(s), not padding with non-post links.")
                return urls
            emit("[step 5] Facebook post mode: no verified post URLs found.")
            return []

        is_article_mode = any(token in target_type for token in ("article", "news"))
        if is_article_mode:
            before_filter = len(urls)
            urls = self._filter_article_target_urls(urls, page.url, count)
            if before_filter != len(urls):
                emit(f"[step 5] Filtered selector URLs to {len(urls)} same-site article URL(s).")

        if any(token in target_type for token in ("article", "news", "post")):
            if len(urls) < count:
                fallback_urls = await self._collect_news_article_urls(page, count, emit)
                urls = self._normalize_target_urls(urls + fallback_urls, page.url, count)
                if is_article_mode:
                    urls = self._filter_article_target_urls(urls, page.url, count)
                if fallback_urls:
                    emit(f"[step 5] Supplemented with article DOM URLs; total target URLs now {len(urls)}/{count}.")
            if urls:
                emit(f"[step 5] Article mode: using {len(urls)} verified article URL(s), not padding with navigation links.")
                return urls
            emit("[step 5] Article mode: no verified article URLs found.")
            return []

        if len(urls) < count:
            fallback_urls = await self._collect_generic_result_urls(page, count, emit)
            urls = self._normalize_target_urls(urls + fallback_urls, page.url, count)
            if fallback_urls:
                emit(f"[step 5] Supplemented with generic DOM URLs; total target URLs now {len(urls)}/{count}.")

        if urls:
            emit(f"[step 5] Using {len(urls)} final target URL(s).")
            return urls
        return []

    def _normalize_target_urls(self, urls: list[str], base_url: str, count: int) -> list[str]:
        from urllib.parse import parse_qs, urljoin, urldefrag, urlparse

        out: list[str] = []
        seen: set[str] = set()
        for raw in urls:
            if not raw:
                continue
            absolute = urljoin(base_url, raw)
            absolute = urldefrag(absolute)[0]
            parsed = urlparse(absolute)
            if parsed.netloc.endswith("youtube.com") and parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [None])[0]
                if video_id:
                    absolute = f"https://www.youtube.com/watch?v={video_id}"
            elif parsed.netloc.endswith("youtube.com") and (
                parsed.path.startswith("/@")
                or parsed.path.startswith("/channel/")
                or parsed.path.startswith("/c/")
            ):
                absolute = f"https://www.youtube.com{parsed.path.rstrip('/')}"
            elif parsed.netloc.endswith("facebook.com") and "/posts/" in parsed.path:
                absolute = f"https://www.facebook.com{parsed.path.rstrip('/')}"
            elif parsed.netloc.endswith("facebook.com") and "/permalink/" in parsed.path:
                absolute = f"https://www.facebook.com{parsed.path.rstrip('/')}"

            if absolute.startswith(("http://", "https://")) and absolute not in seen:
                seen.add(absolute)
                out.append(absolute)
            if len(out) >= count:
                break
        return out

    def _filter_article_target_urls(self, urls: list[str], base_url: str, count: int) -> list[str]:
        from urllib.parse import urlparse

        base = urlparse(base_url)
        base_host = base.hostname or ""
        out: list[str] = []
        seen: set[str] = set()
        blocked_hosts = (
            "doubleclick.",
            "googlesyndication.",
            "googleadservices.",
            "adservice.",
            "eclick.",
            "admicro.",
            "adtima.",
        )
        blocked_paths = (
            "/web_click",
            "/click",
            "/ad/",
            "/ads/",
            "/banner",
        )
        for url in urls:
            parsed = urlparse(url)
            host = parsed.hostname or ""
            path = parsed.path.lower()
            if not host:
                continue
            if host != base_host and not host.endswith("." + base_host):
                continue
            if any(blocked in host for blocked in blocked_hosts):
                continue
            if any(path.startswith(blocked) or blocked in path for blocked in blocked_paths):
                continue
            if not path.endswith(".html"):
                continue
            normalized = url.split("#", 1)[0]
            if normalized in seen:
                continue
            seen.add(normalized)
            out.append(normalized)
            if len(out) >= count:
                break
        return out

    async def _collect_urls_by_selector(
        self,
        page: Page,
        selector: str,
        count: int,
        emit: Callable[[str], None],
    ) -> list[str]:
        try:
            urls = await page.evaluate(
                """({ selector, limit }) => {
                    const anchors = Array.from(document.querySelectorAll(selector));
                    const out = [];
                    const seen = new Set();
                    for (const node of anchors) {
                        const a = node.tagName && node.tagName.toLowerCase() === 'a'
                          ? node
                          : node.closest && node.closest('a[href]');
                        if (!a || !a.href || seen.has(a.href)) continue;
                        seen.add(a.href);
                        out.push(a.href);
                        if (out.length >= limit) break;
                    }
                    return out;
                }""",
                {"selector": selector, "limit": count},
            )
            emit(f"Collected {len(urls)} URL(s) from selector {selector}.")
            return self._normalize_target_urls(urls, page.url, count)
        except Exception as exc:
            emit(f"Failed collecting URLs via LLM selector {selector}: {exc}")
            return []

    async def _open_relevant_navigation_link(
        self,
        page: Page,
        instruction: str,
        query: str,
        emit: Callable[[str], None],
    ) -> bool:
        links = await self._collect_navigation_candidates(page, query, emit)
        if not links:
            emit("[step 3] No navigation/category candidates found.")
            return False
        emit(f"[step 3] Sending {len(links)} navigation/category candidate link(s) to LLM.")
        try:
            choice = await choose_navigation_from_links(
                url=page.url,
                instruction=instruction,
                query=query,
                links=links,
            )
        except Exception as exc:
            emit(f"[step 3] LLM navigation choice failed: {exc}")
            return False

        emit(f"[step 3] LLM navigation choice: {choice.navigation_url!r}. Reason: {choice.reasoning}")
        if not choice.navigation_url:
            return False

        try:
            await page.goto(choice.navigation_url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
            await self._wait_for_page_settle(page, emit)
            return True
        except Exception as exc:
            emit(f"[step 3] Failed to open LLM navigation URL: {exc}")
            return False

    async def _collect_navigation_candidates(
        self,
        page: Page,
        query: str,
        emit: Callable[[str], None],
    ) -> list[dict]:
        try:
            links = await page.evaluate(
                """({ query, limit }) => {
                    const normalize = (value) => (value || '')
                      .toLowerCase()
                      .normalize('NFD')
                      .replace(/[\\u0300-\\u036f]/g, '')
                      .replace(/đ/g, 'd');
                    const queryNorm = normalize(query);
                    const queryTokens = queryNorm.split(/\\s+/).filter((x) => x.length >= 3);
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    const out = [];
                    const seen = new Set();
                    for (const a of anchors) {
                        const text = (a.textContent || a.getAttribute('title') || a.getAttribute('aria-label') || '').trim();
                        const href = new URL(a.getAttribute('href'), location.href).href;
                        if (!text || text.length > 160 || seen.has(href)) continue;
                        const hrefLower = href.toLowerCase();
                        if (hrefLower.includes('/login') || hrefLower.includes('/user') || hrefLower.includes('/account')) continue;
                        const haystack = normalize(`${text} ${a.getAttribute('title') || ''} ${href}`);
                        const inNav = Boolean(a.closest('nav, header, [role="navigation"], .main-nav, .menu, .wrap-all-menu'));
                        const topicHit = queryTokens.length && queryTokens.some((token) => haystack.includes(token));
                        const sectionLike = /\\/(kinh-doanh|the-gioi|thoi-su|giai-tri|the-thao|phap-luat|suc-khoe|giao-duc|du-lich|doi-song|khoa-hoc|bat-dong-san|topic|tag|search|tim-kiem)/.test(hrefLower);
                        if (!inNav && !topicHit && !sectionLike) continue;
                        seen.add(href);
                        out.push({
                            text,
                            title: a.getAttribute('title') || '',
                            href,
                            in_navigation: inNav,
                            topic_hit: Boolean(topicHit),
                        });
                        if (out.length >= limit) break;
                    }
                    return out;
                }""",
                {"query": query, "limit": 80},
            )
            return links
        except Exception as exc:
            emit(f"[step 3] Failed collecting navigation candidates: {exc}")
            return []

    async def _open_direct_search_url(
        self,
        page: Page,
        query: str,
        emit: Callable[[str], None],
    ) -> bool:
        try:
            search_url = await page.evaluate(
                """(query) => {
                    const encode = encodeURIComponent(query);
                    for (const script of Array.from(document.querySelectorAll('script[type="application/ld+json"]'))) {
                        try {
                            const data = JSON.parse(script.textContent || '{}');
                            const items = Array.isArray(data) ? data : [data];
                            for (const item of items) {
                                const action = item && item.potentialAction;
                                const target = action && action.target;
                                const raw = typeof target === 'string' ? target : target && target.urlTemplate;
                                if (raw && raw.includes('{search_term_string}')) {
                                    return raw.replace('{search_term_string}', encode);
                                }
                            }
                        } catch {}
                    }
                    const form = document.querySelector('form[action*="timkiem"], form[action*="search"], form[action]');
                    if (form) {
                        const action = new URL(form.getAttribute('action') || location.href, location.href);
                        const input = form.querySelector('input[name]') || { name: 'q' };
                        action.searchParams.set(input.name || 'q', query);
                        return action.href;
                    }
                    return null;
                }""",
                query,
            )
        except Exception as exc:
            emit(f"[step 3] Failed resolving direct search URL: {exc}")
            return False

        if not search_url:
            emit("[step 3] No direct search URL found in page metadata/forms.")
            return False
        try:
            emit(f"[step 3] Opening direct search URL from page metadata/form: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
            await self._wait_for_page_settle(page, emit)
            return True
        except Exception as exc:
            emit(f"[step 3] Direct search URL failed: {exc}")
            return False

    async def _search_current_page(
        self,
        page: Page,
        query: str,
        emit: Callable[[str], None],
        preferred_selector: Optional[str] = None,
    ) -> bool:
        selectors = []
        if preferred_selector:
            selectors.append(preferred_selector)
        selectors += [
            "input[type='search']",
            "[role='searchbox']",
            "[contenteditable='true'][role='textbox']",
            "input[name='search_query']",
            "input[name='q']",
            "input[aria-label*='Search']",
            "input[aria-label*='Tìm']",
            "input[placeholder*='Search']",
            "input[placeholder*='Search']",
            "input[placeholder*='Tìm']",
            "textarea[name='q']",
            "textarea[aria-label*='Search']",
            "textarea[placeholder*='Search']",
        ]
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if await locator.count() == 0:
                    continue
                emit(f"Filling search selector: {selector}")
                await locator.fill(query, timeout=5000)
                await locator.press("Enter", timeout=5000)
                await self._wait_for_page_settle(page, emit)
                return True
            except Exception as exc:
                emit(f"Search selector failed: {selector} ({exc})")
        emit("No usable search box found on current page.")
        return False

    async def _open_first_youtube_video(self, page: Page, emit: Callable[[str], None]) -> None:
        try:
            emit("Waiting for YouTube video results to appear.")
            await page.locator("a[href*='/watch?v=']").first.wait_for(state="visible", timeout=20000)
        except Exception as exc:
            emit(f"YouTube video links were not visible yet: {exc}")

        selectors = [
            "ytd-video-renderer a#video-title",
            "a#video-title",
            "ytd-rich-item-renderer a#video-title-link",
            "a[href*='/watch?v=']",
        ]
        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = await locator.count()
                emit(f"YouTube first-result selector {selector}: {count} matches")
                if count == 0:
                    continue
                await locator.first.click(timeout=12000)
                await page.wait_for_load_state("domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
                await self._wait_for_page_settle(page, emit)
                emit(f"Opened first YouTube video: {page.url}")
                return
            except Exception as exc:
                emit(f"Failed to open first YouTube result via {selector}: {exc}")
        emit("Could not open first YouTube video; extracting search results page instead.")

    async def _collect_youtube_video_urls(
        self,
        page: Page,
        count: int,
        emit: Callable[[str], None],
    ) -> list[str]:
        try:
            emit("Waiting for YouTube video links to collect target items.")
            await page.locator("a[href*='/watch?v=']").first.wait_for(state="visible", timeout=20000)
        except Exception as exc:
            emit(f"YouTube links not ready for collection: {exc}")
            return []

        urls = await page.evaluate(
            """(limit) => {
                const anchors = Array.from(document.querySelectorAll("ytd-video-renderer a#video-title, a#video-title, a[href*='/watch?v=']"));
                const out = [];
                const seen = new Set();
                for (const a of anchors) {
                    const href = a.href;
                    if (!href || seen.has(href)) continue;
                    if (!href.includes('/watch?v=')) continue;
                    const parsed = new URL(href, location.href);
                    const videoId = parsed.searchParams.get('v');
                    if (!videoId || seen.has(videoId)) continue;
                    const title = (a.textContent || '').trim();
                    const insideVideo = Boolean(a.closest('ytd-video-renderer'));
                    if (!title && !insideVideo) continue;
                    seen.add(videoId);
                    out.push(`https://www.youtube.com/watch?v=${videoId}`);
                    if (out.length >= limit) break;
                }
                return out;
            }""",
            count,
        )
        emit(f"Collected {len(urls)} YouTube target URL(s).")
        return urls

    async def _collect_youtube_channel_urls(
        self,
        page: Page,
        count: int,
        emit: Callable[[str], None],
    ) -> list[str]:
        try:
            emit("Waiting for YouTube channel/profile links to collect target items.")
            await page.locator("a[href^='/@'], a[href*='/channel/'], a[href*='/c/']").first.wait_for(state="visible", timeout=20000)
        except Exception as exc:
            emit(f"YouTube channel/profile links were not visible yet: {exc}")

        urls = await page.evaluate(
            """(limit) => {
                const anchors = Array.from(document.querySelectorAll("ytd-channel-renderer a[href], a[href^='/@'], a[href*='/channel/'], a[href*='/c/']"));
                const out = [];
                const seen = new Set();
                for (const a of anchors) {
                    const href = a.href || '';
                    if (!href) continue;
                    const url = new URL(href, location.href);
                    const path = url.pathname;
                    const isChannel = path.startsWith('/@') || path.startsWith('/channel/') || path.startsWith('/c/');
                    if (!isChannel) continue;
                    const normalized = `${url.origin}${path}`;
                    if (seen.has(normalized)) continue;
                    const text = (a.textContent || '').trim();
                    const insideChannel = Boolean(a.closest('ytd-channel-renderer'));
                    if (!text && !insideChannel) continue;
                    seen.add(normalized);
                    out.push(normalized);
                    if (out.length >= limit) break;
                }
                return out;
            }""",
            count,
        )
        emit(f"Collected {len(urls)} YouTube channel/profile target URL(s).")
        return urls

    async def _collect_news_article_urls(
        self,
        page: Page,
        count: int,
        emit: Callable[[str], None],
    ) -> list[str]:
        urls = await page.evaluate(
            """(limit) => {
                const anchors = Array.from(document.querySelectorAll(
                    [
                      'main article a[href]',
                      'article.item-news a[href]',
                      '.item-news .title-news a[href]',
                      '.title-news a[href]',
                      'h1 a[href]',
                      'h2 a[href]',
                      'h3 a[href]',
                      'article a[href]'
                    ].join(',')
                ));
                const out = [];
                const seen = new Set();
                for (const a of anchors) {
                    const href = a.href || '';
                    const title = (a.textContent || a.getAttribute('title') || '').trim();
                    if (!href || seen.has(href)) continue;
                    const url = new URL(href, location.href);
                    if (url.hostname !== location.hostname && !url.hostname.endsWith('.' + location.hostname)) continue;
                    if (url.hash || url.href.includes('#box_comment')) continue;
                    if (!/\\.html($|[?#])/.test(url.href)) continue;
                    if (title.length < 8 && !a.closest('article')) continue;
                    url.hash = '';
                    const normalized = url.href;
                    if (seen.has(normalized)) continue;
                    seen.add(normalized);
                    out.push(normalized);
                    if (out.length >= limit) break;
                }
                return out;
            }""",
            count,
        )
        emit(f"Collected {len(urls)} article target URL(s).")
        return urls

    async def _collect_facebook_post_urls(
        self,
        page: Page,
        count: int,
        emit: Callable[[str], None],
    ) -> list[str]:
        selector = "a[href*='/posts/'], a[href*='/permalink/']"
        for attempt in range(4):
            try:
                emit(f"Waiting for Facebook post links to collect target items (pass {attempt + 1}).")
                await page.locator(selector).first.wait_for(state="attached", timeout=8000)
            except Exception as exc:
                emit(f"Facebook post links were not visible yet on pass {attempt + 1}: {exc}")
            urls = await self._collect_facebook_post_urls_once(page, count)
            if len(self._normalize_target_urls(urls, page.url, count)) >= count:
                break
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(1800)

        urls = await self._collect_facebook_post_urls_once(page, count)
        emit(f"Collected {len(urls)} Facebook post target URL(s).")
        return urls

    async def _collect_facebook_post_urls_once(self, page: Page, count: int) -> list[str]:
        return await page.evaluate(
            """(limit) => {
                const anchors = Array.from(document.querySelectorAll("a[href*='/posts/'], a[href*='/permalink/']"));
                const out = [];
                const seen = new Set();
                for (const a of anchors) {
                    const href = a.href || '';
                    if (!href) continue;
                    const url = new URL(href, location.href);
                    if (!url.hostname.endsWith('facebook.com')) continue;
                    const isPost = url.pathname.includes('/posts/') || url.pathname.includes('/permalink/');
                    if (!isPost) continue;
                    url.search = '';
                    url.hash = '';
                    const normalized = url.toString().replace(/\\/$/, '');
                    if (seen.has(normalized)) continue;
                    seen.add(normalized);
                    out.push(normalized);
                    if (out.length >= limit) break;
                }
                return out;
            }""",
            count,
        )

    async def _collect_generic_result_urls(
        self,
        page: Page,
        count: int,
        emit: Callable[[str], None],
    ) -> list[str]:
        urls = await page.evaluate(
            """(limit) => {
                const anchors = Array.from(document.querySelectorAll("main a[href], article a[href], a[href]"));
                const out = [];
                const seen = new Set();
                for (const a of anchors) {
                    const href = a.href;
                    const text = (a.textContent || '').trim();
                    if (!href || seen.has(href)) continue;
                    if (href.startsWith('javascript:') || href.includes('#')) continue;
                    if (text.length < 8) continue;
                    seen.add(href);
                    out.push(href);
                    if (out.length >= limit) break;
                }
                return out;
            }""",
            count,
        )
        emit(f"Collected {len(urls)} generic target URL(s).")
        return urls

    async def _open_first_generic_result(self, page: Page, emit: Callable[[str], None]) -> None:
        selectors = [
            "main a[href]",
            "article a[href]",
            "a[href]",
        ]
        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = await locator.count()
                emit(f"Generic first-result selector {selector}: {count} matches")
                if count == 0:
                    continue
                await locator.first.click(timeout=10000)
                await page.wait_for_load_state("domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
                await self._wait_for_page_settle(page, emit)
                emit(f"Opened first result: {page.url}")
                return
            except Exception as exc:
                emit(f"Failed to open first generic result via {selector}: {exc}")

    async def _wait_for_page_settle(self, page: Page, emit: Callable[[str], None]) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            emit("Page did not reach networkidle quickly; continuing with current DOM.")
            await page.wait_for_timeout(2500)

    def _write_outputs(self, metadata: ArticleMetadata, metadata_path: Path, article_path: Path) -> None:
        metadata_path.write_text(
            json.dumps(metadata.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        article_path.write_text(metadata.content, encoding="utf-8")

    def _write_manifest(self, items: list[CrawlItem], metadata_path: Path) -> None:
        payload = {
            "count": len(items),
            "items": [item.model_dump() for item in items],
        }
        metadata_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
