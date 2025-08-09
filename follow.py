import time
import os
import random
import re
import imaplib
import email.utils
import email
import requests
from seleniumwire import webdriver  # Using Selenium Wire for proxy authentication
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import email as email_module
import pyttsx3
import json
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)

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

def notify_captcha():
    engine = pyttsx3.init()
    engine.say("2nd solve it!")
    engine.runAndWait()

# ---------------------------
# Gmail IMAP Config
# ---------------------------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")  # Must match DESTINATION_EMAIL
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Use an app password for Gmail
IMAP_SERVER = "imap.gmail.com"

# === PROXY CONFIGURATION ===
PROXY_HOST = "p.webshare.io"
PROXY_PORT = "80"
PROXY_USER = "nftiuvfu-rotate"
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
# Utility Functions
# ---------------------------
def human_delay(a=2, b=6):
    """Sleep for a random duration between a and b seconds to mimic human behavior."""
    time.sleep(random.uniform(a, b))

def read_credentials(file_path="1st_step.txt"):
    """
    Reads credentials from a file and returns a list of dictionaries.
    Expected format:
    
    Email: example@domain.com
    Password: somepassword
    Username: someusername
    ----------------------------------------
    """
    credentials = []
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
    return credentials

def login_twitter(driver, email, twitter_password, user):
    """
    Logs into Twitter and handles additional verification steps.
    If an OTP confirmation page is detected, the function fetches the OTP from Gmail,
    enters it into the confirmation code input (using data-testid="ocfEnterTextTextInput"),
    and proceeds.
    """
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 80)
    
    try:
        print("\n🔑 Logging into Twitter...")

        # 1. Fill email/username field
        email_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
        )
        email_field.clear()
        email_field.send_keys(user)
        print("✅ Entered email/username.")

        # 2. Click 'Next'
        next_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
        )
        next_btn.click()
        print("✅ Clicked 'Next'.")
        time.sleep(3)

        # 3. Check for additional verification prompt (phone/username)
        try:
            phone_or_username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']"))
            )
            phone_or_username_field.clear()
            phone_or_username_field.send_keys(user)
            print(f"✅ Re-entered username on verification page: {user}")

            next_button_2 = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
            )
            next_button_2.click()
            print("✅ Submitted phone/username verification.")
        except TimeoutException:
            print("✅ No additional verification prompt detected, continuing...")

        # 4. Enter password
        password_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']"))
        )
        password_field.clear()
        password_field.send_keys(twitter_password)
        print("✅ Entered password.")

        # 5. Click Log in
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Log in')]"))
        )
        login_btn.click()
        print("🎉 Login submitted!")
        time.sleep(5)
      
        # 6. Check if an OTP confirmation page is presented
        try:
            # Look for a message indicating that a confirmation code has been sent
            otp_prompt = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Check your email')]"))
            )
            print("📧 Email OTP prompt detected. Fetching OTP from Gmail...")
            otp = get_latest_otp_imap()
            if otp:
                # Locate the confirmation code input field using its data-testid
                otp_field = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")
                    )
                )
                otp_field.clear()
                otp_field.send_keys(otp)
                print("✅ Entered OTP into confirmation code input.")
                # Locate and click the Next button to submit the OTP
                submit_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
                )
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
        status, data = mail.search(
            None,
            'UNSEEN',
            'X-GM-RAW',
            '"newer_than:2m (confirmation code OR We noticed an attempt to log in OR \'one-time\')"'
        )
        if status != "OK":
            print("❌ IMAP search failed.")
            return None
        email_ids = data[0].split()
        if not email_ids:
            print("❌ No new OTP emails found via IMAP.")
            mail.logout()
            return None

        # Create a list to store (timestamp, email_id, message) tuples
        emails_with_dates = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email_module.message_from_bytes(response_part[1])
                    date_tuple = email_module.utils.parsedate_tz(msg["Date"])
                    if date_tuple:
                        timestamp = email_module.utils.mktime_tz(date_tuple)
                        emails_with_dates.append((timestamp, e_id, msg))
        if not emails_with_dates:
            mail.logout()
            return None

        # Sort the list by timestamp (latest first)
        emails_with_dates.sort(key=lambda x: x[0], reverse=True)
        latest_timestamp, latest_email_id, latest_msg = emails_with_dates[0]

        # Extract the OTP from the email body
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
        
        # Look for the phrase and capture the following code (6-12 alphanumeric characters)
        otp_match = re.search(
            r"by entering the following single-use code\.\s*([a-zA-Z0-9]{6,12})",
            body
        )

        if not otp_match:
            # Fallback: search for the first standalone 6-12 character alphanumeric code
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

def get_locked_otp(timeout=60, poll_interval=5, subject_filter="Confirm your email address"):
    """
    Get the OTP for a locked account, polling Gmail at intervals.
    This function is called by handle_locked_account.
    
    Args:
        timeout: Maximum time to wait for the OTP email, in seconds
        poll_interval: Time between email checks, in seconds
        subject_filter: Subject to filter OTP emails by
        
    Returns:
        The OTP if found, or None if not found within the timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            mail.select("inbox")
            
            # Search for unread emails with the specified subject
            status, data = mail.search(
                None,
                'UNSEEN',
                f'SUBJECT "{subject_filter}"'
            )
            
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
                
            # Process the most recent email first
            for e_id in sorted(email_ids, reverse=True):
                status, msg_data = mail.fetch(e_id, "(RFC822)")
                if status != "OK":
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email_module.message_from_bytes(response_part[1])
                        body = ""
                        
                        # Extract the body
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain" and part.get('Content-Disposition') is None:
                                    body += part.get_payload(decode=True).decode(errors="ignore")
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                            
                        print("----- LOCKED ACCOUNT EMAIL BODY START -----")
                        print(body[:500])
                        print("----- LOCKED ACCOUNT EMAIL BODY END -----")
                        
                        # Find the confirmation code (most likely a 6-digit number)
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
    
if __name__ == "__main__":
    creds = read_credentials("comp-cred.txt")
    total_accounts = len(creds)
    print(f"📋 Found {total_accounts} credential sets.")

    account_count = 0  # Initialize the counter

    # Open the completed.txt file in append mode
    with open("comp-cred.txt", "a") as completed_file:
        for cred in creds:
            account_count += 1  # Increment the counter
            user_email = cred.get("email")
            twitter_password = cred.get("password")
            user = cred.get("username")
            print(f"\n🚀 Processing account {account_count} of {total_accounts}: {user_email} | {user}")

            # Setup a new WebDriver instance for each account
            driver = setup_driver()
            driver.get("https://twitter.com/login")
            time.sleep(5)  # Allow time for the page to load

            try:
                test_proxy()
                check_browser_ip(driver)
                login_twitter(driver, user_email, twitter_password, user)
                follow_accounts(driver)
            except Exception as e:
                print(f"❌ Error processing account {account_count} ({user_email}): {e}")

            finally:
                driver.quit()  # Close the browser instance
                print(f"🛑 Closed browser for account {account_count}: {user_email}")
                time.sleep(5)  # Pause before processing the next account

    print("🎉 All accounts processed.")