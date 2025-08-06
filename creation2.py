import time
import random
import string
import re
import os
import json                             # added
import base64                           # added
import zipfile                          # added
import requests
import imaplib
import email
import email.utils
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

load_dotenv()

# ---------------------------
# Proxy settings (Authenticated)
# ---------------------------
PROXY_HOST = "82.24.61.83"
PROXY_PORT = "6302"
PROXY_USER = "nftiuvfu"
PROXY_PASS = "8ris7fu5rgrn"

def create_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass, plugin_path=None):
    if not plugin_path:
        plugin_path = f'proxy_auth_plugin_{random.randint(0,9999)}.zip'
    # manifest.json
    manifest_json = {
      "version": "1.0.0",
      "manifest_version": 2,
      "name": "Chrome Proxy",
      "permissions": [
        "proxy","tabs","unlimitedStorage","storage",
        "<all_urls>","webRequest","webRequestBlocking"
      ],
      "background": {"scripts": ["background.js"]}
    }
    # base64 credentials
    creds_b64 = base64.b64encode(f"{proxy_user}:{proxy_pass}".encode()).decode()
    # background.js
    background_js = f"""
var config = {{
  mode: "fixed_servers",
  rules: {{
    singleProxy: {{ scheme: "http", host: "{proxy_host}", port: parseInt({proxy_port}) }},
    bypassList: ["localhost"]
  }}
}};
chrome.proxy.settings.set({{value: config, scope: "regular"}}, function(){{}});
function callbackFn(details) {{
  details.requestHeaders.push({{
    name: "Proxy-Authorization",
    value: "Basic {creds_b64}"
  }});
  return {{requestHeaders: details.requestHeaders}};
}}
chrome.webRequest.onBeforeSendHeaders.addListener(
  callbackFn,
  {{urls: ["<all_urls>"]}},
  ["blocking","requestHeaders"]
);
"""
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", json.dumps(manifest_json))
        zp.writestr("background.js", background_js)
    return plugin_path

# Create the extension once
PROXY_EXTENSION = create_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

# ---------------------------
# Cloudflare API Config
# ---------------------------
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
DESTINATION_EMAIL = os.getenv("DESTINATION_EMAIL")  # Your fixed destination email (e.g., Gmail)

# ---------------------------
# Gmail IMAP Config
# ---------------------------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")  # Must match DESTINATION_EMAIL
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Use an app password for Gmail
IMAP_SERVER = "imap.gmail.com"

# ---------------------------
# Twitter & Selenium Config
# ---------------------------
TWITTER_PASSWORD = "948332@1EB"
PROFILE_PICTURE_PATH = os.path.abspath("pictures_selfie/selfie_2.jpg")
BANNER_PICTURE_PATH = os.path.abspath("banner/selfie_3.jpg")
GIF_PATH = os.path.abspath("gif/Happy Little Girl GIF by Demic.gif")

if not os.path.exists(GIF_PATH):
    print(f"❌ Error: GIF file not found at {GIF_PATH}")
    exit(1)

# ---------------------------
# Sample Names for Signup
# ---------------------------
first_names = ["Jennifer", "Samantha", "Alicia", "Laura", "Emma", "Sophia", "Ava", "Mia"]
last_names = ["Jaatni", "Roy", "Brooks", "Patel", "Harris", "Carter", "Martin", "Thompson"]

# ---------------------------
# Utility Functions
# ---------------------------
def human_delay(a=2, b=6):
    time.sleep(random.uniform(a, b))


def generate_email_alias():
    first_names_alias = ['Meena', 'Prunkesh', 'Alex', 'Emily', 'Chris', 'Laura']
    last_names_alias = ['Singh', 'Alona', 'Johnson', 'Williams', 'Brown', 'Davis']
    fname = random.choice(first_names_alias)
    lname = random.choice(last_names_alias)
    num = random.randint(1, 99)
    email_alias = f"{fname}.{lname}{num}@deepictures.com"
    print(f"📧 Generated email alias: {email_alias}")
    return email_alias

def create_cloudflare_address(email_alias):
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/email/routing/addresses"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"email": email_alias}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Created Cloudflare Email Address: {email_alias}")
        return email_alias
    else:
        print(f"❌ Failed to create Cloudflare Email Address: {response.text}")
        return None

def get_existing_rules():
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("result", [])
    else:
        print(f"❌ Failed to fetch existing rules: {response.text}")
        return []

def delete_forwarding_rule(rule_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules/{rule_id}"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Deleted forwarding rule: {rule_id}")
        return True
    else:
        print(f"❌ Failed to delete rule: {response.text}")
        return False

def create_forwarding_rule(source_email, destination_email):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "name": f"Forward {source_email} to {destination_email}",
        "enabled": True,
        "matchers": [{"type": "literal", "field": "to", "value": source_email}],
        "actions": [{"type": "forward", "value": [destination_email]}]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Created forwarding rule: {source_email} ➝ {destination_email}")
        return True
    else:
        print(f"❌ Failed to create forwarding rule: {response.text}")
        return False

