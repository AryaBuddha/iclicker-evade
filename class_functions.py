"""Class selection and session management utilities for iClicker automation.

This module provides functions for:
- Selecting classes from the iClicker interface
- Listing available classes
- Interactive class selection
- Waiting for class sessions to start
"""

from typing import List, Optional
import time
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

def select_class_by_name(driver: WebDriver, class_name: str) -> bool:
    """Select a class by its name on the class selection page.

    This function attempts multiple strategies to find and select a class:
    1. iClicker-specific structure search with exact matching
    2. iClicker-specific structure search with partial matching
    3. XPath pattern matching
    4. General element search fallbacks

    Args:
        driver: Selenium WebDriver instance
        class_name: Name of the class to select

    Returns:
        True if class was found and clicked, False otherwise

    Raises:
        Exception: Logs but does not raise exceptions for robustness
    """
    try:
        # Multiple strategies for robust class selection
        
        print(f"Looking for class: {class_name}")
        
        # Strategy 1: Use the specific iClicker class structure
        # /html/body/app-root/ng-component/div/app-courses/main/div/ul[1]/li[1]/a/label
        try:
            print("Strategy 1: Searching iClicker class list structure...")
            
            # Find all class labels in the iClicker structure
            class_labels = driver.find_elements(By.XPATH, "//app-courses/main/div/ul/li/a/label")
            
            for label in class_labels:
                label_text = label.text.strip()
                print(f"Found class: '{label_text}'")
                
                # Check for exact match
                if label_text == class_name:
                    print(f"✅ Exact match found: {class_name}")
                    parent_link = label.find_element(By.XPATH, "..")  # Get parent <a> element
                    driver.execute_script("arguments[0].scrollIntoView(true);", parent_link)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", parent_link)
                    return True
                
                # Check for partial match
                if class_name.lower() in label_text.lower() or label_text.lower() in class_name.lower():
                    print(f"✅ Partial match found: {label_text}")
                    parent_link = label.find_element(By.XPATH, "..")  # Get parent <a> element
                    driver.execute_script("arguments[0].scrollIntoView(true);", parent_link)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", parent_link)
                    return True
            
            print("Strategy 1: No matches found in iClicker structure")
            
        except Exception as e:
            print(f"Strategy 1 failed: {e}")
        
        # Strategy 2: Try the exact XPath pattern you provided
        try:
            print("Strategy 2: Trying exact XPath pattern...")
            
            # Look for labels containing the class name
            class_element = driver.find_element(By.XPATH, f"//app-courses/main/div/ul/li/a/label[contains(text(), '{class_name}')]")
            print(f"Found class element with text: {class_name}")
            
            # Click the parent <a> element
            parent_link = class_element.find_element(By.XPATH, "..")
            driver.execute_script("arguments[0].scrollIntoView(true);", parent_link)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", parent_link)
            return True
            
        except Exception as e:
            print(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Fallback to general label search
        try:
            print("Strategy 3: General label search...")
            
            labels = driver.find_elements(By.TAG_NAME, "label")
            for label in labels:
                label_text = label.text.strip()
                if class_name.lower() in label_text.lower():
                    print(f"Found matching label: {label_text}")
                    
                    # Try to find and click the parent link
                    try:
                        parent_link = label.find_element(By.XPATH, "..")
                        if parent_link.tag_name == "a":
                            driver.execute_script("arguments[0].scrollIntoView(true);", parent_link)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", parent_link)
                            return True
                    except:
                        # If parent isn't a link, click the label itself
                        driver.execute_script("arguments[0].scrollIntoView(true);", label)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", label)
                        return True
            
        except Exception as e:
            print(f"Strategy 3 failed: {e}")
        
        # Strategy 4: Legacy fallback strategies
        strategies = [
            ("buttons", f"//button[contains(text(), '{class_name}')]"),
            ("links", f"//a[contains(text(), '{class_name}')]"),
            ("any element", f"//*[contains(text(), '{class_name}')]")
        ]
        
        for strategy_name, xpath in strategies:
            try:
                print(f"Strategy 4.{len(strategies)}: Trying {strategy_name}...")
                element = driver.find_element(By.XPATH, xpath)
                print(f"Found {strategy_name}: {class_name}")
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", element)
                return True
            except:
                print(f"Strategy 4.{len(strategies)} ({strategy_name}) failed")
                
        print(f"❌ Could not find class: {class_name}")
        return False
        
    except Exception as e:
        print(f"Error in class selection: {e}")
        return False

def list_available_classes(driver: WebDriver) -> List[str]:
    """List all available classes on the current page.

    Scans the page using multiple strategies to find class names:
    1. iClicker-specific structure (primary)
    2. General element scanning (fallback)

    Args:
        driver: Selenium WebDriver instance

    Returns:
        List of class names found on the page (up to 10 displayed)

    Raises:
        Exception: Logs but does not raise exceptions, returns empty list on failure
    """
    try:
        # Scan for available classes using multiple strategies
        
        print("Scanning for available classes...")
        classes = []
        
        # Strategy 1: Use the specific iClicker class structure
        try:
            print("Scanning iClicker class list structure...")
            class_labels = driver.find_elements(By.XPATH, "//app-courses/main/div/ul/li/a/label")
            
            for label in class_labels:
                text = label.text.strip()
                if text and len(text) > 1:  # Filter out empty or very short labels
                    classes.append(text)
                    print(f"  Found: {text}")
                    
        except Exception as e:
            print(f"iClicker structure scan failed: {e}")
        
        # Strategy 2: Fallback to general scanning if iClicker structure not found
        if not classes:
            print("Fallback: Scanning for general elements...")
            
            # Look for labels that might contain class names
            try:
                labels = driver.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    text = label.text.strip()
                    if text and len(text) > 3:  # Filter out empty or very short labels
                        classes.append(text)
            except:
                pass
            
            # Look for links that might contain class names
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    text = link.text.strip()
                    if text and len(text) > 3:  # Filter out empty or very short links
                        classes.append(text)
            except:
                pass
            
            # Look for buttons that might contain class names
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    text = button.text.strip()
                    if text and len(text) > 3:  # Filter out empty or very short buttons
                        classes.append(text)
            except:
                pass
        
        # Remove duplicates and return
        unique_classes = list(dict.fromkeys(classes))  # Preserves order while removing duplicates
        
        if unique_classes:
            print("\nAvailable classes found:")
            for i, class_name in enumerate(unique_classes[:10], 1):  # Show first 10
                print(f"  {i}. {class_name}")
            if len(unique_classes) > 10:
                print(f"  ... and {len(unique_classes) - 10} more")
        else:
            print("No classes found on current page")
            
        return unique_classes
        
    except Exception as e:
        print(f"Error listing classes: {e}")
        return []

def select_class_interactive(driver: WebDriver) -> bool:
    """Interactive class selection with user input.

    Shows available classes and allows the user to select by:
    - Number (index in the list)
    - Name (exact or partial match)

    Args:
        driver: Selenium WebDriver instance

    Returns:
        True if a class was successfully selected, False otherwise

    Raises:
        Exception: Logs but does not raise exceptions for robustness
    """
    try:
        # List available classes
        classes = list_available_classes(driver)
        
        if not classes:
            print("No classes found for interactive selection")
            return False
        
        # Let user choose
        print("\nEnter the name or number of the class you want to select:")
        print("(You can enter partial text - we'll find the best match)")
        
        user_input = input("Class name/number: ").strip()
        
        # Try to match by number first
        try:
            class_index = int(user_input) - 1
            if 0 <= class_index < len(classes):
                selected_class = classes[class_index]
                print(f"Selected class by number: {selected_class}")
                return select_class_by_name(driver, selected_class)
        except ValueError:
            pass
        
        # Try to match by name (partial match)
        for class_name in classes:
            if user_input.lower() in class_name.lower():
                print(f"Found matching class: {class_name}")
                return select_class_by_name(driver, class_name)
        
        # Direct attempt with user input
        print(f"No match found, trying direct selection with: {user_input}")
        return select_class_by_name(driver, user_input)
        
    except Exception as e:
        print(f"Error in interactive class selection: {e}")
        return False

def wait_for_button(driver: WebDriver, polling_interval: int = 5) -> bool:
    """Wait for instructor to start class and automatically click join button.

    Continuously polls the page looking for "Your instructor started class." text.
    Once found, locates and clicks the join button. Displays a spinning progress
    indicator during polling.

    Args:
        driver: Selenium WebDriver instance
        polling_interval: Seconds to wait between checks (default: 5)

    Returns:
        True if class started and button was clicked successfully

    Note:
        This function runs indefinitely until the class starts or the process
        is manually interrupted (Ctrl+C).
    """
    button_xpath = "/html/body/app-root/ng-component/div/app-course/div/div/div[2]/button"
    class_started_text = "Your instructor started class."

    print(f"Waiting for class to start (polling every {polling_interval} seconds)")
    print(f"Looking for text: '{class_started_text}'")

    start_time = time.time()
    attempt = 1
    spinner_chars = "|/-\\"
    spinner_index = 0

    while True:
        # Update spinner and elapsed time on same line
        elapsed = int(time.time() - start_time)
        spinner = spinner_chars[spinner_index % len(spinner_chars)]
        print(f"\r{spinner} Checking if instructor started class... (elapsed: {elapsed}s, attempt: {attempt})", end="", flush=True)

        try:
            # First check if the "Your instructor started class." text is visible on the page
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if class_started_text in page_text:
                print("\n✅ Instructor started class! Looking for join button...")

                # Now look for the button
                try:
                    button = driver.find_element(By.XPATH, button_xpath)
                    print("✅ Join button found!")
                    print("🖱️  Clicking join button...")
                    driver.execute_script("arguments[0].click();", button)
                    print("✅ Join button clicked successfully!")
                    return True
                except Exception as e:
                    print(f"\n❌ Button found but couldn't click: {e}")
                    print("Continuing to check...")
                    # Continue polling in case button becomes clickable

        except Exception as e:
            # Don't print errors every time, just continue silently
            pass

        time.sleep(polling_interval)
        attempt += 1
        spinner_index += 1

def send_question_email(screenshot_path: str, question_text: str, sender_email: str, sender_password: str, recipient_email: str) -> bool:
    """Send an email with the question screenshot attached.

    Args:
        screenshot_path: Path to the screenshot file
        question_text: Text content of the question
        sender_email: Gmail address to send from
        sender_password: App password for the Gmail account
        recipient_email: Email address to send to

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"iClicker Question Alert - {datetime.now().strftime('%H:%M:%S')}"

        # Create email body
        body = f"""
🚨 iClicker Question Detected! 🚨

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Question Content:
{question_text}

Please see the attached screenshot for the complete question and answer options.

---
Sent automatically by iClicker Evade
        """.strip()

        msg.attach(MIMEText(body, 'plain'))

        # Attach screenshot
        if os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-Disposition', f'attachment; filename={os.path.basename(screenshot_path)}')
                msg.attach(image)

        # Send email via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def monitor_for_questions(driver: WebDriver, polling_interval: int = 5, notification_email: Optional[str] = None,
                         sender_email: Optional[str] = None, sender_password: Optional[str] = None) -> None:
    """Monitor for iClicker questions and handle user responses.

    Continuously polls the page looking for question elements. When a question is detected:
    1. Displays the question only once
    2. Takes a screenshot and optionally emails it
    3. Prompts user to select an answer (A, B, C, D, E)
    4. Automatically clicks the selected answer button
    5. Waits for the next question

    Args:
        driver: Selenium WebDriver instance
        polling_interval: Seconds to wait between checks (default: 5)
        notification_email: Email address to send question screenshots to (optional)
        sender_email: Gmail address to send from (required if notification_email is set)
        sender_password: App password for Gmail account (required if notification_email is set)

    Note:
        This function runs indefinitely until manually interrupted (Ctrl+C).
        The question XPath monitored is: /html/body/app-root/ng-component/div/ng-component/app-poll/main/div/app-multiple-choice-question/div[3]
    """
    question_xpath = "/html/body/app-root/ng-component/div/ng-component/app-poll/main/div/app-multiple-choice-question/div[3]"


    print(f"\n🔍 Starting question monitoring (polling every {polling_interval} seconds)")
    print("Waiting for questions to appear...")

    start_time = time.time()
    attempt = 1
    spinner_chars = "|/-\\"
    spinner_index = 0
    current_question_text = None
    question_active = False

    while True:
        try:
            # Check if the question element is visible on the page
            question_element = driver.find_element(By.XPATH, question_xpath)
            if question_element.is_displayed():
                # Check if question has already been answered
                try:
                    selected_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn-selected")
                    if selected_buttons:
                        # Question already answered, skip processing
                        if question_active:
                            question_active = False
                            current_question_text = None
                            print("✅ Question already answered, waiting for next question...")
                        continue
                except:
                    pass  # Continue if we can't check for selected buttons

                # Get current question text to detect if it's a new question
                try:
                    question_text = question_element.text.strip()
                except:
                    question_text = "Question content not available"

                # Only process if this is a new question
                if not question_active or question_text != current_question_text:
                    current_question_text = question_text
                    question_active = True

                    print("\n🚨 QUESTION DETECTED! 🚨")
                    print("📋 An iClicker question has appeared on the page!")

                    # Take screenshot and save to questions folder
                    # Create questions folder if it doesn't exist
                    questions_dir = "questions"
                    if not os.path.exists(questions_dir):
                        os.makedirs(questions_dir)
                        print(f"📁 Created {questions_dir} folder")

                    # Generate unique filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_filename = f"question_{timestamp}.png"
                    screenshot_path = os.path.join(questions_dir, screenshot_filename)

                    try:
                        # Get current window size and total page height
                        original_size = driver.get_window_size()

                        # Get the total height of the page content
                        total_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")

                        # Set window size to capture full page height
                        driver.set_window_size(original_size['width'], total_height)

                        # Scroll to top to ensure we capture from the beginning
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(0.5)  # Brief pause for page to settle

                        # Take full page screenshot
                        driver.save_screenshot(screenshot_path)

                        # Restore original window size
                        driver.set_window_size(original_size['width'], original_size['height'])

                        print(f"📸 Full page screenshot saved: {screenshot_path}")

                    except Exception as e:
                        print(f"❌ Failed to save full page screenshot: {e}")
                        # Fallback to regular screenshot if full page fails
                        try:
                            fallback_path = screenshot_path.replace('.png', '_fallback.png')
                            driver.save_screenshot(fallback_path)
                            print(f"📸 Fallback screenshot saved: {fallback_path}")
                        except:
                            print("❌ Both full page and fallback screenshots failed")

                    # Send email notification if configured
                    if notification_email and sender_email and sender_password:
                        print("📧 Sending email notification...")
                        if send_question_email(screenshot_path, question_text, sender_email, sender_password, notification_email):
                            print(f"✅ Email sent to {notification_email}")
                        else:
                            print("❌ Email sending failed")

                    print(f"❓ Question content:\n{question_text}")

                    # Get user's answer choice
                    while True:
                        try:
                            user_choice = input("\n⚡ Select your answer (A, B, C, D, E): ").strip().upper()
                            if user_choice in ['A', 'B', 'C', 'D', 'E']:
                                break
                            else:
                                print("❌ Invalid choice. Please enter A, B, C, D, or E.")
                        except KeyboardInterrupt:
                            print("\n🛑 Question monitoring interrupted by user")
                            return

                    # Try to click the selected answer
                    print(f"🖱️  Attempting to click answer {user_choice}...")

                    clicked = False
                    # Try multiple strategies to find and click the answer button
                    strategies = [
                        # Strategy 1: Look for buttons with specific answer text
                        f"//button[contains(text(), '{user_choice}') or contains(@aria-label, '{user_choice}')]",
                        # Strategy 2: Look for elements with answer classes
                        f"//button[contains(@class, 'answer-{user_choice.lower()}')]",
                        f"//div[contains(@class, 'answer-{user_choice.lower()}')]//button",
                        # Strategy 3: Look for radio buttons or inputs
                        f"//input[@value='{user_choice}' or @aria-label='{user_choice}']",
                        # Strategy 4: Look for clickable elements with answer text
                        f"//*[contains(text(), '{user_choice}') and (self::button or self::div[@role='button'] or self::a)]"
                    ]

                    for i, strategy_xpath in enumerate(strategies, 1):
                        try:
                            answer_buttons = driver.find_elements(By.XPATH, strategy_xpath)
                            if answer_buttons:
                                # Try clicking the first matching button
                                button = answer_buttons[0]
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", button)
                                print(f"✅ Successfully clicked answer {user_choice}!")
                                clicked = True
                                break
                        except Exception as e:
                            print(f"Strategy {i} failed: {e}")
                            continue

                    if not clicked:
                        print(f"❌ Could not automatically click answer {user_choice}")
                        print("Please manually click the answer in your browser.")

                    print("🔄 Waiting for next question...\n")
            else:
                # Question is no longer visible, reset state
                if question_active:
                    question_active = False
                    current_question_text = None
                    print("📝 Question ended. Waiting for next question...")

        except Exception:
            # Question not found or not visible - continue monitoring
            if question_active:
                # Question disappeared, reset state
                question_active = False
                current_question_text = None

        # Only show spinner when no question is active
        if not question_active:
            elapsed = int(time.time() - start_time)
            spinner = spinner_chars[spinner_index % len(spinner_chars)]
            print(f"\r{spinner} Monitoring for questions... (elapsed: {elapsed}s, attempt: {attempt})", end="", flush=True)
            spinner_index += 1

        time.sleep(polling_interval)
        attempt += 1