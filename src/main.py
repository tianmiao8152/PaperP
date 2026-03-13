import sys
import os

if __name__ == "__main__" and __package__ is None:
    file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(file_path))
    sys.path.append(parent_dir)
    __package__ = "src"

import argparse
from .utils.i18n import t
from .app import PaperPApp

def main():
    """
    主函数，解析命令行参数并启动应用
    """
    parser = argparse.ArgumentParser(description="PaperP - DictPen ADB Password Reset Tool")
    parser.add_argument("--interface", default="0.0.0.0", help="Network interface IP to listen on (Hotspot IP)")
    parser.add_argument("--image", default="image.img", help="Firmware image filename")
    parser.add_argument("--lang", choices=['en', 'cn'], help="Language (en/cn)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose output")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (default is GUI)")
    
    args = parser.parse_args()
    
    if not args.cli:
        try:
            from .ui import main_ui
            main_ui(args)
            return
        except ImportError as e:
            print(t("ui_load_fail").format(e))
            print(t("fallback_cli"))
        except Exception as e:
             print(t("ui_start_error").format(e))
             import traceback
             traceback.print_exc()
             return

    app = PaperPApp(
        interface=args.interface,
        image_path=args.image,
        lang=args.lang,
        debug=args.debug
    )
    
    app.run()

if __name__ == "__main__":
    """
    程序入口点
    """
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(t("press_enter_exit"))
        input()
