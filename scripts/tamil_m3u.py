from m3u_utils import (
    DEFAULT_SKIP_URLS,
    fetch_text,
    filter_reachable_entries,
    get_runtime_options,
    parse_m3u_entries,
    render_m3u,
    sort_entries,
)


def fix_m3u_from_url(urls):
    options = get_runtime_options(default_check_urls=True, default_workers=20)

    for url in urls:
        m3u_content = fetch_text(url, timeout=10)
        if not m3u_content:
            continue
        entries = parse_m3u_entries(
            m3u_content, default_group_title="Others", skip_urls=DEFAULT_SKIP_URLS
        )
        reachable_entries = filter_reachable_entries(
            entries,
            check_urls=options["check_urls"],
            max_workers=options["max_workers"],
            timeout=10,
        )
        print(render_m3u(sort_entries(reachable_entries)))


if __name__ == "__main__":
    m3u_urls = [
        # 'https://raw.githubusercontent.com/manisat30/Sat/main/DSC.m3u',
        # 'https://raw.githubusercontent.com/suvisnimpraven/suvisnimpraven.github.io/main/suresh.m3u8',
        # 'https://live-iptv.github.io/iptv/tamil/tamil_local_copy.m3u',
        "https://iptv-org.github.io/iptv/languages/tam.m3u",
    ]
    fix_m3u_from_url(m3u_urls)
