import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
DEFAULT_SKIP_URLS = {"https://live-iptv.github.io/youtube_live/assets/info.m3u8"}


def _get_requests_module():
    try:
        import requests  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The 'requests' package is required for network operations. "
            "Install dependencies with: python3 -m pip install -r requirements.txt"
        ) from exc
    return requests


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    timeout: int = 10,
    allow_redirects: bool = True,
    stream: bool = False,
    retries: int = 2,
    backoff_seconds: float = 0.5,
) -> object | None:
    requests = _get_requests_module()
    for attempt in range(retries + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=allow_redirects,
                stream=stream,
            )
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < retries:
                response.close()
                time.sleep(backoff_seconds * (2**attempt))
                continue
            return response
        except requests.RequestException:
            if attempt < retries:
                time.sleep(backoff_seconds * (2**attempt))
                continue
    return None


def fetch_text(url: str, *, timeout: int = 10) -> str | None:
    response = request_with_retries("GET", url, timeout=timeout)
    if response is None:
        return None
    try:
        if response.status_code == 200:
            return response.text
        return None
    finally:
        response.close()


def fetch_json(url: str, *, timeout: int = 10, headers: dict | None = None) -> list | dict | None:
    response = request_with_retries("GET", url, timeout=timeout, headers=headers)
    if response is None:
        return None
    try:
        if response.status_code != 200:
            return None
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return None
    finally:
        response.close()


def is_url_reachable(url: str, *, timeout: int = 10) -> bool:
    head_response = request_with_retries("HEAD", url, timeout=timeout, allow_redirects=True)
    if head_response is not None:
        try:
            if head_response.status_code < 400:
                return True
            if head_response.status_code not in (403, 405):
                return False
        finally:
            head_response.close()

    get_response = request_with_retries(
        "GET",
        url,
        timeout=timeout,
        allow_redirects=True,
        stream=True,
    )
    if get_response is None:
        return False
    try:
        return get_response.status_code < 400
    finally:
        get_response.close()


def parse_m3u_entries(
    content: str,
    *,
    default_group_title: str,
    skip_urls: set[str] | None = None,
) -> list[dict]:
    skip_urls = DEFAULT_SKIP_URLS if skip_urls is None else skip_urls
    extinf_pattern = re.compile(r"^#EXTINF:-?\d+\s*(.*?),(.*)$")
    group_pattern = re.compile(r'group-title="([^"]*)"')
    logo_pattern = re.compile(r'tvg-logo="([^"]*)"')

    entries: list[dict] = []
    current_entry: dict | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF"):
            match = extinf_pattern.search(line)
            if not match:
                current_entry = None
                continue

            attributes = match.group(1)
            name = match.group(2).strip()

            group_match = group_pattern.search(attributes)
            group_title = group_match.group(1) if group_match else default_group_title

            logo_match = logo_pattern.search(attributes)
            tvg_logo = logo_match.group(1) if logo_match else ""

            current_entry = {
                "group_title": group_title,
                "tvg_logo": tvg_logo,
                "name": name,
            }
            continue

        if current_entry is not None and not line.startswith("#"):
            if line not in skip_urls:
                entry = current_entry.copy()
                entry["url"] = line
                entries.append(entry)
            current_entry = None

    return entries


def dedupe_entries(entries: Iterable[dict]) -> list[dict]:
    unique_entries: list[dict] = []
    seen_urls: set[str] = set()
    for entry in entries:
        url = entry.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        unique_entries.append(entry)
    return unique_entries


def filter_reachable_entries(
    entries: list[dict],
    *,
    check_reachability: bool,
    max_workers: int = 20,
) -> list[dict]:
    if not check_reachability:
        return list(entries)

    reachable_entries: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(is_url_reachable, entry["url"]): entry
            for entry in entries
        }
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            if future.result():
                reachable_entries.append(entry)

    return reachable_entries


def sort_entries(entries: list[dict], *, keys: tuple[str, ...]) -> list[dict]:
    return sorted(entries, key=lambda entry: tuple(entry[key] for key in keys))


def render_m3u(entries: list[dict]) -> str:
    lines = ["#EXTM3U"]
    for entry in entries:
        lines.append(
            f'#EXTINF:-1 group-title="{entry["group_title"]}" '
            f'tvg-logo="{entry["tvg_logo"]}",{entry["name"]}'
        )
        lines.append(entry["url"])
    return "\n".join(lines)


def normalize_m3u_content(
    content: str,
    *,
    default_group_title: str,
    sort_keys: tuple[str, ...] = ("group_title", "name"),
    check_reachability: bool = True,
    max_workers: int = 20,
    skip_urls: set[str] | None = None,
) -> str:
    entries = parse_m3u_entries(
        content,
        default_group_title=default_group_title,
        skip_urls=skip_urls,
    )
    entries = dedupe_entries(entries)
    entries = filter_reachable_entries(
        entries,
        check_reachability=check_reachability,
        max_workers=max_workers,
    )
    entries = sort_entries(entries, keys=sort_keys)
    return render_m3u(entries)


def extract_json_entries(
    json_data: list,
    *,
    category_filter: Callable[[dict], bool] | None = None,
    channel_filter: Callable[[dict, dict], bool] | None = None,
    group_title_resolver: Callable[[dict], str] | None = None,
    stop_after_first_category_match: bool = False,
) -> list[dict]:
    entries: list[dict] = []

    for category in json_data:
        if category_filter and not category_filter(category):
            continue

        group_title = (
            group_title_resolver(category)
            if group_title_resolver is not None
            else category.get("label", "Unknown Group")
        )

        for channel in category.get("channels", []):
            if channel_filter and not channel_filter(category, channel):
                continue

            url = channel.get("url", "").strip()
            if not url:
                continue

            entries.append(
                {
                    "group_title": group_title,
                    "tvg_logo": channel.get("logo", ""),
                    "name": channel.get("name", channel.get("title", "Unknown")),
                    "url": url,
                }
            )

        if stop_after_first_category_match:
            break

    return entries
