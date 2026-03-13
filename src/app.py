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
    """PaperP应用主类"""
    def __init__(self, interface="0.0.0.0", image_path="image.img", lang=None, debug=False):
        """
        初始化PaperPApp对象
        
        参数:
            interface (str): 网络接口IP地址，默认为"0.0.0.0"
            image_path (str): 固件文件路径，默认为"image.img"
            lang (str): 语言，默认为None
            debug (bool): 是否启用调试模式，默认为False
        """
        self.interface = interface
        self.image_path = image_path
        self.lang = lang
        self.debug = debug
        self.update_data = None
        
    def setup(self):
        """
        初始化应用环境
        - 设置调试模式和日志
        - 检查管理员权限
        - 初始化国际化设置
        - 注册信号处理器以优雅退出
        """
        IO.DEBUG_MODE = self.debug
        
        if self.debug:
            http.client.HTTPConnection.debuglevel = 1
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True

        require_admin()
        
        if self.lang:
            I18N.set_language(I18N.Language.ENGLISH if self.lang == 'en' else I18N.Language.CHINESE)
        else:
            if IO.confirm(t("use_chinese")):
                I18N.set_language(I18N.Language.CHINESE)
        
        IO.info(t("app_starting"))
        
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def cleanup(self, signum, frame):
        """
        退出前清理资源
        - 恢复hosts文件
        - 退出应用
        
        参数:
            signum: 信号编号（如果由信号处理器调用）
            frame: 当前栈帧（如果由信号处理器调用）
        """
        IO.info(t("app_terminating"))
        HostManager.disable_redirect()
        if signum is None:
             pass
        sys.exit(0)

    def run(self):
        """
        应用主执行循环
        1. 抓取OTA请求
        2. 下载更新信息
        3. 下载固件文件
        4. 修改固件哈希
        5. 重新计算段哈希
        6. 修改hosts文件进行重定向
        7. 启动本地HTTP服务器
        """
        has_error = False
        try:
            self.setup()
            
            # 1. 抓取
            capture_result = capture_ota_request(self.interface)
            if not capture_result or not capture_result.product_url:
                IO.error(t("capture_failed"))
                has_error = True
                return

            # 2. 下载信息
            self.update_data = get_update_data(capture_result.product_url, capture_result.request_body)
            if not self.update_data:
                has_error = True
                return
            
            # 提取下载URL
            try:
                delta_url = self.update_data['data']['version']['deltaUrl']
                IO.info(t("firmware_url").format(delta_url))
            except KeyError as e:
                IO.error(t("json_structure_error").format(e))
                has_error = True
                return

            # 3. 下载文件
            if not download_file(delta_url, self.image_path):
                has_error = True
                return

            # 4. 修改文件
            if not Patcher.replace_hash(self.image_path):
                has_error = True
                return

            # 5. 重新计算哈希
            Patcher.update_version_data(self.update_data, self.image_path, self.interface)

            # 6. Host重定向
            if not HostManager.enable_redirect(self.interface):
                has_error = True
                return

            # 7. 启动服务器
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


