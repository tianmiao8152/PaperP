import requests
import json
import os
import hashlib
from .utils import IO, t

def get_update_data(product_url, request_body):
    """
    Replay the OTA check request to get update information.
    """
    # Construct full URL
    # Assuming the domain is iotapi.abupdate.com based on C++ source
    # In C++ it was hardcoded or extracted? Let's check capture result.
    # The capture result only has path like /product/...
    
    url = f"http://iotapi.abupdate.com{product_url}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 8.1.0; P780 Build/O11019)", # Mimic Android device
        "Host": "iotapi.abupdate.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    IO.info(f"Requesting update info from: {url}")
    
    # Force version to 99.99.90 to get full update package
    if 'version' in request_body:
        IO.info(f"Modifying version from {request_body['version']} to 99.99.90 to force full update")
        request_body['version'] = "99.99.90"
        
    try:
        IO.debug(f"Request body: {json.dumps(request_body)}")
        response = requests.post(url, json=request_body, headers=headers)
        
        if response.status_code != 200:
             IO.error(f"Server returned status {response.status_code}: {response.text}")
             response.raise_for_status()
        
        data = response.json()
        IO.debug(f"Update info received: {json.dumps(data)[:200]}...") # Print first 200 chars
        return data
    except Exception as e:
        IO.error(f"Failed to get update data: {e}")
        return None

def download_file(url, filename):
    """
    Download file with progress bar.
    """
    if os.path.exists(filename):
        IO.warn(f"File {filename} already exists.")
        if not IO.confirm("Overwrite? (y: download again, N: use existing file)"):
            IO.info("Using existing file.")
            return True

    IO.info(t("downloading") + f": {url}")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_length > 0:
                        percentage = (downloaded / total_length) * 100
                        print(f"\rDownloading: {percentage:.1f}% ({downloaded}/{total_length})", end="")
        
        print() # Newline
        IO.info(t("download_complete"))
        return True
    except Exception as e:
        IO.error(f"Download failed: {e}")
        return False
