import os
import time
import requests
from DrissionPage import ChromiumPage, ChromiumOptions
from dotenv import load_dotenv
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import email.utils
import pyttsx3


# === PROXY CONFIGURATION ===
PROXY_HOST = "82.23.75.80"
PROXY_PORT = "6336"
PROXY_USER = "nftiuvfu"
PROXY_PASS = "8ris7fu5rgrn"
proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"


def test_proxy():
    proxy = {"http": proxy_url, "https": proxy_url}
    print("📡 Testing proxy connection (via requests)...")
    try:
        response = requests.get("http://api.ipify.org?format=json", proxies=proxy, timeout=10)
        print(f"✅ Proxy is working. IP (via requests): {response.json()['ip']}")
    except Exception as e:
        raise Exception(f"❌ Proxy test failed: {e}")

def check_browser_ip(driver):
    print("🌐 Checking browser IP via Selenium...")
    driver.get("http://api.ipify.org?format=json")
    try:
        ip = driver.find_element(By.TAG_NAME, "body").text
        print(f"✅ Browser IP confirmed: {ip}")
    except Exception as e:
        print(f"❌ Could not determine browser IP: {e}")

# ---------------------------
# Selenium Wire Setup with Proxy
# ---------------------------
def setup_driver():
    seleniumwire_options = {
        'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'}
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              seleniumwire_options=seleniumwire_options,
                              options=chrome_options)
    print("🖥️ Browser driver initialized.")
    return driver

# ---------------------------
# Set up Chromium options
# ---------------------------
# ---------------------------
# Launch browser and open x.com
# ---------------------------
driver = setup_driver()

# Keep Chrome open until you stop it manually
try:
    test_proxy()
    check_browser_ip(driver)
    driver.get("https://x.com/i/flow/login")
    print("✅ Chrome with proxy is running. Press Ctrl+C to quit.")
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("\n🛑 Exiting...")
    driver.quit()
