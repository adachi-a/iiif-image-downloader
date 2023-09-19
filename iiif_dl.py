import json
import os
import sys
import time
import random
from urllib import request, error

MAX_RETRIES = 3  # Maximum number of retries for failed downloads
RETRY_DELAY = 5  # Delay in seconds before retrying a failed download
DOWNLOAD_DELAY = (1, 3)  # Delay between 1 to 3 seconds between successful downloads

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def download_image_from_url(url, filename):
    req = request.Request(url, headers=HEADERS)
    with request.urlopen(req) as response:
        content_length = int(response.getheader('Content-Length', '0'))
        received_data = response.read()

        if content_length != 0 and content_length != len(received_data):
            raise ValueError(f"Expected to download {content_length} bytes but received {len(received_data)} bytes.")

        with open(filename, 'wb') as file:
            file.write(received_data)

def download_with_retries(url, filename):
    for attempt in range(MAX_RETRIES):
        try:
            download_image_from_url(url, filename)
            return True
        except (error.URLError, ValueError):
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    return False

def fetch_manifest_data(manifest_url):
    req = request.Request(manifest_url, headers=HEADERS)
    with request.urlopen(req) as response:
        return json.loads(response.read())

def extract_image_urls(data):
    return [
        image['resource']['service']['@id']
        for seq in data['sequences']
        for canvas in seq['canvases']
        for image in canvas['images']
    ]

def main(manifest_url):
    try:
        data = fetch_manifest_data(manifest_url)
        image_urls = extract_image_urls(data)
    except (error.URLError, json.JSONDecodeError):
        raise ValueError("Invalid Manifest URL or other errors.")

    total_images = len(image_urls)
    print(f'Downloading {total_images} images from {manifest_url}')

    for idx, image_url in enumerate(image_urls, start=1):
        local_filename = f"{idx:0>{len(str(total_images)) + 1}}.jpg"
        if os.path.exists(local_filename):
            continue
        complete_image_url = f"{image_url}/full/full/0/default.jpg"
        if download_with_retries(complete_image_url, local_filename):
            print(f"Downloaded {local_filename} ({idx}/{total_images})")
            time.sleep(random.uniform(*DOWNLOAD_DELAY))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the manifest URL as an argument.")
        sys.exit(1)
    manifest_url = sys.argv[1]
    main(manifest_url)
