import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def fix_m3u_from_url(urls):
    def fetch_m3u_content(url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
        except requests.RequestException:
            pass
        return None

    def is_url_reachable(entry):
        try:
            url_response = requests.head(entry['url'], timeout=10)
            if url_response.status_code == 200:
                return entry
        except requests.RequestException:
            pass
        return None

    def process_m3u_content(content):
        lines = content.split('\n')

        # Extract URLs with associated information
        entries = []
        current_entry = None
        seen_urls = set()  # To track unique URLs
        seen_urls.add("https://live-iptv.github.io/youtube_live/assets/info.m3u8")

        for line in lines:
            if line.startswith('#EXTINF:-1'):
                match = re.search(r'#EXTINF:-1(.*?),(.+)', line)
                if match:
                    attributes = match.group(1)
                    # Extract the first group-title
                    group_title_match = re.search(r'group-title="([^"]*)"', attributes)
                    group_title = group_title_match.group(1) if group_title_match else 'Others'

                    tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', attributes)
                    tvg_logo = tvg_logo_match.group(1) if tvg_logo_match else ''

                    name = match.group(2).strip().split(',')[-1]
                    current_entry = {
                        'group_title': group_title,
                        'tvg_logo': tvg_logo,
                        'name': name,
                    }
            elif current_entry is not None and line.strip():
                current_entry['url'] = line.strip()
                if current_entry['url'] not in seen_urls:
                    entries.append(current_entry)
                    seen_urls.add(current_entry['url'])
                current_entry = None

        # Remove duplicates by converting the list to a set of tuples and back to a list of dicts
        unique_entries = {tuple(entry.items()) for entry in entries}
        unique_entries = [dict(entry) for entry in unique_entries]

        # Verify if URLs are reachable concurrently
        reachable_entries = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_entry = {executor.submit(is_url_reachable, entry): entry for entry in unique_entries}
            for future in as_completed(future_to_entry):
                result = future.result()
                if result is not None:
                    reachable_entries.append(result)

        # Sort entries based on group title
        sorted_entries = sorted(reachable_entries, key=lambda x: x['name'])
        sorted_entries = sorted(sorted_entries, key=lambda x: x['group_title'])

        # Write the sorted M3U content
        sorted_m3u_content = ['#EXTM3U']
        for entry in sorted_entries:
            sorted_m3u_content.append(f'#EXTINF:-1 group-title="{entry["group_title"]}" tvg-logo="{entry["tvg_logo"]}",{entry["name"]}\n{entry["url"]}')

        return '\n'.join(sorted_m3u_content)

    for url in urls:
        m3u_content = fetch_m3u_content(url)
        if m3u_content:
            fixed_content = process_m3u_content(m3u_content)
            print(fixed_content)

if __name__ == "__main__":
    m3u_urls = [
        'https://raw.githubusercontent.com/manisat30/Sat/main/DSC.m3u',
        'https://raw.githubusercontent.com/suvisnimpraven/suvisnimpraven.github.io/main/suresh.m3u8',
        'https://iptv-org.github.io/iptv/languages/tam.m3u',
        'https://live-iptv.github.io/iptv/tamil/tamil_local_copy.m3u'
    ]
    fix_m3u_from_url(m3u_urls)
