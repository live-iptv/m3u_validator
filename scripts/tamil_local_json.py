import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_m3u_from_json(json_url, output_file='output.m3u'):
    try:
        # Fetch the JSON data with error handling
        response = requests.get(json_url, timeout=10)
        response.raise_for_status()
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON response")
            return False

        # URLs to skip
        skip_urls = {
            "https://live-iptv.github.io/youtube_live/assets/info.m3u8",
            # Add more URLs to skip here if needed
        }

        def is_url_valid(url):
            """Check if URL is valid and reachable"""
            if url in skip_urls:
                return False
            try:
                # Use HEAD request for faster validation
                resp = requests.head(url, timeout=5, allow_redirects=True)
                return resp.status_code == 200
            except requests.RequestException:
                return False

        # Process channels concurrently for better performance
        def process_channel(channel):
            name = channel.get('name', 'Unknown')
            logo = channel.get('logo', '')
            url = channel.get('url', '')
            
            if not url or url in skip_urls:
                return None
            
            return {
                'name': name,
                'logo': logo,
                'url': url,
                'group': channel.get('category', 'Unknown')
            }

        valid_channels = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            # First process all channels to extract data
            futures = []
            for category in data:
                for channel in category.get('channels', []):
                    futures.append(executor.submit(process_channel, channel))
            
            # Then validate URLs in parallel
            url_validation_futures = []
            for future in as_completed(futures):
                channel = future.result()
                if channel:
                    url_validation_futures.append(
                        executor.submit(is_url_valid, channel['url'])
                    )
                    valid_channels.append(channel)
            
            # Filter out invalid URLs
            for i, future in enumerate(as_completed(url_validation_futures)):
                if not future.result():
                    valid_channels[i]['url'] = None

        # Filter out channels with invalid URLs
        valid_channels = [c for c in valid_channels if c['url']]

        # Group channels by category
        grouped_channels = {}
        for channel in valid_channels:
            grouped_channels.setdefault(channel['group'], []).append(channel)

        # Create the M3U file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            
            for group, channels in grouped_channels.items():
                for channel in sorted(channels, key=lambda x: x['name']):
                    f.write(f'#EXTINF:-1 group-title="{group}" tvg-logo="{channel["logo"]}",{channel["name"]}\n')
                    f.write(f'{channel["url"]}\n')

        print(f"Successfully created M3U with {len(valid_channels)} valid channels")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch data from API - {str(e)}")
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred - {str(e)}")
        return False

# URL of the JSON data
json_url = 'https://tavapi.inditechman.com/api/tamiltvapp.json'

# Create the M3U file (only if API request succeeds)
if not create_m3u_from_json(json_url):
    print("Skipping M3U file creation due to errors")