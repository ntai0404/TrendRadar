import json
import logging

from .html_utils import (
    compact_html,
    extract_metadata_hints,
    heuristic_article_text,
    merge_metadata_hints,
    page_title,
)
from .llm_client import ask_json
from .models import (
    ArticleMetadata,
    CollectionGoal,
    CollectionGoalPlan,
    CrawlPlan,
    LoginPlan,
    NavigationChoice,
    TargetSelectionPlan,
)
from .skill_loader import load_runtime_skill

logger = logging.getLogger("news_crawler.agent")


async def plan_login(url: str, html: str) -> LoginPlan:
    prompt = f"""
You are controlling Playwright for a news website.
Decide whether this page requires login before the article can be read.
If login is needed, infer robust CSS selectors for username, password and submit.

URL: {url}

HTML sample:
{compact_html(html, limit=25000)}
"""
    try:
        data = await ask_json(
            prompt,
            LoginPlan,
            system="You are a careful browser automation planner. Prefer stable CSS selectors.",
        )
        return LoginPlan(**data)
    except Exception as exc:
        logger.warning("LLM login planning failed: %s", exc)
        return LoginPlan(
            requires_login=False,
            reasoning=f"LLM login planning failed, continuing without login: {exc}",
        )


async def plan_crawl(url: str, instruction: str | None, html: str | None = None) -> CrawlPlan:
    user_instruction = instruction.strip() if instruction else ""
    html_sample = compact_html(html or "", limit=50000, keep_navigation=True) if html else "No HTML sample provided."
    runtime_skill = load_runtime_skill(url)
    prompt = f"""
You are a browser-crawling planner for a multi-platform web scraper.
Convert the user's Vietnamese/English natural-language command into a browser execution plan.

Runtime crawler skills:
{runtime_skill or "No additional runtime skill."}

Important:
- Do not extract content. Only decide what the browser should do before extraction.
- Support many platforms, not only YouTube: Facebook, Instagram, TikTok, X/Twitter, news sites, search pages, product sites, forums, and generic websites.
- If the user asks for information "about" a topic, song, person, post, video, product, page, hashtag, or keyword and the current URL is a searchable platform/homepage, set needs_search=true.
- If the instruction contains a specific URL for a group/page/profile/article/listing, put it in navigation_url and plan from that page after login.
- Preserve the user's intended query. Fix only obvious surrounding command words; do not over-normalize names.
- If the user says "N results/items/videos/posts/articles" or "N ... first", target_count must be N.
- If the user asks for plural latest/newest posts/items/articles without a number, target_count=5.
- If no count is stated, target_count=1.
- If the user asks for multiple items, open_each_result=true so the crawler can produce one metadata/screenshot/content set per item.
- platform_hint should be inferred from URL/instruction when possible, otherwise "generic".
- You are given the current observed HTML. Use it to infer whether the page has a search box, a homepage shell, a results page, a profile page, or a detail page.
- For news sites, if the observed navigation/menu contains a topic or category matching the user's requested topic, prefer navigation_url to that category/listing page over site search.
- If a search box is visible, provide a robust search_box_selector.
- If result/item links are visible, provide result_link_selector.

Current URL: {url}
User instruction: {user_instruction or "No extra instruction."}
Observed HTML sample:
{html_sample}

Examples:
Instruction: "Lấy thông tin về bài hát beaty and a beat"
Plan: needs_search=true, search_query="beaty and a beat", target_count=1, target_type="song_or_video", open_each_result=true

Instruction: "Lấy thông tin về kênh ping lê"
Plan: needs_search=true, search_query="ping lê", target_count=1, target_type="channel_or_profile", open_each_result=true

Instruction: "Lấy nội dung của 10 video đầu tiên của từ khóa 'anh là thằng tôi'"
Plan: needs_search=true, search_query="anh là thằng tôi", target_count=10, target_type="video", open_each_result=true

Instruction: "Cào 5 bài post mới nhất về OpenAI trên Facebook"
Plan: needs_search=true, search_query="OpenAI", target_count=5, target_type="post", open_each_result=true

Instruction: "Lay du lieu cac bai viet moi nhat cua group https://www.facebook.com/groups/comailo"
Plan: navigation_url="https://www.facebook.com/groups/comailo", needs_search=false, search_query=null, target_count=5, target_type="post", open_each_result=true, platform_hint="facebook"

Instruction: "Trích metadata trang hiện tại"
Plan: needs_search=false, search_query=null, target_count=1, target_type="web_page", open_each_result=false
"""
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            data = await ask_json(
                prompt,
                CrawlPlan,
                system="You produce strict JSON crawl plans for browser automation. Return only schema-valid JSON.",
                temperature=0.0,
            )
            plan = CrawlPlan(**data)
            if plan.target_count < 1:
                plan.target_count = 1
            if plan.target_count > 20:
                plan.target_count = 20
            return plan
        except Exception as exc:
            last_error = exc
            logger.warning("LLM crawl planning failed on attempt %s: %s", attempt + 1, exc)

    raise RuntimeError(f"LLM crawl planner failed after retries: {last_error}")


