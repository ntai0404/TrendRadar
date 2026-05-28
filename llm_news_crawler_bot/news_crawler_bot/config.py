from pathlib import Path
import json
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

ROUTER_BASE_URL = os.getenv("ROUTER_BASE_URL", "http://127.0.0.1:20128/v1")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "sk-local-placeholder")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "ag/gemini-3.1-pro-low")

PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
PLAYWRIGHT_TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "60000"))

AUTO_CDP = os.getenv("AUTO_CDP", "true").lower() == "true"
AUTO_CDP_FALLBACK_MODE = os.getenv("AUTO_CDP_FALLBACK_MODE", "bundled").strip().lower()
if AUTO_CDP_FALLBACK_MODE not in {"bundled", "chrome"}:
    AUTO_CDP_FALLBACK_MODE = "bundled"
AUTO_CDP_CREATE = os.getenv("AUTO_CDP_CREATE", "true").lower() == "true"
AUTO_CDP_FIRST_RUN_WAIT_SECONDS = int(os.getenv("AUTO_CDP_FIRST_RUN_WAIT_SECONDS", "60"))
AUTO_CDP_CREATE_DOMAINS = {
    domain.strip().lower().removeprefix("www.")
    for domain in os.getenv("AUTO_CDP_CREATE_DOMAINS", "facebook.com,instagram.com,tiktok.com,x.com,twitter.com").split(",")
    if domain.strip()
}
CDP_START_PORT = int(os.getenv("CDP_START_PORT", "9222"))
CDP_USER_DATA_ROOT = Path(os.getenv("CDP_USER_DATA_ROOT", str(BASE_DIR / ".cdp_profiles")))
if not CDP_USER_DATA_ROOT.is_absolute():
    CDP_USER_DATA_ROOT = BASE_DIR / CDP_USER_DATA_ROOT
CDP_USER_DATA_ROOT.mkdir(parents=True, exist_ok=True)
CDP_RUNTIME_PROFILES_PATH = Path(os.getenv("CDP_RUNTIME_PROFILES_PATH", str(BASE_DIR / "cdp_profiles.runtime.json")))
if not CDP_RUNTIME_PROFILES_PATH.is_absolute():
    CDP_RUNTIME_PROFILES_PATH = BASE_DIR / CDP_RUNTIME_PROFILES_PATH
CHROME_EXECUTABLE = os.getenv("CHROME_EXECUTABLE", "").strip()


def _load_cdp_profiles(raw: str) -> dict[str, str]:
    raw = raw.strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(domain).lower(): str(url) for domain, url in data.items() if url}
    except json.JSONDecodeError:
        pass

    profiles: dict[str, str] = {}
    for pair in raw.split(";"):
        if "=" not in pair:
            continue
        domain, cdp_url = pair.split("=", 1)
        domain = domain.strip().lower()
        cdp_url = cdp_url.strip()
        if domain and cdp_url:
            profiles[domain] = cdp_url
    return profiles


CDP_PROFILES = _load_cdp_profiles(os.getenv("CDP_PROFILES", ""))

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = BASE_DIR / OUTPUT_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
