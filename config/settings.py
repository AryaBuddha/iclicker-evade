"""Configuration management for iClicker Evade.

This module handles loading and validation of application configuration
from environment variables and command-line arguments.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Literal
from dotenv import load_dotenv
import logging

AIProvider = Literal["openai", "gemini", "claude"]

@dataclass
class AppConfig:
    """Application configuration container.

    Holds all configuration values needed by the iClicker Evade application.
    Provides validation and easy access to settings.
    """

    # Required credentials
    iclicker_username: str
    iclicker_password: str

    # Optional settings
    class_name: Optional[str] = None
    headless: bool = True
    polling_interval: int = 5

    # Email notifications
    notification_email: Optional[str] = None
    gmail_sender_email: Optional[str] = None
    gmail_app_password: Optional[str] = None

    # AI answer suggestions
    ai_answer_enabled: bool = False
    ai_provider: AIProvider = "openai"
    ai_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

    # AI behavior flags
    ai_show_answer_in_console: bool = True
    ai_show_answer_in_notification: bool = True
    ai_auto_answer: bool = False

    # Application behavior
    debug_mode: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_required_fields()
        self._validate_email_config()
        self._validate_ai_config()
        self._validate_polling_interval()

    def _validate_required_fields(self) -> None:
        if not self.iclicker_username:
            raise ValueError("iClicker username is required")
        if not self.iclicker_password:
            raise ValueError("iClicker password is required")

    def _validate_email_config(self) -> None:
        if self.notification_email and not (self.gmail_sender_email and self.gmail_app_password):
            raise ValueError("GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD must be set for email notifications")

    def _validate_ai_config(self) -> None:
        if self.ai_answer_enabled:
            api_keys = {
                "openai": self.openai_api_key,
                "gemini": self.gemini_api_key,
                "claude": self.claude_api_key,
            }
            if not api_keys.get(self.ai_provider):
                raise ValueError(f"{self.ai_provider.upper()}_API_KEY must be set when AI answers are enabled with {self.ai_provider}")

    def _validate_polling_interval(self) -> None:
        if not 1 <= self.polling_interval <= 300:
            raise ValueError("Polling interval must be between 1 and 300 seconds")

    @property
    def email_enabled(self) -> bool:
        """Check if email notifications are properly configured."""
        return bool(self.notification_email and self.gmail_sender_email and self.gmail_app_password)

    @property
    def ai_enabled(self) -> bool:
        """Check if AI suggestions are properly configured for the selected provider."""
        if not self.ai_answer_enabled:
            return False

        provider_keys = {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "claude": self.claude_api_key,
        }
        return bool(provider_keys.get(self.ai_provider))

    @property
    def current_ai_api_key(self) -> Optional[str]:
        """Get the API key for the currently configured AI provider."""
        return {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "claude": self.claude_api_key,
        }.get(self.ai_provider)

    def log_config_summary(self) -> None:
        """Log a summary of the current configuration."""
        logger = logging.getLogger(__name__)
        logger.info("=== iClicker Evade Configuration ===")
        logger.info(f"Username: {self.iclicker_username}")
        logger.info(f"Class: {self.class_name or 'Interactive selection'}")
        logger.info(f"Browser mode: {'Headless' if self.headless else 'Visible'}")
        logger.info(f"Polling interval: {self.polling_interval} seconds")

        if self.email_enabled:
            masked_sender = self._mask_email(self.gmail_sender_email)
            masked_recipient = self._mask_email(self.notification_email)
            logger.info(f"Email notifications: {masked_recipient} (from {masked_sender})")
        else:
            logger.info("Email notifications: Disabled")

        if self.ai_enabled:
            logger.info(f"AI suggestions: Enabled (Provider: {self.ai_provider}, Model: {self.ai_model or 'default'})")
            logger.info(f"  - Show in console: {self.ai_show_answer_in_console}")
            logger.info(f"  - Show in notification: {self.ai_show_answer_in_notification}")
            logger.info(f"  - Auto answer: {self.ai_auto_answer}")
        else:
            logger.info("AI answer suggestions: Disabled")

        logger.info(f"Debug mode: {self.debug_mode}")

    def _mask_email(self, email: Optional[str]) -> str:
        if not email:
            return "None"
        try:
            local, domain = email.split('@', 1)
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else local
            return f"{masked_local}@{domain}"
        except ValueError:
            return "invalid@email.com"


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    pass


def load_config(
    headless: bool = True,
    class_name: Optional[str] = None,
    polling_interval: int = 5,
    notification_email: Optional[str] = None,
    ai_answer_enabled: bool = False,
    ai_provider: AIProvider = "openai",
    ai_model: Optional[str] = None,
    ai_show_console: bool = True,
    ai_show_notification: bool = True,
    ai_auto_answer: bool = False,
    debug_mode: bool = False
) -> AppConfig:
    """Load and validate application configuration."""
    load_dotenv()

    try:
        config = AppConfig(
            iclicker_username=os.getenv('ICLICKER_USERNAME') or "",
            iclicker_password=os.getenv('ICLICKER_PASSWORD') or "",
            class_name=class_name or os.getenv('ICLICKER_CLASS_NAME'),
            headless=headless,
            polling_interval=polling_interval,
            notification_email=notification_email,
            gmail_sender_email=os.getenv('GMAIL_SENDER_EMAIL'),
            gmail_app_password=os.getenv('GMAIL_APP_PASSWORD'),
            ai_answer_enabled=ai_answer_enabled,
            ai_provider=ai_provider,
            ai_model=ai_model,
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            claude_api_key=os.getenv('CLAUDE_API_KEY'),
            ai_show_answer_in_console=ai_show_console,
            ai_show_answer_in_notification=ai_show_notification,
            ai_auto_answer=ai_auto_answer,
            debug_mode=debug_mode
        )
        return config
    except ValueError as e:
        raise ConfigValidationError(f"Configuration validation failed: {e}") from e
    except Exception as e:
        raise ConfigValidationError(f"Failed to load configuration: {e}") from e


def setup_logging(debug_mode: bool = False) -> None:
    """Set up application logging."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('iclicker_evade.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    if debug_mode:
        logging.info("Debug logging enabled")


def print_startup_banner(config: AppConfig) -> None:
    """Print a startup banner with configuration summary."""
    print("🚀 Starting iClicker Access Code Generator...")
    print(f"👤 Username: {config.iclicker_username}")
    print(f"🎯 Class: {config.class_name or 'Interactive selection'}")
    print(f"🖥️  Mode: {'Headless' if config.headless else 'Visible'}")
    print(f"⏱️  Polling interval: {config.polling_interval} seconds")

    if config.email_enabled:
        print(f"📧 Email notifications: {config.notification_email}")
    else:
        print("📧 Email notifications: Disabled")

    if config.ai_enabled:
        print(f"🤖 AI suggestions: Enabled (Provider: {config.ai_provider}, Model: {config.ai_model or 'default'})")
        print(f"  - Show in console: {config.ai_show_answer_in_console}")
        print(f"  - Show in notification: {config.ai_show_answer_in_notification}")
        print(f"  - Auto answer: {config.ai_auto_answer}")
    else:
        print("🤖 AI answer suggestions: Disabled")

    if config.debug_mode:
        print("🐛 Debug mode: Enabled")
    print()