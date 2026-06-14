# coding=utf-8
"""
TrendRadar main program

Hot news aggregation and analysis tool
Support: python -m trendradar
"""

import argparse
import copy
import json
import os
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests

from trendradar.context import AppContext
from trendradar import __version__
from trendradar.core import load_config, parse_multi_account_config, validate_paired_configs
from trendradar.core.analyzer import convert_keyword_stats_to_platform_stats
from trendradar.crawler import DataFetcher
from trendradar.storage import convert_crawl_results_to_news_data
from trendradar.utils.time import DEFAULT_TIMEZONE, is_within_days, calculate_days_old
from trendradar.ai import AIAnalyzer, AIAnalysisResult
from trendradar.core.scheduler import ResolvedSchedule
from trendradar.core.cdn import fetch_with_fallback


def _parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string into a tuple"""
    try:
        parts = version_str.strip().split(".")
        if len(parts) >= 3:
            return int(parts[0]), int(parts[1]), int(parts[2])
        return 0, 0, 0
    except (ValueError, AttributeError, TypeError):
        return 0, 0, 0


def _compare_version(local: str, remote: str) -> str:
    """Compare version numbers, return status text"""
    local_tuple = _parse_version(local)
    remote_tuple = _parse_version(remote)

    if local_tuple < remote_tuple:
        return "⚠️ Need Cập nhật"
    elif local_tuple > remote_tuple:
        return "🔮 Ahead version"
    else:
        return "✅ Already up to date"


def _fetch_remote_version(version_url: str, proxy_url: Optional[str] = None) -> Optional[str]:
    """Get remote version number (supports CDN multi-source fallback)"""
    return fetch_with_fallback(version_url, proxy_url)


def _parse_config_versions(content: str) -> Dict[str, str]:
    """Parse configuration file version content into a dictionary"""
    versions = {}
    try:
        if not content:
            return versions
        for line in content.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            name, version = line.split("=", 1)
            versions[name.strip()] = version.strip()
    except Exception as e:
        print(f"[Version Check] Failed to parse config version: {e}")
    return versions


def check_all_versions(
    version_url: str,
    configs_version_url: Optional[str] = None,
    proxy_url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Unified version check: program version + configuration file version

    Args:
        version_url: Remote program version check URL
        configs_version_url: Remote configuration file version check URL (return format: filename=version)
        proxy_url: Proxy URL

    Returns:
        (need_update, remote_version): Whether the program needs Cập nhật and remote version number
    """
    # Get remote version
    remote_version = _fetch_remote_version(version_url, proxy_url)

    # Get remote config version (if URL is provided)
    remote_config_versions = {}
    if configs_version_url:
        content = _fetch_remote_version(configs_version_url, proxy_url)
        if content:
            remote_config_versions = _parse_config_versions(content)

    print("=" * 60)
    print("Version Check")
    print("=" * 60)

    if remote_version:
        print(f"Remote program version: {remote_version}")
    else:
        print("Remote program version: Failed to get")

    if configs_version_url:
        if remote_config_versions:
            print(f"Remote config list: Successfully obtained ({len(remote_config_versions)} files)")
        else:
            print("Remote config list: Failed to get or empty")

    print("-" * 60)

    program_status = _compare_version(__version__, remote_version) if remote_version else "(Cannot compare)"
    print(f"  Main program version: {__version__} {program_status}")

    config_files = [
        Path("config/config.yaml"),
        Path("config/timeline.yaml"),
        Path("config/frequency_words.txt"),
        Path("config/ai_interests.txt"),
        Path("config/ai_analysis_prompt.txt"),
        Path("config/ai_translation_prompt.txt"),
    ]

    version_pattern = re.compile(r"Version:\s*(\d+\.\d+\.\d+)", re.IGNORECASE)

    for config_file in config_files:
        if not config_file.exists():
            print(f"  {config_file.name}: File does not exist")
            continue

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                local_version = None
                for i, line in enumerate(f):
                    if i >= 20:
                        break
                    match = version_pattern.search(line)
                    if match:
                        local_version = match.group(1)
                        break

                # Get the remote version of this file
                target_remote_version = remote_config_versions.get(config_file.name)

                if local_version:
                    if target_remote_version:
                        status = _compare_version(local_version, target_remote_version)
                        print(f"  {config_file.name}: {local_version} {status}")
                    else:
                        print(f"  {config_file.name}: {local_version} (Remote version not found)")
                else:
                    print(f"  {config_file.name}: Local version number not found")
        except Exception as e:
            print(f"  {config_file.name}: Read failed - {e}")

    print("=" * 60)

    # Return the Cập nhật status of the program version
    if remote_version:
        need_update = _parse_version(__version__) < _parse_version(remote_version)
        return need_update, remote_version if need_update else None
    return False, None


