# coding=utf-8
"""
Frequency word configuration loading module

Responsible for loading frequency word rules from the configuration file, supports:
- Normal word groups
- Mandatory words (+ prefix)
- Filter words (! prefix)
- Global filter words ([GLOBAL_FILTER] section)
- Maximum display quantity (@ prefix)
- Regular expressions (/pattern/ syntax)
- Display name (=> alias syntax)
- Group alias ([group alias] syntax, as the first line of the word group)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union


def _parse_word(word: str) -> Dict:
    """
    Parse a single word, identify if it is a regular expression, support display name

    Args:
        word: Original configuration line (e.g. "/JD|Liu Qiangdong/ => JD")

    Returns:
        Dict: Contains word, is_regex, pattern, display_name
    """
    display_name = None

    # 1. Prioritize processing display name (=>)
    # First split out "configuration content" and "display name"
    if '=>' in word:
        parts = re.split(r'\s*=>\s*', word, 1)
        word_config = parts[0].strip()
        # Only when there is content on the right side of => is it used as display_name
        if len(parts) > 1 and parts[1].strip():
            display_name = parts[1].strip()
    else:
        word_config = word.strip()

    # 2. Parse regular expression
    # Rule: Starts with /, ends with / (possibly followed by flags), middle content is greedily extracted
    # [a-z]*$ indicates that flags (such as i, g) are allowed at the end, but will be ignored in the code below
    regex_match = re.match(r'^/(.+)/[a-z]*$', word_config)

    if regex_match:
        pattern_str = regex_match.group(1)
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            
            return {
                "word": pattern_str,
                "is_regex": True,
                "pattern": pattern,
                "display_name": display_name,
            }
        except re.error as e:
            print(f"Warning: Invalid regex pattern '/{pattern_str}/': {e}")
            pass

    return {
        "word": word_config, 
        "is_regex": False, 
        "pattern": None, 
        "display_name": display_name
    }


def _word_matches(word_config: Union[str, Dict], title_lower: str) -> bool:
    """
    Check if the word matches in the title

    Args:
        word_config: Word configuration (string or dictionary)
        title_lower: Lowercase title

    Returns:
        Whether it matches
    """
    if isinstance(word_config, str):
        # Backward compatibility: pure string
        return word_config.lower() in title_lower

    if word_config.get("is_regex") and word_config.get("pattern"):
        # Regex match
        return bool(word_config["pattern"].search(title_lower))
    else:
        # Substring match
        return word_config["word"].lower() in title_lower


def load_frequency_words(
    frequency_file: Optional[str] = None,
) -> Tuple[List[Dict], List[str], List[str]]:
    """
    Load frequency word configuration

    Configuration file format description:
    - Each word group is separated by a blank line
    - [GLOBAL_FILTER] section defines global filter words
    - [WORD_GROUPS] section defines word groups (default)

    Word group syntax:
    - Normal word: written directly, any match is sufficient
    - +word: mandatory word, all mandatory words must match
    - !word: filter word, exclude if matched
    - @number: the maximum number of items displayed for this word group

    Args:
        frequency_file: Frequency word configuration file path, defaults to getting from environment variable FREQUENCY_WORDS_PATH or using config/frequency_words.txt, short file names are searched from config/custom/keyword/

    Returns:
        (Word group list, filter words within word groups, global filter words)

    Raises:
        FileNotFoundError: Frequency word file does not exist
    """
    if frequency_file is None:
        frequency_file = os.environ.get(
            "FREQUENCY_WORDS_PATH", "config/frequency_words.txt"
        )

    frequency_path = Path(frequency_file)
    if not frequency_path.exists():
        # Try as a short file name, concatenate config/custom/keyword/ prefix
        custom_path = Path("config/custom/keyword") / frequency_file
        if custom_path.exists():
            frequency_path = custom_path
        else:
            raise FileNotFoundError(f"Frequency word file {frequency_file} does not exist")

    with open(frequency_path, "r", encoding="utf-8") as f:
        content = f.read()

    word_groups = [group.strip() for group in content.split("\n\n") if group.strip()]

    processed_groups = []
    filter_words = []
    global_filters = []

    # Default region (backward compatible)
    current_section = "WORD_GROUPS"

    for group in word_groups:
        # Filter empty lines and comment lines (starting with #)
        lines = [line.strip() for line in group.split("\n") if line.strip() and not line.strip().startswith("#")]

        if not lines:
            continue

        # Check if it is a region marker
        if lines[0].startswith("[") and lines[0].endswith("]"):
            section_name = lines[0][1:-1].upper()
            if section_name in ("GLOBAL_FILTER", "WORD_GROUPS"):
                current_section = section_name
                lines = lines[1:]  # Remove marker line

        # Process global filter region
        if current_section == "GLOBAL_FILTER":
            # Directly add all non-empty lines to the global filter list
            for line in lines:
                # Ignore special syntax prefixes, extract plain text only
                if line.startswith(("!", "+", "@")):
                    continue  # Global filter region does not support special syntax
                if line:
                    global_filters.append(line)
            continue

        # Process word group region
        words = lines
        group_alias = None  # Group alias ([alias] syntax)

        # Check if the first line is a group alias (not a region marker)
        if words and words[0].startswith("[") and words[0].endswith("]"):
            potential_alias = words[0][1:-1].strip()
            # Exclude region markers (GLOBAL_FILTER, WORD_GROUPS)
            if potential_alias.upper() not in ("GLOBAL_FILTER", "WORD_GROUPS"):
                group_alias = potential_alias
                words = words[1:]  # Remove group alias line

        group_required_words = []
        group_normal_words = []
        group_max_count = 0  # Default no limit

        for word in words:
            if word.startswith("@"):
                # Parse maximum display count (only accepts positive integers)
                try:
                    count = int(word[1:])
                    if count > 0:
                        group_max_count = count
                except (ValueError, IndexError):
                    pass  # Ignore invalid @number format
            elif word.startswith("!"):
                # Filter words (supports regex syntax)
                filter_word = word[1:]
                parsed = _parse_word(filter_word)
                filter_words.append(parsed)
            elif word.startswith("+"):
                # Required words (supports regex syntax)
                req_word = word[1:]
                group_required_words.append(_parse_word(req_word))
            else:
                # Normal words (supports regex syntax)
                group_normal_words.append(_parse_word(word))

        if group_required_words or group_normal_words:
            if group_normal_words:
                group_key = " ".join(w["word"] for w in group_normal_words)
            else:
                group_key = " ".join(w["word"] for w in group_required_words)

            # Generate display name
            # Priority: group alias > line alias concatenation > keyword concatenation
            if group_alias:
                # Has group alias, use directly
                display_name = group_alias
            else:
                # No group alias, concatenate display name of each line (line alias or keyword itself)
                all_words = group_normal_words + group_required_words
                display_parts = []
                for w in all_words:
                    # Prefer line alias, otherwise use keyword itself
                    part = w.get("display_name") or w["word"]
                    display_parts.append(part)
                # Concatenate multiple words with " / "
                display_name = " / ".join(display_parts) if display_parts else None

            processed_groups.append(
                {
                    "required": group_required_words,
                    "normal": group_normal_words,
                    "group_key": group_key,
                    "display_name": display_name,  # May be None
                    "max_count": group_max_count,
                }
            )

    return processed_groups, filter_words, global_filters


def matches_word_groups(
    title: str,
    word_groups: List[Dict],
    filter_words: List,
    global_filters: Optional[List[str]] = None
) -> bool:
    """
    Check if title matches word group rules

    Args:
        title: Title text
        word_groups: Word group list
        filter_words: Filter word list (can be a list of strings or a list of dictionaries)
        global_filters: Global filter word list

    Returns:
        Whether it matches
    """
    # Defensive type check: ensure title is a valid string
    if not isinstance(title, str):
        title = str(title) if title is not None else ""
    if not title.strip():
        return False

    title_lower = title.lower()

    # Global filter check (highest priority)
    if global_filters:
        if any(global_word.lower() in title_lower for global_word in global_filters):
            return False

    # If no word groups are configured, match all titles (supports displaying all news)
    if not word_groups:
        return True

    # Filter word check (compatible with old and new formats)
    for filter_item in filter_words:
        if _word_matches(filter_item, title_lower):
            return False

    # Word group match check
    for group in word_groups:
        required_words = group["required"]
        normal_words = group["normal"]

        # Required word check
        if required_words:
            all_required_present = all(
                _word_matches(req_item, title_lower) for req_item in required_words
            )
            if not all_required_present:
                continue

        # Normal word check
        if normal_words:
            any_normal_present = any(
                _word_matches(normal_item, title_lower) for normal_item in normal_words
            )
            if not any_normal_present:
                continue

        return True

    return False
