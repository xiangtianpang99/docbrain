
import os
import sys
import subprocess
import venv
import platform

def print_banner(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60 + "\n")

def check_python_version():
    print("Checking Python version...")
    if sys.version_info < (3, 10):
        print("Error: docBrain requires Python 3.10 or higher.")
        print(f"Current version: {sys.version.split()[0]}")
        sys.exit(1)
    print(f"Python {sys.version.split()[0]} detected. OK.")

def setup_venv():
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print_banner("Creating Virtual Environment")
        venv.create(venv_dir, with_pip=True)
        print(f"Virtual environment created at {venv_dir}.")
    else:
        print("Virtual environment already exists.")
    return venv_dir

def get_pip_path(venv_dir):
    if platform.system() == "Windows":
        return os.path.join(venv_dir, "Scripts", "pip.exe")
    return os.path.join(venv_dir, "bin", "pip")

def install_requirements(venv_dir):
    pip_path = get_pip_path(venv_dir)
    print_banner("Installing Dependencies (This may take a few minutes)")
    print("This 1.6GB environment ensures all AI processing stays LOCAL for your privacy.")
    try:
        subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        print("\nDependencies installed successfully.")
    except Exception as e:
        print(f"\nError installing dependencies: {e}")
        sys.exit(1)

def setup_env():
    if not os.path.exists(".env"):
        print_banner("Configuration Setup")
        print("A .env file is required for API keys.")
        api_key = input("Please enter your DEEPSEEK_API_KEY: ").strip()
        
        with open(".env", "w") as f:
            f.write(f"DEEPSEEK_API_KEY={api_key}\n")
            f.write("WATCH_DIR=./data\n")
        print(".env file created.")
    else:
        print(".env file detected. Skipping setup.")

def main():
    print_banner("docBrain Bootstrap Loader")
    
    # Switch to project root directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"Working Directory: {os.getcwd()}")

    check_python_version()
    venv_dir = setup_venv()
    install_requirements(venv_dir)
    setup_env()
    
    print_banner("Setup Complete!")
    print("To start docBrain, run:")
    if platform.system() == "Windows":
        print(f"  {venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")
    print("  python src/main.py ask \"Hello\"")

if __name__ == "__main__":
    main()
