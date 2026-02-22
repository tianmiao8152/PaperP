import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import threading
import queue
import time
import sys
import os
import ctypes

# Fix for relative imports when running as script directly
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
    """Redirects IO input to GUI dialogs."""
    def __init__(self, root):
        self.root = root
        self.original_input = IO.input
        self.original_confirm = IO.confirm
        
        # Patch IO methods
        IO.input = self.input
        IO.confirm = self.confirm

    def input(self, msg):
        # We need to run this in the main thread if called from a worker thread
        # But simpledialog waits for input, so it blocks.
        # If we are in the main thread, just call it.
        # If we are in a worker thread, we need to schedule it on main thread and wait.
        # For simplicity, assuming worker threads can invoke dialogs (tkinter is not thread safe, but simpledialog usually works if main loop is running?)
        # Actually no, tkinter calls must be from main thread.
        # So we need a mechanism to ask main thread to show dialog and return result.
        
        # However, for now let's try direct call, if it fails we implement queue based solution.
        # Actually, in this simple app, we can probably get away with it if we are careful.
        # But let's do it properly if possible, or use a simple hack.
        # Given "tkinter is not thread-safe", calling simpledialog from another thread might crash.
        # But since we are blocking the worker thread anyway waiting for input, we can use a variable.
        
        return self._run_in_main(lambda: simpledialog.askstring(t("dialog_input_title"), msg, parent=self.root))

    def confirm(self, msg):
        return self._run_in_main(lambda: messagebox.askyesno(t("dialog_confirm_title"), msg, parent=self.root))

    def _run_in_main(self, func):
        if threading.current_thread() is threading.main_thread():
            return func()
            
        result_queue = queue.Queue()
        def wrapper():
            try:
                res = func()
                result_queue.put((True, res))
            except Exception as e:
                result_queue.put((False, e))
        
        # Schedule on main thread
        # We can use an event or just rely on after
        # But we need to wait.
        # This requires the main loop to be running.
        self.root.after(0, wrapper)
        
        # Block until result
        success, res = result_queue.get()
        if not success:
            raise res
        return res

class LogQueueHandler:
    """Redirects IO output to a queue for UI consumption."""
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.original_info = IO.info
        self.original_warn = IO.warn
        self.original_error = IO.error
        self.original_debug = IO.debug
        
        # Patch IO methods
        IO.info = self.info
        IO.warn = self.warn
        IO.error = self.error
        IO.debug = self.debug

    def info(self, msg):
        self.log_queue.put(("INFO", msg))
        self.original_info(msg)

    def warn(self, msg):
        self.log_queue.put(("WARN", msg))
        self.original_warn(msg)

    def error(self, msg):
        self.log_queue.put(("ERROR", msg))
        self.original_error(msg)
        
    def debug(self, msg):
        self.log_queue.put(("DEBUG", msg))
        self.original_debug(msg)

    def restore(self):
        IO.info = self.original_info
        IO.warn = self.original_warn
        IO.error = self.original_error
        IO.debug = self.original_debug

