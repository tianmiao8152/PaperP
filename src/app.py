import sys
import os
import signal
import logging
import http.client
from .utils.io import IO, require_admin
from .utils.i18n import I18N, t
from .core.capture import capture_ota_request
from .core.downloader import get_update_data, download_file
from .core.patcher import Patcher
from .core.host import HostManager
from .core.server import HttpServer

class PaperPApp:
    def __init__(self, interface="0.0.0.0", image_path="image.img", lang=None, debug=False):
        self.interface = interface
        self.image_path = image_path
        self.lang = lang
        self.debug = debug
        self.update_data = None
        
    def setup(self):
        """
        Initialize the application environment.
        - Set debug mode and logging.
        - Check for administrative privileges.
        - Initialize I18N settings.
        - Register signal handlers for graceful shutdown.
        """
        # Set debug mode
        IO.DEBUG_MODE = self.debug
        
        if self.debug:
            http.client.HTTPConnection.debuglevel = 1
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

        # Check Admin
        require_admin()
        
        # Init I18N
        if self.lang:
            I18N.set_language(I18N.Language.ENGLISH if self.lang == 'en' else I18N.Language.CHINESE)
        else:
            if IO.confirm(t("use_chinese")):
                I18N.set_language(I18N.Language.CHINESE)
        
        IO.info(t("app_starting"))
        
        # Register signal handler
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def cleanup(self, signum, frame):
        """
        Clean up resources before exiting.
        - Restore hosts file.
        - Exit the application.
        
        Args:
            signum: The signal number (if called by signal handler).
            frame: The current stack frame (if called by signal handler).
        """
        IO.info(t("app_terminating"))
        HostManager.disable_redirect()
        if signum is None:
             # Exit normally
             pass
        sys.exit(0)

    def run(self):
        """
        Main execution loop of the application.
        1. Capture OTA request.
        2. Download update information.
        3. Download firmware file.
        4. Patch firmware hash.
        5. Recalculate segment hashes.
        6. Modify hosts file for redirection.
        7. Start local HTTP server.
        """
        has_error = False
        try:
            self.setup()
            
            # 1. Capture
            capture_result = capture_ota_request(self.interface)
            if not capture_result or not capture_result.product_url:
                IO.error(t("capture_failed"))
                has_error = True
                return

            # 2. Download Info
            self.update_data = get_update_data(capture_result.product_url, capture_result.request_body)
            if not self.update_data:
                has_error = True
                return
            
            # Extract download URL
            try:
                delta_url = self.update_data['data']['version']['deltaUrl']
                IO.info(t("firmware_url").format(delta_url))
            except KeyError as e:
                IO.error(t("json_structure_error").format(e))
                has_error = True
                return

            # 3. Download File
            if not download_file(delta_url, self.image_path):
                has_error = True
                return

            # 4. Patch File
            if not Patcher.replace_hash(self.image_path):
                has_error = True
                return

            # 5. Re-calculate Hashes
            Patcher.update_version_data(self.update_data, self.image_path, self.interface)

            # 6. Host Redirect
            if not HostManager.enable_redirect(self.interface):
                has_error = True
                return

            # 7. Start Server
            server = HttpServer(port=80, image_path=os.path.abspath(self.image_path), update_data=self.update_data)
            
            retry_count = 0
            while retry_count < 2:
                try:
                    server.run()
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count < 2:
                        IO.input(t("retry_port"))
                        continue
                    else:
                        has_error = True
                        raise e
            
        except Exception as e:
             IO.error(t("unknown_error").format(e))
             import traceback
             traceback.print_exc()
             has_error = True
        finally:
             if has_error:
                 print(t("press_enter_exit"))
                 input()
             self.cleanup(None, None)