async def decompose_collection_goals(
    url: str,
    instruction: str | None,
    html: str | None = None,
) -> CollectionGoalPlan:
    user_instruction = instruction.strip() if instruction else ""
    runtime_skill = load_runtime_skill(url)
    html_sample = compact_html(html or "", limit=30000, keep_navigation=True) if html else "No HTML sample provided."
    prompt = f"""
You are a workflow decomposer for a multi-item web crawler.
Decide whether the user's command contains multiple independent collection goals that must be crawled separately.

Runtime crawler skills:
{runtime_skill or "No additional runtime skill."}

Rules:
- Split only when the command asks for separate quotas, separate topics, or separate sources, e.g. "5 articles about stocks and 5 articles about AI".
- Do not combine independent topics into one search query.
- Preserve each quota exactly. If a topic has no explicit count but plural items are requested, use 5.
- If there is only one topic/source/task, return one goal matching the original instruction.
- Each goal must be executable as a standalone crawler instruction.
- For news/article requests, target_type="article"; for social group posts, target_type="post"; for YouTube videos, target_type="video".
- If the user gives a direct URL for a group/page/category/listing, put it in navigation_url for that goal.

Current URL: {url}
User instruction: {user_instruction or "No extra instruction."}
Observed HTML sample:
{html_sample}

Examples:
Instruction: "cào 5 bài về chứng khoán 5 bài về AI"
Goals:
[
  {{"query":"chứng khoán","target_count":5,"target_type":"article","instruction":"Cào 5 bài về chứng khoán"}},
  {{"query":"AI","target_count":5,"target_type":"article","instruction":"Cào 5 bài về AI"}}
]

Instruction: "lấy thông tin 10 bài mới về chứng khoán"
Goals:
[
  {{"query":"chứng khoán","target_count":10,"target_type":"article","instruction":"Lấy thông tin 10 bài mới về chứng khoán"}}
]
"""
    try:
        data = await ask_json(
            prompt,
            CollectionGoalPlan,
            system="You decompose crawler instructions into independent collection goals. Return only schema-valid JSON.",
            temperature=0.0,
        )
        plan = CollectionGoalPlan(**data)
        cleaned: list[CollectionGoal] = []
        for goal in plan.goals:
            if goal.target_count < 1:
                goal.target_count = 1
            if goal.target_count > 20:
                goal.target_count = 20
            if not goal.instruction.strip():
                goal.instruction = user_instruction
            cleaned.append(goal)
        plan.goals = cleaned[:5]
        return plan
    except Exception as exc:
        logger.warning("LLM collection-goal decomposition failed: %s", exc)
        return CollectionGoalPlan(
            goals=[CollectionGoal(query=None, target_count=1, instruction=user_instruction)],
            reasoning=f"Decomposition failed, using original instruction: {exc}",
        )


async def select_targets_from_html(
    url: str,
    instruction: str | None,
    html: str,
    target_count: int,
    target_type: str,
    platform_hint: str | None = None,
) -> TargetSelectionPlan:
    user_instruction = instruction.strip() if instruction else ""
    runtime_skill = load_runtime_skill(url, platform_hint)
    prompt = f"""
You are selecting target items from an observed web page for a crawler.
Analyze the current HTML and return the exact target URLs or a CSS selector for target links.

Runtime crawler skills:
{runtime_skill or "No additional runtime skill."}

Rules:
- Use the user's instruction as the main goal.
- Return up to {target_count} target URLs, ordered by relevance/position.
- Prefer detail URLs for the requested target type: video URLs for videos, channel/profile URLs for channels/profiles, post URLs for posts, article URLs for articles, product URLs for products.
- If exact URLs are present in HTML, return them in target_urls.
- If URLs are not directly recoverable but a selector is clear, return result_link_selector.
- Do not return homepage/navigation/login/footer URLs.
- Do not invent URLs.

Current URL: {url}
Platform hint: {platform_hint or "generic"}
Target type: {target_type}
User instruction: {user_instruction or "No extra instruction."}

Observed HTML sample:
{compact_html(html, limit=45000)}
"""
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            data = await ask_json(
                prompt,
                TargetSelectionPlan,
                system="You select crawl target URLs from observed HTML. Return only schema-valid JSON.",
                temperature=0.0,
            )
            plan = TargetSelectionPlan(**data)
            plan.target_urls = plan.target_urls[: max(1, min(target_count, 20))]
            return plan
        except Exception as exc:
            last_error = exc
            logger.warning("LLM target selection failed on attempt %s: %s", attempt + 1, exc)

    raise RuntimeError(f"LLM target selector failed after retries: {last_error}")


