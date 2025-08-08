import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

SKIP_URLS = {
    "https://live-iptv.github.io/youtube_live/assets/info.m3u8"
}

def fix_m3u_from_url(urls):
    def fetch_json_content(url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch JSON from {url}, status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching JSON from {url}: {str(e)}")
        return None

    def is_url_reachable(entry):
        url = entry['url']
        if url in SKIP_URLS:
            return None
            
        try:
            if url.startswith("rtmp://"):
                return entry  # Skip checking RTMP; assume reachable
            
            # Try HEAD first, fall back to GET if not allowed
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return entry
                
            # If HEAD not allowed, try GET
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                return entry
                
        except requests.RequestException as e:
            print(f"URL check failed for {entry['name']} ({url}): {str(e)}")
        return None

    def process_json(json_data):
        entries = []
        seen_urls = set()

        for group in json_data:
            group_title = group.get('label', 'Others')
            for channel in group.get('channels', []):
                url = channel.get('url', '').strip()
                if not url or url in seen_urls:
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

    all_reachable_entries = []
    
    for url in urls:
        print(f"\nProcessing URL: {url}")
        start_time = time.time()
        
        json_content = fetch_json_content(url)
        if not json_content:
            continue

        entries = process_json(json_content)
        print(f"Found {len(entries)} channels in JSON")

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
                    print(f"✓ {result['name']}")
                else:
                    entry = future_to_entry[future]
                    print(f"✗ {entry['name']} (unreachable)")

        all_reachable_entries.extend(reachable_entries)
        print(f"Found {len(reachable_entries)} reachable channels (took {time.time()-start_time:.2f}s)")

    # Sort all entries
    sorted_entries = sorted(
        all_reachable_entries,
        key=lambda x: (x['group_title'].lower(), x['name'].lower())
    )

    # Build M3U content
    m3u_lines = ['#EXTM3U']
    for entry in sorted_entries:
        m3u_lines.append(
            f'#EXTINF:-1 group-title="{entry["group_title"]}" tvg-logo="{entry["tvg_logo"]}",{entry["name"]}'
        )
        m3u_lines.append(entry['url'])

    return '\n'.join(m3u_lines)

if __name__ == "__main__":
    json_urls = [
        'https://tavapi.inditechman.com/api/tamiltvapp.json'
    ]
    
    try:
        m3u_output = fix_m3u_from_url(json_urls)
        print("\nFinal M3U Playlist:")
        print(m3u_output)
        
        # Optionally save to file
        with open('output.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_output)
        print("\nPlaylist saved to output.m3u")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")