# === Main Analyzer ===
class NewsAnalyzer:
    """News Analyzer"""

    # Mode strategy definition
    MODE_STRATEGIES = {
        "incremental": {
            "mode_name": "Incremental mode",
            "description": "Incremental mode (only focus on new news, do not push when there is no new news)",
            "report_type": "Incremental analysis",
            "should_send_notification": True,
        },
        "current": {
            "mode_name": "Bảng xếp hạng hiện tại mode",
            "description": "Bảng xếp hạng hiện tại mode (Bảng xếp hạng hiện tại matching news + new news area + push on time)",
            "report_type": "Bảng xếp hạng hiện tại",
            "should_send_notification": True,
        },
        "daily": {
            "mode_name": "Tổng hợp cả ngày mode",
            "description": "Tổng hợp cả ngày mode (all matched news + newly added news area + scheduled push)",
            "report_type": "Tổng hợp cả ngày",
            "should_send_notification": True,
        },
    }

    def __init__(self, config: Optional[Dict] = None):
        # Use passed configuration or load new configuration
        if config is None:
            print("Loading configuration...")
            config = load_config()
        print(f"TrendRadar v{__version__} configuration loaded")
        print(f"Number of monitored platforms: {len(config['PLATFORMS'])}")
        print(f"Timezone: {config.get('TIMEZONE', DEFAULT_TIMEZONE)}")

        # Create application context
        self.ctx = AppContext(config)

        self.request_interval = self.ctx.config["REQUEST_INTERVAL"]
        self.report_mode = self.ctx.config["REPORT_MODE"]
        self.frequency_file = None
        self.filter_method = None  # None=use global configuration ctx.filter_method
        self.interests_file = None  # None=use global configuration ai_filter.interests_file
        self.rank_threshold = self.ctx.rank_threshold
        self.is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
        self.is_docker_container = self._detect_docker_environment()
        self.update_info = None
        self.proxy_url = None
        self._setup_proxy()
        self.data_fetcher = DataFetcher(self.proxy_url)

        # RSS/platform metadata (used for report header display)
        self._rss_source_total = 0
        self._rss_source_failed = 0
        self._rss_total_count = 0
        self._rss_matched_count = 0
        self._hotlist_total_count = 0

        # Initialize storage manager (using AppContext)
        self._init_storage_manager()
        # Note: update_info is set by main() function to avoid duplicate requests for remote version

    def _init_storage_manager(self) -> None:
        """Initialize storage manager (using AppContext)"""
        # Get data retention days (supports environment variable override)
        env_retention = os.environ.get("STORAGE_RETENTION_DAYS", "").strip()
        if env_retention:
            # Environment variable override configuration
            self.ctx.config["STORAGE"]["RETENTION_DAYS"] = int(env_retention)

        self.storage_manager = self.ctx.get_storage_manager()
        print(f"Storage backend: {self.storage_manager.backend_name}")

        retention_days = self.ctx.config.get("STORAGE", {}).get("RETENTION_DAYS", 0)
        if retention_days > 0:
            print(f"Data retention days: {retention_days} days")

    def _detect_docker_environment(self) -> bool:
        """Detect if running in a Docker container"""
        try:
            if os.environ.get("DOCKER_CONTAINER") == "true":
                return True

            if os.path.exists("/.dockerenv"):
                return True

            return False
        except Exception:
            return False

    def _should_open_browser(self) -> bool:
        """Determine whether to open the browser"""
        return not self.is_github_actions and not self.is_docker_container

    def _setup_proxy(self) -> None:
        """Set proxy configuration"""
        if not self.is_github_actions and self.ctx.config["USE_PROXY"]:
            self.proxy_url = self.ctx.config["DEFAULT_PROXY"]
            print("Local environment, using proxy")
        elif not self.is_github_actions and not self.ctx.config["USE_PROXY"]:
            print("Local environment, proxy not enabled")
        else:
            print("GitHub Actions environment, not using proxy")

    def _set_update_info_from_config(self) -> None:
        """Set Cập nhật information from cached remote version (no duplicate requests)"""
        try:
            version_url = self.ctx.config.get("VERSION_CHECK_URL", "")
            if not version_url:
                return

            remote_version = _fetch_remote_version(version_url, self.proxy_url)
            if remote_version:
                need_update = _parse_version(__version__) < _parse_version(remote_version)
                if need_update:
                    self.update_info = {
                        "current_version": __version__,
                        "remote_version": remote_version,
                    }
        except Exception as e:
            print(f"Version check error: {e}")

    def _get_mode_strategy(self) -> Dict:
        """Get strategy configuration for current mode"""
        return self.MODE_STRATEGIES.get(self.report_mode, self.MODE_STRATEGIES["daily"])

    def _has_notification_configured(self) -> bool:
        """Check if any notification channels are configured"""
        cfg = self.ctx.config
        return any(
            [
                cfg["FEISHU_WEBHOOK_URL"],
                cfg["DINGTALK_WEBHOOK_URL"],
                cfg["WEWORK_WEBHOOK_URL"],
                (cfg["TELEGRAM_BOT_TOKEN"] and cfg["TELEGRAM_CHAT_ID"]),
                (
                    cfg["EMAIL_FROM"]
                    and cfg["EMAIL_PASSWORD"]
                    and cfg["EMAIL_TO"]
                ),
                (cfg["NTFY_SERVER_URL"] and cfg["NTFY_TOPIC"]),
                cfg["BARK_URL"],
                cfg["SLACK_WEBHOOK_URL"],
                cfg["GENERIC_WEBHOOK_URL"],
            ]
        )

    def _has_valid_content(
        self, stats: List[Dict], new_titles: Optional[Dict] = None
    ) -> bool:
        """Check if there is valid news content"""
        if self.report_mode == "incremental":
            # Incremental mode: push as long as there is matched news
            # count_word_frequency already ensures only newly added news is processed (including the first crawl of the day)
            has_matched_news = any(stat["count"] > 0 for stat in stats)
            return has_matched_news
        elif self.report_mode == "current":
            # current mode: as long as stats has content, it means there is matched news
            return any(stat["count"] > 0 for stat in stats)
        else:
            # In daily summary mode, check if there is matched frequency word news or newly added news
            has_matched_news = any(stat["count"] > 0 for stat in stats)
            has_new_news = bool(
                new_titles and any(len(titles) > 0 for titles in new_titles.values())
            )
            return has_matched_news or has_new_news

    def _prepare_ai_analysis_data(
        self,
        ai_mode: str,
        current_results: Optional[Dict] = None,
        current_id_to_name: Optional[Dict] = None,
    ) -> Tuple[List[Dict], Optional[Dict]]:
        """
        Prepare data of specified mode for AI analysis

        Args:
            ai_mode: AI analysis mode (daily/current/incremental)
            current_results: current crawl results (used for incremental mode)
            current_id_to_name: current platform mapping (used for incremental mode)

        Returns:
            Tuple[stats, id_to_name]: statistical data and platform mapping
        """
        try:
            word_groups, filter_words, global_filters = self.ctx.load_frequency_words(self.frequency_file)

            if ai_mode == "incremental":
                # incremental mode: use current crawl data
                if not current_results or not current_id_to_name:
                    print("[AI] incremental mode requires current crawl data, but none was provided")
                    return [], None

                # Prepare current time information
                time_info = self.ctx.format_time()
                title_info = self._prepare_current_title_info(current_results, time_info)

                # Detect new titles
                new_titles = self.ctx.detect_new_titles(list(current_results.keys()))

                # Statistical calculation
                stats, _ = self.ctx.count_frequency(
                    current_results,
                    word_groups,
                    filter_words,
                    current_id_to_name,
                    title_info,
                    new_titles,
                    mode="incremental",
                    global_filters=global_filters,
                    quiet=True,
                )

                # If it is platform mode, convert data structure
                if self.ctx.display_mode == "platform" and stats:
                    stats = convert_keyword_stats_to_platform_stats(
                        stats,
                        self.ctx.weight_config,
                        self.ctx.rank_threshold,
                    )

                return stats, current_id_to_name

            elif ai_mode in ["daily", "current"]:
                # Load historical data
                analysis_data = self._load_analysis_data(quiet=True)
                if not analysis_data:
                    print(f"[AI] Unable to load historical data for {ai_mode} mode analysis")
                    return [], None

                (
                    all_results,
                    id_to_name,
                    title_info,
                    new_titles,
                    _,
                    _,
                    _,
                ) = analysis_data

                # Statistical calculation
                stats, _ = self.ctx.count_frequency(
                    all_results,
                    word_groups,
                    filter_words,
                    id_to_name,
                    title_info,
                    new_titles,
                    mode=ai_mode,
                    global_filters=global_filters,
                    quiet=True,
                )

                # If it is platform mode, convert data structure
                if self.ctx.display_mode == "platform" and stats:
                    stats = convert_keyword_stats_to_platform_stats(
                        stats,
                        self.ctx.weight_config,
                        self.ctx.rank_threshold,
                    )

                return stats, id_to_name
            else:
                print(f"[AI] Unknown AI mode: {ai_mode}")
                return [], None

        except Exception as e:
            print(f"[AI] Error preparing data for {ai_mode} mode: {e}")
            if self.ctx.config.get("DEBUG", False):
                import traceback
                traceback.print_exc()
            return [], None

    def _run_ai_analysis(
        self,
        stats: List[Dict],
        rss_items: Optional[List[Dict]],
        mode: str,
        report_type: str,
        id_to_name: Optional[Dict],
        current_results: Optional[Dict] = None,
        schedule: ResolvedSchedule = None,
        standalone_data: Optional[Dict] = None,
    ) -> Optional[AIAnalysisResult]:
        """Execute AI analysis"""
        analysis_config = self.ctx.config.get("AI_ANALYSIS", {})
        if not analysis_config.get("ENABLED", False):
            return None

        # Scheduling system decision
        if not schedule.analyze:
            print("[AI] Scheduler: AI analysis is not executed in the current time period")
            return None

        if schedule.once_analyze and schedule.period_key:
            scheduler = self.ctx.create_scheduler()
            date_str = self.ctx.format_date()
            if scheduler.already_executed(schedule.period_key, "analyze", date_str):
                print(f"[AI] Scheduler: Time period {schedule.period_name or schedule.period_key} has already been analyzed today, skipping")
                return None
            else:
                print(f"[AI] Scheduler: First analysis today for time period {schedule.period_name or schedule.period_key}")

        print("[AI] Performing AI analysis...")
        try:
            ai_config = self.ctx.config.get("AI", {})
            debug_mode = self.ctx.config.get("DEBUG", False)
            analyzer = AIAnalyzer(ai_config, analysis_config, self.ctx.get_time, debug=debug_mode)

            # Determine the mode used for AI analysis
            ai_mode_config = analysis_config.get("MODE", "follow_report")
            if ai_mode_config == "follow_report":
                # Follow push report mode
                ai_mode = mode
                ai_stats = stats
                ai_id_to_name = id_to_name
            elif ai_mode_config in ["daily", "current", "incremental"]:
                # Use independently configured mode, need to prepare data again
                ai_mode = ai_mode_config
                if ai_mode != mode:
                    print(f"[AI] Using independent analysis mode: {ai_mode} (Push mode: {mode})")
                    print(f"[AI] Preparing data for {ai_mode} mode...")

                    # Re-prepare data according to AI mode
                    ai_stats, ai_id_to_name = self._prepare_ai_analysis_data(
                        ai_mode, current_results, id_to_name
                    )
                    if not ai_stats:
                        print(f"[AI] Warning: Unable to prepare data for {ai_mode} mode, falling back to push mode data")
                        ai_stats = stats
                        ai_id_to_name = id_to_name
                        ai_mode = mode
                else:
                    ai_stats = stats
                    ai_id_to_name = id_to_name
            else:
                # Configuration error, falling back to follow mode
                print(f"[AI] Warning: Invalid ai_analysis.mode configuration '{ai_mode_config}', using push mode '{mode}'")
                ai_mode = mode
                ai_stats = stats
                ai_id_to_name = id_to_name

            # Extract platform list
            platforms = list(ai_id_to_name.values()) if ai_id_to_name else []

            # Extract keyword list
            keywords = [s.get("word", "") for s in ai_stats if s.get("word")] if ai_stats else []

            # Determine report type
            if ai_mode != mode:
                # Determine report type according to AI mode
                ai_report_type = {
                    "daily": "Daily summary",
                    "current": "Bảng xếp hạng hiện tại",
                    "incremental": "Cập nhật thêm"
                }.get(ai_mode, report_type)
            else:
                ai_report_type = report_type

            result = analyzer.analyze(
                stats=ai_stats,
                rss_stats=rss_items,
                report_mode=ai_mode,
                report_type=ai_report_type,
                platforms=platforms,
                keywords=keywords,
                standalone_data=standalone_data,
            )

            # Set the mode used for AI analysis
            if result.success:
                result.ai_mode = ai_mode
                if result.error:
                    # Success but with warnings (e.g., JSON parsing issues but used original text)
                    print(f"[AI] Analysis completed (with warnings: {result.error})")
                else:
                    print("[AI] Analysis completed")

                # Record AI analysis
                if schedule.once_analyze and schedule.period_key:
                    scheduler = self.ctx.create_scheduler()
                    date_str = self.ctx.format_date()
                    scheduler.record_execution(schedule.period_key, "analyze", date_str)
            elif result.skipped:
                print(f"[AI] {result.error}")
            else:
                print(f"[AI] Analysis failed: {result.error}")

            return result
        except Exception as e:
            import traceback
            error_type = type(e).__name__
            error_msg = str(e)
            # Truncate overly long error messages
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            print(f"[AI] Analysis error ({error_type}): {error_msg}")
            # Detailed error log to stderr
            import sys
            print(f"[AI] Detailed error stack:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return AIAnalysisResult(success=False, error=f"{error_type}: {error_msg}")

    def _load_analysis_data(
        self,
        quiet: bool = False,
    ) -> Optional[Tuple[Dict, Dict, Dict, Dict, List, List]]:
        """Unified data loading and preprocessing, filter historical data using the current monitoring platform list"""
        try:
            # Get the currently configured monitoring platform ID list
            current_platform_ids = self.ctx.platform_ids
            if not quiet:
                print(f"Current monitoring platform: {current_platform_ids}")

            all_results, id_to_name, title_info = self.ctx.read_today_titles(
                current_platform_ids, quiet=quiet
            )

            if not all_results and current_platform_ids:
                print("No data found for today")
                return None

            total_titles = sum(len(titles) for titles in all_results.values())
            if not quiet:
                print(f"Read {total_titles} titles (filtered by current monitoring platforms)")

            new_titles = self.ctx.detect_new_titles(current_platform_ids, quiet=quiet)
            word_groups, filter_words, global_filters = self.ctx.load_frequency_words(self.frequency_file)

            return (
                all_results,
                id_to_name,
                title_info,
                new_titles,
                word_groups,
                filter_words,
                global_filters,
            )
        except Exception as e:
            print(f"Data loading failed: {e}")
            return None

    def _prepare_current_title_info(self, results: Dict, time_info: str) -> Dict:
        """Build title information from current crawl results"""
        title_info = {}
        for source_id, titles_data in results.items():
            title_info[source_id] = {}
            for title, title_data in titles_data.items():
                ranks = title_data.get("ranks", [])
                url = title_data.get("url", "")
                mobile_url = title_data.get("mobileUrl", "")

                title_info[source_id][title] = {
                    "first_time": time_info,
                    "last_time": time_info,
                    "count": 1,
                    "ranks": ranks,
                    "url": url,
                    "mobileUrl": mobile_url,
                }
        return title_info

    def _prepare_standalone_data(
        self,
        results: Dict,
        id_to_name: Dict,
        title_info: Optional[Dict] = None,
        rss_items: Optional[List[Dict]] = None,
    ) -> Optional[Dict]:
        """
        Extract independent display area data from raw data

        Pure data preparation method, does not check the display.regions.standalone switch.
        Each consumer decides whether to use it:
        - AI analysis: controlled by ai.include_standalone (gated at the _run_ai_analysis layer)
        - HTML report / Email: controlled by display.regions.standalone (filtered before HTML generation)
        - Webhook push: controlled by display.regions.standalone (gated at the dispatcher layer)

        Args:
            results: Raw crawl results {platform_id: {title: title_data}}
            id_to_name: Mapping of platform ID to name
            title_info: Title meta information (including ranking history, time, etc.)
            rss_items: RSS item list

        Returns:
            Independent display data dictionary, returns None if data source is not configured
        """
        display_config = self.ctx.config.get("DISPLAY", {})
        standalone_config = display_config.get("STANDALONE", {})

        platform_ids = standalone_config.get("PLATFORMS", [])
        rss_feed_ids = standalone_config.get("RSS_FEEDS", [])
        max_items = standalone_config.get("MAX_ITEMS", 20)

        if not platform_ids and not rss_feed_ids:
            return None

        standalone_data = {
            "platforms": [],
            "rss_feeds": [],
        }

        # Find the latest batch time (filtering logic similar to current mode)
        latest_time = None
        if title_info:
            for source_titles in title_info.values():
                for title_data in source_titles.values():
                    last_time = title_data.get("last_time", "")
                    if last_time:
                        if latest_time is None or last_time > latest_time:
                            latest_time = last_time

        # Extract hot list platform data
        for platform_id in platform_ids:
            if platform_id not in results:
                continue

            platform_name = id_to_name.get(platform_id, platform_id)
            platform_titles = results[platform_id]

            items = []
            for title, title_data in platform_titles.items():
                # Get meta information (if title_info exists)
                meta = {}
                if title_info and platform_id in title_info and title in title_info[platform_id]:
                    meta = title_info[platform_id][title]

                # Only keep topics currently on the list (last_time equals the latest time)
                if latest_time and meta:
                    if meta.get("last_time") != latest_time:
                        continue

                # Use the ranking data (title_data) of the current hot list for sorting
                # title_data contains the current ranking returned by the crawler, used to ensure the order of the independent display area is consistent with the hot list
                current_ranks = title_data.get("ranks", [])
                current_rank = current_ranks[-1] if current_ranks else 0

                # Ranking range for display: merge historical ranking and current ranking
                historical_ranks = meta.get("ranks", []) if meta else []
                # Merge and deduplicate, keep order
                all_ranks = historical_ranks.copy()
                for rank in current_ranks:
                    if rank not in all_ranks:
                        all_ranks.append(rank)
                display_ranks = all_ranks if all_ranks else current_ranks

                item = {
                    "title": title,
                    "url": title_data.get("url", ""),
                    "mobileUrl": title_data.get("mobileUrl", ""),
                    "rank": current_rank,  # Current ranking used for sorting
                    "ranks": display_ranks,  # Ranking range for display (historical + current)
                    "first_time": meta.get("first_time", ""),
                    "last_time": meta.get("last_time", ""),
                    "count": meta.get("count", 1),
                    "rank_timeline": meta.get("rank_timeline", []),
                }
                items.append(item)

            # Sort by current ranking
            items.sort(key=lambda x: x["rank"] if x["rank"] > 0 else 9999)

            # Limit the number of items
            if max_items > 0:
                items = items[:max_items]

            if items:
                standalone_data["platforms"].append({
                    "id": platform_id,
                    "name": platform_name,
                    "items": items,
                })

        # Extract RSS data
        if rss_items and rss_feed_ids:
            # Group by feed_id
            feed_items_map = {}
            for item in rss_items:
                feed_id = item.get("feed_id", "")
                if feed_id in rss_feed_ids:
                    if feed_id not in feed_items_map:
                        feed_items_map[feed_id] = {
                            "name": item.get("feed_name", feed_id),
                            "items": [],
                        }
                    feed_items_map[feed_id]["items"].append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "published_at": item.get("published_at", ""),
                        "author": item.get("author", ""),
                    })

            # Limit the number of items and add to results
            for feed_id in rss_feed_ids:
                if feed_id in feed_items_map:
                    feed_data = feed_items_map[feed_id]
                    items = feed_data["items"]
                    if max_items > 0:
                        items = items[:max_items]
                    if items:
                        standalone_data["rss_feeds"].append({
                            "id": feed_id,
                            "name": feed_data["name"],
                            "items": items,
                        })

        # If there is no data, return None
        if not standalone_data["platforms"] and not standalone_data["rss_feeds"]:
            return None

        return standalone_data

    def _run_analysis_pipeline(
        self,
        data_source: Dict,
        mode: str,
        title_info: Dict,
        new_titles: Dict,
        word_groups: List[Dict],
        filter_words: List[str],
        id_to_name: Dict,
        failed_ids: Optional[List] = None,
        global_filters: Optional[List[str]] = None,
        quiet: bool = False,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        standalone_data: Optional[Dict] = None,
        schedule: ResolvedSchedule = None,
        rss_new_urls: Optional[set] = None,
    ) -> Tuple[List[Dict], Optional[str], Optional[AIAnalysisResult], Optional[List[Dict]]]:
        """Unified analysis pipeline: Data processing → Statistical calculation (Keyword/AI filtering) → AI analysis → HTML generation"""

        # Select data processing method based on filtering strategy
        if self.filter_method == "ai":
            # === AI filtering strategy ===
            print("[Filter] Use AI intelligent filtering strategy")
            ai_filter_result = self.ctx.run_ai_filter(interests_file=self.interests_file)

            if ai_filter_result and ai_filter_result.success:
                print(f"[Filter] AI filtering completed: {ai_filter_result.total_matched} matches, {len(ai_filter_result.tags)} tags")
                # Convert to the same data structure as keyword matching
                stats, ai_rss_stats = self.ctx.convert_ai_filter_to_report_data(
                    ai_filter_result, mode=mode,
                    new_titles=new_titles, rss_new_urls=rss_new_urls,
                )
                total_titles = sum(len(titles) for titles in data_source.values())

                # Replace keyword matching RSS results with AI filtered RSS results
                if ai_rss_stats:
                    rss_items = ai_rss_stats
            else:
                # AI filtering failed, fallback to keyword matching
                error_msg = ai_filter_result.error if ai_filter_result else "Unknown error"
                print(f"[Filter] AI filtering failed: {error_msg}, fallback to keyword matching")
                stats, total_titles = self.ctx.count_frequency(
                    data_source, word_groups, filter_words,
                    id_to_name, title_info, new_titles,
                    mode=mode, global_filters=global_filters, quiet=quiet,
                )
        else:
            # === Keyword matching strategy (default) ===
            stats, total_titles = self.ctx.count_frequency(
                data_source, word_groups, filter_words,
                id_to_name, title_info, new_titles,
                mode=mode, global_filters=global_filters, quiet=quiet,
            )

        self._hotlist_total_count = total_titles

        # If it is platform mode, convert data structure
        if self.ctx.display_mode == "platform" and stats:
            stats = convert_keyword_stats_to_platform_stats(
                stats,
                self.ctx.weight_config,
                self.ctx.rank_threshold,
            )

        # AI analysis (if enabled, used for HTML report)
        ai_result = None
        ai_config = self.ctx.config.get("AI_ANALYSIS", {})
        if ai_config.get("ENABLED", False) and stats:
            # Get mode strategy to determine report type
            mode_strategy = self._get_mode_strategy()
            report_type = mode_strategy["report_type"]
            ai_result = self._run_ai_analysis(
                stats, rss_items, mode, report_type, id_to_name,
                current_results=data_source, schedule=schedule,
                standalone_data=standalone_data
            )

        # Translate RSS content (if enabled) — execute before HTML generation to ensure web version can also display translated content
        # Note: Only translate rss_items and rss_new_items, do not translate standalone_data (will be regenerated before notification)
        # Hotlist translation is handled by dispatch_all processing report_data during push
        trans_config = self.ctx.config.get("AI_TRANSLATION", {})
        if trans_config.get("ENABLED", False):
            dispatcher = self.ctx.create_notification_dispatcher()
            display_regions = self.ctx.config.get("DISPLAY", {}).get("REGIONS", {})
            _, rss_items, rss_new_items, _ = \
                dispatcher.translate_content(
                    report_data={"stats": [], "new_titles": []},
                    rss_items=rss_items,
                    rss_new_items=rss_new_items,
                    display_regions=display_regions,
                )

        # Calculate RSS matched items count (shared by HTML and push)
        self._rss_matched_count = sum(stat.get("count", 0) for stat in rss_items) if rss_items else 0

        # HTML generation (if enabled) — use translated data
        html_file = None
        if self.ctx.config["STORAGE"]["FORMATS"]["HTML"]:
            display_regions = self.ctx.config.get("DISPLAY", {}).get("REGIONS", {})
            html_standalone = standalone_data if display_regions.get("STANDALONE", False) else None
            html_ai = ai_result if display_regions.get("AI_ANALYSIS", True) else None
            html_file = self.ctx.generate_html(
                stats,
                total_titles,
                failed_ids=failed_ids,
                new_titles=new_titles,
                id_to_name=id_to_name,
                mode=mode,
                update_info=self.update_info if self.ctx.config["SHOW_VERSION_UPDATE"] else None,
                rss_items=rss_items,
                rss_new_items=rss_new_items,
                ai_analysis=html_ai,
                standalone_data=html_standalone,
                frequency_file=self.frequency_file,
                report_metadata={
                    "hotlist_total": total_titles,
                    "platform_total": len(self.ctx.platform_ids),
                    "rss_matched_count": self._rss_matched_count,
                    "rss_total_count": self._rss_total_count,
                    "rss_source_total": self._rss_source_total,
                    "rss_source_failed": self._rss_source_failed,
                },
            )

        return stats, html_file, ai_result, rss_items

    def _send_notification_if_needed(
        self,
        stats: List[Dict],
        report_type: str,
        mode: str,
        failed_ids: Optional[List] = None,
        new_titles: Optional[Dict] = None,
        id_to_name: Optional[Dict] = None,
        html_file_path: Optional[str] = None,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        standalone_data: Optional[Dict] = None,
        ai_result: Optional[AIAnalysisResult] = None,
        current_results: Optional[Dict] = None,
        schedule: ResolvedSchedule = None,
    ) -> bool:
        """Unified notification sending logic, including all judgment conditions, supporting hotlist + RSS merged push + AI analysis + independent display area"""
        has_notification = self._has_notification_configured()
        cfg = self.ctx.config

        # Check if there is valid content (hotlist or RSS)
        has_news_content = self._has_valid_content(stats, new_titles)
        has_rss_content = bool(rss_items and len(rss_items) > 0)
        has_any_content = has_news_content or has_rss_content

        # Calculate hotlist matched items count
        news_count = sum(len(stat.get("titles", [])) for stat in stats) if stats else 0
        rss_count = sum(stat.get("count", 0) for stat in rss_items) if rss_items else 0

        if (
            cfg["ENABLE_NOTIFICATION"]
            and has_notification
            and has_any_content
        ):
            # Output push content statistics
            content_parts = []
            if news_count > 0:
                content_parts.append(f"Hotlist {news_count} items")
            if rss_count > 0:
                content_parts.append(f"RSS {rss_count} items")
            total_count = news_count + rss_count
            print(f"[Push] Ready to send: {' + '.join(content_parts)}, total {total_count} items")

            # Scheduling system decision
            if not schedule.push:
                print("[Push] Scheduler: Do not execute push in current time period")
                return False

            if schedule.once_push and schedule.period_key:
                scheduler = self.ctx.create_scheduler()
                date_str = self.ctx.format_date()
                if scheduler.already_executed(schedule.period_key, "push", date_str):
                    print(f"[Push] Scheduler: Time period {schedule.period_name or schedule.period_key} has already been pushed today, skip")
                    return False
                else:
                    print(f"[Push] Scheduler: Time period {schedule.period_name or schedule.period_key} first push today")

            # AI analysis: Prioritize using passed results to avoid repeated analysis
            if ai_result is None:
                ai_config = cfg.get("AI_ANALYSIS", {})
                if ai_config.get("ENABLED", False):
                    ai_result = self._run_ai_analysis(
                        stats, rss_items, mode, report_type, id_to_name,
                        current_results=current_results, schedule=schedule
                    )

            # Prepare report data
            report_data = self.ctx.prepare_report(stats, failed_ids, new_titles, id_to_name, mode, frequency_file=self.frequency_file)

            # Inject metadata (used for push header display)
            report_data["hotlist_total"] = self._hotlist_total_count
            report_data["platform_total"] = len(self.ctx.platform_ids)
            report_data["rss_matched_count"] = self._rss_matched_count
            report_data["rss_total_count"] = self._rss_total_count
            report_data["rss_source_total"] = self._rss_source_total
            report_data["rss_source_failed"] = self._rss_source_failed

            # Whether to send version Cập nhật information
            update_info_to_send = self.update_info if cfg["SHOW_VERSION_UPDATE"] else None

            # Use NotificationDispatcher to send to all channels
            # RSS/independent display area data has already been translated in the analysis pipeline, skip repeated translation (only translate hotlist report_data)
            dispatcher = self.ctx.create_notification_dispatcher()
            results = dispatcher.dispatch_all(
                report_data=report_data,
                report_type=report_type,
                update_info=update_info_to_send,
                proxy_url=self.proxy_url,
                mode=mode,
                html_file_path=html_file_path,
                rss_items=rss_items,
                rss_new_items=rss_new_items,
                ai_analysis=ai_result,
                standalone_data=standalone_data,
                skip_translation=True,
            )

            if not results:
                print("No notification channels configured, skip notification sending")
                return False

            # Record push success
            if any(results.values()):
                if schedule.once_push and schedule.period_key:
                    scheduler = self.ctx.create_scheduler()
                    date_str = self.ctx.format_date()
                    scheduler.record_execution(schedule.period_key, "push", date_str)

            return True

        elif cfg["ENABLE_NOTIFICATION"] and not has_notification:
            print("⚠️ Warning: Notification function is enabled but no notification channels are configured, will skip notification sending")
        elif not cfg["ENABLE_NOTIFICATION"]:
            print(f"Skip {report_type} notification: Notification function is disabled")
        elif (
            cfg["ENABLE_NOTIFICATION"]
            and has_notification
            and not has_any_content
        ):
            mode_strategy = self._get_mode_strategy()
            if self.report_mode == "incremental":
                if not has_rss_content:
                    print("Skip notification: No matched news and RSS detected in incremental mode")
                else:
                    print("Skip notification: News did not match keywords in incremental mode")
            else:
                print(
                    f"Skip notification: No matched news detected under {mode_strategy['mode_name']}"
                )

        return False

    def _initialize_and_check_config(self) -> bool:
        """General initialization and configuration check. Returning True means execution can continue."""
        now = self.ctx.get_time()
        print(f"Thời gian hiện tại (Việt Nam): {now.strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.ctx.config["ENABLE_CRAWLER"]:
            print("Crawler function is disabled (ENABLE_CRAWLER=False), program exits")
            return False

        has_notification = self._has_notification_configured()
        if not self.ctx.config["ENABLE_NOTIFICATION"]:
            print("Notification function is disabled (ENABLE_NOTIFICATION=False), will only perform data crawling")
        elif not has_notification:
            print("No notification channels configured, will only perform data crawling, do not send notifications")
        else:
            print("Notification feature enabled, notifications will be sent")

        mode_strategy = self._get_mode_strategy()
        print(f"Report mode: {self.report_mode}")
        print(f"Run mode: {mode_strategy['description']}")
        return True

    def _crawl_data(self) -> Tuple[Dict, Dict, List]:
        """Execute data crawling"""
        ids = []
        for platform in self.ctx.platforms:
            if "name" in platform:
                ids.append((platform["id"], platform["name"]))
            else:
                ids.append(platform["id"])

        print(
            f"Configured monitoring platforms: {[p.get('name', p['id']) for p in self.ctx.platforms]}"
        )
        print(f"Start crawling data, request interval {self.request_interval} milliseconds")
        Path("output").mkdir(parents=True, exist_ok=True)

        results, id_to_name, failed_ids = self.data_fetcher.crawl_websites(
            ids, self.request_interval
        )

        # Convert to NewsData format and save to storage backend
        crawl_time = self.ctx.format_time()
        crawl_date = self.ctx.format_date()
        news_data = convert_crawl_results_to_news_data(
            results, id_to_name, failed_ids, crawl_time, crawl_date
        )

        # Save to storage backend (SQLite)
        if self.storage_manager.save_news_data(news_data):
            print(f"Data saved to storage backend: {self.storage_manager.backend_name}")

        # Save TXT snapshot (if enabled)
        txt_file = self.storage_manager.save_txt_snapshot(news_data)
        if txt_file:
            print(f"TXT snapshot saved: {txt_file}")

        return results, id_to_name, failed_ids

    def _crawl_rss_data(self) -> Tuple[Optional[List[Dict]], Optional[List[Dict]], Optional[List[Dict]], set]:
        """
        Execute RSS data scraping

        Returns:
            (rss_items, rss_new_items, raw_rss_items, rss_new_urls) tuple:
            - rss_items: Statistics item list (processed by mode, used for statistics block)
            - rss_new_items: New item list (used for new block)
            - raw_rss_items: Raw RSS item list (used for independent display area)
            - rss_new_urls: URL set of raw new RSS items (used for AI mode is_new detection)
            If not enabled or failed, return (None, None, None, set())
        """
        crawler_bot_config = self.ctx.config.get("crawler_bot", {})
        crawler_bot_enabled = crawler_bot_config.get("enabled", False)

        if not self.ctx.rss_enabled and not crawler_bot_enabled:
            return None, None, None, set()

        from trendradar.storage.base import RSSData
        crawl_time = datetime.now().strftime("%H:%M")
        crawl_date = datetime.now().strftime("%Y-%m-%d")
        rss_data = RSSData(date=crawl_date, crawl_time=crawl_time, items={})

        rss_feeds = self.ctx.rss_feeds
        if self.ctx.rss_enabled and rss_feeds:
            try:
                from trendradar.crawler.rss import RSSFetcher, RSSFeedConfig

                # Build RSS source configuration
                feeds = []
                for feed_config in rss_feeds:
                    max_age_days_raw = feed_config.get("max_age_days")
                    max_age_days = None
                    if max_age_days_raw is not None:
                        try:
                            max_age_days = int(max_age_days_raw)
                            if max_age_days < 0:
                                max_age_days = None
                        except (ValueError, TypeError):
                            max_age_days = None

                    feed = RSSFeedConfig(
                        id=feed_config.get("id", ""),
                        name=feed_config.get("name", ""),
                        url=feed_config.get("url", ""),
                        max_items=feed_config.get("max_items", 50),
                        enabled=feed_config.get("enabled", True),
                        max_age_days=max_age_days,
                    )
                    if feed.id and feed.url and feed.enabled:
                        feeds.append(feed)

                if feeds:
                    rss_config = self.ctx.rss_config
                    rss_proxy_url = rss_config.get("PROXY_URL", "") or self.proxy_url or ""
                    tz = self.ctx.config.get("TIMEZONE", DEFAULT_TIMEZONE)
                    freshness_config = rss_config.get("FRESHNESS_FILTER", {})
                    freshness_enabled = freshness_config.get("ENABLED", True)
                    default_max_age_days = freshness_config.get("MAX_AGE_DAYS", 3)

                    fetcher = RSSFetcher(
                        feeds=feeds,
                        request_interval=rss_config.get("REQUEST_INTERVAL", 2000),
                        timeout=rss_config.get("TIMEOUT", 15),
                        use_proxy=rss_config.get("USE_PROXY", False),
                        proxy_url=rss_proxy_url,
                        timezone=tz,
                        freshness_enabled=freshness_enabled,
                        default_max_age_days=default_max_age_days,
                    )

                    fetched_rss_data = fetcher.fetch_all()
                    rss_data = fetched_rss_data
                    self._rss_source_total = len(feeds)
                    self._rss_source_failed = len(rss_data.failed_ids)
            except Exception as e:
                print(f"[RSS] Scraping failed: {e}")

        # --- 2. Scrape Crawler Bot data ---
        if crawler_bot_enabled:
            try:
                # Chạy LLM Crawler (Playwright + 9Router) để sinh dữ liệu mới
                try:
                    from trendradar.crawler.llm_bot.pipeline import run_llm_crawler_sync
                    print("[CrawlerBot] Bắt đầu chạy LLM Bot Crawler để lấy tin tức mới...")
                    run_llm_crawler_sync()
                except Exception as e:
                    print(f"[CrawlerBot] Lỗi khi chạy LLM Bot Crawler: {e}")

                from trendradar.crawler import CrawlerBotFetcher
                output_dir = crawler_bot_config.get("output_dir", "llm_news_crawler_bot/output")
                mark_as_processed = crawler_bot_config.get("mark_as_processed", True)
                tz = self.ctx.config.get("TIMEZONE", DEFAULT_TIMEZONE)
                
                bot_fetcher = CrawlerBotFetcher(output_dir, mark_as_processed)
                bot_data = bot_fetcher.fetch_all(tz, rss_data.crawl_time, rss_data.date)
                
                # Merge bot_data into rss_data
                for feed_id, items in bot_data.items.items():
                    if feed_id in rss_data.items:
                        rss_data.items[feed_id].extend(items)
                    else:
                        rss_data.items[feed_id] = items
                        
                for feed_id, feed_name in bot_data.id_to_name.items():
                    rss_data.id_to_name[feed_id] = feed_name
                    
                self._rss_source_total += len(bot_data.id_to_name)
            except Exception as e:
                print(f"[CrawlerBot] Lỗi khi lấy dữ liệu: {e}")

        total_items = sum(len(items) for items in rss_data.items.values())
        if total_items == 0:
            print("[RSS/Crawler] Không có dữ liệu mới.")
            return None, None, None, set()

        # Save to storage backend
        if self.storage_manager.save_rss_data(rss_data):
            print(f"[RSS/Crawler] Data saved to storage backend (Tổng: {total_items} bài viết)")
            return self._process_rss_data_by_mode(rss_data)
        else:
            print(f"[RSS/Crawler] Data saving failed")
            return None, None, None, set()

    def _process_rss_data_by_mode(self, rss_data) -> Tuple[Optional[List[Dict]], Optional[List[Dict]], Optional[List[Dict]], set]:
        """
        Process RSS data according to report mode, return statistics structure in the same format as the hot list

        Three modes:
        - daily: Daily summary, statistics=all items of the day, new=new items this time
        - current: Bảng xếp hạng hiện tại, statistics=Bảng xếp hạng hiện tại items, new=new items this time
        - incremental: Incremental mode, statistics=new items, new=none

        Args:
            rss_data: Currently scraped RSSData object

        Returns:
            (rss_stats, rss_new_stats, raw_rss_items, rss_new_urls) tuple:
            - rss_stats: RSS keyword statistics list (consistent with hot list stats format)
            - rss_new_stats: RSS new keyword statistics list (consistent with hot list stats format)
            - raw_rss_items: Raw RSS item list (used for independent display area)
            - rss_new_urls: URL set of raw new RSS items (unfiltered by keywords, used for AI mode is_new detection)
        """
        from trendradar.core.analyzer import count_rss_frequency

        # Unified control of RSS analysis and display from display.regions.rss
        rss_display_enabled = self.ctx.config.get("DISPLAY", {}).get("REGIONS", {}).get("RSS", True)

        # Load keyword configuration
        try:
            word_groups, filter_words, global_filters = self.ctx.load_frequency_words(self.frequency_file)
        except FileNotFoundError:
            word_groups, filter_words, global_filters = [], [], []

        timezone = self.ctx.timezone
        max_news_per_keyword = self.ctx.config.get("MAX_NEWS_PER_KEYWORD", 0)
        sort_by_position_first = self.ctx.config.get("SORT_BY_POSITION_FIRST", False)

        rss_stats = None
        rss_new_stats = None
        raw_rss_items = None  # Raw RSS item list (used for independent display area)
        rss_new_urls = set()  # Raw new RSS URLs (unfiltered by keywords)

        # 1. First get raw items (used for independent display area, unaffected by display.regions.rss)
        # Get raw items based on mode
        if self.report_mode == "incremental":
            new_items_dict = self.storage_manager.detect_new_rss_items(rss_data)
            if new_items_dict:
                raw_rss_items = self._convert_rss_items_to_list(new_items_dict, rss_data.id_to_name)
        elif self.report_mode == "current":
            latest_data = self.storage_manager.get_latest_rss_data(rss_data.date)
            if latest_data:
                raw_rss_items = self._convert_rss_items_to_list(latest_data.items, latest_data.id_to_name)
        else:  # daily
            all_data = self.storage_manager.get_rss_data(rss_data.date)
            if all_data:
                raw_rss_items = self._convert_rss_items_to_list(all_data.items, all_data.id_to_name)

        # If RSS display is not enabled, skip keyword analysis and only return raw items for the independent display area
        if not rss_display_enabled:
            return None, None, raw_rss_items, rss_new_urls

        # 2. Get new items (for statistics)
        new_items_dict = self.storage_manager.detect_new_rss_items(rss_data)
        new_items_list = None
        if new_items_dict:
            new_items_list = self._convert_rss_items_to_list(new_items_dict, rss_data.id_to_name)
            if new_items_list:
                print(f"[RSS] Detected {len(new_items_list)} new items")
                # Collect raw new URLs (without keyword filtering, used for AI mode is_new detection)
                rss_new_urls = {item["url"] for item in new_items_list if item.get("url")}

        # 3. Get statistical items based on mode
        if self.report_mode == "incremental":
            # Incremental mode: statistical items are the new items
            if not new_items_list:
                print("[RSS] Incremental mode: No new RSS items")
                return None, None, raw_rss_items, rss_new_urls

            rss_stats, total = count_rss_frequency(
                rss_items=new_items_list,
                word_groups=word_groups,
                filter_words=filter_words,
                global_filters=global_filters,
                new_items=new_items_list,  # Incremental mode: all are new
                max_news_per_keyword=max_news_per_keyword,
                sort_by_position_first=sort_by_position_first,
                timezone=timezone,
                rank_threshold=self.rank_threshold,
                quiet=False,
            )
            if not rss_stats:
                print("[RSS] Incremental mode: No content after keyword matching")
                # Even if keyword matching is empty, return raw items for the independent display area
                return None, None, raw_rss_items, rss_new_urls

        elif self.report_mode == "current":
            # Bảng xếp hạng hiện tại mode: statistics = Bảng xếp hạng hiện tại all items
            # raw_rss_items already obtained earlier
            if not raw_rss_items:
                print("[RSS] Bảng xếp hạng hiện tại mode: No RSS data")
                return None, None, None, rss_new_urls

            rss_stats, total = count_rss_frequency(
                rss_items=raw_rss_items,
                word_groups=word_groups,
                filter_words=filter_words,
                global_filters=global_filters,
                new_items=new_items_list,  # Mark as new
                max_news_per_keyword=max_news_per_keyword,
                sort_by_position_first=sort_by_position_first,
                timezone=timezone,
                rank_threshold=self.rank_threshold,
                quiet=False,
            )
            if not rss_stats:
                print("[RSS] Bảng xếp hạng hiện tại mode: No content after keyword matching")
                # Even if keyword matching is empty, return raw items for the independent display area
                return None, None, raw_rss_items, rss_new_urls

            # Generate new statistics
            if new_items_list:
                rss_new_stats, _ = count_rss_frequency(
                    rss_items=new_items_list,
                    word_groups=word_groups,
                    filter_words=filter_words,
                    global_filters=global_filters,
                    new_items=new_items_list,
                    max_news_per_keyword=max_news_per_keyword,
                    sort_by_position_first=sort_by_position_first,
                    timezone=timezone,
                    rank_threshold=self.rank_threshold,
                    quiet=True,
                )

        else:
            # daily mode: statistics = all items of the day
            # raw_rss_items already obtained earlier
            if not raw_rss_items:
                print("[RSS] Daily summary mode: No RSS data")
                return None, None, None, rss_new_urls

            rss_stats, total = count_rss_frequency(
                rss_items=raw_rss_items,
                word_groups=word_groups,
                filter_words=filter_words,
                global_filters=global_filters,
                new_items=new_items_list,  # Mark as new
                max_news_per_keyword=max_news_per_keyword,
                sort_by_position_first=sort_by_position_first,
                timezone=timezone,
                rank_threshold=self.rank_threshold,
                quiet=False,
            )
            if not rss_stats:
                print("[RSS] Daily summary mode: No content after keyword matching")
                # Even if keyword matching is empty, return raw items for the independent display area
                return None, None, raw_rss_items, rss_new_urls

            # Generate new statistics
            if new_items_list:
                rss_new_stats, _ = count_rss_frequency(
                    rss_items=new_items_list,
                    word_groups=word_groups,
                    filter_words=filter_words,
                    global_filters=global_filters,
                    new_items=new_items_list,
                    max_news_per_keyword=max_news_per_keyword,
                    sort_by_position_first=sort_by_position_first,
                    timezone=timezone,
                    rank_threshold=self.rank_threshold,
                    quiet=True,
                )

        self._rss_total_count = total
        return rss_stats, rss_new_stats, raw_rss_items, rss_new_urls

    def _convert_rss_items_to_list(self, items_dict: Dict, id_to_name: Dict) -> List[Dict]:
        """Convert RSS item dictionary to list format and apply freshness filtering (for pushing)"""
        rss_items = []
        filtered_count = 0
        filtered_details = []  # Used for detailed logs in DEBUG mode

        # Get freshness filtering configuration
        rss_config = self.ctx.rss_config
        freshness_config = rss_config.get("FRESHNESS_FILTER", {})
        freshness_enabled = freshness_config.get("ENABLED", True)
        default_max_age_days = freshness_config.get("MAX_AGE_DAYS", 3)
        timezone = self.ctx.config.get("TIMEZONE", DEFAULT_TIMEZONE)
        debug_mode = self.ctx.config.get("DEBUG", False)

        # Build mapping of feed_id -> max_age_days
        feed_max_age_map = {}
        for feed_cfg in self.ctx.rss_feeds:
            feed_id = feed_cfg.get("id", "")
            max_age = feed_cfg.get("max_age_days")
            if max_age is not None:
                try:
                    feed_max_age_map[feed_id] = int(max_age)
                except (ValueError, TypeError):
                    pass

        for feed_id, items in items_dict.items():
            # Determine max_age_days for this feed
            max_days = feed_max_age_map.get(feed_id)
            if max_days is None:
                max_days = default_max_age_days

            for item in items:
                # Apply freshness filtering (only when enabled)
                if freshness_enabled and max_days > 0:
                    if item.published_at and not is_within_days(item.published_at, max_days, timezone):
                        filtered_count += 1
                        # Record detailed information for DEBUG mode
                        if debug_mode:
                            days_old = calculate_days_old(item.published_at, timezone)
                            feed_name = id_to_name.get(feed_id, feed_id)
                            filtered_details.append({
                                "title": item.title[:50] + "..." if len(item.title) > 50 else item.title,
                                "feed": feed_name,
                                "days_old": days_old,
                                "max_days": max_days,
                            })
                        continue  # Skip articles exceeding the specified number of days

                rss_items.append({
                    "title": item.title,
                    "feed_id": feed_id,
                    "feed_name": id_to_name.get(feed_id, feed_id),
                    "url": item.url,
                    "published_at": item.published_at,
                    "summary": item.summary,
                    "author": item.author,
                })

        # Output filtering statistics
        if filtered_count > 0:
            print(f"[RSS] Freshness filtering: Skipped {filtered_count} old articles exceeding the specified number of days (still kept in the database)")
            # Show detailed information in DEBUG mode
            if debug_mode and filtered_details:
                print(f"[RSS] Filtered article details (total {len(filtered_details)} articles):")
                for detail in filtered_details[:10]:  # Show up to 10 items
                    days_str = f"{detail['days_old']:.1f}" if detail['days_old'] else "Unknown"
                    print(f"  - [{days_str} days ago] [{detail['feed']}] {detail['title']} (Limit: {detail['max_days']} days)")
                if len(filtered_details) > 10:
                    print(f"  ... and {len(filtered_details) - 10} more filtered")

        return rss_items

    def _filter_rss_by_keywords(self, rss_items: List[Dict]) -> List[Dict]:
        """Filter RSS items using keyword file"""
        try:
            word_groups, filter_words, global_filters = self.ctx.load_frequency_words(self.frequency_file)
            if word_groups or filter_words or global_filters:
                from trendradar.core.frequency import matches_word_groups
                filtered_items = []
                for item in rss_items:
                    title = item.get("title", "")
                    if matches_word_groups(title, word_groups, filter_words, global_filters):
                        filtered_items.append(item)

                original_count = len(rss_items)
                rss_items = filtered_items
                print(f"[RSS] Remaining after keyword filtering: {len(rss_items)}/{original_count} items")

                if not rss_items:
                    print("[RSS] No matching content after keyword filtering")
                    return []
        except FileNotFoundError:
            # Skip filtering when keyword file does not exist
            pass
        return rss_items

    def _generate_rss_html_report(self, rss_items: list, feeds_info: dict) -> str:
        """Generate RSS HTML report"""
        try:
            from trendradar.report.rss_html import render_rss_html_content
            from pathlib import Path

            html_content = render_rss_html_content(
                rss_items=rss_items,
                total_count=len(rss_items),
                feeds_info=feeds_info,
                get_time_func=self.ctx.get_time,
            )

            # Save HTML file (flattened structure: output/html/date/)
            date_folder = self.ctx.format_date()
            time_filename = self.ctx.format_time()
            output_dir = Path("output") / "html" / date_folder
            output_dir.mkdir(parents=True, exist_ok=True)

            file_path = output_dir / f"rss_{time_filename}.html"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"[RSS] HTML report generated: {file_path}")
            return str(file_path)

        except Exception as e:
            print(f"[RSS] Failed to generate HTML report: {e}")
            return None

    def _execute_mode_strategy(
        self, mode_strategy: Dict, results: Dict, id_to_name: Dict, failed_ids: List,
        rss_items: Optional[List[Dict]] = None,
        rss_new_items: Optional[List[Dict]] = None,
        raw_rss_items: Optional[List[Dict]] = None,
        rss_new_urls: Optional[set] = None,
    ) -> Optional[str]:
        """Execute mode-specific logic, support combined push of hotlist + RSS

        Simplified logic:
        - Generate HTML report on every run (timestamp snapshot + latest/{mode}.html + index.html)
        - Send notifications based on mode
        """
        # Scheduling system
        scheduler = self.ctx.create_scheduler()
        schedule = scheduler.resolve()

        # Override global config with report_mode determined by schedule
        effective_mode = schedule.report_mode
        if effective_mode != self.report_mode:
            print(f"[Schedule] Report mode override: {self.report_mode} -> {effective_mode}")
        self.report_mode = effective_mode

        # Re-fetch mode_strategy to ensure report_type is consistent with the overridden report_mode
        mode_strategy = self._get_mode_strategy()

        # Override default value with frequency_file determined by schedule
        self.frequency_file = schedule.frequency_file

        # Override default value with filtering strategy determined by schedule
        self.filter_method = schedule.filter_method or self.ctx.filter_method

        # Override default value with AI filtering interest file determined by schedule
        self.interests_file = schedule.interests_file

        # If the scheduler says not to collect, skip directly
        if not schedule.collect:
            print("[Schedule] Data collection is not executed in the current time period, skipping analysis pipeline")
            return None
        # Get the list of current monitoring platform IDs
        current_platform_ids = self.ctx.platform_ids

        new_titles = self.ctx.detect_new_titles(current_platform_ids)
        time_info = self.ctx.format_time()
        word_groups, filter_words, global_filters = self.ctx.load_frequency_words(self.frequency_file)

        html_file = None
        stats = []
        ai_result = None
        title_info = None

        # current mode needs to use complete historical data
        if self.report_mode == "current":
            analysis_data = self._load_analysis_data()
            if analysis_data:
                (
                    all_results,
                    historical_id_to_name,
                    historical_title_info,
                    historical_new_titles,
                    _,
                    _,
                    _,
                ) = analysis_data

                print(
                    f"current mode: using filtered historical data, including platforms: {list(all_results.keys())}"
                )

                # Use historical data to prepare independent display area data (including complete title_info)
                standalone_data = self._prepare_standalone_data(
                    all_results, historical_id_to_name, historical_title_info, raw_rss_items
                )

                stats, html_file, ai_result, rss_items = self._run_analysis_pipeline(
                    all_results,
                    self.report_mode,
                    historical_title_info,
                    historical_new_titles,
                    word_groups,
                    filter_words,
                    historical_id_to_name,
                    failed_ids=failed_ids,
                    global_filters=global_filters,
                    rss_items=rss_items,
                    rss_new_items=rss_new_items,
                    standalone_data=standalone_data,
                    schedule=schedule,
                    rss_new_urls=rss_new_urls,
                )

                combined_id_to_name = {**historical_id_to_name, **id_to_name}
                new_titles = historical_new_titles
                id_to_name = combined_id_to_name
                title_info = historical_title_info
                results = all_results
            else:
                print("❌ Fatal error: Cannot read the newly saved data file")
                raise RuntimeError("Data consistency check failed: Failed to read immediately after saving")
        elif self.report_mode == "daily":
            # daily mode: use all-day accumulated data
            analysis_data = self._load_analysis_data()
            if analysis_data:
                (
                    all_results,
                    historical_id_to_name,
                    historical_title_info,
                    historical_new_titles,
                    _,
                    _,
                    _,
                ) = analysis_data

                # Use historical data to prepare independent display area data (including complete title_info)
                standalone_data = self._prepare_standalone_data(
                    all_results, historical_id_to_name, historical_title_info, raw_rss_items
                )

                stats, html_file, ai_result, rss_items = self._run_analysis_pipeline(
                    all_results,
                    self.report_mode,
                    historical_title_info,
                    historical_new_titles,
                    word_groups,
                    filter_words,
                    historical_id_to_name,
                    failed_ids=failed_ids,
                    global_filters=global_filters,
                    rss_items=rss_items,
                    rss_new_items=rss_new_items,
                    standalone_data=standalone_data,
                    schedule=schedule,
                    rss_new_urls=rss_new_urls,
                )

                combined_id_to_name = {**historical_id_to_name, **id_to_name}
                new_titles = historical_new_titles
                id_to_name = combined_id_to_name
                title_info = historical_title_info
                results = all_results
            else:
                # Use current data when there is no historical data
                title_info = self._prepare_current_title_info(results, time_info)
                standalone_data = self._prepare_standalone_data(
                    results, id_to_name, title_info, raw_rss_items
                )
                stats, html_file, ai_result, rss_items = self._run_analysis_pipeline(
                    results,
                    self.report_mode,
                    title_info,
                    new_titles,
                    word_groups,
                    filter_words,
                    id_to_name,
                    failed_ids=failed_ids,
                    global_filters=global_filters,
                    rss_items=rss_items,
                    rss_new_items=rss_new_items,
                    standalone_data=standalone_data,
                    schedule=schedule,
                    rss_new_urls=rss_new_urls,
                )
        else:
            # incremental mode: only use currently fetched data
            title_info = self._prepare_current_title_info(results, time_info)
            standalone_data = self._prepare_standalone_data(
                results, id_to_name, title_info, raw_rss_items
            )
            stats, html_file, ai_result, rss_items = self._run_analysis_pipeline(
                results,
                self.report_mode,
                title_info,
                new_titles,
                word_groups,
                filter_words,
                id_to_name,
                failed_ids=failed_ids,
                global_filters=global_filters,
                rss_items=rss_items,
                rss_new_items=rss_new_items,
                standalone_data=standalone_data,
                schedule=schedule,
                rss_new_urls=rss_new_urls,
            )

        if html_file:
            print(f"HTML report generated: {html_file}")
            print(f"Latest report Cập nhật: output/html/latest/{self.report_mode}.html")

        # Send notifications
        if mode_strategy["should_send_notification"]:
            standalone_data = self._prepare_standalone_data(
                results, id_to_name, title_info, raw_rss_items
            )
            self._send_notification_if_needed(
                stats,
                mode_strategy["report_type"],
                self.report_mode,
                failed_ids=failed_ids,
                new_titles=new_titles,
                id_to_name=id_to_name,
                html_file_path=html_file,
                rss_items=rss_items,
                rss_new_items=rss_new_items,
                standalone_data=standalone_data,
                ai_result=ai_result,
                current_results=results,
                schedule=schedule,
            )

        # Open browser (only in non-container environment)
        if self._should_open_browser() and html_file:
            file_url = "file://" + str(Path(html_file).resolve())
            print(f"Opening HTML report: {file_url}")
            webbrowser.open(file_url)
        elif self.is_docker_container and html_file:
            print(f"HTML report generated (Docker environment): {html_file}")

        return html_file

    def run(self) -> None:
        """Execute analysis process"""
        try:
            if not self._initialize_and_check_config():
                return

            mode_strategy = self._get_mode_strategy()

            # Fetch hotlist data
            results, id_to_name, failed_ids = self._crawl_data()

            # Fetch RSS data (if enabled), return statistical items, new items, and original items
            rss_items, rss_new_items, raw_rss_items, rss_new_urls = self._crawl_rss_data()

            # Execute mode strategy, pass RSS data for merged push
            self._execute_mode_strategy(
                mode_strategy, results, id_to_name, failed_ids,
                rss_items=rss_items, rss_new_items=rss_new_items,
                raw_rss_items=raw_rss_items, rss_new_urls=rss_new_urls
            )

        except Exception as e:
            print(f"Analysis process execution error: {e}")
            if self.ctx.config.get("DEBUG", False):
                raise
        finally:
            # Clean up resources (including expired data cleanup and database connection closure)
            self.ctx.cleanup()