async def choose_navigation_from_links(
    url: str,
    instruction: str | None,
    query: str | None,
    links: list[dict],
) -> NavigationChoice:
    user_instruction = instruction.strip() if instruction else ""
    runtime_skill = load_runtime_skill(url)
    prompt = f"""
You are choosing the next navigation URL for a crawler.
The current page could be a homepage with menu/category/search links.
Pick the best category, topic, listing, or search-results URL before the crawler selects individual items.

Runtime crawler skills:
{runtime_skill or "No additional runtime skill."}

Rules:
- Prefer a category/topic/listing URL that directly matches the user's requested topic.
- For a news site, prefer the site's own category page over generic homepage extraction.
- If no useful category/listing/search URL exists, return navigation_url=null.
- Do not pick login, account, ads, footer-only, or unrelated links.

Current URL: {url}
User instruction: {user_instruction or "No extra instruction."}
Search/topic query: {query or ""}
Candidate links:
{json.dumps(links[:80], ensure_ascii=False, indent=2)}
"""
    data = await ask_json(
        prompt,
        NavigationChoice,
        system="You choose one navigation URL for browser automation. Return only schema-valid JSON.",
        temperature=0.0,
    )
    return NavigationChoice(**data)


async def extract_article(
    url: str,
    final_url: str,
    html: str,
    screenshot_path: str,
    instruction: str | None = None,
) -> ArticleMetadata:
    fallback_title = page_title(html)
    fallback_text = heuristic_article_text(html)
    metadata_hints = extract_metadata_hints(html, final_url)
    user_instruction = instruction.strip() if instruction else "No extra user instruction."
    runtime_skill = load_runtime_skill(final_url)
    prompt = f"""
You are a general-purpose web content extraction agent.
Your job is to extract the most important user-requested content from the FINAL page, not from a menu, login prompt, homepage shell, or unrelated recommendation block.

Runtime crawler skills:
{runtime_skill or "No additional runtime skill."}

Extraction rules:
1. First infer the page type from the final URL and HTML: article/news, video, search result, product/detail page, profile, forum post, document page, or generic web page.
2. Follow the user's extra instruction as the priority signal. If the instruction asks for a specific item, result, video, record, table row, product, or article, extract that target only.
3. Metadata must be extracted before prose content. Use this priority order:
   - JSON-LD/schema.org fields: headline/name, author/creator/channel, publisher, datePublished, dateModified, uploadDate, articleSection, keywords.
   - OpenGraph/Twitter/article meta fields: og:title, article:author, article:published_time, article:modified_time, article:section, article:tag, keywords, og:site_name.
   - Visible semantic HTML: h1, byline, time[datetime], itemprop=datePublished/dateModified, category breadcrumbs, visible tags.
   - Only then infer safe generic values from the visible page text.
4. Fill the output schema in a natural way for the page type:
   - title: primary title/name/headline of the target item.
   - author: author, source, channel, creator, organization, seller, or publisher when visible.
   - published_at: publication/upload/update date from JSON-LD/meta/time tags when present; preserve the original ISO/string value.
   - category: section, topic, product category, or page type when useful.
   - summary: concise 1-3 sentence summary in the content's language.
   - tags: visible tags or inferred keywords directly supported by the page.
   - content: the cleaned main useful text, details, description, transcript-like visible text, table data, or body content of the target.
5. Remove boilerplate: navigation, sidebars, ads, cookie banners, comments, unrelated recommendations, repeated labels, footer text, login hints, and generic site guidance.
6. If the final page is still a search/home/listing page and no specific target was opened, extract the most relevant visible result list instead of pretending it is an article.
7. If a field is not visible or cannot be inferred safely, use null or an empty list. Do not invent dates, authors, or facts.
8. Keep the original language of the page content.

High-confidence metadata hints extracted from HTML standards.
Use these values unless the final page visibly contradicts them:
{json.dumps(metadata_hints, ensure_ascii=False, indent=2)}

User instruction:
{user_instruction}

Source URL: {url}
Final URL: {final_url}
Screenshot path: {screenshot_path}
Fallback title: {fallback_title}
Fallback visible text:
{fallback_text[:18000]}

HTML sample:
{compact_html(html, limit=40000)}
"""
    try:
        data = await ask_json(
            prompt,
            ArticleMetadata,
            system="You extract web page content into strict structured JSON. Return only schema-valid JSON.",
        )
        data.setdefault("source_url", url)
        data.setdefault("final_url", final_url)
        data.setdefault("screenshot_path", screenshot_path)
        return merge_metadata_hints(ArticleMetadata(**data), metadata_hints)
    except Exception as exc:
        logger.warning("LLM article extraction failed, using heuristic fallback: %s", exc)
        return merge_metadata_hints(ArticleMetadata(
            source_url=url,
            final_url=final_url,
            title=fallback_title,
            summary=(fallback_text[:350] + "...") if len(fallback_text) > 350 else fallback_text,
            content=fallback_text or "Article extraction failed.",
            tags=[],
            screenshot_path=screenshot_path,
        ), metadata_hints)
