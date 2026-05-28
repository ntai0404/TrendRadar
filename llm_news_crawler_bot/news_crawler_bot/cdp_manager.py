import json
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

from .config import (
    AUTO_CDP_CREATE_DOMAINS,
    CDP_PROFILES,
    CDP_RUNTIME_PROFILES_PATH,
    CDP_START_PORT,
    CDP_USER_DATA_ROOT,
    CHROME_EXECUTABLE,
)


def normalize_domain(host: str) -> str:
    return host.lower().removeprefix("www.")


def should_auto_create(host: str) -> bool:
    normalized = normalize_domain(host)
    return any(normalized == domain or normalized.endswith("." + domain) for domain in AUTO_CDP_CREATE_DOMAINS)


def load_runtime_profiles() -> dict[str, str]:
    if not CDP_RUNTIME_PROFILES_PATH.exists():
        return {}
    try:
        data = json.loads(CDP_RUNTIME_PROFILES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {normalize_domain(str(domain)): str(url) for domain, url in data.items() if url}


def all_profiles() -> dict[str, str]:
    profiles = {normalize_domain(domain): url for domain, url in CDP_PROFILES.items()}
    profiles.update(load_runtime_profiles())
    return profiles


def save_runtime_profile(domain: str, cdp_url: str) -> None:
    profiles = load_runtime_profiles()
    profiles[normalize_domain(domain)] = cdp_url
    CDP_RUNTIME_PROFILES_PATH.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def profile_for_host(host: str) -> tuple[Optional[str], Optional[str]]:
    normalized = normalize_domain(host)
    for domain, cdp_url in all_profiles().items():
        profile_domain = normalize_domain(domain)
        if normalized == profile_domain or normalized.endswith("." + profile_domain):
            return profile_domain, cdp_url
    return None, None


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _find_free_port(start: int) -> int:
    for port in range(start, start + 200):
        if _is_port_free(port):
            return port
    raise RuntimeError(f"No free CDP port found from {start} to {start + 199}")


def _chrome_candidates() -> list[str]:
    if CHROME_EXECUTABLE:
        return [CHROME_EXECUTABLE]
    return [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\pc\AppData\Local\Google\Chrome\Application\chrome.exe",
        "chrome.exe",
        "msedge.exe",
    ]


def _find_chrome() -> str:
    for candidate in _chrome_candidates():
        if candidate.endswith(".exe") and ("\\" in candidate or "/" in candidate):
            if Path(candidate).exists():
                return candidate
            continue
        return candidate
    raise RuntimeError("Chrome executable not found. Set CHROME_EXECUTABLE in .env.")


def _wait_for_cdp(port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                return response.status == 200
        except Exception:
            time.sleep(0.4)
    return False


def create_cdp_profile(domain: str) -> tuple[str, str]:
    normalized = normalize_domain(domain)
    port = _find_free_port(CDP_START_PORT)
    user_data_dir = CDP_USER_DATA_ROOT / normalized.replace(".", "_")
    user_data_dir.mkdir(parents=True, exist_ok=True)
    chrome = _find_chrome()
    args = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-popup-blocking",
        "about:blank",
    ]
    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if not _wait_for_cdp(port):
        raise RuntimeError(f"Chrome CDP did not start on port {port}")
    cdp_url = f"http://127.0.0.1:{port}"
    save_runtime_profile(normalized, cdp_url)
    return cdp_url, str(user_data_dir)
