# coding=utf-8
"""
AI analyzer module

Call AI large models for deep analysis of hot news
Based on LiteLLM unified interface, supports 100+ AI providers
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from trendradar.ai.client import AIClient
from trendradar.ai.prompt_loader import load_prompt_template


@dataclass
class AIAnalysisResult:
    """AI analysis results"""
    # New version 5 core sections
    core_trends: str = ""                # Core hot spots and public opinion trends
    sentiment_controversy: str = ""      # Public opinion direction and controversy
    signals: str = ""                    # Anomalies and weak signals
    rss_insights: str = ""               # RSS deep insights
    outlook_strategy: str = ""           # Judgment and strategy suggestions
    standalone_summaries: Dict[str, str] = field(default_factory=dict)  # Standalone display area summaries {Source ID: Summary}

    # Basic metadata
    raw_response: str = ""               # Raw response
    success: bool = False                # Whether successful
    skipped: bool = False                # Whether skipped due to no content (not a failure)
    error: str = ""                      # Error message

    # News quantity statistics
    total_news: int = 0                  # Total news count (Hotlist + RSS)
    analyzed_news: int = 0               # Actually analyzed news count
    max_news_limit: int = 0              # Analysis limit configuration value
    hotlist_count: int = 0               # Hotlist news count (Total)
    rss_count: int = 0                   # RSS news count (Total)
    hotlist_analyzed: int = 0            # Hotlist actually analyzed count
    rss_analyzed: int = 0               # RSS actually analyzed count
    standalone_analyzed: int = 0        # Standalone display area actually analyzed count
    ai_mode: str = ""                    # AI analysis mode used (daily/current/incremental)
    include_rss: bool = True             # Whether to enable RSS analysis
    include_standalone: bool = False     # Whether to enable standalone display area analysis


class AIAnalyzer:
    """AI analyzer"""

    def __init__(
        self,
        ai_config: Dict[str, Any],
        analysis_config: Dict[str, Any],
        get_time_func: Callable,
        debug: bool = False,
    ):
        """
        Initialize AI analyzer

        Args:
            ai_config: AI model configuration (LiteLLM format)
            analysis_config: AI analysis function configuration (language, prompt_file, etc.)
            get_time_func: Function to get current time
            debug: Whether to enable debug mode
        """
        self.ai_config = ai_config
        self.analysis_config = analysis_config
        self.get_time_func = get_time_func
        self.debug = debug

        # Create AI client (based on LiteLLM)
        self.client = AIClient(ai_config)

        # Validate configuration
        valid, error = self.client.validate_config()
        if not valid:
            print(f"[AI] Configuration warning: {error}")

        # Get function parameters from analysis configuration
        self.max_news = analysis_config.get("MAX_NEWS_FOR_ANALYSIS", 50)
        self.include_rss = analysis_config.get("INCLUDE_RSS", True)
        self.include_rank_timeline = analysis_config.get("INCLUDE_RANK_TIMELINE", False)
        self.include_standalone = analysis_config.get("INCLUDE_STANDALONE", False)
        self.language = analysis_config.get("LANGUAGE", "Chinese")

        # Load prompt template
        self.system_prompt, self.user_prompt_template = load_prompt_template(
            analysis_config.get("PROMPT_FILE", "ai_analysis_prompt.txt"),
            label="AI",
        )

    def analyze(
        self,
        stats: List[Dict],
        rss_stats: Optional[List[Dict]] = None,
        report_mode: str = "daily",
        report_type: str = "Daily summary",
        platforms: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        standalone_data: Optional[Dict] = None,
    ) -> AIAnalysisResult:
        """
        Execute AI analysis

        Args:
            stats: Hot list statistics
            rss_stats: RSS statistics
            report_mode: Report mode
            report_type: Report type
            platforms: Platform list
            keywords: Keyword list

        Returns:
            AIAnalysisResult: Analysis result
        """
        
        # Print configuration information for easy debugging
        model = self.ai_config.get("MODEL", "unknown")
        api_key = self.client.api_key or ""
        api_base = self.ai_config.get("API_BASE", "")
        masked_key = f"{api_key[:5]}******" if len(api_key) >= 5 else "******"
        model_display = model.replace("/", "/\u200b") if model else "unknown"

        print(f"[AI] Model: {model_display}")
        print(f"[AI] Key : {masked_key}")

        if api_base:
            print(f"[AI] Interface: Custom API endpoint exists")

        timeout = self.ai_config.get("TIMEOUT", 120)
        max_tokens = self.ai_config.get("MAX_TOKENS", 5000)
        print(f"[AI] Parameters: timeout={timeout}, max_tokens={max_tokens}")

        if not self.client.api_key:
            return AIAnalysisResult(
                success=False,
                error="AI API Key is not configured, please set it in config.yaml or the AI_API_KEY environment variable"
            )

        # Prepare news content and get statistics
        news_content, rss_content, hotlist_total, rss_total, analyzed_count, hotlist_analyzed, rss_analyzed = self._prepare_news_content(stats, rss_stats)
        total_news = hotlist_total + rss_total

        if not news_content and not rss_content:
            return AIAnalysisResult(
                success=False,
                skipped=True,
                error="No new hot content in this round, skipping AI analysis",
                total_news=total_news,
                hotlist_count=hotlist_total,
                rss_count=rss_total,
                analyzed_news=0,
                max_news_limit=self.max_news
            )

        # Build prompt
        current_time = self.get_time_func().strftime("%Y-%m-%d %H:%M:%S")

        # Extract keywords
        if not keywords:
            keywords = [s.get("word", "") for s in stats if s.get("word")] if stats else []

        # Use safe string replacement to avoid misparsing other curly braces in the template (such as JSON examples)
        user_prompt = self.user_prompt_template
        user_prompt = user_prompt.replace("{report_mode}", report_mode)
        user_prompt = user_prompt.replace("{report_type}", report_type)
        user_prompt = user_prompt.replace("{current_time}", current_time)
        user_prompt = user_prompt.replace("{news_count}", str(hotlist_total))
        user_prompt = user_prompt.replace("{rss_count}", str(rss_total))
        user_prompt = user_prompt.replace("{platforms}", ", ".join(platforms) if platforms else "Multi-platform")
        user_prompt = user_prompt.replace("{keywords}", ", ".join(keywords[:20]) if keywords else "None")
        user_prompt = user_prompt.replace("{news_content}", news_content)
        user_prompt = user_prompt.replace("{rss_content}", rss_content)
        user_prompt = user_prompt.replace("{language}", self.language)

        # Build independent display area content
        standalone_content = ""
        standalone_count = 0
        if self.include_standalone and standalone_data:
            standalone_content, standalone_count = self._prepare_standalone_content(standalone_data)
        user_prompt = user_prompt.replace("{standalone_content}", standalone_content)

        if self.debug:
            print("\n" + "=" * 80)
            print("[AI Debug] Complete prompt sent to AI")
            print("=" * 80)
            if self.system_prompt:
                print("\n--- System Prompt ---")
                print(self.system_prompt)
            print("\n--- User Prompt ---")
            print(user_prompt)
            print("=" * 80 + "\n")

        # Call AI API (using LiteLLM)
        try:
            response = self._call_ai(user_prompt)
            result = self._parse_response(response)

            # Retry fallback when JSON parsing fails (retry only once)
            if result.error and "JSON parsing error" in result.error:
                print(f"[AI] JSON parsing failed, trying to let AI fix it...")
                retry_result = self._retry_fix_json(response, result.error)
                if retry_result and retry_result.success and not retry_result.error:
                    print("[AI] JSON fix successful")
                    retry_result.raw_response = response
                    result = retry_result
                else:
                    print("[AI] JSON fix failed, using original text as fallback")

            # If RSS analysis is not enabled in the configuration, force clear the RSS insights returned by AI
            if not self.include_rss:
                result.rss_insights = ""

            # If standalone analysis is not enabled in the configuration, force clear
            if not self.include_standalone:
                result.standalone_summaries = {}

            # Fill in statistics
            result.total_news = total_news
            result.hotlist_count = hotlist_total
            result.rss_count = rss_total
            result.analyzed_news = analyzed_count
            result.hotlist_analyzed = hotlist_analyzed
            result.rss_analyzed = rss_analyzed
            result.standalone_analyzed = standalone_count
            result.max_news_limit = self.max_news
            result.include_rss = self.include_rss
            result.include_standalone = self.include_standalone
            return result
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            # Truncate overly long error messages
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            friendly_msg = f"AI analysis failed ({error_type}): {error_msg}"

            return AIAnalysisResult(
                success=False,
                error=friendly_msg
            )

    def _prepare_news_content(
        self,
        stats: List[Dict],
        rss_stats: Optional[List[Dict]] = None,
    ) -> tuple:
        """
        Prepare news content text (enhanced version)

        Hot list news includes: source, title, ranking range, time range, number of occurrences
        RSS includes: source, title, publish time

        Returns:
            tuple: (news_content, rss_content, hotlist_total, rss_total, analyzed_count, hotlist_analyzed, rss_analyzed)
        """
        news_lines = []
        rss_lines = []
        news_count = 0
        rss_count = 0

        # Calculate total number of news
        hotlist_total = sum(len(s.get("titles", [])) for s in stats) if stats else 0
        rss_total = sum(len(s.get("titles", [])) for s in rss_stats) if rss_stats else 0

        # Hot list content
        if stats:
            for stat in stats:
                word = stat.get("word", "")
                titles = stat.get("titles", [])
                if word and titles:
                    news_lines.append(f"\n**{word}** ({len(titles)} items)")
                    for t in titles:
                        if not isinstance(t, dict):
                            continue
                        title = t.get("title", "")
                        if not title:
                            continue

                        # Source
                        source = t.get("source_name", t.get("source", ""))

                        # Build line
                        if source:
                            line = f"- [{source}] {title}"
                        else:
                            line = f"- {title}"

                        # Always show simplified format: rank range + time range + appearance count
                        ranks = t.get("ranks", [])
                        if ranks:
                            min_rank = min(ranks)
                            max_rank = max(ranks)
                            rank_str = f"{min_rank}" if min_rank == max_rank else f"{min_rank}-{max_rank}"
                        else:
                            rank_str = "-"

                        first_time = t.get("first_time", "")
                        last_time = t.get("last_time", "")
                        time_str = self._format_time_range(first_time, last_time)

                        appear_count = t.get("count", 1)

                        line += f" | Rank:{rank_str} | Time:{time_str} | Appearances:{appear_count} times"

                        # When full timeline is enabled, additionally add trajectory
                        if self.include_rank_timeline:
                            rank_timeline = t.get("rank_timeline", [])
                            timeline_str = self._format_rank_timeline(rank_timeline)
                            line += f" | Trajectory:{timeline_str}"

                        news_lines.append(line)

                        news_count += 1
                        if news_count >= self.max_news:
                            break
                if news_count >= self.max_news:
                    break

        # RSS content (built only when enabled)
        if self.include_rss and rss_stats:
            remaining = self.max_news - news_count
            for stat in rss_stats:
                if rss_count >= remaining:
                    break
                word = stat.get("word", "")
                titles = stat.get("titles", [])
                if word and titles:
                    rss_lines.append(f"\n**{word}** ({len(titles)} items)")
                    for t in titles:
                        if not isinstance(t, dict):
                            continue
                        title = t.get("title", "")
                        if not title:
                            continue

                        # Source
                        source = t.get("source_name", t.get("feed_name", ""))

                        # Publish time
                        time_display = t.get("time_display", "")

                        # Build line: [Source] Title | Publish time
                        if source:
                            line = f"- [{source}] {title}"
                        else:
                            line = f"- {title}"
                        if time_display:
                            line += f" | {time_display}"
                        rss_lines.append(line)

                        rss_count += 1
                        if rss_count >= remaining:
                            break

        news_content = "\n".join(news_lines) if news_lines else ""
        rss_content = "\n".join(rss_lines) if rss_lines else ""
        total_count = news_count + rss_count

        return news_content, rss_content, hotlist_total, rss_total, total_count, news_count, rss_count

    def _call_ai(self, user_prompt: str) -> str:
        """Call AI API (using LiteLLM)"""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        return self.client.chat(messages)

    def _retry_fix_json(self, original_response: str, error_msg: str) -> Optional[AIAnalysisResult]:
        """
        When JSON parsing fails, request AI to fix JSON (retry only once)

        Use lightweight prompt, do not repeat the system prompt of the original analysis to save tokens.

        Args:
            original_response: AI original response (JSON format is incorrect)
            error_msg: JSON parsing error message

        Returns:
            Fixed analysis result, returns None on failure
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a JSON fixing assistant. The user will provide a malformed JSON and an error message,"
                    "you need to fix the JSON format errors and return the correct JSON.\n"
                    "Common issues: unescaped double quotes inside string values, missing commas, strings not properly closed, etc.\n"
                    "Return only pure JSON, do not include markdown code block markers (like ```json) or any explanatory text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"The following JSON failed to parse:\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Original content:\n{original_response}\n\n"
                    f"Please fix the format issues in the above JSON (e.g., change double quotes in values to Chinese quotes 「」 or escape them as \\\", "
                    f"missing commas, incomplete strings, etc.), keep the original content semantics unchanged, only fix the format."
                    f"Directly return the fixed pure JSON."
                ),
            },
        ]

        try:
            response = self.client.chat(messages)
            return self._parse_response(response)
        except Exception as e:
            print(f"[AI] Retry fixing JSON exception: {type(e).__name__}: {e}")
            return None

    def _format_time_range(self, first_time: str, last_time: str) -> str:
        """Format time range (simplified display, keep only hours and minutes)"""
        def extract_time(time_str: str) -> str:
            if not time_str:
                return "-"
            # Try to extract HH:MM part
            if " " in time_str:
                parts = time_str.split(" ")
                if len(parts) >= 2:
                    time_part = parts[1]
                    if ":" in time_part:
                        return time_part[:5]  # HH:MM
            elif ":" in time_str:
                return time_str[:5]
            # Handle HH-MM format
            result = time_str[:5] if len(time_str) >= 5 else time_str
            if len(result) == 5 and result[2] == '-':
                result = result.replace('-', ':')
            return result

        first = extract_time(first_time)
        last = extract_time(last_time)

        if first == last or last == "-":
            return first
        return f"{first}~{last}"

    def _format_rank_timeline(self, rank_timeline: List[Dict]) -> str:
        """Format rank timeline"""
        if not rank_timeline:
            return "-"

        parts = []
        for item in rank_timeline:
            time_str = item.get("time", "")
            if len(time_str) == 5 and time_str[2] == '-':
                time_str = time_str.replace('-', ':')
            rank = item.get("rank")
            if rank is None:
                parts.append(f"0({time_str})")
            else:
                parts.append(f"{rank}({time_str})")

        return "→".join(parts)

    def _prepare_standalone_content(self, standalone_data: Dict) -> tuple:
        """
        Convert standalone display area data to text, inject into AI analysis prompt

        Args:
            standalone_data: Standalone display area data {"platforms": [...], "rss_feeds": [...]}

        Returns:
            tuple: (Formatted text content, number of standalone display area items)
        """
        lines = []

        # Hot search platforms
        for platform in standalone_data.get("platforms", []):
            platform_id = platform.get("id", "")
            platform_name = platform.get("name", platform_id)
            items = platform.get("items", [])
            if not items:
                continue

            lines.append(f"### [{platform_name}]")
            for item in items:
                title = item.get("title", "")
                if not title:
                    continue

                line = f"- {title}"

                # Rank information
                ranks = item.get("ranks", [])
                if ranks:
                    min_rank = min(ranks)
                    max_rank = max(ranks)
                    rank_str = f"{min_rank}" if min_rank == max_rank else f"{min_rank}-{max_rank}"
                    line += f" | Rank:{rank_str}"

                # Time range
                first_time = item.get("first_time", "")
                last_time = item.get("last_time", "")
                if first_time:
                    time_str = self._format_time_range(first_time, last_time)
                    line += f" | Time:{time_str}"

                # Appearance count
                count = item.get("count", 1)
                if count > 1:
                    line += f" | Occurrences:{count} times"

                # Ranking trajectory (if enabled)
                if self.include_rank_timeline:
                    rank_timeline = item.get("rank_timeline", [])
                    if rank_timeline:
                        timeline_str = self._format_rank_timeline(rank_timeline)
                        line += f" | Trajectory:{timeline_str}"

                lines.append(line)
            lines.append("")

        # RSS feed
        for feed in standalone_data.get("rss_feeds", []):
            feed_id = feed.get("id", "")
            feed_name = feed.get("name", feed_id)
            items = feed.get("items", [])
            if not items:
                continue

            lines.append(f"### [{feed_name}]")
            for item in items:
                title = item.get("title", "")
                if not title:
                    continue

                line = f"- {title}"
                published_at = item.get("published_at", "")
                if published_at:
                    line += f" | {published_at}"

                lines.append(line)
            lines.append("")

        standalone_count = sum(
            len(p.get("items", [])) for p in standalone_data.get("platforms", [])
        ) + sum(
            len(f.get("items", [])) for f in standalone_data.get("rss_feeds", [])
        )
        return "\n".join(lines), standalone_count

    def _parse_response(self, response: str) -> AIAnalysisResult:
        """Parse AI response"""
        result = AIAnalysisResult(raw_response=response)

        if not response or not response.strip():
            result.error = "AI returned empty response"
            return result

        # Extract JSON text (remove markdown code block tags)
        json_str = response

        if "```json" in response:
            parts = response.split("```json", 1)
            if len(parts) > 1:
                code_block = parts[1]
                end_idx = code_block.find("```")
                if end_idx != -1:
                    json_str = code_block[:end_idx]
                else:
                    json_str = code_block
        elif "```" in response:
            parts = response.split("```", 2)
            if len(parts) >= 2:
                json_str = parts[1]

        json_str = json_str.strip()
        if not json_str:
            result.error = "Extracted JSON content is empty"
            result.core_trends = response[:500] + "..." if len(response) > 500 else response
            result.success = True
            return result

        # Step 1: Standard JSON parsing
        data = None
        parse_error = None

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            parse_error = e

        # Step 2: json_repair local repair
        if data is None:
            try:
                from json_repair import repair_json
                repaired = repair_json(json_str, return_objects=True)
                if isinstance(repaired, dict):
                    data = repaired
                    print("[AI] JSON local repair successful (json_repair)")
            except Exception:
                pass

        # Both steps failed, record error (handled later by the retry mechanism of the analyze method)
        if data is None:
            if parse_error:
                error_context = json_str[max(0, parse_error.pos - 30):parse_error.pos + 30] if json_str and parse_error.pos else ""
                result.error = f"JSON parsing error (position {parse_error.pos}): {parse_error.msg}"
                if error_context:
                    result.error += f", context: ...{error_context}..."
            else:
                result.error = "JSON parsing failed"
            # Fallback: use extracted json_str (without markdown tags), to avoid ```json appearing in push
            result.core_trends = json_str[:500] + "..." if len(json_str) > 500 else json_str
            result.success = True
            return result

        # Parsing successful, extract fields
        try:
            result.core_trends = data.get("core_trends", "")
            result.sentiment_controversy = data.get("sentiment_controversy", "")
            result.signals = data.get("signals", "")
            result.rss_insights = data.get("rss_insights", "")
            result.outlook_strategy = data.get("outlook_strategy", "")

            # Parse independent display area summary
            summaries = data.get("standalone_summaries", {})
            if isinstance(summaries, dict):
                result.standalone_summaries = {
                    str(k): str(v) for k, v in summaries.items()
                }

            result.success = True
        except (KeyError, TypeError, AttributeError) as e:
            result.error = f"Field extraction error: {type(e).__name__}: {e}"
            result.core_trends = json_str[:500] + "..." if len(json_str) > 500 else json_str
            result.success = True

        return result
