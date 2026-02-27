from urllib.parse import urlparse, unquote
import os

from common_utils import PlaylistUtils

def fix_m3u_from_url(urls):
    for url in urls:
        m3u_content = PlaylistUtils.fetch_text(url)
        if m3u_content:
            # Decode the file name to handle special characters
            decoded_file_name = unquote(os.path.splitext(os.path.basename(urlparse(url).path))[0])
            entries = PlaylistUtils.parse_m3u_entries(
                m3u_content,
                default_group_title=decoded_file_name,
            )
            entries = PlaylistUtils.filter_reachable(entries)
            entries = PlaylistUtils.sort_entries(entries)
            fixed_content = PlaylistUtils.to_m3u(entries)
            print(fixed_content)

if __name__ == "__main__":
    m3u_urls = [
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%201.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%202.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20A-B.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20C-H.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20I-L.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20S.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20T-W.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20X.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20Y.m3u',
        'https://raw.githubusercontent.com/eklins/FDTV/main/tv/xxx%20Japan%20Z.m3u',
    ]
    fix_m3u_from_url(m3u_urls)
