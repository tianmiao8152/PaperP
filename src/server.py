from flask import Flask, request, jsonify, send_file
import threading
import logging
import os
from .utils import IO, t

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
            IO.debug("Flask debug logging enabled")
        else:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

        # Configure app
        app.config['UPDATE_DATA'] = self.update_data
        app.config['IMAGE_PATH'] = self.image_path

        IO.info(t("server_start") + f" (Port {self.port})")
        IO.info(t("server_stop_hint"))
        
        try:
            # Run in main thread, blocking
            app.run(host='0.0.0.0', port=self.port, threaded=True)
        except OSError as e:
            if e.errno == 10013 or e.winerror == 10013: # Access denied (usually port in use)
                IO.error(f"Port {self.port} is already in use or permission denied.")
                IO.error("Please stop any other web servers (IIS, Apache, Skype, etc.) running on port 80.")
                IO.error("You can try running 'netstat -ano | findstr :80' to find the process ID.")
            else:
                IO.error(f"Failed to start server: {e}")
        except Exception as e:
            IO.error(f"Unexpected error starting server: {e}")

@app.route('/<path:subpath>', methods=['POST'])
def handle_check_version(subpath):
    # Match any path ending in /ota/checkVersion
    if "ota/checkVersion" in subpath:
        IO.info(f"Received OTA check request: {subpath}")
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
        IO.info(f"Serving firmware: {image_path}")
        # Send file with range support
        return send_file(image_path, conditional=True)
    else:
        IO.error("Firmware file not found")
        return "File not found", 404
