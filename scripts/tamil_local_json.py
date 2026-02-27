from m3u_core import (
    DEFAULT_SKIP_URLS,
    dedupe_entries,
    extract_json_entries,
    fetch_json,
    filter_reachable_entries,
    render_m3u,
    sort_entries,
)

JSON_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; Python script)",
}
SKIP_CATEGORIES = {"Malayalam", "Telugu", "Kannada"}


def _channel_filter(_category: dict, channel: dict) -> bool:
    if channel.get("category", "").strip() in SKIP_CATEGORIES:
        return False
    url = channel.get("url", "").strip()
    return bool(url) and url not in DEFAULT_SKIP_URLS


def fix_m3u_from_url(urls: list[str]) -> None:
    for url in urls:
        json_data = fetch_json(url, headers=JSON_HEADERS)
        if not isinstance(json_data, list):
            continue

        entries = extract_json_entries(
            json_data,
            channel_filter=_channel_filter,
            group_title_resolver=lambda category: category.get("label", "Unknown Group"),
        )
        entries = dedupe_entries(entries)
        entries = filter_reachable_entries(entries, check_reachability=True, max_workers=20)
        entries = sort_entries(entries, keys=("group_title", "name"))
        print(render_m3u(entries))


if __name__ == "__main__":
    json_urls = ["https://tavapi.inditechman.com/api/tamiltvapp.json"]
    fix_m3u_from_url(json_urls)
