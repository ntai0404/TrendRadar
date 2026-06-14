# coding=utf-8
"""
Notification dispatcher module

Provides a unified notification distribution interface.
Supports multi-account configuration for all notification channels, using `;` to separate multiple accounts.

Usage example:
    dispatcher = NotificationDispatcher(config, get_time_func, split_content_func)
    results = dispatcher.dispatch_all(report_data, report_type, ...)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from trendradar.core.config import (
    get_account_at_index,
    limit_accounts,
    parse_multi_account_config,
    validate_paired_configs,
)

from .senders import (
    send_to_bark,
    send_to_dingtalk,
    send_to_email,
    send_to_feishu,
    send_to_ntfy,
    send_to_slack,
    send_to_telegram,
    send_to_wework,
    send_to_generic_webhook,
)


# Import during type checking, do not import at runtime (to avoid circular imports)
if TYPE_CHECKING:
    from trendradar.ai import AIAnalysisResult, AITranslator


class NotificationDispatcher:
    """
    Unified multi-account notification dispatcher

    Encapsulates multi-account sending logic, providing a concise dispatch_all interface.
    Internally handles account parsing, quantity limits, pairing verification, and other logic.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        get_time_func: Callable,
        split_content_func: Callable,
        translator: Optional["AITranslator"] = None,
    ):
        """
        Initialize the notification dispatcher

        Args:
            config: Complete configuration dictionary, containing configurations for all notification channels
            get_time_func: Function to get the current time
            split_content_func: Content batching function
            translator: AI translator instance (optional)
        """
        self.config = config
        self.get_time_func = get_time_func
        self.split_content_func = split_content_func
        self.max_accounts = config.get("MAX_ACCOUNTS_PER_CHANNEL", 3)
        self.translator = translator

    def translate_content(
        self,
        report_data: Dict,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        standalone_data: Optional[Dict] = None,
        display_regions: Optional[Dict] = None,
        skip_rss: bool = False,
    ) -> tuple:
        """
        Translate push content

        Args:
            report_data: Report data
            rss_items: RSS statistics items
            rss_new_items: RSS new items
            standalone_data: Standalone display area data
            display_regions: Region display configuration (skip translation for undisplayed regions)
            skip_rss: Skip RSS and standalone display area translation (used when data has already been translated upstream)

        Returns:
            tuple: (Translated report_data, rss_items, rss_new_items, standalone_data)
        """
        if not self.translator or not self.translator.enabled:
            return report_data, rss_items, rss_new_items, standalone_data

        import copy
        print(f"[Translation] Starting to translate content to {self.translator.target_language}...")

        scope = self.translator.scope
        display_regions = display_regions or {}

        # Deep copy to avoid modifying original data
        report_data = copy.deepcopy(report_data)
        rss_items = copy.deepcopy(rss_items) if rss_items else None
        rss_new_items = copy.deepcopy(rss_new_items) if rss_new_items else None
        standalone_data = copy.deepcopy(standalone_data) if standalone_data else None

        # Collect all titles that need to be translated
        titles_to_translate = []
        title_locations = []  # Record title locations for backfilling

        # 1. Hot list titles (scope enabled and region displayed)
        if scope.get("HOTLIST", True) and display_regions.get("HOTLIST", True):
            for stat_idx, stat in enumerate(report_data.get("stats", [])):
                for title_idx, title_data in enumerate(stat.get("titles", [])):
                    titles_to_translate.append(title_data.get("title", ""))
                    title_locations.append(("stats", stat_idx, title_idx))

            # 2. New hot spot titles
            for source_idx, source in enumerate(report_data.get("new_titles", [])):
                for title_idx, title_data in enumerate(source.get("titles", [])):
                    titles_to_translate.append(title_data.get("title", ""))
                    title_locations.append(("new_titles", source_idx, title_idx))

        # 3. RSS statistics titles (structure is consistent with stats: [{word, count, titles: [{title, ...}]}])
        if not skip_rss and rss_items and scope.get("RSS", True) and display_regions.get("RSS", True):
            for stat_idx, stat in enumerate(rss_items):
                for title_idx, title_data in enumerate(stat.get("titles", [])):
                    titles_to_translate.append(title_data.get("title", ""))
                    title_locations.append(("rss_items", stat_idx, title_idx))

        # 4. RSS new titles (structure is consistent with stats)
        if not skip_rss and rss_new_items and scope.get("RSS", True) and display_regions.get("RSS", True) and display_regions.get("NEW_ITEMS", True):
            for stat_idx, stat in enumerate(rss_new_items):
                for title_idx, title_data in enumerate(stat.get("titles", [])):
                    titles_to_translate.append(title_data.get("title", ""))
                    title_locations.append(("rss_new_items", stat_idx, title_idx))

        # 5. Standalone display area - Hot list platforms
        if standalone_data and scope.get("STANDALONE", True) and display_regions.get("STANDALONE", False):
            for plat_idx, platform in enumerate(standalone_data.get("platforms", [])):
                for item_idx, item in enumerate(platform.get("items", [])):
                    titles_to_translate.append(item.get("title", ""))
                    title_locations.append(("standalone_platforms", plat_idx, item_idx))

            # 6. Standalone display area - RSS feeds (skip translated ones)
            if not skip_rss:
                for feed_idx, feed in enumerate(standalone_data.get("rss_feeds", [])):
                    for item_idx, item in enumerate(feed.get("items", [])):
                        titles_to_translate.append(item.get("title", ""))
                        title_locations.append(("standalone_rss", feed_idx, item_idx))

        if not titles_to_translate:
            print("[Translation] No content needs to be translated")
            return report_data, rss_items, rss_new_items, standalone_data

        print(f"[Translation] A total of {len(titles_to_translate)} titles to be translated")

        # Batch translation
        result = self.translator.translate_batch(titles_to_translate)

        if result.success_count == 0:
            print(f"[Translation] Translation failed: {result.results[0].error if result.results else 'Unknown error'}")
            return report_data, rss_items, rss_new_items, standalone_data

        print(f"[Translation] Translation completed: {result.success_count}/{result.total_count} successful")

        # debug mode: Output complete prompt, AI original response, item-by-item comparison
        if self.config.get("DEBUG", False):
            if result.prompt:
                print(f"[Translation][DEBUG] === Prompt sent to AI ===")
                print(result.prompt)
                print(f"[Translation][DEBUG] === End of Prompt ===")
            if result.raw_response:
                print(f"[Translation][DEBUG] === AI original response ===")
                print(result.raw_response)
                print(f"[Translation][DEBUG] === Response ended ===")
            # Line count mismatch warning
            expected = len(titles_to_translate)
            if result.parsed_count != expected:
                print(f"[Translation][DEBUG] ⚠️ Line count mismatch: expected {expected} items, AI returned {result.parsed_count} items")
            # Item-by-item comparison
            unchanged_count = 0
            for i, res in enumerate(result.results):
                if not res.success and res.error:
                    print(f"[Translation][DEBUG] [{i+1}] !! Failed: {res.error}")
                elif res.original_text == res.translated_text:
                    unchanged_count += 1
                else:
                    print(f"[Translation][DEBUG] [{i+1}] {res.original_text} => {res.translated_text}")
            if unchanged_count > 0:
                print(f"[Translation][DEBUG] (Another {unchanged_count} items unchanged, omitted)")

        # Backfill translation results (replace only when translated text is not empty, to prevent empty translation from overwriting original title)
        for i, (loc_type, idx1, idx2) in enumerate(title_locations):
            if i < len(result.results) and result.results[i].success:
                translated = result.results[i].translated_text
                if not translated or not translated.strip():
                    continue
                if loc_type == "stats":
                    report_data["stats"][idx1]["titles"][idx2]["title"] = translated
                elif loc_type == "new_titles":
                    report_data["new_titles"][idx1]["titles"][idx2]["title"] = translated
                elif loc_type == "rss_items" and rss_items:
                    rss_items[idx1]["titles"][idx2]["title"] = translated
                elif loc_type == "rss_new_items" and rss_new_items:
                    rss_new_items[idx1]["titles"][idx2]["title"] = translated
                elif loc_type == "standalone_platforms" and standalone_data:
                    standalone_data["platforms"][idx1]["items"][idx2]["title"] = translated
                elif loc_type == "standalone_rss" and standalone_data:
                    standalone_data["rss_feeds"][idx1]["items"][idx2]["title"] = translated

        return report_data, rss_items, rss_new_items, standalone_data

    def dispatch_all(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily",
        html_file_path: Optional[str] = None,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        standalone_data: Optional[Dict] = None,
        skip_translation: bool = False,
    ) -> Dict[str, bool]:
        """
        Distribute notifications to all configured channels (supports hotlist + RSS merged push + AI analysis + standalone display area)

        Args:
            report_data: Report data (generated by prepare_report_data)
            report_type: Report type (e.g., "Tổng hợp cả ngày", "Bảng xếp hạng hiện tại", "Incremental analysis")
            update_info: Version Cập nhật info (optional)
            proxy_url: Proxy URL (optional)
            mode: Report mode (daily/current/incremental)
            html_file_path: HTML report file path (used by email)
            rss_items: RSS statistics item list (used for RSS statistics block)
            rss_new_items: RSS new item list (used for RSS new block)
            ai_analysis: AI analysis results (optional)
            standalone_data: Standalone display area data (optional)
            skip_translation: Skip translation (used when data has already been translated upstream)

        Returns:
            Dict[str, bool]: Send results for each channel, key is channel name, value is whether successful
        """
        results = {}

        # Get region display configuration
        display_regions = self.config.get("DISPLAY", {}).get("REGIONS", {})

        # Execute translation (if enabled, skip undisplayed regions based on display_regions)
        # When skip_translation=True, RSS has already been translated upstream, skip duplicate RSS translation
        if not skip_translation:
            report_data, rss_items, rss_new_items, standalone_data = self.translate_content(
                report_data, rss_items, rss_new_items, standalone_data, display_regions
            )
        else:
            # RSS already translated, only translate hotlist report_data and standalone display area hotlist part
            report_data, _, _, standalone_data = self.translate_content(
                report_data, standalone_data=standalone_data, display_regions=display_regions,
                skip_rss=True,
            )

        # Feishu
        if self.config.get("FEISHU_WEBHOOK_URL"):
            results["feishu"] = self._send_feishu(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # DingTalk
        if self.config.get("DINGTALK_WEBHOOK_URL"):
            results["dingtalk"] = self._send_dingtalk(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # WeChat Work
        if self.config.get("WEWORK_WEBHOOK_URL"):
            results["wework"] = self._send_wework(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # Telegram (requires pairing verification)
        if self.config.get("TELEGRAM_BOT_TOKEN") and self.config.get("TELEGRAM_CHAT_ID"):
            results["telegram"] = self._send_telegram(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # ntfy (requires pairing verification)
        if self.config.get("NTFY_SERVER_URL") and self.config.get("NTFY_TOPIC"):
            results["ntfy"] = self._send_ntfy(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # Bark
        if self.config.get("BARK_URL"):
            results["bark"] = self._send_bark(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # Slack
        if self.config.get("SLACK_WEBHOOK_URL"):
            results["slack"] = self._send_slack(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # General Webhook
        if self.config.get("GENERIC_WEBHOOK_URL"):
            results["generic_webhook"] = self._send_generic_webhook(
                report_data, report_type, update_info, proxy_url, mode, rss_items, rss_new_items,
                ai_analysis, display_regions, standalone_data
            )

        # Email (keep original logic, already supports multiple recipients, AI analysis is embedded in HTML)
        if (
            self.config.get("EMAIL_FROM")
            and self.config.get("EMAIL_PASSWORD")
            and self.config.get("EMAIL_TO")
        ):
            results["email"] = self._send_email(report_type, html_file_path)

        return results

    def _send_to_multi_accounts(
        self,
        channel_name: str,
        config_value: str,
        send_func: Callable[..., bool],
        **kwargs,
    ) -> bool:
        """
        General multi-account sending logic

        Args:
            channel_name: Channel name (used for logs and account quantity limit prompts)
            config_value: Configuration value (may contain multiple accounts, separated by ;)
            send_func: Send function, signature is (account, account_label=..., **kwargs) -> bool
            **kwargs: Other parameters passed to the send function

        Returns:
            bool: Returns True if any account sends successfully
        """
        accounts = parse_multi_account_config(config_value)
        if not accounts:
            return False

        accounts = limit_accounts(accounts, self.max_accounts, channel_name)
        results = []

        for i, account in enumerate(accounts):
            if account:
                account_label = f"Account {i+1}" if len(accounts) > 1 else ""
                result = send_func(account, account_label=account_label, **kwargs)
                results.append(result)

        return any(results) if results else False

    def _apply_display_regions(
        self,
        report_data: Dict,
        display_regions: Optional[Dict],
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        standalone_data: Optional[Dict] = None,
    ) -> tuple:
        """Filter data of each region based on display_regions, return (report_data, rss_items, rss_new_items, ai_analysis, standalone_data)"""
        display_regions = display_regions or {}
        if not display_regions.get("HOTLIST", True):
            report_data = {"stats": [], "failed_ids": [], "new_titles": [], "id_to_name": {}}
        show_rss = display_regions.get("RSS", True)
        return (
            report_data,
            rss_items if show_rss else None,
            rss_new_items if (show_rss and display_regions.get("NEW_ITEMS", True)) else None,
            ai_analysis if display_regions.get("AI_ANALYSIS", True) else None,
            standalone_data if display_regions.get("STANDALONE", False) else None,
        )

    def _send_feishu(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to Feishu (multiple accounts, supports hotlist + RSS merge + AI analysis + independent display area)"""
        rd, ri, rn, ai, sd = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )

        return self._send_to_multi_accounts(
            channel_name="Feishu",
            config_value=self.config["FEISHU_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_feishu(
                webhook_url=url,
                report_data=rd,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("FEISHU_BATCH_SIZE", 29000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
                get_time_func=self.get_time_func,
                rss_items=ri,
                rss_new_items=rn,
                ai_analysis=ai,
                display_regions=display_regions or {},
                standalone_data=sd,
            ),
        )

    def _send_dingtalk(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to DingTalk (multiple accounts, supports hotlist + RSS merge + AI analysis + independent display area)"""
        rd, ri, rn, ai, sd = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )

        return self._send_to_multi_accounts(
            channel_name="DingTalk",
            config_value=self.config["DINGTALK_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_dingtalk(
                webhook_url=url,
                report_data=rd,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("DINGTALK_BATCH_SIZE", 20000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
                rss_items=ri,
                rss_new_items=rn,
                ai_analysis=ai,
                display_regions=display_regions or {},
                standalone_data=sd,
            ),
        )

    def _send_wework(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to WeChat Work (multiple accounts, supports hotlist + RSS merge + AI analysis + independent display area)"""
        rd, ri, rn, ai, sd = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )

        return self._send_to_multi_accounts(
            channel_name="WeChat Work",
            config_value=self.config["WEWORK_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_wework(
                webhook_url=url,
                report_data=rd,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("MESSAGE_BATCH_SIZE", 4000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                msg_type=self.config.get("WEWORK_MSG_TYPE", "markdown"),
                split_content_func=self.split_content_func,
                rss_items=ri,
                rss_new_items=rn,
                ai_analysis=ai,
                display_regions=display_regions or {},
                standalone_data=sd,
            ),
        )

    def _send_telegram(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to Telegram (multiple accounts, requires token and chat_id pairing verification, supports hotlist + RSS merge + AI analysis + independent display area)"""
        report_data, rss_items, rss_new_items, ai_analysis, standalone_data = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )
        display_regions = display_regions or {}

        telegram_tokens = parse_multi_account_config(self.config["TELEGRAM_BOT_TOKEN"])
        telegram_chat_ids = parse_multi_account_config(self.config["TELEGRAM_CHAT_ID"])

        if not telegram_tokens or not telegram_chat_ids:
            return False

        valid, count = validate_paired_configs(
            {"bot_token": telegram_tokens, "chat_id": telegram_chat_ids},
            "Telegram",
            required_keys=["bot_token", "chat_id"],
        )
        if not valid or count == 0:
            return False

        telegram_tokens = limit_accounts(telegram_tokens, self.max_accounts, "Telegram")
        telegram_chat_ids = telegram_chat_ids[: len(telegram_tokens)]

        results = []
        for i in range(len(telegram_tokens)):
            token = telegram_tokens[i]
            chat_id = telegram_chat_ids[i]
            if token and chat_id:
                account_label = f"Account {i+1}" if len(telegram_tokens) > 1 else ""
                result = send_to_telegram(
                    bot_token=token,
                    chat_id=chat_id,
                    report_data=report_data,
                    report_type=report_type,
                    update_info=update_info,
                    proxy_url=proxy_url,
                    mode=mode,
                    account_label=account_label,
                    batch_size=self.config.get("MESSAGE_BATCH_SIZE", 4000),
                    batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                    split_content_func=self.split_content_func,
                    rss_items=rss_items,
                    rss_new_items=rss_new_items,
                    ai_analysis=ai_analysis,
                    display_regions=display_regions,
                    standalone_data=standalone_data,
                )
                results.append(result)

        return any(results) if results else False

    def _send_ntfy(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to ntfy (multiple accounts, requires topic and token pairing verification, supports hotlist + RSS merge + AI analysis + independent display area)"""
        report_data, rss_items, rss_new_items, ai_analysis, standalone_data = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )
        display_regions = display_regions or {}

        ntfy_server_url = self.config["NTFY_SERVER_URL"]
        ntfy_topics = parse_multi_account_config(self.config["NTFY_TOPIC"])
        ntfy_tokens = parse_multi_account_config(self.config.get("NTFY_TOKEN", ""))

        if not ntfy_server_url or not ntfy_topics:
            return False

        if ntfy_tokens and len(ntfy_tokens) != len(ntfy_topics):
            print(
                f"❌ ntfy configuration error: number of topics ({len(ntfy_topics)}) and number of tokens ({len(ntfy_tokens)}) do not match, skipping ntfy push"
            )
            return False

        ntfy_topics = limit_accounts(ntfy_topics, self.max_accounts, "ntfy")
        if ntfy_tokens:
            ntfy_tokens = ntfy_tokens[: len(ntfy_topics)]

        results = []
        for i, topic in enumerate(ntfy_topics):
            if topic:
                token = get_account_at_index(ntfy_tokens, i, "") if ntfy_tokens else ""
                account_label = f"Account {i+1}" if len(ntfy_topics) > 1 else ""
                result = send_to_ntfy(
                    server_url=ntfy_server_url,
                    topic=topic,
                    token=token,
                    report_data=report_data,
                    report_type=report_type,
                    update_info=update_info,
                    proxy_url=proxy_url,
                    mode=mode,
                    account_label=account_label,
                    batch_size=3800,
                    split_content_func=self.split_content_func,
                    rss_items=rss_items,
                    rss_new_items=rss_new_items,
                    ai_analysis=ai_analysis,
                    display_regions=display_regions,
                    standalone_data=standalone_data,
                )
                results.append(result)

        return any(results) if results else False

    def _send_bark(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to Bark (multiple accounts, supports hotlist + RSS merge + AI analysis + independent display area)"""
        rd, ri, rn, ai, sd = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )

        return self._send_to_multi_accounts(
            channel_name="Bark",
            config_value=self.config["BARK_URL"],
            send_func=lambda url, account_label: send_to_bark(
                bark_url=url,
                report_data=rd,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("BARK_BATCH_SIZE", 3600),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
                rss_items=ri,
                rss_new_items=rn,
                ai_analysis=ai,
                display_regions=display_regions or {},
                standalone_data=sd,
            ),
        )

    def _send_slack(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to Slack (multiple accounts, supports hotlist + RSS merge + AI analysis + independent display area)"""
        rd, ri, rn, ai, sd = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )

        return self._send_to_multi_accounts(
            channel_name="Slack",
            config_value=self.config["SLACK_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_slack(
                webhook_url=url,
                report_data=rd,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("SLACK_BATCH_SIZE", 4000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
                rss_items=ri,
                rss_new_items=rn,
                ai_analysis=ai,
                display_regions=display_regions or {},
                standalone_data=sd,
            ),
        )

    def _send_generic_webhook(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        ai_analysis: Optional[AIAnalysisResult] = None,
        display_regions: Optional[Dict] = None,
        standalone_data: Optional[Dict] = None,
    ) -> bool:
        """Send to General Webhook (multiple accounts, supports hotlist + RSS merge + AI analysis + independent display area)"""
        report_data, rss_items, rss_new_items, ai_analysis, standalone_data = self._apply_display_regions(
            report_data, display_regions, rss_items, rss_new_items, ai_analysis, standalone_data
        )
        display_regions = display_regions or {}

        urls = parse_multi_account_config(self.config.get("GENERIC_WEBHOOK_URL", ""))
        templates = parse_multi_account_config(self.config.get("GENERIC_WEBHOOK_TEMPLATE", ""))

        if not urls:
            return False

        urls = limit_accounts(urls, self.max_accounts, "General Webhook")
        results = []

        for i, url in enumerate(urls):
            if not url:
                continue

            template = ""
            if templates:
                if i < len(templates):
                    template = templates[i]
                elif len(templates) == 1:
                    template = templates[0]

            account_label = f"Account {i+1}" if len(urls) > 1 else ""

            result = send_to_generic_webhook(
                webhook_url=url,
                payload_template=template,
                report_data=report_data,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("MESSAGE_BATCH_SIZE", 4000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
                rss_items=rss_items,
                rss_new_items=rss_new_items,
                ai_analysis=ai_analysis,
                display_regions=display_regions,
                standalone_data=standalone_data,
            )
            results.append(result)

        return any(results) if results else False

    def _send_email(
        self,
        report_type: str,
        html_file_path: Optional[str],
    ) -> bool:
        """Send email (keep original logic, already supports multiple recipients)

        Note:
            AI analysis content is already embedded during HTML generation, no need to pass it here
        """
        return send_to_email(
            from_email=self.config["EMAIL_FROM"],
            password=self.config["EMAIL_PASSWORD"],
            to_email=self.config["EMAIL_TO"],
            report_type=report_type,
            html_file_path=html_file_path,
            custom_smtp_server=self.config.get("EMAIL_SMTP_SERVER", ""),
            custom_smtp_port=self.config.get("EMAIL_SMTP_PORT", ""),
            get_time_func=self.get_time_func,
        )

