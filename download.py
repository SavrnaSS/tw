import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

def download_instagram_pictures(hashtag, num_pictures, username, password):
    """
    Downloads pictures from Instagram based on a hashtag using Selenium.
    """
    hashtag = hashtag.lstrip('#')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chromedriver_name = 'chromedriver'
    if os.name == 'nt':
        chromedriver_name += '.exe'
    chromedriver_path = os.path.join(script_dir, chromedriver_name)
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service)

    try:
        # Navigate to Instagram login page
        driver.get("https://www.instagram.com/accounts/login/")
        print("Logging in...")

        # Accept cookies if shown
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Allow')] | //button[contains(text(),'Accept')]"))
            )
            cookie_button.click()
            print("Accepted cookies.")
        except:
            pass

        # Enter username
        username_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.send_keys(username)

        # Enter password
        password_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)

        # Click login button
        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        print("Login button clicked...")

        # Handle post-login popups
        time.sleep(5)
        handle_popups(driver)
        time.sleep(2)
        handle_popups(driver)

        # Navigate to the hashtag page
        hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        driver.get(hashtag_url)
        print(f"Navigating to hashtag page: {hashtag_url}")
        time.sleep(10)

        # Wait for images to load
        print("Waiting for page content to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[starts-with(@href, '/p/')]//img"))
        )
        time.sleep(5)

        # Scroll and collect image URLs
        print(f"Collecting up to {num_pictures} image URLs...")
        image_urls = scroll_and_collect(driver, num_pictures)
        print(f"Collected {len(image_urls)} image URLs.")

        # Create a directory to save pictures
        save_dir = "profileselfie"
        os.makedirs(save_dir, exist_ok=True)
        print(f"Saving pictures to folder: {os.path.abspath(save_dir)}")

        if not image_urls:
            print("No images found to download.")
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved page source to 'page_source.html' for debugging.")
        else:
            print(f"Starting download of {len(image_urls)} pictures...")
            for index, url in enumerate(image_urls):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        file_path = os.path.join(save_dir, f"selfie_{index}.jpg")
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        print(f"Saved picture {index + 1}/{len(image_urls)} to {file_path}")
                    else:
                        print(f"Failed to download image {index + 1}: HTTP {response.status_code}")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error downloading image {index + 1}: {e}")

    finally:
        driver.quit()
        print("Browser closed.")

def handle_popups(driver):
    """Dismiss post-login popups like 'Not Now' or 'Save Info'."""
    try:
        popup_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now'] | //button[contains(text(),'Save Info')] | //button[contains(text(),'Turn On')]"))
        )
        popup_button.click()
        print("Dismissed a popup.")
    except:
        pass

def scroll_and_collect(driver, num_pictures):
    """Scroll the page to load posts and collect image URLs."""
    collected_urls = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    max_attempts = 15

    for attempt in range(max_attempts):
        images = driver.find_elements(By.XPATH, "//a[starts-with(@href, '/p/')]//img")
        print(f"Attempt {attempt + 1}: Found {len(images)} images on page.")

        for img in images:
            url = img.get_attribute("src")
            if url and url.startswith("https://") and url not in collected_urls:
                collected_urls.add(url)
                if len(collected_urls) >= num_pictures:
                    return list(collected_urls)[:num_pictures]

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("No more images loaded.")
            break
        last_height = new_height

    return list(collected_urls)[:num_pictures]

# Example usage
if __name__ == "__main__":
    username = "m4memeofficial"     
    password = "H926Xoajsisyaoshwuyduwuw"        
    hashtag = "#chilling"
    num_pictures = 200
    download_instagram_pictures(hashtag, num_pictures, username, password)
