from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time

def setup_chrome_driver(headless=True):
    """Set up Chrome driver with WebAuthn disabled
    
    Args:
        headless (bool): Whether to run Chrome in headless mode. Default True.
    """
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-webauthn")
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "webauthn.virtual_authenticator_enabled": False
    })
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Add script to disable WebAuthn APIs before navigating
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": r"""
        (() => {
            // Hide WebAuthn so sites can't trigger the native passkey sheet
            try { Object.defineProperty(window, 'PublicKeyCredential', { value: undefined }); } catch(e) {}
            const shim = {
                get: () => Promise.reject(new DOMException('NotAllowedError', 'NotAllowedError')),
                create: () => Promise.reject(new DOMException('NotAllowedError', 'NotAllowedError')),
                preventSilentAccess: () => Promise.resolve(),
            };
            try { Object.defineProperty(navigator, 'credentials', { get() { return shim; } }); } catch(e) {}
        })();
        """
    })
    
    return driver

def navigate_to_university_selection(driver, university_name):
    """Navigate to iClicker and select university, then click continue"""
    try:
        print("Navigating to iClicker student login...")
        driver.get("https://student.iclicker.com/#/login")
        
        wait = WebDriverWait(driver, 10)
        
        print("Looking for initial button...")
        initial_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/div[2]/button"))
        )
        
        print("Clicking initial button...")
        initial_button.click()
        
        time.sleep(2)
        
        print("Looking for university dropdown...")
        dropdown = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/app-login/div[2]/main/div[4]/div[2]/div/select"))
        )
        
        print("Clicking dropdown...")
        select = Select(dropdown)
        
        print(f"Selecting {university_name}...")
        select.select_by_visible_text(university_name)
        
        print("Looking for continue button...")
        button = wait.until(
            EC.presence_of_element_located((By.XPATH, "/html/body/app-root/app-login/div[2]/main/div[4]/div[2]/div/button"))
        )
        
        print("Scrolling to button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(1)
        
        print("Clicking continue button...")
        driver.execute_script("arguments[0].click();", button)
        
        print("Waiting for login page to load...")
        time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"Error in university selection: {e}")
        return False