def get_latest_otp_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, 'UNSEEN', 'X-GM-RAW', '"newer_than:2m (OTP OR verification OR \'one-time\')"')
        if status != "OK":
            print("❌ IMAP search failed.")
            return None
        email_ids = data[0].split()
        if not email_ids:
            print("❌ No new OTP emails found via IMAP.")
            mail.logout()
            return None

        emails_with_dates = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    date_tuple = email.utils.parsedate_tz(msg["Date"])
                    if date_tuple:
                        timestamp = email.utils.mktime_tz(date_tuple)
                        emails_with_dates.append((timestamp, e_id, msg))
        if not emails_with_dates:
            mail.logout()
            return None

        emails_with_dates.sort(key=lambda x: x[0], reverse=True)
        latest_timestamp, latest_email_id, latest_msg = emails_with_dates[0]
        body = ""
        if latest_msg.is_multipart():
            for part in latest_msg.walk():
                if part.get_content_type() == "text/plain" and part.get('Content-Disposition') is None:
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = latest_msg.get_payload(decode=True).decode(errors="ignore")
        
        otp_match = re.search(r"\b(\d{6})\b", body)
        if otp_match:
            otp = otp_match.group(1)
            mail.store(latest_email_id, '+FLAGS', '\\Deleted')
            mail.expunge()
            mail.logout()
            return otp

        mail.logout()
        return None
    except Exception as e:
        print(f"❌ Error fetching OTP via IMAP: {e}")
        return None

def handle_locked_account(driver):
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'locked')]")))
    except TimeoutException:
        return True

    try:
        start_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@class, 'EdgeButton--primary') and (@value='Start' or @value='Continue to X')]"))
        )
        start_btn.click()
    except TimeoutException:
        return False

    try:
        send_email_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Send email']"))
        )
        send_email_btn.click()
    except TimeoutException:
        return False

    otp = get_latest_otp_imap()
    if not otp:
        return False

    try:
        token_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='token']")))
        token_field.clear()
        token_field.send_keys(otp)
        token_field.submit()
        return True
    except TimeoutException:
        return False

def signup_twitter(driver, email_alias):
    driver.get("https://twitter.com/i/flow/signup")
    wait = WebDriverWait(driver, 30)
    human_delay()

    selectors = [
        "//span[contains(text(),'Create account')]",
        "//div[contains(text(),'Create account')]",
        "//button[contains(.,'Create account')]"
    ]
    create_account_btn = None
    for xpath in selectors:
        try:
            create_account_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            if create_account_btn:
                break
        except Exception:
            pass
    if not create_account_btn:
        driver.save_screenshot("signup_page_debug.png")
        raise TimeoutException("Unable to locate 'Create account' button.")
    create_account_btn.click()
    human_delay()

    name_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='name']")))
    random_full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    name_field.send_keys(random_full_name)
    human_delay()
    time.sleep(5)

    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
    email_field.send_keys(email_alias)
    human_delay()

    wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'SELECTOR_1')]"))).send_keys("January")
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'SELECTOR_2')]"))).send_keys("9")
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'SELECTOR_3')]"))).send_keys("2002")
    human_delay()

    for _ in range(3):
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]")))
            next_btn.click()
            human_delay()
            break
        except Exception:
            human_delay(2, 4)
    return driver

def verify_twitter(driver, email_alias, profile_pic_path=None):
    wait = WebDriverWait(driver, 20)
    otp = None
    for attempt in range(10):
        otp = get_latest_otp_imap()
        if otp:
            break
        human_delay(5, 7)
    if not otp:
        return

    otp_field = wait.until(EC.presence_of_element_located((By.NAME, "verfication_code")))
    otp_field.send_keys(otp)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
    human_delay()

    password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_field.send_keys(TWITTER_PASSWORD)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Sign up']"))).click()
    human_delay(3, 5)

    if profile_pic_path and os.path.exists(profile_pic_path):
        try:
            file_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file' and @accept='image/jpeg,image/png,image/webp']")
            ))
            driver.execute_script("arguments[0].style.display = 'block';", file_input)
            file_input.send_keys(os.path.abspath(profile_pic_path))
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Apply')]"))).click()
            human_delay()
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
            human_delay()
        except WebDriverException:
            pass

    username = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))).get_attribute("value")
    print(f"🎉 Created: {email_alias} / {TWITTER_PASSWORD} / @{username}")
    with open("credentials.txt", "a") as f:
        f.write(f"Email: {email_alias}\nPassword: {TWITTER_PASSWORD}\nUsername: {username}\n{'-'*40}\n")

def login_twitter_simple(driver, email):
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 30)
    try:
        email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        email_field.clear()
        email_field.send_keys(email)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))).click()
        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']")))
        password_field.clear()
        password_field.send_keys(TWITTER_PASSWORD)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Log in')]"))).click()
        time.sleep(5)
    except Exception:
        pass

def logout_twitter(driver):
    wait = WebDriverWait(driver, 20)
    try:
        driver.find_element(By.XPATH, "//button[@aria-label='Account menu']").click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//a[@data-testid='AccountSwitcher_Logout_Button']").click()
        driver.find_element(By.XPATH, "//span[contains(text(),'Log out')]").click()
        time.sleep(5)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        while True:
            existing_rules = get_existing_rules()
            if len(existing_rules) >= 10:
                if delete_forwarding_rule(existing_rules[0]["id"]):
                    pass
                else:
                    break

            alias = generate_email_alias()
            created_alias = create_cloudflare_address(alias) or alias

            options = uc.ChromeOptions()
            # now use extension instead of proxy_url
            options.add_extension(PROXY_EXTENSION)
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = uc.Chrome(options=options)

            try:
                if create_forwarding_rule(created_alias, DESTINATION_EMAIL):
                    driver.get("https://twitter.com/i/flow/signup")
                    time.sleep(3)
                    signup_twitter(driver, created_alias)
                    verify_twitter(driver, created_alias, PROFILE_PICTURE_PATH)
                    logout_twitter(driver)
                    driver.delete_all_cookies()
                else:
                    print(f"⚠️ Skipping signup for {created_alias}")
            except Exception as e:
                print(f"❌ Error during account creation: {e}")
            finally:
                driver.quit()
            
            time.sleep(10)

    except KeyboardInterrupt:
        print("⏹ Stopped manually.")
