# coding=utf-8
"""
Timeline scheduler

Unified timeline scheduling system, replacing scattered push_window / analysis_window logic.
Implements flexible time period scheduling based on the periods + day_plans + week_map model.
"""

import copy
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from datetime import datetime


@dataclass
class ResolvedSchedule:
    """Scheduling result after parsing the current time"""
    period_key: Optional[str]       # Hit period key, None=default configuration
    period_name: Optional[str]      # Hit display name
    day_plan: str                   # Current day plan
    collect: bool
    analyze: bool
    push: bool
    report_mode: str
    ai_mode: str
    once_analyze: bool
    once_push: bool
    frequency_file: Optional[str] = None  # Frequency word file path, None=use default
    filter_method: Optional[str] = None   # Filter strategy: "keyword"|"ai", None=use global configuration
    interests_file: Optional[str] = None  # AI filter interests file, None=use default


class Scheduler:
    """
    Timeline scheduler

    Parse the behavior to be executed at the current time according to the timeline configuration (periods + day_plans + week_map).
    Supports:
    - Preset templates + custom mode
    - Cross-day time periods (e.g., 22:00-07:00)
    - Daily / weekly differentiated configuration
    - once execution deduplication (analyze / push independent dimensions)
    - Conflict strategy (error_on_overlap / last_wins)
    """

    def __init__(
        self,
        schedule_config: Dict[str, Any],
        timeline_data: Dict[str, Any],
        storage_backend: Any,
        get_time_func: Callable[[], datetime],
        fallback_report_mode: str = "current",
    ):
        """
        Initialize scheduler

        Args:
            schedule_config: schedule section in config.yaml (including preset, etc.)
            timeline_data: Complete data of timeline.yaml
            storage_backend: Storage backend (used for once deduplication records)
            get_time_func: Function to get the current time (should use the configured timezone)
            fallback_report_mode: report_mode used as fallback when scheduling is not enabled (from report.mode in config.yaml)
        """
        self.schedule_config = schedule_config
        self.storage = storage_backend
        self.get_time = get_time_func
        self.enabled = schedule_config.get("enabled", True)
        self.fallback_report_mode = fallback_report_mode

        # Load and build the final timeline
        self.timeline = self._build_timeline(schedule_config, timeline_data)
        if self.enabled:
            self._validate_timeline(self.timeline)

    def _build_timeline(
        self,
        schedule_config: Dict[str, Any],
        timeline_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build timeline from preset or custom"""
        preset = schedule_config.get("preset", "always_on")

        if preset == "custom":
            timeline = copy.deepcopy(timeline_data.get("custom", {}))
        else:
            presets = timeline_data.get("presets", {})
            if preset not in presets:
                raise ValueError(
                    f"Unknown preset template: '{preset}', optional values: "
                    f"{', '.join(presets.keys())}, custom"
                )
            timeline = copy.deepcopy(presets[preset])

        # Ensure periods is a dict (may be empty {})
        if timeline.get("periods") is None:
            timeline["periods"] = {}

        return timeline

    def resolve(self) -> ResolvedSchedule:
        """
        Parse the scheduling configuration corresponding to the current time

        Returns:
            ResolvedSchedule contains the behavior to be executed currently
        """
        if not self.enabled:
            # Return default full-featured configuration when scheduling is not enabled, report_mode falls back to use config.yaml's report.mode
            return ResolvedSchedule(
                period_key=None,
                period_name=None,
                day_plan="disabled",
                collect=True,
                analyze=True,
                push=True,
                report_mode=self.fallback_report_mode,
                ai_mode="follow_report",
                once_analyze=False,
                once_push=False,
            )

        now = self.get_time()
        weekday = now.isoweekday()  # 1=Monday ... 7=Sunday
        now_hhmm = now.strftime("%H:%M")

        # Find the day plan for the current day
        day_plan_key = self.timeline["week_map"].get(weekday)
        if day_plan_key is None:
            raise ValueError(f"week_map is missing weekday mapping: {weekday}")

        day_plan = self.timeline["day_plans"].get(day_plan_key)
        if day_plan is None:
            raise ValueError(f"week_map[{weekday}] references a non-existent day_plan: {day_plan_key}")

        # Find the currently active time period
        period_key = self._find_active_period(now_hhmm, day_plan)

        # Merge default configuration and time period configuration
        merged = self._merge_with_default(period_key)

        # Print scheduling log
        weekday_names = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
        period_display = "Default configuration (no time period hit)"
        if period_key:
            period_cfg = self.timeline["periods"][period_key]
            period_name = period_cfg.get("name", period_key)
            start = period_cfg.get("start", "?")
            end = period_cfg.get("end", "?")
            period_display = f"{period_name} ({start}-{end})"

        print(f"[Scheduler] Weekday {weekday_names.get(weekday, '?')}, Daily plan: {day_plan_key}")
        print(f"[Scheduler] Current time period: {period_display}")

        resolved = ResolvedSchedule(
            period_key=period_key,
            period_name=(
                self.timeline["periods"][period_key].get("name")
                if period_key
                else None
            ),
            day_plan=day_plan_key,
            collect=merged.get("collect", True),
            analyze=merged.get("analyze", False),
            push=merged.get("push", False),
            report_mode=merged.get("report_mode", "current"),
            ai_mode=self._resolve_ai_mode(merged),
            once_analyze=merged.get("once", {}).get("analyze", False),
            once_push=merged.get("once", {}).get("push", False),
            frequency_file=merged.get("frequency_file"),
            filter_method=merged.get("filter_method"),
            interests_file=merged.get("interests_file"),
        )

        # Print action summary
        actions = []
        if resolved.collect:
            actions.append("Collect")
        if resolved.analyze:
            actions.append(f"Analyze(AI:{resolved.ai_mode})")
        if resolved.push:
            actions.append(f"Push(Mode:{resolved.report_mode})")
        print(f"[Scheduler] Actions: {', '.join(actions) if actions else 'None'}")
        if resolved.frequency_file:
            print(f"[Scheduler] Frequency word file: {resolved.frequency_file}")

        return resolved

    def _find_active_period(
        self, now_hhmm: str, day_plan: Dict[str, Any]
    ) -> Optional[str]:
        """
        Find the active time period hit by the current time

        Args:
            now_hhmm: Current time HH:MM
            day_plan: Daily plan configuration

        Returns:
            Hit period key, or None
        """
        candidates = []
        for idx, key in enumerate(day_plan.get("periods", [])):
            period = self.timeline["periods"].get(key)
            if period is None:
                continue
            if self._in_range(now_hhmm, period["start"], period["end"]):
                candidates.append((idx, key))

        if not candidates:
            return None

        # Check for conflicts
        if len(candidates) > 1:
            policy = self.timeline.get("overlap", {}).get("policy", "error_on_overlap")
            conflicting = [c[1] for c in candidates]

            if policy == "error_on_overlap":
                raise ValueError(
                    f"Time period overlap conflict detected: {', '.join(conflicting)} overlap at {now_hhmm}."
                    f"Please adjust the time period configuration, or set overlap.policy to 'last_wins'"
                )

            # last_wins: Output overlap warning, the latter in the list takes precedence
            print(
                f"[Scheduler] Time period overlap detected: {', '.join(conflicting)} overlap at {now_hhmm}"
            )
            winner = candidates[-1]
            print(f"[Scheduler] Conflict policy: last_wins, effective time period: {winner[1]}")
            return winner[1]

        return candidates[0][1]

    @staticmethod
    def _in_range(now_hhmm: str, start: str, end: str) -> bool:
        """
        Check if the time is within the range (supports cross-day)

        Args:
            now_hhmm: Current time HH:MM
            start: Start time HH:MM
            end: End time HH:MM

        Returns:
            Whether it is within the range
        """
        if start <= end:
            # Normal range, e.g., 08:00-09:00 (half-open interval [start, end))
            return start <= now_hhmm < end
        else:
            # Cross-day range, e.g., 22:00-07:00 (half-open interval [start, end))
            return now_hhmm >= start or now_hhmm < end

    def _merge_with_default(self, period_key: Optional[str]) -> Dict[str, Any]:
        """Merge default configuration and time period configuration"""
        base = copy.deepcopy(self.timeline.get("default", {}))
        if not period_key:
            return base

        period = copy.deepcopy(self.timeline["periods"][period_key])

        # Merge once sub-objects first
        merged_once = dict(base.get("once", {}))
        merged_once.update(period.get("once", {}))

        # Scalar field override
        base.update(period)

        # Restore the merged once
        if merged_once:
            base["once"] = merged_once

        return base

    @staticmethod
    def _resolve_ai_mode(cfg: Dict[str, Any]) -> str:
        """Parse the final AI mode"""
        ai_mode = cfg.get("ai_mode", "follow_report")
        if ai_mode == "follow_report":
            return cfg.get("report_mode", "current")
        return ai_mode

    def already_executed(self, period_key: str, action: str, date_str: str) -> bool:
        """
        Check if a certain action in the specified time period has been executed today

        Args:
            period_key: Time period key
            action: Action type (analyze / push)
            date_str: Date YYYY-MM-DD

        Returns:
            Whether it has been executed
        """
        return self.storage.has_period_executed(date_str, period_key, action)

    def record_execution(self, period_key: str, action: str, date_str: str) -> None:
        """
        Record the action execution of the time period

        Args:
            period_key: Time period key
            action: Action type (analyze / push)
            date_str: Date YYYY-MM-DD
        """
        self.storage.record_period_execution(date_str, period_key, action)

    # ========================================
    # Validate
    # ========================================

    def _validate_timeline(self, timeline: Dict[str, Any]) -> None:
        """
        Validate timeline configuration on startup

        Raises:
            ValueError: Raised when configuration is invalid
        """
        required_top_keys = ["default", "periods", "day_plans", "week_map"]
        for key in required_top_keys:
            if key not in timeline:
                raise ValueError(f"timeline missing required field: {key}")

        # week_map must cover 1..7
        for day in range(1, 8):
            if day not in timeline["week_map"]:
                raise ValueError(f"week_map missing day mapping: {day}")

        # day_plan referential integrity
        for day, plan_key in timeline["week_map"].items():
            if plan_key not in timeline["day_plans"]:
                raise ValueError(
                    f"week_map[{day}] references non-existent day_plan: {plan_key}"
                )

        # period referential integrity
        for plan_key, plan in timeline["day_plans"].items():
            for period_key in plan.get("periods", []):
                if period_key not in timeline["periods"]:
                    raise ValueError(
                        f"day_plan[{plan_key}] references non-existent period: {period_key}"
                    )

        # Time format validation
        for period_key, period in timeline["periods"].items():
            if "start" not in period or "end" not in period:
                raise ValueError(
                    f"period '{period_key}' missing start or end field"
                )
            self._validate_hhmm(period["start"], f"{period_key}.start")
            self._validate_hhmm(period["end"], f"{period_key}.end")
            if period["start"] == period["end"]:
                raise ValueError(
                    f"period '{period_key}' start and end cannot be the same: {period['start']}"
                )

        # Check for overlap under conflict policy
        policy = timeline.get("overlap", {}).get("policy", "error_on_overlap")
        if policy == "error_on_overlap":
            self._check_period_overlaps(timeline)

    def _check_period_overlaps(self, timeline: Dict[str, Any]) -> None:
        """
        Check if time periods in each day plan overlap

        Only called when overlap.policy == "error_on_overlap"
        """
        periods = timeline.get("periods", {})

        for plan_key, plan in timeline["day_plans"].items():
            period_keys = plan.get("periods", [])
            if len(period_keys) <= 1:
                continue

            # Collect the range of each time period
            ranges = []
            for pk in period_keys:
                p = periods.get(pk, {})
                if "start" in p and "end" in p:
                    ranges.append((pk, p["start"], p["end"]))

            # Check for overlap pairwise
            for i in range(len(ranges)):
                for j in range(i + 1, len(ranges)):
                    if self._ranges_overlap(
                        ranges[i][1], ranges[i][2],
                        ranges[j][1], ranges[j][2],
                    ):
                        raise ValueError(
                            f"day_plan '{plan_key}' time period '{ranges[i][0]}' "
                            f"({ranges[i][1]}-{ranges[i][2]}) and '{ranges[j][0]}' "
                            f"({ranges[j][1]}-{ranges[j][2]}) overlap."
                            f"Please adjust the time periods, or set overlap.policy to 'last_wins'"
                        )

    @staticmethod
    def _ranges_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
        """Check if two time ranges overlap (supports cross-day)"""
        def to_minutes(t: str) -> int:
            h, m = t.split(":")
            return int(h) * 60 + int(m)

        def expand_range(start: str, end: str) -> List[tuple]:
            """Expand time range into a list of minute segments, split into two segments when crossing days"""
            s = to_minutes(start)
            e = to_minutes(end)
            if s <= e:
                return [(s, e)]
            else:
                # Cross-day: split into [start, 24:00) and [00:00, end)
                return [(s, 24 * 60), (0, e)]

        segs1 = expand_range(s1, e1)
        segs2 = expand_range(s2, e2)

        for a_start, a_end in segs1:
            for b_start, b_end in segs2:
                # Condition for two half-open intervals to overlap
                if a_start < b_end and b_start < a_end:
                    return True
        return False

    @staticmethod
    def _validate_hhmm(value: str, field_name: str) -> None:
        """Validate HH:MM format"""
        if not re.match(r"^\d{2}:\d{2}$", value):
            raise ValueError(f"{field_name} format error: '{value}', expected HH:MM")
        h, m = value.split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError(f"{field_name} time value out of range: '{value}'")
