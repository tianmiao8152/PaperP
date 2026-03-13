import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import threading
import queue
import time
import sys
import os
import ctypes

if __name__ == "__main__" and __package__ is None:
    file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(file_path))
    sys.path.append(parent_dir)
    __package__ = "src"

from .utils.io import IO, require_admin
from .utils.i18n import I18N, t
from .app import PaperPApp
from .core.capture import capture_ota_request
from .core.downloader import get_update_data, download_file
from .core.patcher import Patcher
from .core.host import HostManager
from .core.server import HttpServer

class GUIInputHandler:
    """GUI输入处理器，将IO输入重定向到GUI对话框"""
    def __init__(self, root):
        """
        初始化GUIInputHandler对象
        
        参数:
            root: Tkinter根窗口
        """
        self.root = root
        self.original_input = IO.input
        self.original_confirm = IO.confirm
        
        IO.input = self.input
        IO.confirm = self.confirm

    def input(self, msg):
        """
        显示输入对话框
        
        参数:
            msg (str): 提示消息
        
        返回:
            str: 用户输入的内容
        """
        return self._run_in_main(lambda: simpledialog.askstring(t("dialog_input_title"), msg, parent=self.root))

    def confirm(self, msg):
        """
        显示确认对话框
        
        参数:
            msg (str): 确认消息
        
        返回:
            bool: 用户是否确认（是返回True，否返回False）
        """
        return self._run_in_main(lambda: messagebox.askyesno(t("dialog_confirm_title"), msg, parent=self.root))

    def _run_in_main(self, func):
        """
        在主线程中运行函数
        
        参数:
            func (function): 要运行的函数
        
        返回:
            any: 函数的返回值
        """
        if threading.current_thread() is threading.main_thread():
            return func()
            
        result_queue = queue.Queue()
        def wrapper():
            try:
                res = func()
                result_queue.put((True, res))
            except Exception as e:
                result_queue.put((False, e))
        
        self.root.after(0, wrapper)
        
        success, res = result_queue.get()
        if not success:
            raise res
        return res

class LogQueueHandler:
    """日志队列处理器，将IO输出重定向到队列供UI使用"""
    def __init__(self, log_queue):
        """
        初始化LogQueueHandler对象
        
        参数:
            log_queue: 日志队列
        """
        self.log_queue = log_queue
        self.original_info = IO.info
        self.original_warn = IO.warn
        self.original_error = IO.error
        self.original_debug = IO.debug
        
        IO.info = self.info
        IO.warn = self.warn
        IO.error = self.error
        IO.debug = self.debug

    def info(self, msg):
        """
        处理信息级别的日志
        
        参数:
            msg (str): 日志消息
        """
        self.log_queue.put(("INFO", msg))
        self.original_info(msg)

    def warn(self, msg):
        """
        处理警告级别的日志
        
        参数:
            msg (str): 日志消息
        """
        self.log_queue.put(("WARN", msg))
        self.original_warn(msg)

    def error(self, msg):
        """
        处理错误级别的日志
        
        参数:
            msg (str): 日志消息
        """
        self.log_queue.put(("ERROR", msg))
        self.original_error(msg)
        
    def debug(self, msg):
        """
        处理调试级别的日志
        
        参数:
            msg (str): 日志消息
        """
        self.log_queue.put(("DEBUG", msg))
        self.original_debug(msg)

    def restore(self):
        """
        恢复原始IO方法
        """
        IO.info = self.original_info
        IO.warn = self.original_warn
        IO.error = self.original_error
        IO.debug = self.original_debug

