import time
import os
import random
import re
import imaplib
import email.utils
import email
import requests
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
from dotenv import load_dotenv
from selenium.common.exceptions import ElementClickInterceptedException

load_dotenv()

# Base path relative to script
base_dir = os.path.dirname(__file__)
banner_path = [
    os.path.join(base_dir, "Banner/selfie_1.jpg"),
    os.path.join(base_dir, "Banner/selfie_2.jpg"),
    os.path.join(base_dir, "Banner/selfie_3.jpg"),
    os.path.join(base_dir, "Banner/selfie_4.jpg"),
    os.path.join(base_dir, "Banner/selfie_5.jpg"),
]

GIF_PATH = os.path.abspath("gif/Happy Jonah Hill GIF.gif")

# List of 20 bio messages to randomly choose from
bio_messages = [
    "Living rent-free in your mind 💅✨", "Sweet but psycho, you choose 🍭🖤", "Flirting with chaos & stealing hearts 💋🔥",
    "Your internet crush with main character energy 🎬💖", "Too pretty to be stressing 😘🚀", "DND: Manifesting my dream life ✨🔮",
    "Sassy, classy, but a little bad-assy 😏💃", "No thoughts, just vibes & aesthetics 🌸💭", "Serving looks, spilling tea, making moves ☕💄",
    "Caught between being an angel & a menace 😇😈", "Glitching through life like a bad WiFi connection 📡💫",
    "Not your ex, but still your biggest regret 💔😉", "Just a walking red flag with great eyeliner 🚩💋",
    "More mystery than your favorite thriller novel 📖👀", "Running on coffee, confidence, and chaos ☕👠",
    "Offline? Never heard of her. 🤳💖", "Dressed to kill, but only slaying in selfies 📸🖤", "90% attitude, 10% battery life 🔋🔥",
    "Heartbreaker with a soft side 💔✨", "Making memories & breaking algorithms 🖥️💄"
]

# List of Twitter accounts to follow
accounts_to_follow = [
    "onlyarcadeace", "alviachokelal", "cliftymarie", "agniys", "devohconcept", "oviedolewis"
]

# ---------------------------
# Gmail IMAP Config
# ---------------------------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

# === PROXY CONFIGURATION ===
PROXY_HOST = "82.22.177.152"
PROXY_PORT = "5370"
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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              seleniumwire_options=seleniumwire_options,
                              options=chrome_options)
    print("🖥️ Browser driver initialized in headless mode.")
    return driver

# ---------------------------
# Utility Functions
# ---------------------------
def human_delay(a=2, b=6):
    time.sleep(random.uniform(a, b))

def read_credentials(file_path="comp-cred.txt"):
    """
    Reads credentials from a file and returns a list of dictionaries.
    Expected format:
    
    Email: example@domain.com
    Password: somepassword
    Username: someusername
    ----------------------------------------
    """
    credentials = []
    try:
        with open(file_path, "r") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return credentials

    block = {}
    for line in lines:
        if not line.strip() or line.startswith("-"):
            if block:
                # Ensure all required fields are present
                if "email" in block and "password" in block and "username" in block:
                    credentials.append(block)
                else:
                    print(f"Warning: Incomplete block skipped: {block}")
                block = {}
        else:
            if "Email:" in line:
                parts = line.split("Email:", 1)
                if len(parts) > 1:
                    block["email"] = parts[1].strip()
                else:
                    print(f"Warning: Invalid email format in line: {line}")
            elif "Password:" in line:
                parts = line.split("Password:", 1)
                if len(parts) > 1:
                    block["password"] = parts[1].strip()
                else:
                    print(f"Warning: Invalid password format in line: {line}")
            elif "Username:" in line:
                parts = line.split("Username:", 1)
                if len(parts) > 1:
                    block["username"] = parts[1].strip()
                else:
                    print(f"Warning: Invalid username format in line: {line}")
            else:
                print(f"Warning: Unrecognized line: {line}")
    if block:
        if "email" in block and "password" in block and "username" in block:
            credentials.append(block)
        else:
            print(f"Warning: Incomplete block skipped: {block}")
    return credentials

