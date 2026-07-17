from common_utils import PlaylistUtils

def fix_m3u_from_url(urls):
    def process_json_content(json_data):
        entries = []
        skip_urls = {"https://live-iptv.github.io/youtube_live/assets/info.m3u8"}

        for category in json_data:
            group_title = category.get('label', 'Unknown Group')
            
            # ✅ Only process if the group title is "Malayalam"
            if group_title != "Malayalam":
                continue

            for channel in category.get('channels', []):
                url = channel.get('url', '')
                if url in skip_urls:
                    continue
                entry = {
                    'group_title': 'Entertainment',
                    'tvg_logo': channel.get('logo', ''),
                    'name': channel.get('name', channel.get('title', 'Unknown')),
                    'url': url
                }
                entries.append(entry)

            # ✅ Break after processing Malayalam group only (assuming only one exists)
            break

        entries = PlaylistUtils.deduplicate_by_url(entries)
        entries = PlaylistUtils.filter_reachable(
            entries,
            allow_redirects=True,
        )
        entries = sorted(entries, key=lambda x: x['name'])
        return PlaylistUtils.to_m3u(entries)

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
