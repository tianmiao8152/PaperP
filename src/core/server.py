import threading
from werkzeug.serving import make_server
from flask import Flask, jsonify, send_file, request
import logging
import os
import subprocess
from ..utils import IO, t

app = Flask(__name__)

class ProgressFileWrapper:
    """文件进度包装类，用于在文件下载时提供进度回调"""
    def __init__(self, path, callback):
        """
        初始化ProgressFileWrapper对象
        
        参数:
            path (str): 文件路径
            callback (function): 进度回调函数
        """
        self.f = open(path, 'rb')
        self.file_size = os.path.getsize(path)
        self.callback = callback

    def read(self, size=-1):
        """
        读取文件内容并触发进度回调
        
        参数:
            size (int): 读取大小
        
        返回:
            bytes: 读取的文件内容
        """
        data = self.f.read(size)
        if self.callback:
            try:
                self.callback(self.f.tell(), self.file_size)
            except:
                pass
        return data

    def seek(self, offset, whence=0):
        """
        移动文件指针
        
        参数:
            offset (int): 偏移量
            whence (int): 参考位置
        
        返回:
            int: 新的文件指针位置
        """
        return self.f.seek(offset, whence)

    def tell(self):
        """
        获取当前文件指针位置
        
        返回:
            int: 文件指针位置
        """
        return self.f.tell()

    def close(self):
        """
        关闭文件
        """
        self.f.close()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class HttpServer:
    """HTTP服务器类，用于提供OTA更新服务"""
    def __init__(self, port=80, image_path="image.img", update_data=None, progress_callback=None):
        """
        初始化HttpServer对象
        
        参数:
            port (int): 服务器端口，默认为80
            image_path (str): 固件文件路径，默认为"image.img"
            update_data (dict): 更新数据，默认为None
            progress_callback (function): 进度回调函数，默认为None
        """
        self.port = port
        self.image_path = image_path
        self.update_data = update_data
        self.progress_callback = progress_callback
        self.server = None
        self.thread = None

    def run(self):
        """
        运行HTTP服务器
        """
        if IO.DEBUG_MODE:
            logging.getLogger('werkzeug').setLevel(logging.INFO)
            IO.debug(t("flask_debug_enabled"))
        else:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

        app.config['UPDATE_DATA'] = self.update_data
        app.config['IMAGE_PATH'] = self.image_path
        app.config['PROGRESS_CALLBACK'] = self.progress_callback

        IO.info(t("server_start").format(self.port))
        
        try:
            self.server = make_server('0.0.0.0', self.port, app, threaded=True)
            self.server.serve_forever()
        except Exception as e:
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
        """
        在单独的线程中启动服务器
        
        参数:
            error_callback (function): 错误回调函数，默认为None
        """
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
        """
        停止服务器
        """
        if self.server:
            try:
                self.server.shutdown()
                if hasattr(self.server, 'server_close'):
                    self.server.server_close()
            except Exception as e:
                IO.warn(t("server_shutdown_error").format(e))
            finally:
                self.server = None
                IO.info(t("server_stopped"))

    @staticmethod
    def force_stop_port_80():
        """
        强制停止占用80端口的进程
        """
        try:
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
    """
    处理OTA检查请求
    
    参数:
        subpath (str): URL子路径
    
    返回:
        Response: 更新数据或错误信息
    """
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
    """
    提供固件文件下载
    
    返回:
        Response: 固件文件或错误信息
    """
    image_path = app.config.get('IMAGE_PATH')
    progress_callback = app.config.get('PROGRESS_CALLBACK')
    
    IO.info(t("image_request_received").format(request.remote_addr))
    
    if os.path.exists(image_path):
        IO.info(t("serving_firmware").format(image_path))
        
        if progress_callback:
            try:
                wrapper = ProgressFileWrapper(image_path, progress_callback)
                
                return send_file(
                    wrapper, 
                    mimetype='application/octet-stream', 
                    as_attachment=True, 
                    download_name='image.img',
                    conditional=True
                )
            except Exception as e:
                IO.error(t("serve_progress_error").format(e))
                return send_file(image_path, conditional=True)
        else:
            return send_file(image_path, conditional=True)
    else:
        IO.error(t("firmware_not_found"))
        return "File not found", 404

@app.route('/<path:subpath>/ota/checkVersion', methods=['POST'])
def handle_check_version_explicit(subpath):
    """
    处理显式的OTA检查请求路径
    
    参数:
        subpath (str): URL子路径
    
    返回:
        Response: 更新数据或错误信息
    """
    return handle_check_version(f"{subpath}/ota/checkVersion")
    
@app.route('/ota/checkVersion', methods=['POST'])
def handle_check_version_root():
    """
    处理根路径的OTA检查请求
    
    返回:
        Response: 更新数据或错误信息
    """
    return handle_check_version("ota/checkVersion")
