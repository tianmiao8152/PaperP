import sys
import os

# Fix for relative imports when running as script directly (e.g. after UAC elevation)
if __name__ == "__main__" and __package__ is None:
    # Add the parent directory to sys.path
    file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(file_path))
    sys.path.append(parent_dir)
    __package__ = "src"

import argparse
from .utils.i18n import t
from .app import PaperPApp

def main():
    # Parse args
    parser = argparse.ArgumentParser(description="PaperP - DictPen ADB Password Reset Tool")
    parser.add_argument("--interface", default="0.0.0.0", help="Network interface IP to listen on (Hotspot IP)")
    parser.add_argument("--image", default="image.img", help="Firmware image filename")
    parser.add_argument("--lang", choices=['en', 'cn'], help="Language (en/cn)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose output")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (default is GUI)")
    
    args = parser.parse_args()
    
    # Check if we should run GUI
    # If no arguments provided (except script name), default to GUI
    # Or if --cli is not specified
    # However, if user provided other args (like --interface), they might expect CLI behavior?
    # User requirement: "Default open English UI interface"
    # Let's say: if --cli is NOT set, try to open UI. 
    # But we should pass args to UI? The UI currently hardcodes some defaults.
    # Let's update UI to accept args if possible, or just ignore for now.
    
    if not args.cli:
        try:
            from .ui import main_ui
            # We can pass args to main_ui if we update it
            main_ui(args)
            return
        except ImportError as e:
            print(f"Failed to load UI: {e}")
            print("Falling back to CLI mode.")
        except Exception as e:
             print(f"Error starting UI: {e}")
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
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback input if t() fails or other issues
        print("Press Enter to exit...")
        input()
