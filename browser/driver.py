import os
import sys
import subprocess
import time
from pathlib import Path

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import config


def get_chrome_version():
    try:
        result = subprocess.run(
            ["google-chrome", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return "Unknown"


def get_chrome_major_version():
    version_str = get_chrome_version()
    if version_str == "Unknown":
        return None
    try:
        parts = version_str.split()
        if len(parts) >= 2:
            version_num = parts[-1]
            major = version_num.split(".")[0]
            return int(major)
    except Exception:
        pass
    return None


def get_chromedriver_path():
    from browser.driver import get_chrome_version
    
    version_str = get_chrome_version()
    if version_str == "Unknown":
        return None
    
    try:
        version_num = version_str.split()[-1]
        base_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "linux64"
        
        for entry in sorted(base_path.iterdir(), reverse=True):
            if entry.is_dir() and entry.name.startswith("146"):
                driver_file = entry / "chromedriver"
                if driver_file.exists():
                    return str(driver_file)
    except Exception:
        pass
    
    return None


def get_chromedriver_version():
    try:
        import selenium
        from selenium.webdriver.chrome.service import Service
        service = Service()
        service.start()
        version = service.service_url
        service.stop()
        return version
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ["chromedriver", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception:
        pass
    
    return "(managed by undetected-chromedriver)"


def print_version_info():
    print("\n" + "=" * 50)
    print("Browser Version Info:")
    print("=" * 50)
    print(f"  Chrome:       {get_chrome_version()}")
    print(f"  ChromeDriver: {get_chromedriver_version()}")
    print("=" * 50 + "\n")


def get_chrome_options():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


def init_driver(force_new_session=False):
    import shutil
    
    session_dir = config.SESSION_DIR
    session_dir.mkdir(exist_ok=True)

    lock_files = [
        session_dir / "SingletonCookie",
        session_dir / "SingletonLock",
        session_dir / "SingletonSocket",
    ]

    for lock_file in lock_files:
        try:
            if lock_file.exists() or lock_file.is_symlink():
                lock_file.unlink()
        except Exception:
            pass

    if force_new_session:
        default_dir = session_dir / "Default"
        if default_dir.exists():
            for item in ["Cookies", "Cookies-journal", "Login Data", "Login Data For Account", "Account Web Data"]:
                f = default_dir / item
                if f.exists():
                    try:
                        f.unlink()
                    except Exception:
                        pass

        try:
            subprocess.run(["pkill", "-9", "-f", "chrome"], 
                         capture_output=True, timeout=5)
            time.sleep(2)
        except Exception:
            pass
    else:
        existing_chrome = subprocess.run(
            ["pgrep", "-f", f"chrome.*{session_dir.name}"],
            capture_output=True, text=True
        )
        if existing_chrome.returncode == 0:
            print("Existing Chrome session detected, reusing session...")

    use_session = session_dir
    
    version_main = get_chrome_major_version()
    
    chromedriver_path = get_chromedriver_path()
    
    if chromedriver_path:
        try:
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--user-data-dir={use_session}")
            options.add_argument("--remote-debugging-port=9222")
            
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            print(f"Failed with user-data-dir: {e}")
            if not force_new_session:
                print("Keeping existing session...")
                raise
            
            try:
                options = Options()
                options.add_argument("--start-maximized")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
                return driver
            except Exception as e2:
                print(f"Failed again: {e2}")
    
    version_main = get_chrome_major_version()

    if version_main is not None and version_main > 145:
        version_main = 145

    try:
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = uc.Chrome(
            options=options,
            user_data_dir=str(use_session),
            version_main=version_main,
            use_subprocess=False,
        )
        return driver
    except Exception as e:
        print(f"Failed with version_main={version_main}: {e}")
        print("Trying with version_main=None...")
        
        try:
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            driver = uc.Chrome(
                options=options,
                user_data_dir=str(use_session),
                version_main=None,
                use_subprocess=False,
            )
            return driver
        except Exception as e2:
            print(f"Failed again: {e2}")
            sys.exit(1)


def close_driver(driver: uc.Chrome):
    try:
        driver.quit()
    except Exception:
        pass
