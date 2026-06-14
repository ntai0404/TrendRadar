# coding=utf-8
"""
AI intelligent filtering module

Tag classification of news via AI:
1. Phase A: Extract structured tags from user interest descriptions
2. Phase B: Batch classify news titles by tags
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from trendradar.ai.client import AIClient
from trendradar.ai.prompt_loader import load_prompt_template


@dataclass
class AIFilterResult:
    """AI filtering results, passed to the report and notification modules"""
    tags: List[Dict] = field(default_factory=list)
    # [{"tag": str, "description": str, "count": int, "items": [
    #     {"title": str, "source_id": str, "source_name": str,
    #      "url": str, "mobile_url": str, "rank": int, "ranks": [...],
    #      "first_time": str, "last_time": str, "count": int,
    #      "relevance_score": float, "source_type": str}
    # ]}]
    total_matched: int = 0       # Total matched news
    total_processed: int = 0     # Total processed news
    success: bool = False
    error: str = ""


class AIFilter:
    """AI intelligent filter"""

    def __init__(
        self,
        ai_config: Dict[str, Any],
        filter_config: Dict[str, Any],
        get_time_func: Callable,
        debug: bool = False,
    ):
        self.client = AIClient(ai_config)
        self.filter_config = filter_config
        self.batch_size = filter_config.get("BATCH_SIZE", 200)
        self.get_time_func = get_time_func
        self.debug = debug

        # Load prompt templates
        self.classify_system, self.classify_user = load_prompt_template(
            filter_config.get("PROMPT_FILE", "ai_filter_prompt.txt"),
            config_subdir="ai_filter", label="AI filter",
        )
        self.extract_system, self.extract_user = load_prompt_template(
            filter_config.get("EXTRACT_PROMPT_FILE", "ai_filter_extract_prompt.txt"),
            config_subdir="ai_filter", label="AI filter",
        )
        self.update_tags_system, self.update_tags_user = load_prompt_template(
            filter_config.get("UPDATE_TAGS_PROMPT_FILE", "update_tags_prompt.txt"),
            config_subdir="ai_filter", label="AI filter",
        )

    def compute_interests_hash(self, interests_content: str, filename: str = "ai_interests.txt") -> str:
        """Calculate the hash of the interest description, format is filename:md5"""
        # Remove leading/trailing whitespace and comment lines to ensure hash only changes when content changes
        lines = []
        for line in interests_content.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
        normalized = "\n".join(lines)
        content_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        return f"{filename}:{content_hash}"

    def load_interests_content(self, interests_file: Optional[str] = None) -> Optional[str]:
        """Load interest description file content

        Parsing logic:
        - interests_file is None: use default config/ai_interests.txt
        - interests_file has a value: only check config/custom/ai/{filename}

        Note: The caller (context.py) has completed the merge decision for config/timeline,
        filter_config is not read a second time here to avoid semantic conflicts.
        """
        config_dir = Path(__file__).parent.parent.parent / "config"
        configured_file = interests_file

        if configured_file:
            # Custom interest file: only check custom/ai directory
            filename = configured_file
            interests_path = config_dir / "custom" / "ai" / filename
            if not interests_path.exists():
                print(f"[AI filter] Custom interest description file does not exist: {filename}")
                print(f"[AI filter]   Searched: {interests_path}")
                return None
        else:
            # Default interest file: fixed to use config/ai_interests.txt
            filename = "ai_interests.txt"
            interests_path = config_dir / filename
            if not interests_path.exists():
                print(f"[AI filter] Default interest description file does not exist: {filename}")
                print(f"[AI filter]   Searched: {interests_path}")
                return None

        if not interests_path.exists():
            print(f"[AI filter] Interest description file does not exist: {interests_path}")
            return None

        content = interests_path.read_text(encoding="utf-8").strip()
        if not content:
            print("[AI filter] Interest description file is empty")
            return None

        return content

    def extract_tags(self, interests_content: str) -> List[Dict]:
        """
        Phase A: Extract structured tags from interest descriptions

        Args:
            interests_content: User's interest description text

        Returns:
            [{"tag": str, "description": str}, ...]
        """
        if not self.extract_user:
            print("[AI filter] Tag extraction prompt template is empty")
            return []

        user_prompt = self.extract_user.replace("{interests_content}", interests_content)

        messages = []
        if self.extract_system:
            messages.append({"role": "system", "content": self.extract_system})
        messages.append({"role": "user", "content": user_prompt})

        if self.debug:
            print(f"\n[AI filter][DEBUG] === Tag extraction Prompt ===")
            for m in messages:
                print(f"[{m['role']}]\n{m['content']}")
            print(f"[AI filter][DEBUG] === Prompt end ===")

        try:
            response = self.client.chat(messages)

            if self.debug:
                print(f"\n[AI filter][DEBUG] === Tag extraction AI raw response ===")
                # Try to format JSON for easier reading
                self._print_formatted_json(response)
                print(f"[AI filter][DEBUG] === Response end ===")

            tags = self._parse_tags_response(response)
            print(f"[AI filter] Extracted {len(tags)} tags")
            for t in tags:
                print(f"   {t['tag']}: {t.get('description', '')}")

            if self.debug:
                json_str = self._extract_json(response)
                if not json_str:
                    print(f"[AI filter][DEBUG] Cannot extract JSON from response")
                else:
                    raw_data = json.loads(json_str)
                    raw_tags = raw_data.get("tags", [])
                    skipped = len(raw_tags) - len(tags)
                    if skipped > 0:
                        print(f"[AI filter][DEBUG] Raw tags {len(raw_tags)}, valid {len(tags)}, skipped {skipped} (missing tag field or invalid format)")

            return tags
        except json.JSONDecodeError as e:
            print(f"[AI filter] Tag extraction failed: JSON parsing error: {e}")
            if self.debug:
                print(f"[AI Filter][DEBUG] Attempted to parse JSON content: {self._extract_json(response) if response else '(Empty response)'}")
            return []
        except Exception as e:
            print(f"[AI Filter] Tag extraction failed: {type(e).__name__}: {e}")
            return []

    def update_tags(self, old_tags: List[Dict], interests_content: str) -> Optional[Dict]:
        """
        Phase A': AI compares old tags and new interest descriptions, provides Cập nhật plan

        Args:
            old_tags: [{"tag": str, "description": str, "id": int}, ...]
            interests_content: New interest description text

        Returns:
            {"keep": [{"tag": str, "description": str}],
             "add": [{"tag": str, "description": str}],
             "remove": [str],
             "change_ratio": float}
            Returns None on failure
        """
        if not self.update_tags_user:
            print("[AI Filter] Tag Cập nhật prompt template is empty, falling back to re-extraction")
            return None

        # Construct old tags JSON
        old_tags_json = json.dumps(
            [{"tag": t["tag"], "description": t.get("description", "")} for t in old_tags],
            ensure_ascii=False, indent=2
        )

        user_prompt = self.update_tags_user.replace(
            "{old_tags_json}", old_tags_json
        ).replace(
            "{interests_content}", interests_content
        )

        messages = []
        if self.update_tags_system:
            messages.append({"role": "system", "content": self.update_tags_system})
        messages.append({"role": "user", "content": user_prompt})

        if self.debug:
            print(f"\n[AI Filter][DEBUG] === Tag Cập nhật Prompt ===")
            for m in messages:
                print(f"[{m['role']}]\n{m['content']}")
            print(f"[AI Filter][DEBUG] === Prompt End ===")

        try:
            response = self.client.chat(messages)

            if self.debug:
                print(f"\n[AI Filter][DEBUG] === Tag Cập nhật AI raw response ===")
                self._print_formatted_json(response)
                print(f"[AI Filter][DEBUG] === Response End ===")

            result = self._parse_update_tags_response(response)
            if result is None:
                return None

            keep_count = len(result.get("keep", []))
            add_count = len(result.get("add", []))
            remove_count = len(result.get("remove", []))
            ratio = result.get("change_ratio", 0)
            print(f"[AI Filter] AI Tag Cập nhật plan: Keep {keep_count}, Add {add_count}, Remove {remove_count}, change_ratio={ratio:.2f}")

            return result
        except Exception as e:
            print(f"[AI Filter] Tag Cập nhật failed: {type(e).__name__}: {e}")
            return None

    def _parse_update_tags_response(self, response: str) -> Optional[Dict]:
        """Parse Tag Cập nhật AI response"""
        json_str = self._extract_json(response)
        if not json_str:
            print("[AI Filter] Cannot extract JSON from Tag Cập nhật response")
            return None

        data = json.loads(json_str)

        # Validate required fields
        keep = data.get("keep", [])
        add = data.get("add", [])
        remove = data.get("remove", [])
        change_ratio = float(data.get("change_ratio", 0))

        # Validate keep/add format
        validated_keep = []
        for t in keep:
            if isinstance(t, dict) and "tag" in t:
                validated_keep.append({
                    "tag": str(t["tag"]).strip(),
                    "description": str(t.get("description", "")).strip(),
                })

        validated_add = []
        for t in add:
            if isinstance(t, dict) and "tag" in t:
                validated_add.append({
                    "tag": str(t["tag"]).strip(),
                    "description": str(t.get("description", "")).strip(),
                })

        validated_remove = [str(r).strip() for r in remove if r]

        # change_ratio limited to 0~1
        change_ratio = max(0.0, min(1.0, change_ratio))

        return {
            "keep": validated_keep,
            "add": validated_add,
            "remove": validated_remove,
            "change_ratio": change_ratio,
        }

    def _parse_tags_response(self, response: str) -> List[Dict]:
        """Parse tag extraction AI response"""
        json_str = self._extract_json(response)
        if not json_str:
            return []

        data = json.loads(json_str)
        tags_raw = data.get("tags", [])

        tags = []
        for t in tags_raw:
            if not isinstance(t, dict) or "tag" not in t:
                continue
            tags.append({
                "tag": str(t["tag"]).strip(),
                "description": str(t.get("description", "")).strip(),
            })

        return tags

    def classify_batch(
        self,
        titles: List[Dict],
        tags: List[Dict],
        interests_content: str = "",
    ) -> List[Dict]:
        """
        Phase B: Classify a batch of news titles

        Args:
            titles: [{"id": news_item_id, "title": str, "source": str}]
            tags: [{"id": tag_id, "tag": str, "description": str}]
            interests_content: User's interest description (including quality filtering requirements)

        Returns:
            [{"news_item_id": int, "tag_id": int, "relevance_score": float}, ...]
        """
        if not titles or not tags:
            return []

        if not self.classify_user:
            print("[AI Filter] Classification prompt template is empty")
            return []

        # Build tag list text
        tags_list = "\n".join(
            f"{t['id']}. {t['tag']}: {t.get('description', '')}"
            for t in tags
        )

        # Build news list text
        news_list = "\n".join(
            f"{t['id']}. [{t.get('source', '')}] {t['title']}"
            for t in titles
        )

        # Fill template
        user_prompt = self.classify_user
        user_prompt = user_prompt.replace("{interests_content}", interests_content)
        user_prompt = user_prompt.replace("{tags_list}", tags_list)
        user_prompt = user_prompt.replace("{news_count}", str(len(titles)))
        user_prompt = user_prompt.replace("{news_list}", news_list)

        messages = []
        if self.classify_system:
            messages.append({"role": "system", "content": self.classify_system})
        messages.append({"role": "user", "content": user_prompt})

        if self.debug:
            print(f"\n[AI Filter][DEBUG] === Classification Prompt (title count={len(titles)}, tags={len(tags)}) ===")
            for m in messages:
                role = m['role']
                content = m['content']
                # Truncate overly long news list: only show first 5 and last 5
                lines = content.split('\n')
                # Find news list area and truncate
                if len(lines) > 30:
                    # Show first 15 lines + omission prompt + last 10 lines
                    head = lines[:15]
                    tail = lines[-10:]
                    omitted = len(lines) - 25
                    truncated = '\n'.join(head) + f'\n... (omitted {omitted} lines) ...\n' + '\n'.join(tail)
                    print(f"[{role}]\n{truncated}")
                else:
                    print(f"[{role}]\n{content}")
            print(f"[AI Filter][DEBUG] === Prompt End (length: {sum(len(m['content']) for m in messages)} characters) ===")

        try:
            response = self.client.chat(messages)

            return self._parse_classify_response(response, titles, tags)
        except Exception as e:
            print(f"[AI Filter] Classification request failed: {type(e).__name__}: {e}")
            return []

    def _parse_classify_response(
        self,
        response: str,
        titles: List[Dict],
        tags: List[Dict],
    ) -> List[Dict]:
        """Parse classification AI response

        Supports two JSON formats:
        - New format (flat): [{"id": 1, "tag_id": 1, "score": 0.9}, ...]
        - Old format (nested): [{"id": 1, "tags": [{"tag_id": 1, "score": 0.9}]}, ...]

        Keep only one highest scoring tag per news, preventing the same item from appearing under multiple tags.
        """
        json_str = self._extract_json(response)
        if not json_str:
            if self.debug:
                print(f"[AI Filter][DEBUG] Cannot extract JSON from classification response, first 500 characters of raw response: {(response or '')[:500]}")
            return []

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"[AI Filter][DEBUG] Classification response JSON parsing failed: {e}")
                print(f"[AI Filter][DEBUG] First 500 characters of extracted JSON text: {json_str[:500]}")
            return []

        if not isinstance(data, list):
            if self.debug:
                print(f"[AI Filter][DEBUG] Classification response top level is not an array, actual type: {type(data).__name__}")
            return []

        # Build id mapping
        title_ids = {t["id"] for t in titles}
        title_map = {t["id"]: t["title"] for t in titles}
        tag_id_set = {t["id"] for t in tags}
        tag_name_map = {t["id"]: t["tag"] for t in tags}

        # Keep only one highest scoring tag per news
        best_per_news: Dict[int, Dict] = {}  # news_id -> {"tag_id": ..., "score": ...}
        skipped_news_ids = 0
        skipped_tag_ids = 0
        skipped_empty = 0

        for item in data:
            if not isinstance(item, dict):
                continue
            news_id = item.get("id")
            if news_id not in title_ids:
                skipped_news_ids += 1
                continue

            # Collect all candidate tags for this news
            candidates = []

            if "tag_id" in item:
                # New format (flat): {"id": 1, "tag_id": 1, "score": 0.9}
                candidates.append({"tag_id": item["tag_id"], "score": item.get("score", 0.5)})
            elif "tags" in item:
                # Old format (nested): {"id": 1, "tags": [{"tag_id": 1, "score": 0.9}]}
                matched_tags = item.get("tags", [])
                if isinstance(matched_tags, list):
                    if not matched_tags:
                        skipped_empty += 1
                        continue
                    candidates.extend(matched_tags)

            if not candidates:
                skipped_empty += 1
                continue

            # Get the highest scoring valid tag
            best_tag_id = None
            best_score = -1.0

            for tag_match in candidates:
                if not isinstance(tag_match, dict):
                    continue
                tag_id = tag_match.get("tag_id")
                if tag_id not in tag_id_set:
                    skipped_tag_ids += 1
                    continue

                score = tag_match.get("score", 0.5)
                try:
                    score = float(score)
                    score = max(0.0, min(1.0, score))
                except (ValueError, TypeError):
                    score = 0.5

                if score > best_score:
                    best_score = score
                    best_tag_id = tag_id

            if best_tag_id is not None:
                # If the same news is returned multiple times, keep only the higher score
                existing = best_per_news.get(news_id)
                if existing is None or best_score > existing["relevance_score"]:
                    best_per_news[news_id] = {
                        "news_item_id": news_id,
                        "tag_id": best_tag_id,
                        "relevance_score": best_score,
                    }

        results = list(best_per_news.values())

        if self.debug:
            ai_returned = len(data)
            print(f"[AI Filter][DEBUG] --- Classification parsing results ---")
            print(f"[AI Filter][DEBUG] AI returned {ai_returned} items, valid {len(results)} items (keep only highest scoring tag per news)")
            if skipped_empty > 0:
                print(f"[AI Filter][DEBUG] Skipped empty tags: {skipped_empty} items")
            if skipped_news_ids > 0:
                print(f"[AI Filter][DEBUG] !! Skipped invalid news_id: {skipped_news_ids} items")
            if skipped_tag_ids > 0:
                print(f"[AI Filter][DEBUG] !! Skipped invalid tag_id: {skipped_tag_ids} items")

            # Summarize by tag
            tag_summary: Dict[int, List[str]] = {}
            for r in results:
                tid = r["tag_id"]
                if tid not in tag_summary:
                    tag_summary[tid] = []
                tag_summary[tid].append(
                    f"  [{r['news_item_id']}] {title_map.get(r['news_item_id'], '?')[:40]} (score={r['relevance_score']:.2f})"
                )

            for tid, items in tag_summary.items():
                tname = tag_name_map.get(tid, f"tag_{tid}")
                print(f"[AI Filter][DEBUG] Tag '{tname}' matched {len(items)} items:")
                for line in items:
                    print(line)

        return results

    def _extract_json(self, response: str) -> Optional[str]:
        """Extract JSON string from AI response"""
        if not response or not response.strip():
            return None

        json_str = response.strip()

        if "```json" in json_str:
            parts = json_str.split("```json", 1)
            if len(parts) > 1:
                code_block = parts[1]
                end_idx = code_block.find("```")
                json_str = code_block[:end_idx] if end_idx != -1 else code_block
        elif "```" in json_str:
            parts = json_str.split("```", 2)
            if len(parts) >= 2:
                json_str = parts[1]

        json_str = json_str.strip()
        return json_str if json_str else None

    def _print_formatted_json(self, response: str) -> None:
        """Format and print JSON in AI response for easier debug reading"""
        if not response:
            print("(Empty response)")
            return

        json_str = self._extract_json(response)
        if json_str:
            try:
                data = json.loads(json_str)
                if isinstance(data, list):
                    # Array: compress each element into one line
                    lines = [json.dumps(item, ensure_ascii=False) for item in data]
                    print("[\n  " + ",\n  ".join(lines) + "\n]")
                else:
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                return
            except json.JSONDecodeError:
                pass

        # JSON parsing failed, print original response directly
        print(response)
