import time
import random
import re
import os
import requests
import imaplib
import email
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
import threading

load_dotenv()

# === PROXY CONFIGURATION ===
PROXY_HOST = "p.webshare.io"
PROXY_PORT = "80"
PROXY_USER = "nftiuvfu-rotate"
PROXY_PASS = "8ris7fu5rgrn"
proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# === Cloudflare API Config ===
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
DESTINATION_EMAIL = os.getenv("DESTINATION_EMAIL")

# === Gmail IMAP Config ===
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

# === Twitter & File Config ===
TWITTER_PASSWORD = "948332@1EB"
profile_picture_paths = [os.path.abspath(f"profileselfie/selfie_{i}.jpg") for i in range(3, 10)]
pic_index = 0
BANNER_PICTURE_PATH = os.path.abspath("banner/selfie_7.jpg")

GIF_PATHS = [
    os.path.abspath("Gif/Bop Nodding Head GIF by Demic.gif"),
    # ... keep all your existing paths ...
]

first_names = ["Lily", "Chloe", "Grace", "Ella", "Nora", "Zoe", "Leah", "Avery", "Scarlett", "Violet"]
last_names = ["Clark", "Lewis", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill"]

# ---------------------------
# Utility Functions
# ---------------------------
def human_delay(a=2, b=6):
    time.sleep(random.uniform(a, b))

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

def setup_driver():
    seleniumwire_options = {
        'proxy': {'http': proxy_url, 'https': proxy_url, 'no_proxy': 'localhost,127.0.0.1'}
    }

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver_path = os.path.join(os.getcwd(), "chromedriver")

    try:
        driver = webdriver.Chrome(
            service=Service(driver_path),
            seleniumwire_options=seleniumwire_options,
            options=chrome_options
        )

        print("🖥️ ChromeDriver launched in full desktop mode.")

        return driver
    except Exception as e:
        raise Exception(f"❌ Failed to launch ChromeDriver: {e}")


def generate_email_alias():
    first_names_alias = ["Olivia", "Ava", "Sophia", "Isabella", "Mia", "Charlotte", "Amelia", "Evelyn", "Abigail", "Harper"]
    last_names_alias = ["Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Lee", "Walker", "Hall"]
    fname = random.choice(first_names_alias)
    lname = random.choice(last_names_alias)
    num = random.randint(1, 99)
    alias = f"{fname}.{lname}{num}@deepictures.com"
    print(f"📧 Generated email alias: {alias}")
    return alias

def create_cloudflare_address(email_alias):
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/email/routing/addresses"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"email": email_alias}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Created Cloudflare Email Address: {email_alias}")
        return email_alias
    else:
        print(f"❌ Failed to create Cloudflare Email Address: {response.text}")
        return None

# --- Functions to Manage Forwarding Rules ---
def get_forwarding_rules():
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("result", [])
    else:
        print(f"❌ Failed to fetch forwarding rules: {response.text}")
        return []

def delete_forwarding_rule(rule_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/email/routing/rules/{rule_id}"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        print(f"✅ Deleted forwarding rule: {rule_id}")
    else:
        print(f"❌ Failed to delete forwarding rule: {response.text}")

def manage_forwarding_rules(max_rules=10):
    rules = get_forwarding_rules()
    if len(rules) >= max_rules:
        rules.sort(key=lambda x: x.get("created_at", ""))
        oldest_rule = rules[0]
        delete_forwarding_rule(oldest_rule["id"])
    else:
        print(f"ℹ️ Current number of rules: {len(rules)} (limit: {max_rules})")

def create_forwarding_rule(source_email, destination_email):
    manage_forwarding_rules(max_rules=10)  # Adjust max_rules based on your Cloudflare plan
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
    else:
        print(f"❌ Failed to create forwarding rule: {response.text}")

def get_latest_otp_imap():
    try:
        print("📥 Connecting to IMAP server to fetch OTP...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, 'UNSEEN', 'X-GM-RAW',
                                   '"newer_than:2m (OTP OR verification OR \'one-time\')"')
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
                    dt = email.utils.parsedate_tz(msg["Date"])
                    if dt:
                        timestamp = email.utils.mktime_tz(dt)
                        emails_with_dates.append((timestamp, e_id, msg))
        if not emails_with_dates:
            mail.logout()
            return None
        emails_with_dates.sort(key=lambda x: x[0], reverse=True)
        _, latest_email_id, latest_msg = emails_with_dates[0]
        body = ""
        if latest_msg.is_multipart():
            for part in latest_msg.walk():
                if part.get_content_type() == "text/plain" and part.get('Content-Disposition') is None:
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = latest_msg.get_payload(decode=True).decode(errors="ignore")
        print("📧 Raw email body (first 300 chars):")
        print(body[:300])
        otp_match = re.search(r"\b(\d{6})\b", body)
        if otp_match:
            otp = otp_match.group(1)
            print(f"✅ OTP Found: {otp}")
            mail.store(latest_email_id, '+FLAGS', '\\Deleted')
            mail.expunge()
            mail.logout()
            return otp
        mail.logout()
        print("❌ OTP not found in the fetched email.")
        return None
    except Exception as e:
        print(f"❌ Error fetching OTP via IMAP: {e}")
        return None

def handle_locked_account(driver):
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'locked')]")))
        print("⚠️ Locked account detected, proceeding with verification flow.")
    except TimeoutException:
        print("✅ No locked account message found; skipping locked account flow.")
        return True
    try:
        start_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@type='submit' and contains(@class, 'EdgeButton--primary') and (@value='Start' or @value='Continue to X')]")
        ))
        start_btn.click()
        print("✅ Clicked the locked account flow start button.")
    except TimeoutException:
        print("❌ Locked account start button not found; cannot proceed with locked account flow.")
        return False
    try:
        send_email_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@type='submit' and @value='Send email']"))
        )
        send_email_btn.click()
        print("✅ Clicked 'Send email' button.")
    except TimeoutException:
        print("❌ 'Send email' button not found.")
        return False
    otp = get_latest_otp_imap()
    if not otp:
        print("❌ OTP not retrieved.")
        return False
    print(f"✅ OTP retrieved: {otp}")
    try:
        token_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='token']")))
        token_field.clear()
        token_field.send_keys(otp)
        print("✅ Entered OTP into token field.")
        token_field.submit()
        print("✅ Submitted OTP.")
        return True
    except TimeoutException:
        print("❌ OTP token input field not found.")
        return False

