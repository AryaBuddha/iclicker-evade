"""Question monitoring and interaction for iClicker sessions.

This module provides the QuestionMonitor class which handles real-time
detection of iClicker questions, screenshot capture, user interaction,
and automated answer submission.
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from notifications.email_service import EmailNotificationService
from ai_services.base_ai_service import BaseAIService, AIAnswerSuggestion

if TYPE_CHECKING:
    from config.settings import AppConfig


class QuestionMonitor:
    """Monitors iClicker sessions for questions and handles user responses."""

    QUESTION_XPATH = "/html/body/app-root/ng-component/div/ng-component/app-poll/main/div/app-multiple-choice-question/div[3]"
    SELECTED_BUTTON_SELECTOR = "button.btn-selected"
    VALID_ANSWERS = ['A', 'B', 'C', 'D', 'E']

    def __init__(
        self,
        driver: WebDriver,
        config: 'AppConfig',
        email_service: Optional[EmailNotificationService] = None,
        ai_service: Optional[BaseAIService] = None,
        recipient_email: Optional[str] = None
    ) -> None:
        """Initialize the question monitor."""
        self.driver = driver
        self.config = config
        self.email_service = email_service
        self.ai_service = ai_service
        self._recipient_email = recipient_email

        self.polling_interval = config.polling_interval
        self.questions_dir = "questions"
        self.question_xpath = self.QUESTION_XPATH
        self.logger = logging.getLogger(__name__)

        self._current_question_text: Optional[str] = None
        self._question_active = False
        self._monitoring_active = False

        self._ensure_questions_directory()

    def start_monitoring(self) -> None:
        """Start continuous question monitoring."""
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
                self._check_for_questions()
                if not self._question_active:
                    self._display_monitoring_status(start_time, attempt, spinner_chars[spinner_index % len(spinner_chars)])
                    spinner_index += 1
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
        """Stop the question monitoring loop."""
        self._monitoring_active = False
        self.logger.info("Question monitoring stopped")

    def _check_for_questions(self) -> None:
        """Check for questions and process them if found."""
        try:
            question_element = self.driver.find_element(By.XPATH, self.question_xpath)
            if not question_element.is_displayed():
                self._handle_question_disappeared()
                return

            if self._is_question_answered():
                self._handle_already_answered_question()
                return

            question_text = self._extract_question_text(question_element)
            if self._is_new_question(question_text):
                asyncio.run(self._process_new_question(question_text))

        except NoSuchElementException:
            if self._question_active:
                self._handle_question_disappeared()
        except WebDriverException as e:
            self.logger.warning(f"WebDriver error while checking for questions: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error checking for questions: {e}")

    def _is_question_answered(self) -> bool:
        """Check if the current question has already been answered."""
        try:
            return len(self.driver.find_elements(By.CSS_SELECTOR, self.SELECTED_BUTTON_SELECTOR)) > 0
        except WebDriverException:
            return False

    def _extract_question_text(self, question_element) -> str:
        """Extract text content from a question element."""
        try:
            return question_element.text.strip()
        except Exception as e:
            self.logger.warning(f"Failed to extract question text: {e}")
            return "Question content not available"

    def _is_new_question(self, question_text: str) -> bool:
        """Determine if this is a new question."""
        return not self._question_active or question_text != self._current_question_text

    async def _process_new_question(self, question_text: str) -> None:
        """Process a newly detected question."""
        self._current_question_text = question_text
        self._question_active = True

        self.logger.info("New iClicker question detected")
        print("\n🚨 QUESTION DETECTED! 🚨")
        print("📋 An iClicker question has appeared on the page!")

        screenshot_path = self._capture_screenshot()

        ai_suggestion = None
        if self.ai_service and screenshot_path and self.config.ai_answer_enabled:
            ai_suggestion = await self._get_ai_suggestion(screenshot_path, question_text)

        if self.email_service and screenshot_path and self.config.email_enabled:
            self._send_email_notification(question_text, screenshot_path, ai_suggestion)

        print(f"❓ Question content:\n{question_text}")

        if ai_suggestion and self.config.ai_show_answer_in_console:
            self._display_ai_suggestion(ai_suggestion)

        answer_to_submit = None
        if ai_suggestion and self.config.ai_auto_answer:
            answer_to_submit = ai_suggestion.suggested_answer
            print(f"🤖 Auto-submitting AI answer: {answer_to_submit}")
        else:
            answer_to_submit = self._get_user_answer(ai_suggestion)

        if answer_to_submit:
            self._click_answer(answer_to_submit)

        print("🔄 Waiting for next question...\n")

    def _handle_question_disappeared(self) -> None:
        """Handle when a question is no longer visible."""
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
        """Capture a full-page screenshot."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.questions_dir, f"question_{timestamp}.png")

            # Full page screenshot logic
            original_size = self.driver.get_window_size()
            total_height = self.driver.execute_script("return document.body.parentNode.scrollHeight")
            self.driver.set_window_size(original_size['width'], total_height)
            time.sleep(0.5)
            self.driver.save_screenshot(screenshot_path)
            self.driver.set_window_size(original_size['width'], original_size['height'])

            print(f"📸 Full page screenshot saved: {screenshot_path}")
            self.logger.info(f"Screenshot captured: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            print(f"❌ Failed to save screenshot: {e}")
            return None

    async def _get_ai_suggestion(self, screenshot_path: str, question_text: str) -> Optional[AIAnswerSuggestion]:
        """Get AI suggestion for the question."""
        print("🤖 Getting AI answer suggestion...")
        try:
            suggestion = await self.ai_service.analyze_question(screenshot_path, question_text)
            print("✅ AI analysis completed")
            self.logger.info(f"AI suggested answer: {suggestion.suggested_answer} ({suggestion.confidence_percentage})")
            return suggestion
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            self.logger.error(f"AI analysis error: {e}")
            return None

    def _display_ai_suggestion(self, suggestion: AIAnswerSuggestion) -> None:
        """Display AI suggestion to the user."""
        print("\n🤖 AI SUGGESTION:")
        print(f"   Answer: {suggestion.suggested_answer}")
        print(f"   Confidence: {suggestion.confidence_percentage}")
        print(f"   Reasoning: {suggestion.reasoning}")
        print(f"   Model: {suggestion.model_used}")
        print(f"   Processing time: {suggestion.processing_time:.2f}s")

    def _send_email_notification(self, question_text: str, screenshot_path: str, ai_suggestion: Optional[AIAnswerSuggestion]) -> None:
        """Send email notification for a detected question."""
        if not (self.email_service and self._recipient_email):
            return

        print("📧 Sending email notification...")
        enhanced_question_text = question_text
        if ai_suggestion and self.config.ai_show_answer_in_notification:
            enhanced_question_text += (f"\n\n🤖 AI SUGGESTION:\n"
                                     f"Answer: {ai_suggestion.suggested_answer} ({ai_suggestion.confidence_percentage})\n"
                                     f"Reasoning: {ai_suggestion.reasoning}")
        try:
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

    def _get_user_answer(self, ai_suggestion: Optional[AIAnswerSuggestion]) -> Optional[str]:
        """Prompt user to select an answer choice."""
        prompt = "\n⚡ Select your answer (A-E): "
        if ai_suggestion:
            prompt = f"\n⚡ Select your answer (A-E) [AI suggests: {ai_suggestion.suggested_answer}]: "

        while True:
            try:
                user_input = input(prompt).strip().upper()
                if not user_input and ai_suggestion:
                    print(f"Using AI suggestion: {ai_suggestion.suggested_answer}")
                    return ai_suggestion.suggested_answer
                if user_input in self.VALID_ANSWERS:
                    return user_input
                elif not user_input:
                    print("❌ No answer provided. Please enter A, B, C, D, or E.")
                else:
                    print("❌ Invalid choice. Please enter A, B, C, D, or E.")
            except (KeyboardInterrupt, EOFError):
                print("\n🛑 Answer selection interrupted")
                self.logger.info("Answer selection interrupted by user")
                return None

    def _click_answer(self, answer: str) -> None:
        """Attempt to click the selected answer button."""
        print(f"🖱️  Attempting to click answer {answer}...")
        strategies = [
            f"//button[normalize-space()='{answer}']",
            f"//button[contains(text(), '{answer}') or contains(@aria-label, '{answer}')]",
            f"//button[contains(@class, 'answer-{answer.lower()}')]",
        ]
        for i, strategy_xpath in enumerate(strategies, 1):
            try:
                button = self.driver.find_element(By.XPATH, strategy_xpath)
                self.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", button)
                print(f"✅ Successfully clicked answer {answer}!")
                self.logger.info(f"Answer {answer} clicked using strategy {i}")
                return
            except Exception as e:
                self.logger.debug(f"Answer clicking strategy {i} failed: {e}")

        print(f"❌ Could not automatically click answer {answer}. Please click it manually.")
        self.logger.warning(f"Failed to click answer {answer} with all strategies")

    def _ensure_questions_directory(self) -> None:
        """Ensure the questions directory exists."""
        if not os.path.exists(self.questions_dir):
            os.makedirs(self.questions_dir)
            self.logger.info(f"Created questions directory: {self.questions_dir}")

    def _display_monitoring_status(self, start_time: float, attempt: int, spinner_char: str) -> None:
        """Display the current monitoring status."""
        elapsed = int(time.time() - start_time)
        print(f"\r{spinner_char} Monitoring for questions... (elapsed: {elapsed}s, attempt: {attempt})", end="", flush=True)