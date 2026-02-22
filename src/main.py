import sys
import os

# Fix for relative imports when running as script directly (e.g. after UAC elevation)
if __name__ == "__main__" and __package__ is None:
    # Add the parent directory to sys.path
    file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(file_path))
    sys.path.append(parent_dir)
    __package__ = "src"

import signal
import json
import argparse
from .utils import IO, I18N, t, require_admin
from .capture import capture_ota_request
from .download import get_update_data, download_file
from .patcher import Patcher
from .host import HostManager
from .server import HttpServer, app

def cleanup(signum, frame):
    IO.info(t("app_terminating"))
    HostManager.disable_redirect()
    if signum is None:
        input("Press Enter to exit...")
    sys.exit(0)

def main():
    # Parse args
    parser = argparse.ArgumentParser(description="PaperP - DictPen ADB Password Reset Tool")
    parser.add_argument("--interface", default="0.0.0.0", help="Network interface IP to listen on (Hotspot IP)")
    parser.add_argument("--image", default="image.img", help="Firmware image filename")
    parser.add_argument("--lang", choices=['en', 'cn'], help="Language (en/cn)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose output")
    
    args = parser.parse_args()
    
    # Set debug mode
    IO.DEBUG_MODE = args.debug
    
    if args.debug:
        import logging
        import http.client
        http.client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    # Check Admin first
    require_admin()
    
    # Init I18N
    if args.lang:
        I18N.set_language(I18N.Language.ENGLISH if args.lang == 'en' else I18N.Language.CHINESE)
    else:
        # Ask user
        if IO.confirm(t("use_chinese")):
            I18N.set_language(I18N.Language.CHINESE)
    
    IO.info(t("app_starting"))
    
    # Register signal handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 1. Capture
    capture_result = capture_ota_request(args.interface)
    if not capture_result or not capture_result.product_url:
        IO.error("Capture failed or aborted.")
        return

    # 2. Download Info
    update_data = get_update_data(capture_result.product_url, capture_result.request_body)
    if not update_data:
        return
        
    try:
        # Extract download URL
        # Structure based on C++: data -> version -> deltaUrl
        delta_url = update_data['data']['version']['deltaUrl']
        IO.info(f"Firmware URL: {delta_url}")
        
        # 3. Download File
        if not download_file(delta_url, args.image):
            return
            
        # 4. Patch File
        if not Patcher.replace_hash(args.image):
            return
            
        # 5. Re-calculate Hashes for JSON
        IO.info(t("calculating_hash"))
        
        # Segment MD5s
        segment_md5_str = update_data['data']['version']['segmentMd5']
        # It seems segmentMd5 is a JSON string inside the JSON object?
        # C++: nlohmann::json::parse(std::string(updateData["data"]["version"]["segmentMd5"]))
        if isinstance(segment_md5_str, str):
            segment_md5 = json.loads(segment_md5_str)
        else:
            segment_md5 = segment_md5_str
            
        for item in segment_md5:
            start = item['startpos']
            end = item['endpos']
            item['md5'] = Patcher.calc_segment_md5(args.image, start, end)
            
        # Update JSON
        # Note: If it was a string, we might need to dump it back to string.
        # But requests.json() returns python dicts.
        # If the original API returned a string for this field, we should probably dump it back.
        # Let's assume we keep it as object if possible, or dump if needed.
        # C++ dumps it back: updateData["data"]["version"]["segmentMd5"] = segmentMd5.dump();
        if isinstance(segment_md5_str, str):
            update_data['data']['version']['segmentMd5'] = json.dumps(segment_md5)
        else:
            update_data['data']['version']['segmentMd5'] = segment_md5
            
        # Full MD5 & SHA1
        update_data['data']['version']['md5sum'] = Patcher.calc_md5(args.image)
        update_data['data']['version']['sha'] = Patcher.calc_sha1(args.image)
        
        # Modify URLs to point to us
        # C++: "http://192.168.137.1/image.img"
        local_url = f"http://{args.interface}/image.img"
        update_data['data']['version']['deltaUrl'] = local_url
        update_data['data']['version']['bakUrl'] = local_url
        
        IO.debug(json.dumps(update_data, indent=2))
        
        # 6. Host Redirect
        if not HostManager.enable_redirect(args.interface):
            return
            
        # 7. Start Server
        # We need to configure the app with the data
        app.config['UPDATE_DATA'] = update_data
        app.config['IMAGE_PATH'] = os.path.abspath(args.image)
        
        IO.info(t("server_start"))
        IO.info(t("server_stop_hint"))
        
        # Blocking run
        app.run(host='0.0.0.0', port=80, threaded=True)
        
    except KeyError as e:
        IO.error(f"JSON structure mismatch: {e}")
    except Exception as e:
        IO.error(f"An error occurred: {e}")
    finally:
        cleanup(None, None)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
