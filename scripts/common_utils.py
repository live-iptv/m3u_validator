import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Iterable, List, Optional, Sequence, Set

import requests


class PlaylistUtils:
    ALLOWED_STATUS_CODES = {200, 206, 301, 302, 303, 307, 308}

    @staticmethod
    def fetch_text(url: str, timeout: int = 10) -> Optional[str]:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.text
        except requests.RequestException:
            pass
        return None

    @staticmethod
    def fetch_json(url: str, timeout: int = 10) -> Optional[object]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; Python script)",
        }
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except (requests.RequestException, ValueError):
            pass
        return None

    @staticmethod
    def parse_m3u_entries(
        content: str,
        default_group_title: str = "Others",
        skip_urls: Optional[Set[str]] = None,
    ) -> List[Dict[str, str]]:
        lines = content.split("\n")
        entries: List[Dict[str, str]] = []
        current_entry: Optional[Dict[str, str]] = None
        seen_urls: Set[str] = set(skip_urls or set())

        for line in lines:
            if line.startswith("#EXTINF:-1"):
                match = re.search(r"#EXTINF:-1(.*?),(.+)", line)
                if match:
                    attributes = match.group(1)
                    group_title_match = re.search(r'group-title="([^"]*)"', attributes)
                    group_title = (
                        group_title_match.group(1)
                        if group_title_match
                        else default_group_title
                    )

                    tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', attributes)
                    tvg_logo = tvg_logo_match.group(1) if tvg_logo_match else ""

                    name = match.group(2).strip().split(",")[-1]
                    current_entry = {
                        "group_title": group_title,
                        "tvg_logo": tvg_logo,
                        "name": name,
                    }
            elif current_entry is not None and line.strip():
                current_entry["url"] = line.strip()
                if current_entry["url"] not in seen_urls:
                    entries.append(current_entry)
                    seen_urls.add(current_entry["url"])
                current_entry = None

        return entries

    @staticmethod
    def deduplicate_by_url(entries: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
        unique_entries: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()
        for entry in entries:
            url = entry.get("url", "")
            if url and url not in seen_urls:
                unique_entries.append(entry)
                seen_urls.add(url)
        return unique_entries

    @staticmethod
    def filter_reachable(
        entries: Sequence[Dict[str, str]],
        allow_redirects: bool = False,
    ) -> List[Dict[str, str]]:
        def is_url_reachable(entry: Dict[str, str]) -> Optional[Dict[str, str]]:
            try:
                response = requests.head(
                    entry["url"],
                    timeout=10,
                    allow_redirects=allow_redirects,
                )
                if response.status_code in PlaylistUtils.ALLOWED_STATUS_CODES:
                    return entry
            except requests.RequestException:
                pass
            return None

        reachable_entries: List[Dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(is_url_reachable, entry) for entry in entries]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    reachable_entries.append(result)
        return reachable_entries

    @staticmethod
    def sort_entries(entries: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
        sorted_entries = sorted(entries, key=lambda x: x["name"])
        sorted_entries = sorted(sorted_entries, key=lambda x: x["group_title"])
        return sorted_entries

    @staticmethod
    def to_m3u(entries: Sequence[Dict[str, str]]) -> str:
        m3u_content = ["#EXTM3U"]
        for entry in entries:
            m3u_content.append(
                f'#EXTINF:-1 group-title="{entry["group_title"]}" '
                f'tvg-logo="{entry["tvg_logo"]}",{entry["name"]}\n{entry["url"]}'
            )
        return "\n".join(m3u_content)