def _record_doctor_result(results: List[Tuple[str, str, str]], status: str, item: str, detail: str) -> None:
    """Record and print doctor check results"""
    icon_map = {
        "pass": "✅",
        "warn": "⚠️",
        "fail": "❌",
    }
    icon = icon_map.get(status, "•")
    results.append((status, item, detail))
    print(f"{icon} {item}: {detail}")


def _save_doctor_report(
    results: List[Tuple[str, str, str]],
    pass_count: int,
    warn_count: int,
    fail_count: int,
    config_path: Optional[str],
) -> None:
    """Save doctor examination report to JSON file"""
    report = {
        "version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": config_path or os.environ.get("CONFIG_PATH", "config/config.yaml"),
        "summary": {
            "pass": pass_count,
            "warn": warn_count,
            "fail": fail_count,
            "ok": fail_count == 0,
        },
        "checks": [
            {"status": status, "item": item, "detail": detail}
            for status, item, detail in results
        ],
    }

    try:
        output_dir = Path("output") / "meta"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "doctor_report.json"
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Examination report saved: {output_path}")
    except Exception as e:
        print(f"⚠️ Examination report save failed: {e}")


def _run_doctor(config_path: Optional[str] = None) -> bool:
    """Run environment examination"""
    print("=" * 60)
    print(f"TrendRadar v{__version__} environment examination")
    print("=" * 60)

    results: List[Tuple[str, str, str]] = []
    config = None

    # 1) Python version check
    py_ok = sys.version_info >= (3, 10)
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if py_ok:
        _record_doctor_result(results, "pass", "Python version", f"{py_version} (Satisfies >= 3.10)")
    else:
        _record_doctor_result(results, "fail", "Python version", f"{py_version} (Does not satisfy >= 3.10)")

    # 2) Key file check
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", "config/config.yaml")

    required_files = [
        (config_path, "Main configuration file"),
        ("config/frequency_words.txt", "Keyword file"),
    ]
    optional_files = [
        ("config/timeline.yaml", "Schedule file"),
    ]

    for path_str, desc in required_files:
        if Path(path_str).exists():
            _record_doctor_result(results, "pass", desc, f"Found: {path_str}")
        else:
            _record_doctor_result(results, "fail", desc, f"Missing: {path_str}")

    for path_str, desc in optional_files:
        if Path(path_str).exists():
            _record_doctor_result(results, "pass", desc, f"Found: {path_str}")
        else:
            _record_doctor_result(results, "warn", desc, f"Not found: {path_str} (Will use default schedule template)")

    # 3) Configuration load check
    try:
        config = load_config(config_path)
        _record_doctor_result(results, "pass", "Configuration load", f"Load successful: {config_path}")
    except Exception as e:
        _record_doctor_result(results, "fail", "Configuration load", f"Load failed: {e}")

    # Subsequent checks depend on configuration object
    if config:
        # 4) Schedule configuration check
        try:
            ctx = AppContext(config)
            schedule = ctx.create_scheduler().resolve()
            detail = f"Schedule parsing successful (report_mode={schedule.report_mode}, ai_mode={schedule.ai_mode})"
            _record_doctor_result(results, "pass", "Schedule configuration", detail)
        except Exception as e:
            _record_doctor_result(results, "fail", "Schedule configuration", f"Parsing failed: {e}")

        # 5) AI configuration check (distinguish severity levels by functional scenario)
        ai_analysis_enabled = config.get("AI_ANALYSIS", {}).get("ENABLED", False)
        ai_translation_enabled = config.get("AI_TRANSLATION", {}).get("ENABLED", False)
        ai_filter_enabled = config.get("FILTER", {}).get("METHOD", "keyword") == "ai"
        ai_enabled = ai_analysis_enabled or ai_translation_enabled or ai_filter_enabled

        if ai_enabled:
            try:
                from trendradar.ai.client import AIClient
                valid, message = AIClient(config.get("AI", {})).validate_config()
                if valid:
                    _record_doctor_result(results, "pass", "AI configuration", f"Model: {config.get('AI', {}).get('MODEL', '')}")
                else:
                    # AI analysis/translation is a hard dependency; when AI filtering is missing, it will automatically fallback to keyword matching
                    if ai_analysis_enabled or ai_translation_enabled:
                        _record_doctor_result(results, "fail", "AI configuration", message)
                    else:
                        _record_doctor_result(results, "warn", "AI configuration", f"{message} (AI filtering will fallback to keyword mode)")
            except Exception as e:
                _record_doctor_result(results, "fail", "AI configuration", f"Validation exception: {e}")
        else:
            _record_doctor_result(results, "warn", "AI configuration", "AI function not enabled, skipping validation")

        # 6) Storage configuration check
        try:
            storage_cfg = config.get("STORAGE", {})
            backend = storage_cfg.get("BACKEND", "auto")
            remote = storage_cfg.get("REMOTE", {})
            missing_remote_keys = [
                k for k in ("BUCKET_NAME", "ACCESS_KEY_ID", "SECRET_ACCESS_KEY", "ENDPOINT_URL")
                if not remote.get(k)
            ]

            if backend == "remote" and missing_remote_keys:
                _record_doctor_result(
                    results, "fail", "Storage configuration",
                    f"remote mode missing configuration: {', '.join(missing_remote_keys)}"
                )
            elif backend == "auto" and os.environ.get("GITHUB_ACTIONS") == "true" and missing_remote_keys:
                _record_doctor_result(
                    results, "warn", "Storage configuration",
                    "GitHub Actions + auto mode has not fully configured remote storage, which may cause data loss"
                )
            else:
                sm = AppContext(config).get_storage_manager()
                _record_doctor_result(results, "pass", "Storage Configuration", f"Current backend: {sm.backend_name}")
        except Exception as e:
            _record_doctor_result(results, "fail", "Storage Configuration", f"Check failed: {e}")

        # 7) Notification channel configuration check
        channel_details = []
        channel_issues = []
        max_accounts = config.get("MAX_ACCOUNTS_PER_CHANNEL", 3)

        # Normal single-value/multi-value channels
        for key, name in [
            ("FEISHU_WEBHOOK_URL", "Feishu"),
            ("DINGTALK_WEBHOOK_URL", "DingTalk"),
            ("WEWORK_WEBHOOK_URL", "WeCom"),
            ("BARK_URL", "Bark"),
            ("SLACK_WEBHOOK_URL", "Slack"),
            ("GENERIC_WEBHOOK_URL", "Generic Webhook"),
        ]:
            values = parse_multi_account_config(config.get(key, ""))
            if values:
                channel_details.append(f"{name}({min(len(values), max_accounts)})")

        # Telegram pairing validation
        tg_tokens = parse_multi_account_config(config.get("TELEGRAM_BOT_TOKEN", ""))
        tg_chats = parse_multi_account_config(config.get("TELEGRAM_CHAT_ID", ""))
        if tg_tokens or tg_chats:
            valid, count = validate_paired_configs(
                {"bot_token": tg_tokens, "chat_id": tg_chats},
                "Telegram",
                required_keys=["bot_token", "chat_id"],
            )
            if valid and count > 0:
                channel_details.append(f"Telegram({min(count, max_accounts)})")
            else:
                channel_issues.append("Telegram bot_token/chat_id configuration incomplete or quantity inconsistent")

        # ntfy pairing validation (token optional)
        ntfy_server = config.get("NTFY_SERVER_URL", "")
        ntfy_topics = parse_multi_account_config(config.get("NTFY_TOPIC", ""))
        ntfy_tokens = parse_multi_account_config(config.get("NTFY_TOKEN", ""))
        if ntfy_server and ntfy_topics:
            if ntfy_tokens:
                valid, count = validate_paired_configs(
                    {"topic": ntfy_topics, "token": ntfy_tokens},
                    "ntfy",
                )
                if valid and count > 0:
                    channel_details.append(f"ntfy({min(count, max_accounts)})")
                else:
                    channel_issues.append("ntfy topic/token quantity inconsistent")
            else:
                channel_details.append(f"ntfy({min(len(ntfy_topics), max_accounts)})")

        # Email configuration completeness
        email_ready = all(
            [
                config.get("EMAIL_FROM"),
                config.get("EMAIL_PASSWORD"),
                config.get("EMAIL_TO"),
            ]
        )
        if email_ready:
            channel_details.append("Email")
        elif any([config.get("EMAIL_FROM"), config.get("EMAIL_PASSWORD"), config.get("EMAIL_TO")]):
            channel_issues.append("Email configuration incomplete (requires from/password/to configured simultaneously)")

        if channel_issues and not channel_details:
            _record_doctor_result(results, "fail", "Notification Configuration", "; ".join(channel_issues))
        elif channel_issues and channel_details:
            detail = f"Available channels: {', '.join(channel_details)}; Issues: {'; '.join(channel_issues)}"
            _record_doctor_result(results, "warn", "Notification Configuration", detail)
        elif channel_details:
            _record_doctor_result(results, "pass", "Notification Configuration", f"Available channels: {', '.join(channel_details)}")
        else:
            _record_doctor_result(results, "warn", "Notification Configuration", "No notification channels configured")

        # 8) Output directory writable check
        try:
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)
            probe_file = output_dir / ".doctor_write_probe"
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink(missing_ok=True)
            _record_doctor_result(results, "pass", "Output Directory", f"Writable: {output_dir}")
        except Exception as e:
            _record_doctor_result(results, "fail", "Output Directory", f"Not writable: {e}")

    pass_count = sum(1 for status, _, _ in results if status == "pass")
    warn_count = sum(1 for status, _, _ in results if status == "warn")
    fail_count = sum(1 for status, _, _ in results if status == "fail")

    _save_doctor_report(results, pass_count, warn_count, fail_count, config_path)

    print("-" * 60)
    print(f"Checkup results: ✅ {pass_count} passed  ⚠️ {warn_count} warnings  ❌ {fail_count} failed")
    print("=" * 60)

    if fail_count == 0:
        print("Checkup passed.")
        return True

    print("Checkup failed, please fix the failed items first.")
    return False


