import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# URLs to skip (like redirect pages or dummy streams)
SKIP_URLS = {
    "https://live-iptv.github.io/youtube_live/assets/info.m3u8"
}

def fix_m3u_from_url(urls):
    def fetch_json_content(url):
        headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36'
    }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERROR] Failed to fetch JSON from {url}: {e}")
            return None

    def is_url_reachable(entry):
        url = entry['url']
        try:
            if url.startswith("rtmp://"):
                return entry  # Assume RTMP is valid
            head = requests.head(url, timeout=10, allow_redirects=True)
            if head.status_code == 200:
                return entry
        except Exception as e:
            print(f"[WARNING] URL unreachable: {url} ({e})")
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
                    'tvg_logo': channel.get('logo', '').strip(),
                    'name': channel.get('name') or channel.get('title', 'No Name'),
                    'url': url
                }

                seen_urls.add(url)
                entries.append(entry)

        return entries

    all_entries = []
    for url in urls:
        json_content = fetch_json_content(url)
        if not json_content:
            continue
        all_entries.extend(process_json(json_content))

    # Check reachability
    reachable_entries = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(is_url_reachable, entry): entry for entry in all_entries}
        for future in as_completed(futures):
            result = future.result()
            if result:
                reachable_entries.append(result)

    # Sort and generate .m3u output
    sorted_entries = sorted(
        reachable_entries,
        key=lambda x: (x['group_title'].lower(), x['name'].lower())
    )

    m3u_lines = ['#EXTM3U']
    for entry in sorted_entries:
        m3u_lines.append(
            f'#EXTINF:-1 group-title="{entry["group_title"]}" tvg-logo="{entry["tvg_logo"]}",{entry["name"]}'
        )
        m3u_lines.append(entry['url'])

    m3u_output = '\n'.join(m3u_lines)
    print(m3u_output)

    return m3u_output


if __name__ == "__main__":
    json_urls = [
        'https://tavapi.inditechman.com/api/tamiltvapp.json'
    ]
    fix_m3u_from_url(json_urls)