def signup_twitter(driver, email_alias):
    driver.get("https://twitter.com/i/flow/signup")
    wait = WebDriverWait(driver, 30)
    human_delay()

    # === Step 1: Find "Create account" button ===
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

    # === Step 2: Fill Name ===
    name_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='name']")))
    random_full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    name_field.send_keys(random_full_name)
    human_delay()
    time.sleep(5)

    # === Step 3: Use email instead ===
    try:
        use_email_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Use email instead']"))
        )
        use_email_btn.click()
        print("✅ Clicked 'Use email instead'.")
        human_delay()
    except TimeoutException:
        print("⚠️ 'Use email instead' not found, continuing...")

    # === Step 4: Fill email ===
    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
    email_field.send_keys(email_alias)
    human_delay()

    # === Step 5: Fill Date of Birth ===
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'SELECTOR_1')]"))).send_keys("January")
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'SELECTOR_2')]"))).send_keys("9")
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'SELECTOR_3')]"))).send_keys("2002")
    human_delay(3, 5)

    # === Step 6: Click "Next" once ===
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]")))
        next_btn.click()
        human_delay()
        time.sleep(4)
    except TimeoutException:
        print("⚠️ 'Next' button not found after DOB step.")

    # === Step 7: Handle optional checkboxes ===
    checkbox_selectors = [
        "input[aria-describedby='CHECKBOX_1_LABEL']",
        "input[aria-describedby='CHECKBOX_2_LABEL']",
        "input[aria-describedby='CHECKBOX_3_LABEL']"
    ]
    for selector in checkbox_selectors:
        try:
            checkbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if not checkbox.is_selected():
                checkbox.click()
                print(f"✅ Checked: {selector}")
            else:
                print(f"⚠️ Already checked: {selector}")
            human_delay()
        except TimeoutException:
            print(f"⚠️ Checkbox not found: {selector}")

    # === Step 8: Click "Next" after checkboxes ===
    try:
        next_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-testid='ocfSettingsListNextButton']")
        ))
        next_button.click()
        print("✅ Clicked the final Next button!")
        time.sleep(5)
        human_delay()
    except TimeoutException as e:
        print("⚠️ Final 'Next' button not found:", e)

    # === Step 9: Bounce-back safety check ===
    try:
        bounced = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Create your account']"))
        )
        if bounced:
            print("❌ Twitter blocked signup and redirected back to 'Create your account'. Restarting browser...")
            driver.quit()   # close Chrome session
            return None     # signal caller to start fresh
    except TimeoutException:
        print("✅ Not bounced back, continuing flow...")

    return driver


