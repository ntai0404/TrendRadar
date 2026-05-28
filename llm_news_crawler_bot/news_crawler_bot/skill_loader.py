from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]
PROMPT_DIR = BASE_DIR / "prompt_skills"
CORE_SKILL_PATH = PROMPT_DIR / "core.md"
SOURCE_SKILLS_DIR = PROMPT_DIR / "sources"


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def hostname_from_url(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url).hostname or ""
    return host.lower().removeprefix("www.")


def _candidate_source_files(host: str) -> list[Path]:
    if not host:
        return []
    parts = host.split(".")
    candidates = [host]
    if len(parts) > 2:
        candidates.append(".".join(parts[-2:]))
    return [SOURCE_SKILLS_DIR / f"{candidate}.md" for candidate in dict.fromkeys(candidates)]


def load_runtime_skill(url: str | None, platform_hint: str | None = None) -> str:
    chunks: list[str] = []
    core = _read(CORE_SKILL_PATH)
    if core:
        chunks.append(f"<core_crawler_skill>\n{core}\n</core_crawler_skill>")

    host = hostname_from_url(url)
    for path in _candidate_source_files(host):
        source_skill = _read(path)
        if source_skill:
            chunks.append(f"<source_skill file=\"{path.name}\">\n{source_skill}\n</source_skill>")
            break

    if platform_hint:
        platform_path = SOURCE_SKILLS_DIR / f"{platform_hint.lower()}.md"
        platform_skill = _read(platform_path)
        if platform_skill:
            chunks.append(f"<platform_skill file=\"{platform_path.name}\">\n{platform_skill}\n</platform_skill>")

    return "\n\n".join(chunks)