def _build_test_report_data(ctx: AppContext) -> Dict:
    """Construct report data for notification testing"""
    now = ctx.get_time()
    time_display = now.strftime("%H:%M")
    title = f"TrendRadar Notification Test Message ({now.strftime('%Y-%m-%d %H:%M:%S')})"

    return {
        "stats": [
            {
                "word": "Connectivity Test",
                "count": 1,
                "titles": [
                    {
                        "title": title,
                        "source_name": "TrendRadar",
                        "url": "https://github.com/sansan0/TrendRadar",
                        "mobile_url": "",
                        "ranks": [1],
                        "rank_threshold": ctx.rank_threshold,
                        "count": 1,
                        "is_new": True,
                        "time_display": time_display,
                        "matched_keyword": "Connectivity Test",
                    }
                ],
            }
        ],
        "failed_ids": [],
        "new_titles": [],
        "id_to_name": {},
    }


def _create_test_html_file(ctx: AppContext) -> Optional[str]:
    """Create HTML file for email testing"""
    try:
        now = ctx.get_time()
        output_dir = Path("output") / "html" / ctx.format_date()
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / f"notification_test_{ctx.format_time()}.html"
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>TrendRadar Notification Test</title></head>
<body>
<h2>TrendRadar Notification Connectivity Test</h2>
<p>Test time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({ctx.timezone})</p>
<p>This is a test message to verify if the email channel is reachable.</p>
</body>
</html>"""
        html_path.write_text(html_content, encoding="utf-8")
        return str(html_path)
    except Exception as e:
        print(f"[Test Notification] Failed to create test HTML: {e}")
        return None


def _run_test_notification(config: Dict) -> bool:
    """Send test notification to configured channels"""
    from trendradar.notification import NotificationDispatcher

    ctx = AppContext(config)

    try:
        # Check if notification channels are configured
        has_notification = any(
            [
                config.get("FEISHU_WEBHOOK_URL"),
                config.get("DINGTALK_WEBHOOK_URL"),
                config.get("WEWORK_WEBHOOK_URL"),
                (config.get("TELEGRAM_BOT_TOKEN") and config.get("TELEGRAM_CHAT_ID")),
                (config.get("EMAIL_FROM") and config.get("EMAIL_PASSWORD") and config.get("EMAIL_TO")),
                (config.get("NTFY_SERVER_URL") and config.get("NTFY_TOPIC")),
                config.get("BARK_URL"),
                config.get("SLACK_WEBHOOK_URL"),
                config.get("GENERIC_WEBHOOK_URL"),
            ]
        )
        if not has_notification:
            print("No available notification channels detected, please configure in config.yaml or environment variables first.")
            return False

        # Fix display area during testing to prevent empty test content caused by user closing HOTLIST
        test_config = copy.deepcopy(config)
        test_display = test_config.setdefault("DISPLAY", {})
        test_regions = test_display.setdefault("REGIONS", {})
        test_regions.update(
            {
                "HOTLIST": True,
                "NEW_ITEMS": False,
                "RSS": False,
                "STANDALONE": False,
                "AI_ANALYSIS": False,
            }
        )

        # Disable translation during testing to avoid triggering additional AI calls
        if "AI_TRANSLATION" in test_config:
            test_config["AI_TRANSLATION"]["ENABLED"] = False

        proxy_url = test_config.get("DEFAULT_PROXY", "") if test_config.get("USE_PROXY") else None
        if proxy_url:
            print("[Test Notification] Proxy configuration detected, will send using proxy")

        dispatcher = NotificationDispatcher(
            config=test_config,
            get_time_func=ctx.get_time,
            split_content_func=ctx.split_content,
            translator=None,
        )

        report_data = _build_test_report_data(ctx)
        html_file_path = _create_test_html_file(ctx)

        print("=" * 60)
        print("Notification connectivity test")
        print("=" * 60)

        results = dispatcher.dispatch_all(
            report_data=report_data,
            report_type="Notification connectivity test",
            proxy_url=proxy_url,
            mode="daily",
            html_file_path=html_file_path,
        )

        if not results:
            print("No valid notification channels to test (configuration may be incomplete).")
            return False

        print("-" * 60)
        success_count = 0
        for channel, ok in results.items():
            if ok:
                success_count += 1
                print(f"✅ {channel}: Test successful")
            else:
                print(f"❌ {channel}: Test failed")

        print("-" * 60)
        print(f"Test results: {success_count}/{len(results)} channels successful")
        return success_count > 0
    finally:
        ctx.cleanup()


def main():
    """Main program entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="TrendRadar - Hot news aggregation and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Schedule status commands:
  --show-schedule        Show current schedule status (time periods, behavior switches)
