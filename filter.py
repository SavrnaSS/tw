from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
import os
from webdriver_manager.chrome import ChromeDriverManager

def parse_credentials(file_path):
    """Parse the comp-cred.txt file into a list of account dictionaries."""
    accounts = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    current_account = {}
    for line in lines:
        line = line.strip()
        if line.startswith('---'):
            if current_account:
                accounts.append(current_account)
                current_account = {}
        elif line:
            key, value = line.split(':', 1)
            current_account[key.strip()] = value.strip()
    if current_account:
        accounts.append(current_account)
    return accounts

def main():
    # Parse accounts from comp-cred.txt
    accounts = parse_credentials('comp-cred.txt')
    print(f"Found {len(accounts)} accounts to check.")

    # Set up Selenium with headed Chrome (visible UI)
    options = Options()
    # Removed --headless to run in headed mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    restricted_accounts = []

    # Check each account
    for account in accounts:
        username = account['Username']
        print(f"Checking account: {username}")
        try:
            # Visit the Twitter profile
            driver.get(f"https://twitter.com/{username}")
            wait = WebDriverWait(driver, 20)  # Wait up to 20 seconds for page load
            try:
                # Look for the restriction message using data-testid
                wait.until(EC.text_to_be_present_in_element(
                    (By.XPATH, "//div[@data-testid='empty_state_header_text']"),
                    "Caution: This account is temporarily restricted"
                ))
                print(f"Account {username} is restricted.")
                restricted_accounts.append(account)
            except TimeoutException:
                print(f"No restriction message found for {username}")
        except Exception as e:
            print(f"Error checking account {username}: {e}")

        # Random delay between 5-10 seconds to avoid rate limiting
        time.sleep(random.uniform(5, 10))

    # Clean up
    driver.quit()

    # Save restricted accounts to restricted.txt
    with open('restricted.txt', 'w') as f:
        for account in restricted_accounts:
            f.write(f"Email: {account['Email']}\n")
            f.write(f"Password: {account['Password']}\n")
            f.write(f"Username: {account['Username']}\n")
            f.write("-" * 40 + "\n")

    print("Finished checking all accounts.")

if __name__ == "__main__":
    main()