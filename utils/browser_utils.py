"""Browser utility functions for iClicker Evade.

This module provides browser setup and management utilities,
particularly for Chrome WebDriver configuration.
"""

import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager


def setup_chrome_driver(headless: bool = True) -> WebDriver:
    """Set up and configure a Chrome WebDriver instance with iClicker-specific settings.

    Creates a Chrome WebDriver optimized for iClicker automation, including
    WebAuthn disabling and anti-detection measures.

    Args:
        headless: Whether to run Chrome in headless mode (no GUI)

    Returns:
        Configured Chrome WebDriver instance

    Raises:
        Exception: If WebDriver setup fails

    Example:
        >>> driver = setup_chrome_driver(headless=False)
        >>> driver.get("https://student.iclicker.com")
        >>> driver.quit()
    """
    logger = logging.getLogger(__name__)

    try:
        # Configure Chrome options for iClicker compatibility
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if headless:
            chrome_options.add_argument("--headless")

        # iClicker-specific options
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-webauthn")

        # Anti-detection measures
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Disable WebAuthn and credential management
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webauthn.virtual_authenticator_enabled": False
        })

        # Set window size for consistent screenshots
        chrome_options.add_argument("--window-size=1920,1080")

        # Automatically manage ChromeDriver installation
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception:
            # Fallback to system ChromeDriver if webdriver-manager fails
            logger.warning("ChromeDriverManager failed, using system ChromeDriver")
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

        # Set timeouts
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)

        logger.info(f"Chrome WebDriver initialized with iClicker settings (headless={headless})")
        return driver

    except Exception as e:
        logger.error(f"Failed to setup Chrome WebDriver: {e}")
        raise RuntimeError(f"WebDriver setup failed: {e}") from e


def safe_quit_driver(driver: WebDriver) -> None:
    """Safely quit a WebDriver instance.

    Attempts to close the browser gracefully, handling any exceptions
    that might occur during cleanup.

    Args:
        driver: WebDriver instance to quit
    """
    logger = logging.getLogger(__name__)

    try:
        if driver:
            driver.quit()
            logger.info("WebDriver closed successfully")
    except Exception as e:
        logger.warning(f"Error closing WebDriver: {e}")


def take_full_page_screenshot(driver: WebDriver, filepath: str) -> bool:
    """Take a full-page screenshot of the current page.

    Resizes the browser window to capture the entire page content,
    then restores the original window size.

    Args:
        driver: WebDriver instance
        filepath: Path where screenshot should be saved

    Returns:
        True if screenshot was successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        # Save current window size
        original_size = driver.get_window_size()

        # Calculate total page height
        total_height = driver.execute_script(
            "return Math.max("
            "document.body.scrollHeight, document.body.offsetHeight, "
            "document.documentElement.clientHeight, "
            "document.documentElement.scrollHeight, "
            "document.documentElement.offsetHeight"
            ");"
        )

        # Set window size to capture full page
        driver.set_window_size(original_size['width'], total_height)

        # Scroll to top
        driver.execute_script("window.scrollTo(0, 0);")

        # Take screenshot
        success = driver.save_screenshot(filepath)

        # Restore original window size
        driver.set_window_size(original_size['width'], original_size['height'])

        if success:
            logger.debug(f"Full page screenshot saved: {filepath}")
        else:
            logger.warning(f"Screenshot may have failed: {filepath}")

        return success

    except Exception as e:
        logger.error(f"Failed to take full page screenshot: {e}")
        return False