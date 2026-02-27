import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import requests

DEFAULT_SKIP_URLS = {"https://live-iptv.github.io/youtube_live/assets/info.m3u8"}
_EXTINF_RE = re.compile(r"#EXTINF:-1(.*?),(.+)")
_GROUP_RE = re.compile(r'group-title="([^"]*)"')
_LOGO_RE = re.compile(r'tvg-logo="([^"]*)"')


def fetch_text(url: str, timeout: int = 10) -> Optional[str]:
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        return None
    return None


def fetch_json(url: str, timeout: int = 10) -> Optional[Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; Python script)",
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.json()
    except (requests.RequestException, ValueError):
        return None
    return None


def parse_m3u_entries(
    content: str,
    default_group_title: str,
    skip_urls: Optional[Set[str]] = None,
) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    current_entry: Optional[Dict[str, str]] = None
    seen_urls: Set[str] = set(skip_urls or set())

    for line in content.splitlines():
        if line.startswith("#EXTINF:-1"):
            match = _EXTINF_RE.search(line)
            if not match:
                continue
            attributes = match.group(1)
            group_match = _GROUP_RE.search(attributes)
            logo_match = _LOGO_RE.search(attributes)
            current_entry = {
                "group_title": group_match.group(1) if group_match else default_group_title,
                "tvg_logo": logo_match.group(1) if logo_match else "",
                "name": match.group(2).strip().split(",")[-1],
            }
        elif current_entry is not None and line.strip():
            url = line.strip()
            if url and url not in seen_urls:
                current_entry["url"] = url
                entries.append(current_entry)
                seen_urls.add(url)
            current_entry = None

    return entries


def is_url_reachable(url: str, timeout: int = 10) -> bool:
    try:
        head_response = requests.head(url, timeout=timeout, allow_redirects=True)
        if 200 <= head_response.status_code < 400:
            return True
        # Some streams block HEAD even when GET is valid.
        if head_response.status_code in (403, 405):
            get_response = requests.get(url, timeout=timeout, stream=True, allow_redirects=True)
            ok = 200 <= get_response.status_code < 400
            get_response.close()
            return ok
    except requests.RequestException:
        return False
    return False


def filter_reachable_entries(
    entries: Sequence[Dict[str, str]],
    check_urls: bool,
    max_workers: int = 20,
    timeout: int = 10,
) -> List[Dict[str, str]]:
    if not check_urls:
        return list(entries)

    def _check(entry: Dict[str, str]) -> Optional[Dict[str, str]]:
        if is_url_reachable(entry["url"], timeout=timeout):
            return entry
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return [entry for entry in executor.map(_check, entries) if entry is not None]


def sort_entries(entries: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(entries, key=lambda entry: (entry["group_title"], entry["name"]))


def render_m3u(entries: Iterable[Dict[str, str]]) -> str:
    content = ["#EXTM3U"]
    for entry in entries:
        content.append(
            f'#EXTINF:-1 group-title="{entry["group_title"]}" '
            f'tvg-logo="{entry["tvg_logo"]}",{entry["name"]}\n{entry["url"]}'
        )
    return "\n".join(content)


def get_runtime_options(default_check_urls: bool, default_workers: int = 20) -> Dict[str, Any]:
    raw_check = os.getenv("M3U_CHECK_URLS")
    if raw_check is None:
        check_urls = default_check_urls
    else:
        check_urls = raw_check.lower() not in {"0", "false", "no", "off"}

    raw_workers = os.getenv("M3U_MAX_WORKERS")
    try:
        max_workers = int(raw_workers) if raw_workers else default_workers
    except ValueError:
        max_workers = default_workers

    if max_workers < 1:
        max_workers = 1

    return {"check_urls": check_urls, "max_workers": max_workers}
