import os
from urllib.parse import unquote, urlparse

from m3u_utils import (
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

        decoded_file_name = unquote(os.path.splitext(os.path.basename(urlparse(url).path))[0])
        entries = parse_m3u_entries(
            m3u_content,
            default_group_title=decoded_file_name,
            skip_urls=None,
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
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%201.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%202.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20A-B.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20C-H.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20I-L.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20S.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20T-W.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20X.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20Y.m3u",
        "https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20Z.m3u",
    ]
    fix_m3u_from_url(m3u_urls)
