from m3u_utils import (
    DEFAULT_SKIP_URLS,
    fetch_json,
    filter_reachable_entries,
    get_runtime_options,
    render_m3u,
)


def fix_m3u_from_url(urls):
    options = get_runtime_options(default_check_urls=True, default_workers=20)

    def process_json_content(json_data):
        entries = []
        seen_urls = set(DEFAULT_SKIP_URLS)

        for category in json_data:
            group_title = category.get("label", "Unknown Group")
            if group_title != "Malayalam":
                continue

            for channel in category.get("channels", []):
                url = channel.get("url", "")
                if not url or url in seen_urls:
                    continue

                entries.append(
                    {
                        "group_title": "Entertainment",
                        "tvg_logo": channel.get("logo", ""),
                        "name": channel.get("name", channel.get("title", "Unknown")),
                        "url": url,
                    }
                )
                seen_urls.add(url)

            break

        reachable_entries = filter_reachable_entries(
            entries,
            check_urls=options["check_urls"],
            max_workers=options["max_workers"],
            timeout=10,
        )

        # Single group title, so sort by name only.
        reachable_entries.sort(key=lambda entry: entry["name"])
        return render_m3u(reachable_entries)

    for url in urls:
        json_data = fetch_json(url, timeout=10)
        if json_data:
            print(process_json_content(json_data))


if __name__ == "__main__":
    json_urls = [
        "https://tavapi.inditechman.com/api/tamiltvapp.json",
    ]
    fix_m3u_from_url(json_urls)
