from flask import Flask, jsonify, send_file
import logging
import os
from ..utils import IO, t

app = Flask(__name__)

# Suppress Flask default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class HttpServer:
    def __init__(self, port=80, image_path="image.img", update_data=None):
        self.port = port
        self.image_path = image_path
        self.update_data = update_data
        self.server_thread = None

    def run(self):
        # Configure logging based on debug mode
        if IO.DEBUG_MODE:
            logging.getLogger('werkzeug').setLevel(logging.INFO)
            IO.debug(t("flask_debug_enabled"))
        else:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

        # Configure app
        app.config['UPDATE_DATA'] = self.update_data
        app.config['IMAGE_PATH'] = self.image_path

        IO.info(t("server_start").format(self.port))
        IO.info(t("server_stop_hint"))
        
        retry_count = 0
        max_retries = 1
        
        while retry_count <= max_retries:
            try:
                # Run in main thread, blocking
                app.run(host='0.0.0.0', port=self.port, threaded=True)
                break
            except Exception as e:
                # Check for port occupied in generic Exception or OSError
                is_port_error = False
                if isinstance(e, OSError) and (e.errno in (10013, 10048) or getattr(e, 'winerror', 0) in (10013, 10048)):
                    is_port_error = True
                elif "address already in use" in str(e).lower() or "access denied" in str(e).lower():
                    is_port_error = True

                if is_port_error:
                    IO.error(t("port_occupied").format(self.port))
                    IO.error(t("stop_other_servers"))
                    IO.error(t("check_netstat"))
                else:
                    IO.error(t("server_start_fail").format(e))
                
                if retry_count < max_retries:
                    retry_count += 1
                    IO.info(t("server_restart_hint"))
                    continue

                print(t("press_enter_exit"))
                input()
                raise e

@app.route('/<path:subpath>', methods=['POST'])
def handle_check_version(subpath):
    # Match any path ending in /ota/checkVersion
    if "ota/checkVersion" in subpath:
        IO.info(t("ota_check_received").format(subpath))
        update_data = app.config.get('UPDATE_DATA')
        if update_data:
            return jsonify(update_data)
        else:
            return "No update data configured", 500
    return "Not Found", 404

@app.route('/image.img', methods=['GET'])
def serve_image():
    image_path = app.config.get('IMAGE_PATH')
    if os.path.exists(image_path):
        IO.info(t("serving_firmware").format(image_path))
        # Send file with range support
        return send_file(image_path, conditional=True)
    else:
        IO.error(t("firmware_not_found"))
        return "File not found", 404
