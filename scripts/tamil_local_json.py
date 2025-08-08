import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

SKIP_URLS = {
    "https://live-iptv.github.io/youtube_live/assets/info.m3u8"
}

def fix_m3u_from_url(urls):
    def fetch_json_content(url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return None

    def is_url_reachable(entry):
        try:
            if entry['url'].startswith("rtmp://"):
                return entry  # Skip checking RTMP; assume reachable
            head = requests.head(entry['url'], timeout=10, allow_redirects=True)
            if head.status_code == 200:
                return entry
        except requests.RequestException:
            pass
        return None

    def process_json(json_data):
        entries = []
        seen_urls = set()

        for group in json_data:
            group_title = group.get('label', 'Others')
            for channel in group.get('channels', []):
                url = channel.get('url', '').strip()
                if not url or url in seen_urls or url in SKIP_URLS:
                    continue

                entry = {
                    'group_title': channel.get('category', group_title),
                    'tvg_logo': channel.get('logo', ''),
                    'name': channel.get('name') or channel.get('title', 'No Name'),
                    'url': url
                }

                seen_urls.add(url)
                entries.append(entry)

        return entries

    for url in urls:
        json_content = fetch_json_content(url)
        if not json_content:
            continue

        entries = process_json(json_content)

        # Check reachability
        reachable_entries = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_entry = {
                executor.submit(is_url_reachable, entry): entry for entry in entries
            }
            for future in as_completed(future_to_entry):
                result = future.result()
                if result:
                    reachable_entries.append(result)

        # Sort entries
        sorted_entries = sorted(
            reachable_entries,
            key=lambda x: (x['group_title'].lower(), x['name'].lower())
        )

        # Build M3U content
        m3u_lines = ['#EXTM3U']
        for entry in sorted_entries:
            m3u_lines.append(
                f'#EXTINF:-1 group-title="{entry["group_title"]}" tvg-logo="{entry["tvg_logo"]}",{entry["name"]}'
            )
            m3u_lines.append(entry['url'])

        m3u_output = '\n'.join(m3u_lines)
        print(m3u_output)

if __name__ == "__main__":
    m3u_urls = [
        'https://tavapi.inditechman.com/api/tamiltvapp.json'
    ]
    fix_m3u_from_url(m3u_urls)
