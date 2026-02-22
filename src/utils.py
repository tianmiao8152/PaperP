import sys
import ctypes
import os
import platform
import subprocess
from colorama import init, Fore, Style
from .i18n import I18N, t

# 初始化 colorama
init()

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
