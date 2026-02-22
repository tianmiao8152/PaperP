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
    
    args = parser.parse_args()
    
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
