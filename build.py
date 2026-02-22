import os
import sys
import subprocess

def install_nuitka():
    print("Installing Nuitka and dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka", "zstandard"])

def build():
    # Ensure Nuitka is installed
    try:
        import nuitka
    except ImportError:
        install_nuitka()

    output_dir = "dist"
    main_script = "src/main.py"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Nuitka arguments
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--include-package=src",    # Include our package
        "--output-dir=" + output_dir,
        "--output-filename=PaperP.exe",
        "--windows-uac-admin",      # Request Admin rights
        "--assume-yes-for-downloads",
        "--remove-output",          # Clean up build artifacts
        main_script
    ]
    
    print(f"Building {main_script} with Nuitka...")
    print("Command:", " ".join(cmd))
    
    subprocess.check_call(cmd)
    
    print(f"Build complete! Executable is in {output_dir}/PaperP.exe")

if __name__ == "__main__":
    build()
