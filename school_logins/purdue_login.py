from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from iclicker_signin import navigate_to_university_selection

def purdue_login(driver, username, password):
    """Handle Purdue login flow up to getting access code (before class selection)
    
    Args:
        driver: Selenium WebDriver instance
        username (str): Login username
        password (str): Login password
        
    Returns:
        str: Access code if successful, None if failed
    """
    try:
        # First, navigate to university selection and select Purdue
        print("🏫 UNIVERSITY SELECTION")
        if not navigate_to_university_selection(driver, "Purdue University West Lafayette/Indianapolis"):
            print("❌ Failed to navigate to university selection")
            return None
        
        wait = WebDriverWait(driver, 10)
        
        print("\n🔐 PURDUE LOGIN")
        print("Looking for username field...")
        username_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/main/section/div/div/div/div/div/div/form/fieldset/div[1]/input"))
        )
        
        print("Looking for password field...")
        password_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/main/section/div/div/div/div/div/div/form/fieldset/div[2]/input"))
        )
        
        print("Entering username...")
        username_field.send_keys(username)
        
        print("Entering password...")
        password_field.send_keys(password)
        
        print("Looking for login button...")
        login_button = wait.until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/main/section/div/div/div/div/div/div/form/fieldset/div[3]/button[2]"))
        )
        
        print("Scrolling to login button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(1)
        
        print("Clicking login button...")
        driver.execute_script("arguments[0].click();", login_button)
        
        print("Waiting for page to load...")
        time.sleep(5)
        
    
        
        print("Looking for access code...")
        access_code_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[1]/div/div[2]/div[3]"))
        )
        
        access_code = access_code_element.text
        print(f"\n🎉 Access Code: {access_code}")
        
        # Wait for user confirmation before continuing to class selection
        while True:
            user_input = input("\nType 'y' to continue to class selection: ").strip().lower()
            if user_input == 'y':
                break
            print("Please type 'y' to continue...")
        
        print("Proceeding to class selection...")

        time.sleep(10)
        
        return access_code
        
    except Exception as e:
        print(f"❌ Error in Purdue login: {e}")
        return None