class Step:
    def __init__(self, id, name_key, action, parent, callback):
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
        # Initially hidden
        
    def draw_indicator(self):
        self.indicator.delete("all")
        if self.status == "PENDING":
            self.indicator.create_oval(2, 2, 18, 18, outline="#ccc", width=2)
            self.indicator.create_text(10, 10, text=str(self.id), fill="#ccc", font=("Arial", 8, "bold"))
        elif self.status == "RUNNING":
            # Simple spinner animation
            self.indicator.create_arc(2, 2, 18, 18, start=self.spinner_angle, extent=270, outline="#007bff", width=2, style="arc")
        elif self.status == "COMPLETED":
            self.indicator.create_oval(2, 2, 18, 18, fill="#28a745", outline="#28a745")
            self.indicator.create_line(5, 10, 9, 14, 15, 6, fill="white", width=2)
        elif self.status == "ERROR":
            self.indicator.create_oval(2, 2, 18, 18, fill="#dc3545", outline="#dc3545")
            self.indicator.create_line(6, 6, 14, 14, fill="white", width=2)
            self.indicator.create_line(14, 6, 6, 14, fill="white", width=2)

    def animate(self):
        if self.status == "RUNNING":
            self.spinner_angle = (self.spinner_angle - 20) % 360
            self.draw_indicator()
            self.spinner_id = self.indicator.after(50, self.animate)

    def on_click(self, event):
        if self.status != "RUNNING":
            self.callback(self)
            
    def update_text(self):
        if self.label_name:
            self.label_name.config(text=t(self.name_key))

    def update_progress(self, current, total):
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
        super_set_status = getattr(super(), "set_status", None)
        # Reset progress bar when status changes (especially when finished)
        if status != "RUNNING" and self.progress and self.progress.winfo_ismapped():
            self.progress.pack_forget()
            self.label_name.pack(side="left", fill="x", expand=True)
            
        self.status = status
        self.draw_indicator()
        if status == "RUNNING":
            self.animate()

    def animate(self):
        if self.status == "RUNNING":
            self.spinner_angle = (self.spinner_angle - 20) % 360
            self.draw_indicator()
            self.spinner_id = self.indicator.after(50, self.animate)

    def on_click(self, event):
        if self.status != "RUNNING":
            self.callback(self)
            
    def update_text(self):
        if self.label_name:
            self.label_name.config(text=t(self.name_key))

