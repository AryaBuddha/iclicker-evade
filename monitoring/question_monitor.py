"""Question monitoring and interaction for iClicker sessions.

This module provides the QuestionMonitor class which handles real-time
detection of iClicker questions, screenshot capture, user interaction,
and automated answer submission.
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Optional
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from notifications.email_service import EmailNotificationService
from ai_services.base_ai_service import BaseAIService, AIAnswerSuggestion


class QuestionMonitor:
    """Monitors iClicker sessions for questions and handles user responses.

    This class provides comprehensive question monitoring including:
    - Real-time question detection using DOM monitoring
    - Full-page screenshot capture with timestamp naming
    - Email notifications when questions appear
    - User-guided answer selection with validation
    - Automatic answer button clicking with multiple fallback strategies
    - Smart detection of already-answered questions

    Attributes:
        driver (WebDriver): Selenium WebDriver instance for browser control
        polling_interval (int): Seconds between monitoring checks
        email_service (Optional[EmailNotificationService]): Email notification service
        ai_service (Optional[BaseAIService]): AI service for answer suggestions
        questions_dir (str): Directory path for saving screenshots
        question_xpath (str): XPath for detecting question elements
        logger (logging.Logger): Logger instance for this monitor
    """

    # XPath for detecting iClicker questions in the DOM
    QUESTION_XPATH = "/html/body/app-root/ng-component/div/ng-component/app-poll/main/div/app-multiple-choice-question/div[3]"

    # CSS selector for detecting already-selected answer buttons
    SELECTED_BUTTON_SELECTOR = "button.btn-selected"

    # Valid answer choices for iClicker questions
    VALID_ANSWERS = ['A', 'B', 'C', 'D', 'E']

    def __init__(
        self,
        driver: WebDriver,
        polling_interval: int = 5,
        email_service: Optional[EmailNotificationService] = None,
        ai_service: Optional[BaseAIService] = None,
        recipient_email: Optional[str] = None
    ) -> None:
        """Initialize the question monitor.

        Args:
            driver: Selenium WebDriver instance for browser interaction
            polling_interval: Seconds to wait between monitoring checks
            email_service: Optional email service for notifications
            ai_service: Optional AI service for answer suggestions
            recipient_email: Email address to send notifications to

        Raises:
            ValueError: If polling_interval is less than 1 second
        """
        if polling_interval < 1:
            raise ValueError("Polling interval must be at least 1 second")

        self.driver = driver
        self.polling_interval = polling_interval
        self.email_service = email_service
        self.ai_service = ai_service
        self._recipient_email = recipient_email
        self.questions_dir = "questions"
        self.question_xpath = self.QUESTION_XPATH

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Internal state tracking
        self._current_question_text: Optional[str] = None
        self._question_active = False
        self._monitoring_active = False

        # Create questions directory if needed
        self._ensure_questions_directory()

    def start_monitoring(self) -> None:
        """Start continuous question monitoring.

        Begins the main monitoring loop which polls for questions at the
        specified interval. Continues until manually interrupted or an
        unrecoverable error occurs.

        The monitoring process:
        1. Checks for question elements in the DOM
        2. Detects if questions are already answered
        3. Takes screenshots and sends notifications for new questions
        4. Prompts user for answer selection
        5. Automatically clicks the selected answer
        6. Continues monitoring for subsequent questions

        Raises:
            KeyboardInterrupt: When monitoring is manually interrupted
        """
        self._monitoring_active = True
        self.logger.info(f"Starting question monitoring (polling every {self.polling_interval}s)")
        print(f"\n🔍 Starting question monitoring (polling every {self.polling_interval} seconds)")
        print("Waiting for questions to appear...")

        start_time = time.time()
        attempt = 1
        spinner_chars = "|/-\\"
        spinner_index = 0

        try:
            while self._monitoring_active:
                # Check for questions and handle them
                self._check_for_questions()

                # Show spinner when no question is active
                if not self._question_active:
                    self._display_monitoring_status(start_time, attempt, spinner_chars[spinner_index % len(spinner_chars)])
                    spinner_index += 1

                # Wait before next check
                time.sleep(self.polling_interval)
                attempt += 1

        except KeyboardInterrupt:
            self.logger.info("Question monitoring interrupted by user")
            print("\n🛑 Question monitoring interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in question monitoring: {e}")
            print(f"\n❌ Unexpected error in monitoring: {e}")
            raise
        finally:
            self._monitoring_active = False

    def stop_monitoring(self) -> None:
        """Stop the question monitoring loop.

        Gracefully stops the monitoring process. Can be called from
        another thread to stop monitoring.
        """
        self._monitoring_active = False
        self.logger.info("Question monitoring stopped")

    def _check_for_questions(self) -> None:
        """Check for questions and process them if found.

        This method handles the core question detection and processing logic:
        1. Looks for question elements in the DOM
        2. Checks if questions are already answered
        3. Processes new questions with screenshots and user interaction
        """
        try:
            # Look for question element
            question_element = self.driver.find_element(By.XPATH, self.question_xpath)

            if not question_element.is_displayed():
                self._handle_question_disappeared()
                return

            # Check if question is already answered
            if self._is_question_answered():
                self._handle_already_answered_question()
                return

            # Extract question text
            question_text = self._extract_question_text(question_element)

            # Check if this is a new question
            if self._is_new_question(question_text):
                self._process_new_question(question_text)

        except NoSuchElementException:
            # No question element found - reset state if needed
            if self._question_active:
                self._handle_question_disappeared()
        except WebDriverException as e:
            self.logger.warning(f"WebDriver error while checking for questions: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error checking for questions: {e}")

    def _is_question_answered(self) -> bool:
        """Check if the current question has already been answered.

        Returns:
            True if a selected answer button is found, False otherwise
        """
        try:
            selected_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTED_BUTTON_SELECTOR)
            return len(selected_buttons) > 0
        except WebDriverException:
            return False

    def _extract_question_text(self, question_element) -> str:
        """Extract text content from a question element.

        Args:
            question_element: Selenium WebElement containing the question

        Returns:
            Extracted question text, or a default message if extraction fails
        """
        try:
            return question_element.text.strip()
        except Exception as e:
            self.logger.warning(f"Failed to extract question text: {e}")
            return "Question content not available"

    def _is_new_question(self, question_text: str) -> bool:
        """Determine if this is a new question that hasn't been processed.

        Args:
            question_text: Text content of the current question

        Returns:
            True if this is a new question, False if already processed
        """
        return not self._question_active or question_text != self._current_question_text

    def _process_new_question(self, question_text: str) -> None:
        """Process a newly detected question.

        Args:
            question_text: Text content of the question
        """
        self._current_question_text = question_text
        self._question_active = True

        self.logger.info("New iClicker question detected")
        print("\n🚨 QUESTION DETECTED! 🚨")
        print("📋 An iClicker question has appeared on the page!")

        # Take screenshot
        screenshot_path = self._capture_screenshot()

        # Get AI suggestion if enabled
        ai_suggestion = None
        if self.ai_service and screenshot_path:
            ai_suggestion = self._get_ai_suggestion(screenshot_path, question_text)

        # Send email notification if configured
        if self.email_service and screenshot_path:
            self._send_email_notification(question_text, screenshot_path, ai_suggestion)

        # Display question and AI suggestion
        print(f"❓ Question content:\n{question_text}")

        if ai_suggestion:
            self._display_ai_suggestion(ai_suggestion)

        # Get user input (with AI suggestion as context)
        user_answer = self._get_user_answer(ai_suggestion)

        # Attempt to click the selected answer
        if user_answer:
            self._click_answer(user_answer)

        print("🔄 Waiting for next question...\n")

    def _handle_question_disappeared(self) -> None:
        """Handle the case when a question is no longer visible."""
        if self._question_active:
            self._question_active = False
            self._current_question_text = None
            print("📝 Question ended. Waiting for next question...")

    def _handle_already_answered_question(self) -> None:
        """Handle questions that have already been answered."""
        if self._question_active:
            self._question_active = False
            self._current_question_text = None
            print("✅ Question already answered, waiting for next question...")

    def _capture_screenshot(self) -> Optional[str]:
        """Capture a full-page screenshot of the current question.

        Returns:
            Path to the saved screenshot file, or None if capture failed
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"question_{timestamp}.png"
            screenshot_path = os.path.join(self.questions_dir, screenshot_filename)

            # Save current window size
            original_size = self.driver.get_window_size()

            # Calculate total page height for full capture
            total_height = self.driver.execute_script(
                "return Math.max("
                "document.body.scrollHeight, document.body.offsetHeight, "
                "document.documentElement.clientHeight, "
                "document.documentElement.scrollHeight, "
                "document.documentElement.offsetHeight"
                ");"
            )

            # Resize window to capture full page
            self.driver.set_window_size(original_size['width'], total_height)

            # Scroll to top and take screenshot
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)  # Allow page to settle
            self.driver.save_screenshot(screenshot_path)

            # Restore original window size
            self.driver.set_window_size(original_size['width'], original_size['height'])

            print(f"📸 Full page screenshot saved: {screenshot_path}")
            self.logger.info(f"Screenshot captured: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            print(f"❌ Failed to save screenshot: {e}")

            # Try fallback regular screenshot
            try:
                fallback_path = screenshot_path.replace('.png', '_fallback.png')
                self.driver.save_screenshot(fallback_path)
                print(f"📸 Fallback screenshot saved: {fallback_path}")
                return fallback_path
            except Exception:
                print("❌ Both full page and fallback screenshots failed")
                return None

    def _get_ai_suggestion(self, screenshot_path: str, question_text: str) -> Optional[AIAnswerSuggestion]:
        """Get AI suggestion for the question.

        Args:
            screenshot_path: Path to the screenshot file
            question_text: Text content of the question

        Returns:
            AI suggestion or None if failed
        """
        print("🤖 Getting AI answer suggestion...")

        try:
            # Handle async AI analysis properly
            try:
                # Try to get existing event loop
                loop = asyncio.get_running_loop()
                # If we're already in an event loop, we can't use run_until_complete
                # So we'll need to run in a thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_ai_analysis_sync, screenshot_path, question_text)
                    suggestion = future.result(timeout=30)  # 30 second timeout
            except RuntimeError:
                # No event loop running, we can create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    suggestion = loop.run_until_complete(
                        self.ai_service.analyze_question(screenshot_path, question_text)
                    )
                finally:
                    loop.close()

            print("✅ AI analysis completed")
            self.logger.info(f"AI suggested answer: {suggestion.suggested_answer} ({suggestion.confidence_percentage})")
            return suggestion

        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            self.logger.error(f"AI analysis error: {e}")
            return None

    def _run_ai_analysis_sync(self, screenshot_path: str, question_text: str) -> AIAnswerSuggestion:
        """Run AI analysis in a synchronous manner for thread pool execution.

        Args:
            screenshot_path: Path to the screenshot file
            question_text: Text content of the question

        Returns:
            AI suggestion
        """
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.ai_service.analyze_question(screenshot_path, question_text)
            )
        finally:
            loop.close()

    def _display_ai_suggestion(self, suggestion: AIAnswerSuggestion) -> None:
        """Display AI suggestion to the user.

        Args:
            suggestion: AI answer suggestion to display
        """
        print("\n🤖 AI SUGGESTION:")
        print(f"   Answer: {suggestion.suggested_answer}")
        print(f"   Confidence: {suggestion.confidence_percentage}")
        print(f"   Reasoning: {suggestion.reasoning}")
        print(f"   Model: {suggestion.model_used}")
        print(f"   Processing time: {suggestion.processing_time:.2f}s")

    def _send_email_notification(self, question_text: str, screenshot_path: str, ai_suggestion: Optional[AIAnswerSuggestion] = None) -> None:
        """Send email notification for a detected question.

        Args:
            question_text: Text content of the question
            screenshot_path: Path to the screenshot file
            ai_suggestion: Optional AI suggestion to include
        """
        if not self.email_service:
            return

        print("📧 Sending email notification...")

        try:
            # Check if we have both email service and recipient configured
            if not self._recipient_email:
                self.logger.warning("No recipient email configured for notifications")
                return

            # Create enhanced question text with AI suggestion
            enhanced_question_text = question_text
            if ai_suggestion:
                enhanced_question_text += f"\n\n🤖 AI SUGGESTION:\nAnswer: {ai_suggestion.suggested_answer} ({ai_suggestion.confidence_percentage})\nReasoning: {ai_suggestion.reasoning}"

            success = self.email_service.send_question_alert(
                recipient_email=self._recipient_email,
                question_text=enhanced_question_text,
                screenshot_path=screenshot_path
            )

            if success:
                print("✅ Email notification sent successfully")
                self.logger.info("Email notification sent")
            else:
                print("❌ Email notification failed")
                self.logger.warning("Email notification failed")

        except Exception as e:
            print(f"❌ Email notification error: {e}")
            self.logger.error(f"Email notification error: {e}")

    def _get_user_answer(self, ai_suggestion: Optional[AIAnswerSuggestion] = None) -> Optional[str]:
        """Prompt user to select an answer choice.

        Args:
            ai_suggestion: Optional AI suggestion to show as default

        Returns:
            Selected answer choice (A-E) or None if interrupted
        """
        while True:
            try:
                # Create prompt with AI suggestion context
                if ai_suggestion:
                    prompt = f"\n⚡ Select your answer (A, B, C, D, E) [AI suggests: {ai_suggestion.suggested_answer}]: "
                else:
                    prompt = "\n⚡ Select your answer (A, B, C, D, E): "

                user_input = input(prompt).strip().upper()

                # If user just presses enter and we have an AI suggestion, use it
                if not user_input and ai_suggestion:
                    print(f"Using AI suggestion: {ai_suggestion.suggested_answer}")
                    return ai_suggestion.suggested_answer

                if user_input in self.VALID_ANSWERS:
                    return user_input
                elif not user_input:
                    print("❌ No answer provided. Please enter A, B, C, D, or E.")
                else:
                    print("❌ Invalid choice. Please enter A, B, C, D, or E.")

            except KeyboardInterrupt:
                print("\n🛑 Answer selection interrupted")
                self.logger.info("Answer selection interrupted by user")
                return None
            except EOFError:
                print("\n🛑 Input stream closed")
                return None

    def _click_answer(self, answer: str) -> None:
        """Attempt to click the selected answer button.

        Uses multiple strategies to locate and click the answer button,
        providing fallbacks if the primary method fails.

        Args:
            answer: The selected answer choice (A, B, C, D, E)
        """
        print(f"🖱️  Attempting to click answer {answer}...")

        # Multiple strategies for finding answer buttons
        strategies = [
            # Strategy 1: Look for buttons with specific answer text
            f"//button[contains(text(), '{answer}') or contains(@aria-label, '{answer}')]",
            # Strategy 2: Look for elements with answer classes
            f"//button[contains(@class, 'answer-{answer.lower()}')]",
            f"//div[contains(@class, 'answer-{answer.lower()}')]//button",
            # Strategy 3: Look for radio buttons or inputs
            f"//input[@value='{answer}' or @aria-label='{answer}']",
            # Strategy 4: Look for clickable elements with answer text
            f"//*[contains(text(), '{answer}') and (self::button or self::div[@role='button'] or self::a)]"
        ]

        for i, strategy_xpath in enumerate(strategies, 1):
            try:
                answer_buttons = self.driver.find_elements(By.XPATH, strategy_xpath)
                if answer_buttons:
                    button = answer_buttons[0]
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", button)

                    print(f"✅ Successfully clicked answer {answer}!")
                    self.logger.info(f"Answer {answer} clicked using strategy {i}")
                    return

            except Exception as e:
                self.logger.debug(f"Answer clicking strategy {i} failed: {e}")
                continue

        # If all strategies failed
        print(f"❌ Could not automatically click answer {answer}")
        print("Please manually click the answer in your browser.")
        self.logger.warning(f"Failed to click answer {answer} with all strategies")

    def _ensure_questions_directory(self) -> None:
        """Ensure the questions directory exists for screenshot storage."""
        if not os.path.exists(self.questions_dir):
            os.makedirs(self.questions_dir)
            self.logger.info(f"Created questions directory: {self.questions_dir}")

    def _display_monitoring_status(self, start_time: float, attempt: int, spinner_char: str) -> None:
        """Display the current monitoring status with spinner.

        Args:
            start_time: Time when monitoring started
            attempt: Current monitoring attempt number
            spinner_char: Character to display as spinner
        """
        elapsed = int(time.time() - start_time)
        print(f"\r{spinner_char} Monitoring for questions... (elapsed: {elapsed}s, attempt: {attempt})", end="", flush=True)