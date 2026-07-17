from common_utils import PlaylistUtils

def fix_m3u_from_url(urls):
    def process_json_content(json_data):
        entries = []
        skip_categories = {"Malayalam", "Telugu", "Kannada"}
        skip_urls = {"https://live-iptv.github.io/youtube_live/assets/info.m3u8"}

        for category in json_data:
            group_title = category.get('label', 'Unknown Group')

            for channel in category.get('channels', []):
                cat = channel.get('category', '').strip()

                # Skip unwanted categories
                if cat in skip_categories:
                    continue

                url = channel.get('url', '')
                if url in skip_urls:
                    continue

                entry = {
                    'group_title': group_title,
                    'tvg_logo': channel.get('logo', ''),
                    'name': channel.get('name', channel.get('title', 'Unknown')),
                    'url': url
                }
                entries.append(entry)

        entries = PlaylistUtils.deduplicate_by_url(entries)
        entries = PlaylistUtils.filter_reachable(
            entries,
            allow_redirects=True,
        )
        entries = PlaylistUtils.sort_entries(entries)
        return PlaylistUtils.to_m3u(entries)

    # Process each JSON URL
    for url in urls:
        json_data = PlaylistUtils.fetch_json(url)
        if json_data:
            fixed_content = process_json_content(json_data)
            print(fixed_content)


if __name__ == "__main__":
    json_urls = [
        'https://tavapi.inditechman.com/api/tamiltvapp.json'
    ]
    fix_m3u_from_url(json_urls)