class PaperUI:
    def __init__(self, root, app_context):
        self.root = root
        self.app = app_context
        self.root.title(t("window_title"))
        self.root.geometry("900x600")
        
        # Data
        self.log_queue = queue.Queue()
        self.log_handler = LogQueueHandler(self.log_queue)
        
        # Setup GUI Input Handler
        self.input_handler = GUIInputHandler(self.root)
        
        # Patch IO methods (The Input Handler __init__ already does this, but we override with bound methods for clarity)
        # Note: GUIInputHandler patches IO.input and IO.confirm to point to its own methods.
        # We don't need to overwrite them again unless we want to change behavior.
        # The infinite recursion was caused by:
        # 1. IO.confirm -> self.gui_confirm
        # 2. self.gui_confirm -> self.input_handler.confirm
        # 3. self.input_handler.confirm -> assigned to self.gui_confirm (in previous buggy code)
        
        # Correct approach:
        # GUIInputHandler methods call simpledialog/messagebox.
        # IO methods should point to GUIInputHandler methods.
        # We don't need self.gui_input/confirm wrapper methods if we just use input_handler directly or let IO use it.

        self.steps = []
        self.current_step_index = 0
        
        # Setup UI
        self.setup_ui()
        
        # Start Ticker
        self.root.after(100, self.process_log_queue)
        
        # Initial Log
        IO.info(t("ui_init"))

    def setup_ui(self):
        # Main Layout
        self.main_container = tk.PanedWindow(self.root, orient="horizontal", sashwidth=4, bg="#dcdcdc")
        self.main_container.pack(fill="both", expand=True)
        
        # Left Panel (Navigation)
        self.left_panel = tk.Frame(self.main_container, bg="#f8f9fa", width=250)
        self.main_container.add(self.left_panel, minsize=200)
        
        # Header in Left Panel
        header_frame = tk.Frame(self.left_panel, bg="#f8f9fa", pady=10)
        header_frame.pack(fill="x")
        self.header_label = tk.Label(header_frame, text=t("app_title"), font=("Segoe UI", 14, "bold"), bg="#f8f9fa")
        self.header_label.pack()
        
        # IP Configuration
        ip_frame = tk.Frame(self.left_panel, bg="#f8f9fa", pady=5, padx=10)
        ip_frame.pack(fill="x")
        self.ip_label = tk.Label(ip_frame, text=t("local_ip_label"), bg="#f8f9fa", anchor="w")
        self.ip_label.pack(fill="x")
        self.ip_var = tk.StringVar(value=self.get_best_ip())
        self.ip_entry = tk.Entry(ip_frame, textvariable=self.ip_var)
        self.ip_entry.pack(fill="x")
        
        # Shortcuts Frame (Bottom Left)
        self.shortcuts_frame = tk.Frame(self.left_panel, bg="#f8f9fa", pady=10)
        self.shortcuts_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        # Restore Hosts Button
        self.btn_restore_hosts = tk.Button(self.shortcuts_frame, text=t("restore_hosts_btn"), command=self.restore_hosts, bg="white", relief="groove")
        self.btn_restore_hosts.pack(fill="x", pady=2)

        # Force Stop Service Button
        self.btn_force_stop = tk.Button(self.shortcuts_frame, text=t("force_stop_service_btn"), command=self.force_stop_service, bg="white", relief="groove")
        self.btn_force_stop.pack(fill="x", pady=2)

        # Steps Container
        self.steps_frame = tk.Frame(self.left_panel, bg="#f8f9fa")
        self.steps_frame.pack(fill="both", expand=True, padx=10)
        
        # Define Steps
        self.define_steps()
        
        # Right Panel (Log)
        self.right_panel = tk.Frame(self.main_container, bg="white")
        self.main_container.add(self.right_panel, minsize=400)
        
        # Toolbar
        toolbar = tk.Frame(self.right_panel, bg="#e9ecef", height=40)
        toolbar.pack(fill="x")
        
        self.lang_btn = tk.Button(toolbar, text=t("language_switch_btn"), command=self.toggle_language, bg="white", relief="flat")
        self.lang_btn.pack(side="right", padx=10, pady=5)
        
        self.log_console_label = tk.Label(toolbar, text=t("log_console_label"), font=("Segoe UI", 10, "bold"), bg="#e9ecef")
        self.log_console_label.pack(side="left", padx=10)
        
        # Log Area
        self.log_area = scrolledtext.ScrolledText(self.right_panel, state="disabled", font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure Tags
        self.log_area.tag_config("INFO", foreground="black")
        self.log_area.tag_config("WARN", foreground="#856404", background="#fff3cd")
        self.log_area.tag_config("ERROR", foreground="#721c24", background="#f8d7da")
        self.log_area.tag_config("DEBUG", foreground="gray")

    def get_best_ip(self):
        try:
            # Try to find 192.168.137.1 first (Windows Hotspot default)
            import socket
            hostname = socket.gethostname()
            # gethostbyname_ex returns (hostname, aliases, ipaddrs)
            ips = socket.gethostbyname_ex(hostname)[2]
            
            # Priority 1: Hotspot IP
            for ip in ips:
                if ip.startswith("192.168.137."):
                    return ip
            
            # Priority 2: Connect to internet to find main interface
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            # Fallback
            return "127.0.0.1"

    def define_steps(self):
        # Clear existing
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
        
        # Add translation keys if not exists (temporary, should be in i18n.py)
        # We will add them to i18n later or handle fallback
        
        for i, (key, action) in enumerate(step_defs):
            step = Step(i+1, key, action, self.steps_frame, self.on_step_click)
            step.render(self.steps_frame)
            self.steps.append(step)

    def gui_input(self, msg):
        return self.input_handler.input(msg)
        
    def gui_confirm(self, msg):
        return self.input_handler.confirm(msg)

    def on_step_click(self, step):
        # Handle Server Step separately (Toggle logic)
        if step.name_key == "step_server":
            if step.status == "RUNNING":
                # Stop server logic
                if hasattr(self, 'server_instance') and self.server_instance:
                    IO.info(t("stopping_server"))
                    # Run stop in a thread to avoid blocking UI
                    def stop_server_thread():
                        try:
                            self.server_instance.stop()
                            # Update UI in main thread
                            self.root.after(0, lambda: self._on_server_stopped(step))
                        except Exception as e:
                            IO.error(t("server_shutdown_error").format(e))
                    
                    threading.Thread(target=stop_server_thread).start()
                else:
                    # If status says RUNNING but no instance, just reset
                    step.set_status("PENDING")
                    
                return
            # Else proceed to start logic

        # Basic dependency check
        # Enforce strict order for all steps
        if step.id > 1:
            prev_step = self.steps[step.id - 2]
            if prev_step.status != "COMPLETED":
                # Special handling for step 5 (Network) and 6 (Server)
                # If they are already running, we might want to stop them? 
                # But here we are checking if we can START the current step.
                
                # Check if previous step is "KEEP_RUNNING" (like server?) No, server is the last one.
                
                IO.warn(t("complete_prev_step").format(t(prev_step.name_key)))
                return

        # Start step in a thread
        if step.status == "RUNNING":
            return
            
        step.set_status("RUNNING")
        threading.Thread(target=self.run_step_wrapper, args=(step,)).start()

    def _on_server_stopped(self, step):
        self.server_instance = None
        step.set_status("PENDING")
        IO.info(t("server_stop_success"))
        
    def run_step_wrapper(self, step):
        try:
            success = step.action()
            # Update status in main thread via after (or just set variable, thread safe enough for simple string assignment usually, but better use after)
            self.root.after(0, lambda: self.step_finished(step, success))
        except Exception as e:
            IO.error(t("step_error").format(step.id, e))
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.step_finished(step, False))

    def step_finished(self, step, success):
        if success == "KEEP_RUNNING":
            # Keep it running (e.g. Server)
            pass
        elif success:
            step.set_status("COMPLETED")
            # Auto-advance logic could go here
        else:
            step.set_status("ERROR")

    def process_log_queue(self):
        while not self.log_queue.empty():
            try:
                level, msg = self.log_queue.get_nowait()
                self.log_area.config(state="normal")
                self.log_area.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n", level)
                self.log_area.see("end")
                self.log_area.config(state="disabled")
            except queue.Empty:
                break
        
        # Schedule next check
        self.root.after(100, self.process_log_queue)

    def toggle_language(self):
        current = I18N.current_language
        new_lang = I18N.Language.CHINESE if current == I18N.Language.ENGLISH else I18N.Language.ENGLISH
        I18N.set_language(new_lang)
        
        # Update UI texts
        for step in self.steps:
            step.update_text()
            
        # Update Shortcuts
        if hasattr(self, 'btn_restore_hosts'):
            self.btn_restore_hosts.config(text=t("restore_hosts_btn"))
        if hasattr(self, 'btn_force_stop'):
            self.btn_force_stop.config(text=t("force_stop_service_btn"))
            
        # Update Main UI Labels
        if hasattr(self, 'header_label'):
             self.header_label.config(text=t("app_title"))
        if hasattr(self, 'ip_label'):
             self.ip_label.config(text=t("local_ip_label"))
        if hasattr(self, 'log_console_label'):
             self.log_console_label.config(text=t("log_console_label"))
        if hasattr(self, 'lang_btn') and "language_switch_btn" in I18N.translations:
             self.lang_btn.config(text=t("language_switch_btn"))
        
        IO.info(t("lang_switch_log").format(t("lang_chinese") if new_lang == I18N.Language.CHINESE else t("lang_english")))

    # --- Shortcuts ---
    def restore_hosts(self):
        if self.gui_confirm(t("hosts_backup_restore") + "?"):
            threading.Thread(target=HostManager.disable_redirect).start()

    def force_stop_service(self):
        if self.gui_confirm(t("force_stop_service_btn") + "?"):
            threading.Thread(target=HttpServer.force_stop_port_80).start()

    # --- Step Actions ---

    def run_capture(self):
        # Update interface from UI just in case
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
        if not hasattr(self.app, 'capture_result'):
            IO.error(t("no_capture_result"))
            return False
            
        self.app.update_data = get_update_data(self.app.capture_result.product_url, self.app.capture_result.request_body)
        if self.app.update_data:
            IO.info("Update data received.")
            return True
        return False

    def run_download_file(self):
        if not self.app.update_data:
            IO.error("No update data found.")
            return False
            
        try:
            delta_url = self.app.update_data['data']['version']['deltaUrl']
            IO.info(t("firmware_url").format(delta_url))
            
            # Find the download step to update progress
            # We know it is index 2 (Step 3)
            step = self.steps[2]
            
            def progress_cb(current, total):
                self.root.after(0, lambda: step.update_progress(current, total))
                
            return download_file(delta_url, self.app.image_path, progress_callback=progress_cb)
        except KeyError as e:
            IO.error(t("json_structure_error").format(e))
            return False

    def run_patch(self):
        if not os.path.exists(self.app.image_path):
            IO.error(t("file_exists").format(self.app.image_path) + " (Not Found)")
            return False
            
        if not Patcher.replace_hash(self.app.image_path):
            return False
        
        # Ensure we use the latest IP from UI
        ip = self.ip_var.get().strip()
        if ip and ip != "0.0.0.0":
            self.app.interface = ip
        else:
            self.app.interface = "192.168.137.1"
            self.ip_var.set("192.168.137.1")
            
        # Re-calculate hashes
        Patcher.update_version_data(self.app.update_data, self.app.image_path, self.app.interface)
        return True

    def run_network(self):
        ip = self.ip_var.get().strip()
        if not ip or ip == "0.0.0.0":
            IO.error("Invalid IP address. Please check 'Local IP' field.")
            return False
            
        self.app.interface = ip
        return HostManager.enable_redirect(ip)

    def run_server(self):
        try:
            # Improved Port Check Logic
            # 1. Try to bind to port 80. If successful, port is free.
            # 2. If bind fails, port is occupied.
            import socket
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Set SO_REUSEADDR to avoid false positives if we just closed it
                test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_sock.bind(('0.0.0.0', 80))
                test_sock.close()
            except OSError as e:
                IO.error(t("port_occupied").format(80))
                IO.error(f"Bind check failed: {e}")
                IO.error(t("stop_other_servers"))
                return False

            # Define progress callback
            step = self.steps[5] # Step 6 is index 5
            def progress_cb(current, total):
                # Update progress in main thread
                self.root.after(0, lambda: step.update_progress(current, total))

            self.server_instance = HttpServer(
                port=80, 
                image_path=os.path.abspath(self.app.image_path), 
                update_data=self.app.update_data,
                progress_callback=progress_cb
            )
            
            # Use a queue to receive error from the server thread
            error_queue = queue.Queue()
            
            def on_server_error(e):
                error_queue.put(e)
                
            self.server_instance.start_threaded(error_callback=on_server_error)
            
            # We need to pass the error_queue to the checker
            self.root.after(500, lambda: self.check_server_error(error_queue))
            
            return "KEEP_RUNNING"
        except Exception as e:
            IO.error(f"Server error: {e}")
            return False

    def check_server_error(self, error_queue):
        try:
            error = error_queue.get_nowait()
            if error:
                # Found error, stop everything and show error
                IO.error(f"Server failed to start: {error}")
                # Find the server step
                server_step = next((s for s in self.steps if s.name_key == "step_server"), None)
                if server_step:
                    server_step.set_status("ERROR")
                    self.server_instance = None
        except queue.Empty:
            # No error yet, check again later if server is still supposed to be running
            if hasattr(self, 'server_instance') and self.server_instance:
                 self.root.after(500, lambda: self.check_server_error(error_queue))

def main_ui(args=None):
    require_admin()
    
    # Initialize I18N
    lang = I18N.Language.ENGLISH
    if args and args.lang == 'cn':
        lang = I18N.Language.CHINESE
    I18N.set_language(lang)
    
    # Debug
    if args and args.debug:
        IO.DEBUG_MODE = True
        
    # Hide console if not in debug mode
    if not IO.DEBUG_MODE:
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass
    
    # Add UI specific translations
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
    
    # Create app context
    interface = args.interface if args and args.interface else "0.0.0.0"
    image = args.image if args and args.image else "image.img"
    
    app_context = PaperPApp(interface=interface, image_path=image)
    
    app = PaperUI(root, app_context)
    root.mainloop()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="0.0.0.0")
    parser.add_argument("--image", default="image.img")
    parser.add_argument("--lang", choices=['en', 'cn'])
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    main_ui(args)