def login_twitter(driver, email, twitter_password, user):
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 80)
    
    try:
        print("\n🔑 Logging into Twitter...")
        email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        email_field.clear()
        email_field.send_keys(user)
        print("✅ Entered email/username.")
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]")))
        next_btn.click()
        print("✅ Clicked 'Next'.")
        time.sleep(3)

        try:
            phone_or_username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']")))
            phone_or_username_field.clear()
            phone_or_username_field.send_keys(email)
            print(f"✅ Re-entered email on verification page: {email}")
            next_button_2 = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]")))
            next_button_2.click()
            print("✅ Submitted phone/email verification.")
        except TimeoutException:
            print("✅ No additional verification prompt detected, continuing...")

        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']")))
        password_field.clear()
        password_field.send_keys(twitter_password)
        print("✅ Entered password.")
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Log in')]")))
        login_btn.click()
        print("🎉 Login submitted!")
        time.sleep(5)
      
        try:
            otp_prompt = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Check your email')]")))
            print("📧 Email OTP prompt detected. Fetching OTP from Gmail...")
            otp = get_latest_otp_imap()
            if otp:
                otp_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")))
                otp_field.clear()
                otp_field.send_keys(otp)
                print("✅ Entered OTP into confirmation code input.")
                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]")))
                submit_btn.click()
                print("✅ OTP submitted, continuing login flow.")
                time.sleep(5)
            else:
                print("❌ OTP was not retrieved from Gmail.")
        except TimeoutException:
            print("✅ No email OTP prompt detected; continuing normally.")

    except Exception as e:
        print(f"❌ Error during login flow: {e}")

def get_latest_otp_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, 'UNSEEN', 'X-GM-RAW', '"newer_than:2m (confirmation code OR We noticed an attempt to log in OR \'one-time\')"')
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
        
        print("----- RAW EMAIL BODY START -----")
        print(body[:500])
        print("----- RAW EMAIL BODY END -----")
        
        otp_match = re.search(r"by entering the following single-use code\.\s*([a-zA-Z0-9]{6,12})", body)
        if not otp_match:
            otp_match = re.search(r"\b([a-zA-Z0-9]{6,12})\b", body)

        if otp_match:
            otp = otp_match.group(1).strip()
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
        locked_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Your account has been locked')]")))
        print("⚠️ Locked account detected, proceeding with verification flow.")
    except TimeoutException:
        print("✅ No locked account message found; skipping locked account flow.")
        return True

    try:
        start_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'EdgeButton--primary') or contains(text(), 'Start') or contains(@value, 'Start')]")))
        start_btn.click()
        print("✅ Clicked 'Start' button.")
    except TimeoutException:
        print("❌ 'Start' button not found; cannot proceed with locked account flow.")
        return False

    try:
        send_email_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Send email']")))
        send_email_btn.click()
        print("✅ Clicked 'Send email' button.")
    except TimeoutException:
        print("❌ 'Send email' button not found.")
        return False

    time.sleep(10)
    otp = get_locked_otp(timeout=60, poll_interval=5, subject_filter="Confirm your email address")
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
    except TimeoutException:
        print("❌ OTP token input field not found.")
        return False

    try:
        captcha_xpath = "//iframe[@id='arkose_iframe']"
        captcha_wait = WebDriverWait(driver, 5)
        captcha_element = captcha_wait.until(EC.presence_of_element_located((By.XPATH, captcha_xpath)))
        if captcha_element:
            print("⚠️ Captcha challenge detected! Please solve it manually or use an automated service.")
            wait.until(EC.invisibility_of_element_located((By.XPATH, captcha_xpath)))
            print("✅ Captcha challenge solved.")
    except TimeoutException:
        print("✅ No captcha challenge detected, proceeding.")

    try:
        time.sleep(5)
        continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@class, 'EdgeButton--primary') and @value='Continue to X']")))
        continue_btn.click()
        print("✅ Clicked 'Continue to X' button.")
    except TimeoutException:
        print("❌ 'Continue to X' button not found.")
        return False

    print("✅ Proceeding to the next step after verification.")
    return True

