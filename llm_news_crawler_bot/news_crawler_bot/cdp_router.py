import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from .cdp_manager import create_cdp_profile, profile_for_host, should_auto_create
from .config import AUTO_CDP, AUTO_CDP_CREATE, AUTO_CDP_FALLBACK_MODE


@dataclass
class BrowserSelection:
    browser_mode: str
    cdp_url: Optional[str]
    reason: str
    created_profile: bool = False


def _hostname(value: str) -> str:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    return host.lower().removeprefix("www.")


def _instruction_hosts(instruction: Optional[str]) -> list[str]:
    if not instruction:
        return []
    hosts: list[str] = []
    for raw_url in re.findall(r"https?://[^\s'\"<>]+", instruction):
        host = _hostname(raw_url)
        if host and host not in hosts:
            hosts.append(host)
    return hosts


def select_browser(
    url: str,
    instruction: Optional[str],
    browser_mode: str,
    cdp_url: Optional[str],
) -> BrowserSelection:
    if browser_mode == "cdp" and cdp_url:
        return BrowserSelection("cdp", cdp_url, "CDP profile explicitly provided by request")

    if cdp_url and browser_mode in {"auto", "bundled", "chrome"}:
        return BrowserSelection("cdp", cdp_url, "CDP URL provided by request")

    if AUTO_CDP and browser_mode in {"auto", "bundled"}:
        hosts = [_hostname(url), *_instruction_hosts(instruction)]
        for host in hosts:
            domain, profile_url = profile_for_host(host)
            if domain and profile_url:
                return BrowserSelection("cdp", profile_url, f"CDP profile found for {domain}")
        if AUTO_CDP_CREATE:
            for host in hosts:
                if should_auto_create(host):
                    cdp_url, user_data_dir = create_cdp_profile(host)
                    return BrowserSelection(
                        "cdp",
                        cdp_url,
                        f"created new CDP profile for {host}; user data dir={user_data_dir}",
                        created_profile=True,
                    )

    fallback = AUTO_CDP_FALLBACK_MODE if browser_mode == "auto" else browser_mode
    return BrowserSelection(
        fallback,
        None,
        f"no CDP profile found; launching temporary {fallback} browser",
    )