class Step:
    """步骤类，用于表示应用中的各个步骤"""
    def __init__(self, id, name_key, action, parent, callback):
        """
        初始化Step对象
        
        参数:
            id (int): 步骤ID
            name_key (str): 步骤名称的翻译键
            action (function): 步骤的执行函数
            parent: 父容器
            callback (function): 点击回调函数
        """
        self.id = id
        self.name_key = name_key
        self.action = action
        self.parent = parent
        self.callback = callback
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED, ERROR
        self.frame = None
        self.label_id = None
        self.label_name = None
        self.indicator = None
        self.spinner_angle = 0
        self.spinner_id = None

    def render(self, container):
        """
        在容器中渲染步骤
        
        参数:
            container: 容器
        """
        self.frame = tk.Frame(container, bg="#f0f0f0", pady=5, padx=5, cursor="hand2")
        self.frame.pack(fill="x", pady=2)
        self.frame.bind("<Button-1>", self.on_click)
        
        self.indicator = tk.Canvas(self.frame, width=20, height=20, bg="#f0f0f0", highlightthickness=0)
        self.indicator.pack(side="left", padx=5)
        self.indicator.bind("<Button-1>", self.on_click)
        self.draw_indicator()
        
        self.label_name = tk.Label(self.frame, text=t(self.name_key), bg="#f0f0f0", font=("Segoe UI", 10))
        self.label_name.pack(side="left", fill="x", expand=True)
        self.label_name.bind("<Button-1>", self.on_click)
        
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", length=100, mode="determinate")

    def draw_indicator(self):
        """
        绘制步骤状态指示器
        """
        self.indicator.delete("all")
        if self.status == "PENDING":
            self.indicator.create_oval(2, 2, 18, 18, outline="#ccc", width=2)
            self.indicator.create_text(10, 10, text=str(self.id), fill="#ccc", font=("Arial", 8, "bold"))
        elif self.status == "RUNNING":
            self.indicator.create_arc(2, 2, 18, 18, start=self.spinner_angle, extent=270, outline="#007bff", width=2, style="arc")
        elif self.status == "COMPLETED":
            self.indicator.create_oval(2, 2, 18, 18, fill="#28a745", outline="#28a745")
            self.indicator.create_line(5, 10, 9, 14, 15, 6, fill="white", width=2)
        elif self.status == "ERROR":
            self.indicator.create_oval(2, 2, 18, 18, fill="#dc3545", outline="#dc3545")
            self.indicator.create_line(6, 6, 14, 14, fill="white", width=2)
            self.indicator.create_line(14, 6, 6, 14, fill="white", width=2)

    def animate(self):
        """
        动画效果
        """
        if self.status == "RUNNING":
            self.spinner_angle = (self.spinner_angle - 20) % 360
            self.draw_indicator()
            self.spinner_id = self.indicator.after(50, self.animate)

    def on_click(self, event):
        """
        点击事件处理
        
        参数:
            event: 事件对象
        """
        if self.status != "RUNNING":
            self.callback(self)
            
    def update_text(self):
        """
        更新步骤文本
        """
        if self.label_name:
            self.label_name.config(text=t(self.name_key))

    def update_progress(self, current, total):
        """
        更新进度条
        
        参数:
            current (int): 当前进度
            total (int): 总进度
        """
        if total > 0:
            if not self.progress.winfo_ismapped():
                self.label_name.pack_forget()
                self.progress.pack(side="left", fill="x", expand=True, padx=5)
            self.progress["maximum"] = total
            self.progress["value"] = current
        else:
            if self.progress.winfo_ismapped():
                self.progress.pack_forget()
                self.label_name.pack(side="left", fill="x", expand=True)

    def set_status(self, status):
        """
        设置步骤状态
        
        参数:
            status (str): 状态
        """
        super_set_status = getattr(super(), "set_status", None)
        if status != "RUNNING" and self.progress and self.progress.winfo_ismapped():
            self.progress.pack_forget()
            self.label_name.pack(side="left", fill="x", expand=True)
            
        self.status = status
        self.draw_indicator()
        if status == "RUNNING":
            self.animate()

