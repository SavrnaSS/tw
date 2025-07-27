import time
import os
import random
import requests
import subprocess
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# Proxy credentials (adjust as needed)
PROXY_USER = "nftiuvfu"
PROXY_PASS = "8ris7fu5rgrn"

# List of Twitter accounts to follow
accounts_to_follow = [
    "AlyssaCart91902", "onlyarcadeace", "alviachokelal", "cliftymarie", "agniys", "devohconcept", "oviedolewis"
]

def kill_chrome_processes():
    """Kills all Chrome and ChromeDriver processes forcefully."""
    print("🛑 Terminating all Chrome and ChromeDriver processes...")
    subprocess.run(["pkill", "-9", "-f", "chrome"], check=False)
    subprocess.run(["pkill", "-9", "-f", "chromedriver"], check=False)
    time.sleep(5)  # Delay to ensure processes are fully terminated

def read_proxy_hosts(file_path="proxy-cred.txt"):
    """Reads proxy hosts and ports from a file."""
    hosts = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    host, port = line.split(":")
                    hosts.append((host, port))
    except Exception as e:
        print(f"❌ Error reading proxy-cred.txt: {e}")
    return hosts

def human_delay(a=2, b=6):
    """Sleep for a random duration between a and b seconds to mimic human behavior."""
    time.sleep(random.uniform(a, b))

def read_credentials(file_path="comp-cred.txt"):
    """Reads account credentials from a file."""
    credentials = []
    try:
        with open(file_path, "r") as f:
            lines = f.read().splitlines()
        block = {}
        for line in lines:
            if not line.strip() or line.startswith("-"):
                if block:
                    credentials.append(block)
                    block = {}
            else:
                if line.startswith("Email:"):
                    block["email"] = line.split("Email:")[1].strip()
                elif line.startswith("Password:"):
                    block["password"] = line.split("Password:")[1].strip()
                elif line.startswith("Username:"):
                    block["username"] = line.split("Username:")[1].strip()
        if block:
            credentials.append(block)
    except Exception as e:
        print(f"❌ Error reading comp-cred.txt: {e}")
    return credentials

def test_proxy(proxy_url):
    """Tests if the proxy is working using requests."""
    proxy = {"http": proxy_url, "https": proxy_url}
    print("📡 Testing proxy connection (via requests)...")
    try:
        response = requests.get("http://api.ipify.org?format=json", proxies=proxy, timeout=10)
        print(f"✅ Proxy is working. IP (via requests): {response.json()['ip']}")
        return True
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        return False

def check_browser_ip(driver):
    """Checks the browser's IP address via Selenium."""
    print("🌐 Checking browser IP via Selenium...")
    driver.get("http://api.ipify.org?format=json")
    try:
        ip = driver.find_element(By.TAG_NAME, "body").text
        print(f"✅ Browser IP confirmed: {ip}")
        return True
    except Exception as e:
        print(f"❌ Could not determine browser IP: {e}")
        return False

def setup_driver(proxy_url):
    """Sets up a Chrome WebDriver in headless mode."""
    seleniumwire_options = {
        'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'}
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            seleniumwire_options=seleniumwire_options,
            options=chrome_options
        )
        print("🖥️ Browser driver initialized successfully in headless mode.")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize driver: {e}")
        raise

def login_twitter(driver, email, twitter_password, user):
    """Logs into Twitter with the provided credentials."""
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 80)
    try:
        print("\n🔑 Logging into Twitter...")
        email_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
        )
        email_field.clear()
        email_field.send_keys(user)
        print("✅ Entered username.")

        next_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
        )
        next_btn.click()
        print("✅ Clicked 'Next'.")
        time.sleep(2)

        password_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']"))
        )
        password_field.clear()
        password_field.send_keys(twitter_password)
        print("✅ Entered password.")

        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Log in')]"))
        )
        login_btn.click()
        print("🎉 Login submitted!")
        time.sleep(4)
        return True
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False

def follow_accounts(driver):
    try:
        successful_follows = 0

        for account in accounts_to_follow:
            try:
                driver.get(f"https://twitter.com/{account}")
                
                # Wait for profile to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='primaryColumn']"))
                )

                human_delay(2, 3)

                # Find the Follow button using accurate XPath
                follow_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH, "//button[.//span[text()='Follow'] and contains(@data-testid, '-follow')]"
                    ))
                )

                follow_button.click()
                print(f"✅ Followed account: @{account}")
                successful_follows += 1
                human_delay(2, 5)

            except Exception as e:
                print(f"⚠️ Could not follow @{account}: {e}")

        print(f"✅ Successfully followed {successful_follows} out of {len(accounts_to_follow)} accounts")
        return successful_follows > 0

    except Exception as e:
        print(f"❌ Error in follow_accounts: {e}")
        return False

def process_account(cred, proxy_hosts):
    """Processes a single account with retry logic."""
    user_email = cred.get("email")
    twitter_password = cred.get("password")
    user = cred.get("username")
    print(f"\n🚀 Processing account: {user_email} | {user}")

    max_retries = 3
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries}")
        host, port = random.choice(proxy_hosts)
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{host}:{port}"

        if not test_proxy(proxy_url):
            print(f"❌ Proxy failed, retrying...")
            time.sleep(5)
            continue

        driver = None
        try:
            driver = setup_driver(proxy_url)
            if check_browser_ip(driver):
                if login_twitter(driver, user_email, twitter_password, user):
                    if follow_accounts(driver):
                        print(f"✅ Successfully processed account: {user_email}")
                        return True
            time.sleep(5)
        except Exception as e:
            print(f"❌ Error processing account: {e}")
        finally:
            if driver is not None:
                print("🧹 Quitting driver...")
                driver.quit()
            kill_chrome_processes()
            time.sleep(15)  # Delay to ensure cleanup
        print(f"❌ Retry {attempt + 1} failed, waiting before retry...")
        time.sleep(30)
    print(f"❌ Failed to process account {user_email} after {max_retries} attempts.")
    return False

if __name__ == "__main__":
    kill_chrome_processes()  # Initial cleanup
    print("🛑 Initial process cleanup complete.")

    creds = read_credentials("comp-cred.txt")
    total_accounts = len(creds)
    print(f"📋 Found {total_accounts} credential sets.")

    proxy_hosts = read_proxy_hosts("proxy-cred.txt")
    print(f"📡 Loaded {len(proxy_hosts)} proxy hosts.")

    if not proxy_hosts:
        raise ValueError("No proxy hosts found in proxy-cred.txt")

    processed_accounts = 0
    while processed_accounts < total_accounts:
        for cred in creds[processed_accounts:]:
            if process_account(cred, proxy_hosts):
                processed_accounts += 1
            else:
                print(f"⚠️ Skipping to next account, will retry later...")
        if processed_accounts < total_accounts:
            print(f"🔄 Retrying unprocessed accounts in 60 seconds...")
            time.sleep(60)

    print("🎉 All accounts processed successfully!")