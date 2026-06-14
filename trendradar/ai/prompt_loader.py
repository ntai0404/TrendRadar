# coding=utf-8
"""
Prompt word template loading tool

Load the prompt word file in the [system]/[user] format from the configuration directory,
For shared use by modules such as analyzer, translator, and filter.
"""

from pathlib import Path
from typing import Tuple

# Project config root directory
_CONFIG_ROOT = Path(__file__).parent.parent.parent / "config"


def load_prompt_template(
    prompt_file: str,
    config_subdir: str = "",
    label: str = "AI",
) -> Tuple[str, str]:
    """
    Load the prompt word template file and parse the [system] and [user] parts.

    Args:
        prompt_file: prompt word file name
        config_subdir: subdirectory under config (such as "ai_filter"), if it is empty, search directly under config/
        label: log label, used to prompt printing when files are missing

    Returns:
        (system_prompt, user_prompt_template) tuple
    """
    config_dir = _CONFIG_ROOT / config_subdir if config_subdir else _CONFIG_ROOT
    prompt_path = config_dir / prompt_file

    if not prompt_path.exists():
        print(f"[{label}] prompt word file does not exist: {prompt_path}")
        return "", ""

    content = prompt_path.read_text(encoding="utf-8")

    system_prompt = ""
    user_prompt = ""

    if "[system]" in content and "[user]" in content:
        parts = content.split("[user]")
        system_part = parts[0]
        user_part = parts[1] if len(parts) > 1 else ""

        if "[system]" in system_part:
            system_prompt = system_part.split("[system]")[1].strip()

        user_prompt = user_part.strip()
    else:
        user_prompt = content

    return system_prompt, user_prompt
