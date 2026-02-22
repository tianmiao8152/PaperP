import sys
import ctypes
import os
import platform
import subprocess
from colorama import init, Fore, Style

# 初始化 colorama
init()

class Language:
    ENGLISH = 0
    CHINESE = 1

class I18N:
    Language = Language
    current_language = Language.ENGLISH
    
    translations = {
        # App messages
        "app_starting": {Language.ENGLISH: "Application starting...", Language.CHINESE: "正在启动应用..."},
        "app_terminating": {Language.ENGLISH: "Application terminating normally", Language.CHINESE: "应用正常关闭"},
        "paper": {Language.ENGLISH: "PAPER - Pen Adb Password Easily Reset", Language.CHINESE: "PAPER - 一键重置词典笔 ADB 密码"},
        
        # IO messages
        "confirm_prefix": {Language.ENGLISH: "[CONFIRM]", Language.CHINESE: "[确认]"},
        "confirm_suffix": {Language.ENGLISH: "[y/N]", Language.CHINESE: "[是(y)/否(N)]"},
        "input_prefix": {Language.ENGLISH: "[INPUT]", Language.CHINESE: "[输入]"},
        "debug_prefix": {Language.ENGLISH: "[DEBUG]", Language.CHINESE: "[调试]"},
        "info_prefix": {Language.ENGLISH: "[INFO]", Language.CHINESE: "[信息]"},
        "warn_prefix": {Language.ENGLISH: "[WARN]", Language.CHINESE: "[警告]"},
        "error_prefix": {Language.ENGLISH: "[ERROR]", Language.CHINESE: "[错误]"},
        "use_chinese": {Language.ENGLISH: "Use Chinese language? / 使用中文界面？", Language.CHINESE: "Use Chinese language? / 使用中文界面？"},
        
        # Admin
        "admin_required": {Language.ENGLISH: "This action requires administrative privileges.", Language.CHINESE: "此操作需要管理员权限。"},
        "relaunch_admin": {Language.ENGLISH: "Relaunching as administrator...", Language.CHINESE: "正在以管理员身份重新启动..."},
        
        # Capture
        "starting_capture": {Language.ENGLISH: "Starting packet capture...", Language.CHINESE: "正在启动抓包..."},
        "waiting_packet": {Language.ENGLISH: "Waiting for update packets... Please check updates on your dictpen", Language.CHINESE: "正在等待更新数据包...请在词典笔上检查更新"},
        "captured_request": {Language.ENGLISH: "Captured update request for product", Language.CHINESE: "已抓取到产品更新请求"},
        "interface_not_found": {Language.ENGLISH: "Interface not found", Language.CHINESE: "未找到网络接口"},
        
        # Download
        "downloading": {Language.ENGLISH: "Downloading firmware...", Language.CHINESE: "正在下载固件..."},
        "download_complete": {Language.ENGLISH: "Download completed", Language.CHINESE: "下载完成"},
        
        # Patch
        "patching": {Language.ENGLISH: "Patching firmware...", Language.CHINESE: "正在修改固件..."},
        "hash_found": {Language.ENGLISH: "Hash pattern found", Language.CHINESE: "找到哈希模式"},
        "input_password": {Language.ENGLISH: "Please input new password", Language.CHINESE: "请输入新密码"},
        "patch_success": {Language.ENGLISH: "Firmware patched successfully", Language.CHINESE: "固件修改成功"},
        
        # Host/Server
        "hosts_modified": {Language.ENGLISH: "Hosts file modified", Language.CHINESE: "Hosts 文件已修改"},
        "hosts_restored": {Language.ENGLISH: "Hosts file restored", Language.CHINESE: "Hosts 文件已恢复"},
        "server_start": {Language.ENGLISH: "Server started on port 80", Language.CHINESE: "服务器已在 80 端口启动"},
        "server_stop_hint": {Language.ENGLISH: "Press Ctrl+C to stop", Language.CHINESE: "按 Ctrl+C 停止"},
    }

    @staticmethod
    def t(key):
        if key not in I18N.translations:
            return key
        return I18N.translations[key].get(I18N.current_language, key)

    @staticmethod
    def set_language(lang):
        I18N.current_language = lang

def t(key):
    return I18N.t(key)

class IO:
    DEBUG_MODE = False

    @staticmethod
    def info(msg):
        print(f"{Fore.BLUE}{t('info_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def debug(msg):
        if IO.DEBUG_MODE:
            print(f"{Fore.CYAN}{t('debug_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def warn(msg):
        print(f"{Fore.YELLOW}{t('warn_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def error(msg):
        print(f"{Fore.RED}{t('error_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def input(msg):
        print(f"{Fore.MAGENTA}{t('input_prefix')} {msg}{Style.RESET_ALL}", end=" ", flush=True)
        return input()

    @staticmethod
    def confirm(msg):
        print(f"{Fore.MAGENTA}{t('confirm_prefix')} {msg} {t('confirm_suffix')}{Style.RESET_ALL}", end=" ", flush=True)
        try:
            import msvcrt
            res = msvcrt.getch().decode('utf-8').lower()
            print(res)
            return res == 'y'
        except:
            res = input().lower()
            return res == 'y'

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def require_admin():
    if not is_admin():
        IO.warn(t("admin_required"))
        IO.info(t("relaunch_admin"))
        # Re-run the program with admin rights
        # Handle spaces in paths by quoting
        script = sys.argv[0]
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        cmd = f'"{script}" {params}'
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, cmd, None, 1)
        sys.exit(0)
