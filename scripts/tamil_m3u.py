from common_utils import PlaylistUtils

def fix_m3u_from_url(urls):
    skip_urls = {"https://live-iptv.github.io/youtube_live/assets/info.m3u8"}

    for url in urls:
        m3u_content = PlaylistUtils.fetch_text(url)
        if m3u_content:
            entries = PlaylistUtils.parse_m3u_entries(
                m3u_content,
                default_group_title="Others",
                skip_urls=skip_urls,
            )
            entries = PlaylistUtils.filter_reachable(entries, max_workers=20)
            entries = PlaylistUtils.sort_entries(entries)
            fixed_content = PlaylistUtils.to_m3u(entries)
            print(fixed_content)

if __name__ == "__main__":
    m3u_urls = [
        # 'https://raw.githubusercontent.com/manisat30/Sat/main/DSC.m3u',
        # 'https://raw.githubusercontent.com/suvisnimpraven/suvisnimpraven.github.io/main/suresh.m3u8',
        # 'https://live-iptv.github.io/iptv/tamil/tamil_local_copy.m3u',
        'https://iptv-org.github.io/iptv/languages/tam.m3u'
    ]
    fix_m3u_from_url(m3u_urls)