def verify_twitter(driver, email_alias, profile_pic_path=None):
    wait = WebDriverWait(driver, 40)
    def notify_captcha():
        engine = pyttsx3.init()
        engine.say("Please solve the CAPTCHA!")
        engine.runAndWait()
        wait_for_captcha_solution(driver)
    try:
        captcha_iframes = driver.find_elements(By.XPATH, "//iframe")
        captcha_present = False
        for iframe in captcha_iframes:
            src = iframe.get_attribute("src")
            if src and ("hcaptcha" in src.lower() or "recaptcha" in src.lower()):
                captcha_present = True
                break
        page_text = driver.page_source.lower()
        if any(keyword in page_text for keyword in ["captcha", "hcaptcha", "recaptcha", "verify you're a human"]):
            captcha_present = True
        if captcha_present:
            print("⚠️ CAPTCHA detected! Please solve it manually.")
            human_delay()
            notify_captcha()
        else:
            print("✅ No CAPTCHA detected.")
    except Exception as e:
        print(f"❌ Error during CAPTCHA detection: {e}")
        return
    otp = None
    for attempt in range(20):
        otp = get_latest_otp_imap()
        if otp:
            break
        print(f"⌛ Waiting for OTP... (Attempt {attempt + 1}/20)")
        human_delay(5, 7)
    if not otp:
        print("❌ Failed to retrieve OTP.")
        return
    try:
        print("✍️ Entering OTP...")
        otp_field = wait.until(EC.presence_of_element_located((By.NAME, "verfication_code")))
        otp_field.send_keys(otp)
        print("✅ OTP entered successfully!")
        human_delay()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
        print("✅ Proceeded past OTP screen.")
        human_delay()
        print("🔒 Setting up password...")
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.send_keys(TWITTER_PASSWORD)
        print("✅ Password set.")
        human_delay()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Sign up']"))).click()
        print("✅ Account creation finalized.")
        human_delay(3, 5)
        if profile_pic_path and os.path.exists(profile_pic_path):
            print("🖼️ Uploading profile picture...")
            try:
                file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file' and @accept='image/jpeg,image/png,image/webp']")))
                driver.execute_script("arguments[0].style.display = 'block';", file_input)
                file_input.send_keys(os.path.abspath(profile_pic_path))
                print("✅ Profile picture uploaded.")
                human_delay()
                time.sleep(3)
                wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Apply')]"))).click()
                print("✅ Clicked 'Apply' button.")
                human_delay()
                time.sleep(2)
                wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
                print("✅ Clicked 'Next' button after profile upload.")
                human_delay()
                time.sleep(5)
            except WebDriverException as e:
                print(f"❌ Profile picture upload failed: {e}")
        elif profile_pic_path:
            print(f"❌ Invalid profile path: {profile_pic_path}")
        username_element = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']")))
        username = username_element.get_attribute("value")
        print("\n🎉 Account creation completed!")
        print(f"🔹 Email: {email_alias}")
        print(f"🔹 Password: {TWITTER_PASSWORD}")
        print(f"🔹 Username: {username}")
        with open("credentials.txt", "a") as f:
            f.write(f"Email: {email_alias}\n")
            f.write(f"Password: {TWITTER_PASSWORD}\n")
            f.write(f"Username: {username}\n")
            f.write("-" * 40 + "\n")
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("📸 Saved error screenshot to error_screenshot.png")


def wait_for_captcha_solution(driver):
    time.sleep(12)  # Initial delay to allow the page to load
    while True:
        try:
            captcha_present = False
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if src and "captcha" in src.lower():
                    captcha_present = True
                    break
            if "Authenticate your account" in driver.page_source:
                captcha_present = True
            if not captcha_present:
                print("✅ No CAPTCHA detected or already solved.")
                break
            else:
                print("⚠️ CAPTCHA detected! Please solve it manually.")
                os.system("say 'CAPTCHA detected, please solve it'")  # macOS sound notification
                #input("✅ Press Enter after solving CAPTCHA...")
                time.sleep(2)  # Wait for the page to update after solving
        except Exception as e:
            print(f"❌ Error checking CAPTCHA: {e}")
            break

if __name__ == "__main__":
    i = 0  # Initialize i before the loop
    pic_index = 0  # ensure pic_index starts here
    try:
        while True:
            driver = setup_driver()
            gif_path = GIF_PATHS[i % len(GIF_PATHS)]
            try:
                test_proxy()
                check_browser_ip(driver)
                alias = generate_email_alias()
                created_alias = create_cloudflare_address(alias)
                if created_alias is None:
                    print("⚠️ Falling back to generated alias.")
                    created_alias = alias
                create_forwarding_rule(created_alias, DESTINATION_EMAIL)

                # Call signup
                result = signup_twitter(driver, created_alias)
                if result is None:
                    # signup_twitter already closed driver on bounce-back
                    print("🔄 Restarting signup due to bounce-back issue...")
                    continue  # go back to loop, new driver will be created

                # If signup succeeded, continue normal flow
                wait_for_captcha_solution(driver)
                selected_profile_pic = profile_picture_paths[pic_index]
                pic_index = (pic_index + 1) % len(profile_picture_paths)
                verify_twitter(driver, created_alias, selected_profile_pic)
                print(f"🎉 Account creation for {created_alias} completed.")

            except Exception as e:
                print(f"❌ Error during account creation: {e}")
            finally:
                try:
                    driver.quit()
                    print("✅ Browser closed. Starting fresh for next account...")
                except Exception:
                    print("⚠️ Browser already closed or crashed.")
                time.sleep(10)
                i += 1  # Increment i for the next iteration
    except KeyboardInterrupt:
        print("⏹ Script stopped manually.")
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
