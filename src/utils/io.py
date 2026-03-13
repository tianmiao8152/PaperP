import sys
import ctypes
import os
import platform
import subprocess
from colorama import init, Fore, Style
from .i18n import I18N, t

init()

class IO:
    """输入输出类，用于处理控制台输出和用户输入"""
    DEBUG_MODE = False

    @staticmethod
    def info(msg):
        """
        输出信息级别的消息
        
        参数:
            msg (str): 消息内容
        """
        print(f"{Fore.BLUE}{t('info_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def debug(msg):
        """
        输出调试级别的消息
        
        参数:
            msg (str): 消息内容
        """
        if IO.DEBUG_MODE:
            print(f"{Fore.CYAN}{t('debug_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def warn(msg):
        """
        输出警告级别的消息
        
        参数:
            msg (str): 消息内容
        """
        print(f"{Fore.YELLOW}{t('warn_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def error(msg):
        """
        输出错误级别的消息
        
        参数:
            msg (str): 消息内容
        """
        print(f"{Fore.RED}{t('error_prefix')} {msg}{Style.RESET_ALL}")

    @staticmethod
    def input(msg):
        """
        接收用户输入
        
        参数:
            msg (str): 提示消息
        
        返回:
            str: 用户输入的内容
        """
        print(f"{Fore.MAGENTA}{t('input_prefix')} {msg}{Style.RESET_ALL}", end=" ", flush=True)
        return input()

    @staticmethod
    def confirm(msg):
        """
        确认用户输入
        
        参数:
            msg (str): 确认消息
        
        返回:
            bool: 用户是否确认（是返回True，否返回False）
        """
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
    """
    检查当前用户是否是管理员
    
    返回:
        bool: 是否是管理员
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def require_admin():
    """
    要求以管理员权限运行
    如果当前用户不是管理员，则以管理员权限重新启动程序
    """
    if not is_admin():
        IO.warn(t("admin_required"))
        IO.info(t("relaunch_admin"))
        script = sys.argv[0]
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        cmd = f'"{script}" {params}'
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, cmd, None, 1)
        sys.exit(0)
