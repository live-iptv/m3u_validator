import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def fix_m3u_from_url(urls):
    def fetch_json_content(url):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible; Python script)'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except (requests.RequestException, ValueError):
            pass
        return None

    def is_url_reachable(entry):
        try:
            url_response = requests.head(entry['url'], timeout=10, allow_redirects=True)
            if url_response.status_code in (200, 301, 302):
                return entry
        except requests.RequestException:
            pass
        return None

    def process_json_content(json_data):
        entries = []

        for category in json_data:
            group_title = category.get('label', 'Unknown Group')
            
            # ✅ Only process if the group title is "Malayalam"
            if group_title != "Malayalam":
                continue

            for channel in category.get('channels', []):
                url = channel.get('url', '')
                # Skip this specific URL
                if url == "https://live-iptv.github.io/youtube_live/assets/info.m3u8":
                    continue
                entry = {
                    'group_title': group_title,
                    'tvg_logo': channel.get('logo', ''),
                    'name': channel.get('name', channel.get('title', 'Unknown')),
                    'url': url
                }
                entries.append(entry)

            # ✅ Break after processing Malayalam group only (assuming only one exists)
            break

        # Remove duplicates by URL
        unique_entries = []
        seen_urls = set()
        for entry in entries:
            if entry['url'] not in seen_urls and entry['url']:
                unique_entries.append(entry)
                seen_urls.add(entry['url'])

        # Verify if URLs are reachable concurrently
        reachable_entries = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_entry = {executor.submit(is_url_reachable, entry): entry for entry in unique_entries}
            for future in as_completed(future_to_entry):
                result = future.result()
                if result is not None:
                    reachable_entries.append(result)

        # Sort entries by name (since group_title is the same)
        sorted_entries = sorted(reachable_entries, key=lambda x: x['name'])

        # Generate M3U content
        m3u_content = ['#EXTM3U']
        for entry in sorted_entries:
            m3u_content.append(
                f'#EXTINF:-1 group-title="{entry["group_title"]}" tvg-logo="{entry["tvg_logo"]}",{entry["name"]}\n'
                f'{entry["url"]}'
            )

        return '\n'.join(m3u_content)

    for url in urls:
        json_data = fetch_json_content(url)
        if json_data:
            fixed_content = process_json_content(json_data)
            print(fixed_content)

if __name__ == "__main__":
    json_urls = [
        'https://tavapi.inditechman.com/api/tamiltvapp.json'
    ]
    fix_m3u_from_url(json_urls)
