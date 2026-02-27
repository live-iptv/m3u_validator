import os
from urllib.parse import unquote, urlparse

from m3u_core import fetch_text, normalize_m3u_content


def _default_group_title_from_url(url: str) -> str:
    return unquote(os.path.splitext(os.path.basename(urlparse(url).path))[0])


def fix_m3u_from_url(urls: list[str]) -> None:
    for url in urls:
        m3u_content = fetch_text(url)
        if not m3u_content:
            continue

        fixed_content = normalize_m3u_content(
            m3u_content,
            default_group_title=_default_group_title_from_url(url),
            sort_keys=("group_title", "name"),
            check_reachability=True,
            max_workers=20,
            skip_urls=set(),
        )
        print(fixed_content)


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
