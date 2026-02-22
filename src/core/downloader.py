import requests
import json
import os
from ..utils import IO, t

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

    IO.info(t("requesting_update").format(url))
    
    # Force version to 99.99.90 to get full update package
    if 'version' in request_body:
        IO.info(t("force_version").format(request_body['version']))
        request_body['version'] = "99.99.90"
        
    try:
        IO.debug(t("request_body_log").format(json.dumps(request_body)))
        response = requests.post(url, json=request_body, headers=headers)
        
        if response.status_code != 200:
             IO.error(t("server_status_error").format(response.status_code, response.text))
             response.raise_for_status()
        
        data = response.json()
        IO.debug(t("update_info_received").format(json.dumps(data)[:200])) # Print first 200 chars
        return data
    except Exception as e:
        IO.error(t("get_update_fail").format(e))
        return None

def download_file(url, filename):
    """
    Download file with progress bar.
    """
    if os.path.exists(filename):
        IO.warn(t("file_exists").format(filename))
        if not IO.confirm(t("overwrite_confirm")):
            IO.info(t("using_existing"))
            return True

    IO.info(t("downloading_url").format(url))
    
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
                        print(f"\r{t('download_progress').format(percentage, downloaded, total_length)}", end="")
        
        print() # Newline
        IO.info(t("download_complete"))
        return True
    except Exception as e:
        IO.error(t("download_fail").format(e))
        return False
