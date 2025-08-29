import os
import time
import requests
import logging
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Enable debug logs for troubleshooting
logging.basicConfig(level=logging.INFO)  # Change to DEBUG for more logs

# === CONFIG ===
USE_PROXY = True  # Set to False to disable proxy for debugging


# === PROXY CONFIGURATION ===
PROXY_HOST = "p.webshare.io"
PROXY_PORT = "80"
PROXY_USER = "nftiuvfu-rotate"
PROXY_PASS = "8ris7fu5rgrn"
proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# === Proxy test using requests ===
def test_proxy():
    print("📡 Testing proxy connection (via requests)...")
    proxy = {"http": proxy_url, "https": proxy_url}
    try:
        response = requests.get("http://api.ipify.org?format=json", proxies=proxy, timeout=10)
        print(f"✅ Proxy is working. IP (via requests): {response.json()['ip']}")
    except Exception as e:
        raise Exception(f"❌ Proxy test failed: {e}")

# === IP check inside browser ===
def check_browser_ip(driver):
    print("🌐 Checking browser IP via Selenium...")
    try:
        driver.get("http://api.ipify.org?format=json")
        ip = driver.find_element(By.TAG_NAME, "body").text
        print(f"✅ Browser IP confirmed: {ip}")
    except Exception as e:
        print(f"❌ Could not determine browser IP: {e}")

# === Setup WebDriver ===
def setup_driver():
    print("⚙️ Setting up Chrome driver...")

    seleniumwire_options = {}
    if USE_PROXY:
        seleniumwire_options = {
            'proxy': {
                'http': proxy_url,
                'https': proxy_url,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Path to chromedriver in the same directory
    driver_path = os.path.join(os.getcwd(), "chromedriver")

    try:
        driver = webdriver.Chrome(
            service=Service(driver_path),
            seleniumwire_options=seleniumwire_options if USE_PROXY else None,
            options=chrome_options
        )
        print("🖥️ ChromeDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        raise Exception(f"❌ ChromeDriver launch failed: {e}")

# === Main Script ===
if __name__ == "__main__":
    print("🚀 Script started.")

    try:
        if USE_PROXY:
            test_proxy()
        else:
            print("⚠️ Proxy disabled. Skipping proxy test.")

        driver = setup_driver()
        check_browser_ip(driver)

        print("🔗 Navigating to x.com login page...")
        driver.get("https://x.com/i/flow/login")

        print("✅ Browser is running with proxy (if enabled). Press Ctrl+C to quit.")
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        print("\n🛑 Script interrupted. Closing browser...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            driver.quit()
            print("🧹 ChromeDriver closed cleanly.")
        except:
            pass