class PaperUI:
    """PaperP应用的GUI类"""
    def __init__(self, root, app_context):
        """
        初始化PaperUI对象
        
        参数:
            root: Tkinter根窗口
            app_context: PaperPApp对象
        """
        self.root = root
        self.app = app_context
        self.root.title(t("window_title"))
        self.root.geometry("900x600")
        
        self.log_queue = queue.Queue()
        self.log_handler = LogQueueHandler(self.log_queue)
        
        self.input_handler = GUIInputHandler(self.root)

        self.steps = []
        self.current_step_index = 0
        
        self.setup_ui()
        
        self.root.after(100, self.process_log_queue)
        
        IO.info(t("ui_init"))

    def setup_ui(self):
        """
        设置UI界面
        """
        self.main_container = tk.PanedWindow(self.root, orient="horizontal", sashwidth=4, bg="#dcdcdc")
        self.main_container.pack(fill="both", expand=True)
        
        self.left_panel = tk.Frame(self.main_container, bg="#f8f9fa", width=250)
        self.main_container.add(self.left_panel, minsize=200)
        
        header_frame = tk.Frame(self.left_panel, bg="#f8f9fa", pady=10)
        header_frame.pack(fill="x")
        self.header_label = tk.Label(header_frame, text=t("app_title"), font=("Segoe UI", 14, "bold"), bg="#f8f9fa")
        self.header_label.pack()
        
        ip_frame = tk.Frame(self.left_panel, bg="#f8f9fa", pady=5, padx=10)
        ip_frame.pack(fill="x")
        self.ip_label = tk.Label(ip_frame, text=t("local_ip_label"), bg="#f8f9fa", anchor="w")
        self.ip_label.pack(fill="x")
        self.ip_var = tk.StringVar(value=self.get_best_ip())
        self.ip_entry = tk.Entry(ip_frame, textvariable=self.ip_var)
        self.ip_entry.pack(fill="x")
        
        self.shortcuts_frame = tk.Frame(self.left_panel, bg="#f8f9fa", pady=10)
        self.shortcuts_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.btn_restore_hosts = tk.Button(self.shortcuts_frame, text=t("restore_hosts_btn"), command=self.restore_hosts, bg="white", relief="groove")
        self.btn_restore_hosts.pack(fill="x", pady=2)

        self.btn_force_stop = tk.Button(self.shortcuts_frame, text=t("force_stop_service_btn"), command=self.force_stop_service, bg="white", relief="groove")
        self.btn_force_stop.pack(fill="x", pady=2)

        self.steps_frame = tk.Frame(self.left_panel, bg="#f8f9fa")
        self.steps_frame.pack(fill="both", expand=True, padx=10)
        
        self.define_steps()
        
        self.right_panel = tk.Frame(self.main_container, bg="white")
        self.main_container.add(self.right_panel, minsize=400)
        
        toolbar = tk.Frame(self.right_panel, bg="#e9ecef", height=40)
        toolbar.pack(fill="x")
        
        self.lang_btn = tk.Button(toolbar, text=t("language_switch_btn"), command=self.toggle_language, bg="white", relief="flat")
        self.lang_btn.pack(side="right", padx=10, pady=5)
        
        self.log_console_label = tk.Label(toolbar, text=t("log_console_label"), font=("Segoe UI", 10, "bold"), bg="#e9ecef")
        self.log_console_label.pack(side="left", padx=10)
        
        self.log_area = scrolledtext.ScrolledText(self.right_panel, state="disabled", font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_area.tag_config("INFO", foreground="black")
        self.log_area.tag_config("WARN", foreground="#856404", background="#fff3cd")
        self.log_area.tag_config("ERROR", foreground="#721c24", background="#f8d7da")
        self.log_area.tag_config("DEBUG", foreground="gray")

    def get_best_ip(self):
        """
        获取最佳IP地址
        
        返回:
            str: IP地址
        """
        try:
            import socket
            hostname = socket.gethostname()
            ips = socket.gethostbyname_ex(hostname)[2]
            
            for ip in ips:
                if ip.startswith("192.168.137."):
                    return ip
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def define_steps(self):
        """
        定义步骤
        """
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        self.steps = []
        
        step_defs = [
            ("step_capture", self.run_capture),
            ("step_download_info", self.run_download_info),
            ("step_download_file", self.run_download_file),
            ("step_patch", self.run_patch),
            ("step_network", self.run_network),
            ("step_server", self.run_server)
        ]
        
        for i, (key, action) in enumerate(step_defs):
            step = Step(i+1, key, action, self.steps_frame, self.on_step_click)
            step.render(self.steps_frame)
            self.steps.append(step)

    def gui_input(self, msg):
        """
        显示输入对话框（便捷方法）
        
        参数:
            msg (str): 提示消息
        
        返回:
            str: 用户输入的内容
        """
        return self.input_handler.input(msg)
        
    def gui_confirm(self, msg):
        """
        显示确认对话框（便捷方法）
        
        参数:
            msg (str): 确认消息
        
        返回:
            bool: 用户是否确认（是返回True，否返回False）
        """
        return self.input_handler.confirm(msg)

    def on_step_click(self, step):
        """
        步骤点击事件处理
        
        参数:
            step: Step对象
        """
        if step.name_key == "step_server":
            if step.status == "RUNNING":
                if hasattr(self, 'server_instance') and self.server_instance:
                    IO.info(t("stopping_server"))
                    def stop_server_thread():
                        try:
                            self.server_instance.stop()
                            self.root.after(0, lambda: self._on_server_stopped(step))
                        except Exception as e:
                            IO.error(t("server_shutdown_error").format(e))
                    
                    threading.Thread(target=stop_server_thread).start()
                else:
                    step.set_status("PENDING")
                    
                return

        if step.id > 1:
            prev_step = self.steps[step.id - 2]
            if prev_step.status != "COMPLETED":
                IO.warn(t("complete_prev_step").format(t(prev_step.name_key)))
                return

        if step.status == "RUNNING":
            return
            
        step.set_status("RUNNING")
        threading.Thread(target=self.run_step_wrapper, args=(step,)).start()

    def _on_server_stopped(self, step):
        """
        服务器停止回调
        
        参数:
            step: Step对象
        """
        self.server_instance = None
        step.set_status("PENDING")
        IO.info(t("server_stop_success"))
        
    def run_step_wrapper(self, step):
        """
        步骤执行包装器
        
        参数:
            step: Step对象
        """
        try:
            success = step.action()
            self.root.after(0, lambda: self.step_finished(step, success))
        except Exception as e:
            IO.error(t("step_error").format(step.id, e))
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.step_finished(step, False))

    def step_finished(self, step, success):
        """
        步骤完成回调
        
        参数:
            step: Step对象
            success: 执行结果
        """
        if success == "KEEP_RUNNING":
            pass
        elif success:
            step.set_status("COMPLETED")
        else:
            step.set_status("ERROR")

    def process_log_queue(self):
        """
        处理日志队列
        """
        while not self.log_queue.empty():
            try:
                level, msg = self.log_queue.get_nowait()
                self.log_area.config(state="normal")
                self.log_area.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n", level)
                self.log_area.see("end")
                self.log_area.config(state="disabled")
            except queue.Empty:
                break
        
        self.root.after(100, self.process_log_queue)

    def toggle_language(self):
        """
        切换语言
        """
        current = I18N.current_language
        new_lang = I18N.Language.CHINESE if current == I18N.Language.ENGLISH else I18N.Language.ENGLISH
        I18N.set_language(new_lang)
        
        for step in self.steps:
            step.update_text()
            
        if hasattr(self, 'btn_restore_hosts'):
            self.btn_restore_hosts.config(text=t("restore_hosts_btn"))
        if hasattr(self, 'btn_force_stop'):
            self.btn_force_stop.config(text=t("force_stop_service_btn"))
            
        if hasattr(self, 'header_label'):
             self.header_label.config(text=t("app_title"))
        if hasattr(self, 'ip_label'):
             self.ip_label.config(text=t("local_ip_label"))
        if hasattr(self, 'log_console_label'):
             self.log_console_label.config(text=t("log_console_label"))
        if hasattr(self, 'lang_btn') and "language_switch_btn" in I18N.translations:
             self.lang_btn.config(text=t("language_switch_btn"))
        
        IO.info(t("lang_switch_log").format(t("lang_chinese") if new_lang == I18N.Language.CHINESE else t("lang_english")))

    def restore_hosts(self):
        """
        恢复hosts文件
        """
        if self.gui_confirm(t("hosts_backup_restore") + "?"):
            threading.Thread(target=HostManager.disable_redirect).start()

    def force_stop_service(self):
        """
        强制停止服务
        """
        if self.gui_confirm(t("force_stop_service_btn") + "?"):
            threading.Thread(target=HttpServer.force_stop_port_80).start()

    def run_capture(self):
        """
        执行抓包步骤
        
        返回:
            bool: 是否成功
        """
        ip = self.ip_var.get().strip()
        if ip and ip != "0.0.0.0":
            self.app.interface = ip
        else:
            self.app.interface = "192.168.137.1"
            self.ip_var.set("192.168.137.1")
            
        IO.info(t("starting_capture_ui"))
        result = capture_ota_request(self.app.interface)
        if result and result.product_url:
            self.app.capture_result = result
            IO.info(t("captured_request"))
            return True
        else:
            IO.error(t("capture_failed"))
            return False

    def run_download_info(self):
        """
        执行下载信息步骤
        
        返回:
            bool: 是否成功
        """
        if not hasattr(self.app, 'capture_result'):
            IO.error(t("no_capture_result"))
            return False
            
        self.app.update_data = get_update_data(self.app.capture_result.product_url, self.app.capture_result.request_body)
        if self.app.update_data:
            IO.info("Update data received.")
            return True
        return False

    def run_download_file(self):
        """
        执行下载文件步骤
        
        返回:
            bool: 是否成功
        """
        if not self.app.update_data:
            IO.error("No update data found.")
            return False
            
        try:
            delta_url = self.app.update_data['data']['version']['deltaUrl']
            IO.info(t("firmware_url").format(delta_url))
            
            step = self.steps[2]
            
            def progress_cb(current, total):
                self.root.after(0, lambda: step.update_progress(current, total))
                
            return download_file(delta_url, self.app.image_path, progress_callback=progress_cb)
        except KeyError as e:
            IO.error(t("json_structure_error").format(e))
            return False

    def run_patch(self):
        """
        执行修改固件步骤
        
        返回:
            bool: 是否成功
        """
        if not os.path.exists(self.app.image_path):
            IO.error(t("file_exists").format(self.app.image_path) + " (Not Found)")
            return False
            
        if not Patcher.replace_hash(self.app.image_path):
            return False
        
        ip = self.ip_var.get().strip()
        if ip and ip != "0.0.0.0":
            self.app.interface = ip
        else:
            self.app.interface = "192.168.137.1"
            self.ip_var.set("192.168.137.1")
            
        Patcher.update_version_data(self.app.update_data, self.app.image_path, self.app.interface)
        return True

    def run_network(self):
        """
        执行网络配置步骤
        
        返回:
            bool: 是否成功
        """
        ip = self.ip_var.get().strip()
        if not ip or ip == "0.0.0.0":
            IO.error("Invalid IP address. Please check 'Local IP' field.")
            return False
            
        self.app.interface = ip
        return HostManager.enable_redirect(ip)

    def run_server(self):
        """
        执行启动服务器步骤
        
        返回:
            str|bool: "KEEP_RUNNING"或是否成功
        """
        try:
            import socket
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_sock.bind(('0.0.0.0', 80))
                test_sock.close()
            except OSError as e:
                IO.error(t("port_occupied").format(80))
                IO.error(f"Bind check failed: {e}")
                IO.error(t("stop_other_servers"))
                return False

            step = self.steps[5]
            def progress_cb(current, total):
                self.root.after(0, lambda: step.update_progress(current, total))

            self.server_instance = HttpServer(
                port=80, 
                image_path=os.path.abspath(self.app.image_path), 
                update_data=self.app.update_data,
                progress_callback=progress_cb
            )
            
            error_queue = queue.Queue()
            
            def on_server_error(e):
                error_queue.put(e)
                
            self.server_instance.start_threaded(error_callback=on_server_error)
            
            self.root.after(500, lambda: self.check_server_error(error_queue))
            
            return "KEEP_RUNNING"
        except Exception as e:
            IO.error(f"Server error: {e}")
            return False

    def check_server_error(self, error_queue):
        """
        检查服务器错误
        
        参数:
            error_queue: 错误队列
        """
        try:
            error = error_queue.get_nowait()
            if error:
                IO.error(f"Server failed to start: {error}")
                server_step = next((s for s in self.steps if s.name_key == "step_server"), None)
                if server_step:
                    server_step.set_status("ERROR")
                    self.server_instance = None
        except queue.Empty:
            if hasattr(self, 'server_instance') and self.server_instance:
                 self.root.after(500, lambda: self.check_server_error(error_queue))