Diagnostic commands:
  --doctor               Run environment and configuration checkup
  --test-notification    Send test notification to configured channels

Examples:
  python -m trendradar                    # Normal run
  python -m trendradar --show-schedule    # View current schedule status
  python -m trendradar --doctor           # Run one-click checkup
  python -m trendradar --test-notification # Test notification channel connectivity
"""
    )
    parser.add_argument(
        "--show-schedule",
        action="store_true",
        help="Show current schedule status"
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run environment and configuration checkup"
    )
    parser.add_argument(
        "--test-notification",
        action="store_true",
        help="Send test notification to configured channels"
    )

    args = parser.parse_args()

    debug_mode = False
    try:
        # Handle doctor command (does not depend on full run process)
        if args.doctor:
            ok = _run_doctor()
            if not ok:
                raise SystemExit(1)
            return

        # Load configuration first
        config = load_config()

        # Handle status view command
        if args.show_schedule:
            _handle_status_commands(config)
            return

        # Handle notification test command
        if args.test_notification:
            ok = _run_test_notification(config)
            if not ok:
                raise SystemExit(1)
            return

        version_url = config.get("VERSION_CHECK_URL", "")
        configs_version_url = config.get("CONFIGS_VERSION_CHECK_URL", "")

        # Unified version check (program version + config file version, only request remote once)
        need_update = False
        remote_version = None
        if version_url:
            need_update, remote_version = check_all_versions(version_url, configs_version_url)

        # Reuse loaded configuration to avoid duplicate loading
        analyzer = NewsAnalyzer(config=config)

        # Set Cập nhật information (reuse fetched remote version, no duplicate requests)
        if analyzer.is_github_actions and need_update and remote_version:
            analyzer.update_info = {
                "current_version": __version__,
                "remote_version": remote_version,
            }

        # Get debug configuration
        debug_mode = analyzer.ctx.config.get("DEBUG", False)
        analyzer.run()
    except FileNotFoundError as e:
        print(f"❌ Configuration file error: {e}")
        print("\nPlease ensure the following files exist:")
        print("  • config/config.yaml")
        print("  • config/frequency_words.txt")
        print("\nRefer to project documentation for correct configuration")
    except Exception as e:
        print(f"❌ Program execution error: {e}")
        if debug_mode:
            raise


def _handle_status_commands(config: Dict) -> None:
    """Handle status check command - Display current scheduling status"""
    from trendradar.context import AppContext

    ctx = AppContext(config)

    print("=" * 60)
    print(f"TrendRadar v{__version__} Scheduling status")
    print("=" * 60)

    try:
        scheduler = ctx.create_scheduler()
        schedule = scheduler.resolve()

        now = ctx.get_time()
        date_str = ctx.format_date()

        print(f"\n⏰ Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({ctx.timezone})")
        print(f"📅 Current date: {date_str}")

        print(f"\n📋 Scheduling information:")
        print(f"  Daily plan: {schedule.day_plan}")
        if schedule.period_key:
            print(f"  Current time period: {schedule.period_name or schedule.period_key} ({schedule.period_key})")
        else:
            print(f"  Current time period: None (using default configuration)")

        print(f"\n🔧 Behavior switches:")
        print(f"  Collect data: {'✅ Yes' if schedule.collect else '❌ No'}")
        print(f"  AI analysis:  {'✅ Yes' if schedule.analyze else '❌ No'}")
        print(f"  Push notifications: {'✅ Yes' if schedule.push else '❌ No'}")
        print(f"  Report mode: {schedule.report_mode}")
        print(f"  AI mode:  {schedule.ai_mode}")

        if schedule.period_key:
            print(f"\n🔁 One-time control:")
            if schedule.once_analyze:
                already_analyzed = scheduler.already_executed(schedule.period_key, "analyze", date_str)
                print(f"  AI analysis:  Only once {'(Executed today ⚠️)' if already_analyzed else '(Not executed today ✅)'}")
            else:
                print(f"  AI analysis:  Unlimited times")
            if schedule.once_push:
                already_pushed = scheduler.already_executed(schedule.period_key, "push", date_str)
                print(f"  Push notifications: Only once {'(Executed today ⚠️)' if already_pushed else '(Not executed today ✅)'}")
            else:
                print(f"  Push notifications: Unlimited times")

    except Exception as e:
        print(f"\n❌ Failed to get scheduling status: {e}")

    print("\n" + "=" * 60)

    # Clean up resources
    ctx.cleanup()


if __name__ == "__main__":
    main()