def get_locked_otp(timeout=60, poll_interval=5, subject_filter="Confirm your email address"):
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            mail.select("inbox")
            status, data = mail.search(None, 'UNSEEN', f'SUBJECT "{subject_filter}"')
            if status != "OK":
                print("❌ IMAP search failed in get_locked_otp.")
                mail.logout()
                time.sleep(poll_interval)
                continue
                
            email_ids = data[0].split()
            if not email_ids:
                print(f"⏳ No matching emails found, checking again in {poll_interval} seconds...")
                mail.logout()
                time.sleep(poll_interval)
                continue
                
            for e_id in sorted(email_ids, reverse=True):
                status, msg_data = mail.fetch(e_id, "(RFC822)")
                if status != "OK":
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain" and part.get('Content-Disposition') is None:
                                    body += part.get_payload(decode=True).decode(errors="ignore")
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                            
                        print("----- LOCKED ACCOUNT EMAIL BODY START -----")
                        print(body[:500])
                        print("----- LOCKED ACCOUNT EMAIL BODY END -----")
                        otp_match = re.search(r"\b(\d{6})\b", body)
                        if otp_match:
                            otp = otp_match.group(1).strip()
                            print(f"✅ Locked Account OTP Found: {otp}")
                            mail.store(e_id, '+FLAGS', '\\Deleted')
                            mail.expunge()
                            mail.logout()
                            return otp
            
            mail.logout()
            print("⏳ No OTP found in current emails, checking again...")
            time.sleep(poll_interval)
            
        except Exception as e:
            print(f"❌ Error in get_locked_otp: {e}")
            time.sleep(poll_interval)
            
    print("❌ Timeout: No OTP found for locked account verification.")
    return None

def update_profile_info(driver):
    try:
        driver.get("https://twitter.com/settings/profile")
        wait = WebDriverWait(driver, 30)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        banner_click_area = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Add banner photo' or @aria-label='Edit banner photo']")))
        banner_click_area.click()
        print("✅ Clicked on banner area to open upload modal.")
        time.sleep(2)

        banner_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        banner_input.send_keys(random.choice(banner_path))
        print("✅ Banner file sent to the input element.")
        time.sleep(5)

        try:
            apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Apply']")))
            apply_btn.click()
            print("✅ Clicked 'Apply' button for banner.")
            time.sleep(3)
        except TimeoutException:
            print("⚠️ No 'Apply' button found, continuing.")

        try:
            bio_input = wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@name='description']")))
            bio_text = random.choice(bio_messages)
            bio_text_json = json.dumps(bio_text)
            driver.execute_script(f"""
                arguments[0].value = {bio_text_json};
                arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
            """, bio_input)
            print("✅ Added bio to profile using JavaScript with JSON encoding.")
        except Exception as e:
            print(f"❌ Error adding bio: {e}")
            return False

        try:
            location_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='location']")))
            location_input.clear()
            location_input.send_keys("Frankfurt, Germany")
            print("✅ Added location to profile.")
        except Exception as e:
            print(f"❌ Error adding location: {e}")
            return False

        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='Profile_Save_Button']")))
        save_btn.click()
        print("✅ Saved profile changes.")
        time.sleep(5)
        return True

    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        return False

if __name__ == "__main__":
    creds = read_credentials("comp-cred.txt")
    total_accounts = len(creds)
    print(f"📋 Found {total_accounts} credential sets.")

    account_count = 0
    with open("completed.txt", "a") as completed_file:
        for cred in creds:
            account_count += 1
            user_email = cred.get("email")
            twitter_password = cred.get("password")
            user = cred.get("username")
            print(f"\n🚀 Processing account {account_count} of {total_accounts}: {user_email} | {user}")

            driver = setup_driver()
            driver.get("https://twitter.com/login")
            time.sleep(5)

            try:
                test_proxy()
                check_browser_ip(driver)
                login_twitter(driver, user_email, twitter_password, user)
                if handle_locked_account(driver):
                    if update_profile_info(driver):
                        completed_file.write(f"Email: {user_email}\n")
                        completed_file.write(f"Password: {twitter_password}\n")
                        completed_file.write(f"Username: {user}\n")
                        completed_file.write(f"{'-' * 40}\n")
                        print(f"✅ Successfully processed and recorded account: {user_email}")
                    else:
                        print(f"❌ Failed to update profile for account: {user_email}")
                else:
                    print(f"❌ Skipping posting and profile update due to locked account flow failure: {user_email}")

            except Exception as e:
                print(f"❌ Error processing account {account_count} ({user_email}): {e}")

            finally:
                driver.quit()
                print(f"🛑 Closed browser for account {account_count}: {user_email}")
                time.sleep(5)

    print("🎉 All accounts processed.")