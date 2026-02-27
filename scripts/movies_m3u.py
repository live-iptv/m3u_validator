from m3u_core import fetch_text, normalize_m3u_content


def fix_m3u_from_url(urls: list[str]) -> None:
    for url in urls:
        m3u_content = fetch_text(url)
        if not m3u_content:
            continue

        fixed_content = normalize_m3u_content(
            m3u_content,
            default_group_title="Movies",
            sort_keys=("group_title", "name"),
            check_reachability=True,
            max_workers=20,
        )
        print(fixed_content)


if __name__ == "__main__":
    m3u_urls = ["https://live-iptv.github.io/iptv/movies.m3u"]
    fix_m3u_from_url(m3u_urls)