def main_ui(args=None):
    """
    启动GUI界面
    
    参数:
        args: 命令行参数
    """
    require_admin()
    
    lang = I18N.Language.ENGLISH
    if args and args.lang == 'cn':
        lang = I18N.Language.CHINESE
    I18N.set_language(lang)
    
    if args and args.debug:
        IO.DEBUG_MODE = True
        
    if not IO.DEBUG_MODE:
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass
    
    I18N.translations.update({
        "step_capture": {I18N.Language.ENGLISH: "1. Capture Request", I18N.Language.CHINESE: "1. 抓取请求"},
        "step_download_info": {I18N.Language.ENGLISH: "2. Get Update Info", I18N.Language.CHINESE: "2. 获取更新信息"},
        "step_download_file": {I18N.Language.ENGLISH: "3. Download Firmware", I18N.Language.CHINESE: "3. 下载固件"},
        "step_patch": {I18N.Language.ENGLISH: "4. Patch Firmware", I18N.Language.CHINESE: "4. 修改固件"},
        "step_network": {I18N.Language.ENGLISH: "5. Setup Network", I18N.Language.CHINESE: "5. 配置网络"},
        "step_server": {I18N.Language.ENGLISH: "6. Start Server", I18N.Language.CHINESE: "6. 启动服务"},
        "complete_prev_step": {I18N.Language.ENGLISH: "Please complete '{}' first.", I18N.Language.CHINESE: "请先完成 '{}'。"}
    })

    root = tk.Tk()
    
    interface = args.interface if args and args.interface else "0.0.0.0"
    image = args.image if args and args.image else "image.img"
    
    app_context = PaperPApp(interface=interface, image_path=image)
    
    app = PaperUI(root, app_context)
    root.mainloop()

if __name__ == "__main__":
    """
    UI模块入口点
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="0.0.0.0")
    parser.add_argument("--image", default="image.img")
    parser.add_argument("--lang", choices=['en', 'cn'])
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    main_ui(args)
