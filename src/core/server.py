import threading
from werkzeug.serving import make_server
from flask import Flask, jsonify, send_file, request
import logging
import os
import subprocess
from ..utils import IO, t

app = Flask(__name__)

class ProgressFileWrapper:
    def __init__(self, path, callback):
        self.f = open(path, 'rb')
        self.file_size = os.path.getsize(path)
        self.callback = callback

    def read(self, size=-1):
        data = self.f.read(size)
        if self.callback:
            try:
                self.callback(self.f.tell(), self.file_size)
            except:
                pass
        return data

    def seek(self, offset, whence=0):
        return self.f.seek(offset, whence)

    def tell(self):
        return self.f.tell()

    def close(self):
        self.f.close()

# Suppress Flask default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class HttpServer:
    def __init__(self, port=80, image_path="image.img", update_data=None, progress_callback=None):
        self.port = port
        self.image_path = image_path
        self.update_data = update_data
        self.progress_callback = progress_callback
        self.server = None
        self.thread = None

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
        app.config['PROGRESS_CALLBACK'] = self.progress_callback

        IO.info(t("server_start").format(self.port))
        
        try:
            self.server = make_server('0.0.0.0', self.port, app, threaded=True)
            self.server.serve_forever()
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
            raise e

    def start_threaded(self, error_callback=None):
        """Start server in a separate thread."""
        def run_wrapper():
            try:
                self.run()
            except Exception as e:
                if error_callback:
                    error_callback(e)
                    
        self.thread = threading.Thread(target=run_wrapper)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the server."""
        if self.server:
            try:
                self.server.shutdown()
                # Also close the socket explicitly if possible, though shutdown should do it.
                if hasattr(self.server, 'server_close'):
                    self.server.server_close()
            except Exception as e:
                IO.warn(f"Error during server shutdown: {e}")
            finally:
                self.server = None
                IO.info("Server stopped.")

    @staticmethod
    def force_stop_port_80():
        try:
            # Find PID using port 80
            cmd = "netstat -ano"
            output_bytes = subprocess.check_output(cmd, shell=True)
            try:
                output = output_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    output = output_bytes.decode('gbk')
                except UnicodeDecodeError:
                    output = output_bytes.decode(errors='ignore')

            pids = set()
            for line in output.splitlines():
                if ":80 " in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    # 0 is System Idle Process, 4 is System, usually we can't kill them but sometimes IIS uses System (http.sys)
                    # We should be careful. But user asked for "Force stop".
                    if pid != "0": 
                        pids.add(pid)
            
            if not pids:
                IO.info(t("no_process_on_port_80"))
                return

            for pid in pids:
                IO.warn(t("killing_process").format(pid))
                subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                
            IO.info(t("port_80_cleared"))
        except Exception as e:
            IO.error(t("force_stop_fail").format(e))


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
    progress_callback = app.config.get('PROGRESS_CALLBACK')
    
    # Debug info
    IO.info(f"Request for image.img received from {request.remote_addr}")
    
    if os.path.exists(image_path):
        IO.info(t("serving_firmware").format(image_path))
        
        # If callback exists, wrap the file
        if progress_callback:
            try:
                # Werkzeug send_file supports file-like objects
                # We need to provide mimetype and last_modified to support range requests properly if possible
                # But simple file wrapper might break range support if not fully compliant.
                # However, for simple progress, we can try.
                # Note: Flask's send_file with a file object might read it all in memory or stream it.
                # We want streaming.
                
                # Using ProgressFileWrapper
                wrapper = ProgressFileWrapper(image_path, progress_callback)
                
                # To support Range requests with file-like object, Werkzeug needs 'seek' and 'tell' (which we added)
                # and we should provide file size implicitly or explicitly?
                # send_file uses os.fstat if it's a real file.
                # For file-like object, we might need to be careful.
                
                # Actually, simplest way to keep Range support working perfectly with Flask 
                # while having progress is tricky because send_file handles the open() internally if path is passed.
                # If we pass a file object, we take responsibility.
                
                return send_file(
                    wrapper, 
                    mimetype='application/octet-stream', 
                    as_attachment=True, 
                    download_name='image.img',
                    conditional=True
                )
            except Exception as e:
                IO.error(f"Error serving with progress: {e}")
                # Fallback to standard send_file
                return send_file(image_path, conditional=True)
        else:
            # Send file with range support (standard)
            return send_file(image_path, conditional=True)
    else:
        IO.error(t("firmware_not_found"))
        return "File not found", 404

# Add explicit route for handling checkVersion with trailing slash or without
@app.route('/<path:subpath>/ota/checkVersion', methods=['POST'])
def handle_check_version_explicit(subpath):
    return handle_check_version(f"{subpath}/ota/checkVersion")
    
@app.route('/ota/checkVersion', methods=['POST'])
def handle_check_version_root():
    return handle_check_version("ota/checkVersion")
