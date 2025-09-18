"""Configuration management for iClicker Evade.

This module handles loading and validation of application configuration
from environment variables and command-line arguments.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
import logging


@dataclass
class AppConfig:
    """Application configuration container.

    Holds all configuration values needed by the iClicker Evade application.
    Provides validation and easy access to settings.

    Attributes:
        # Required iClicker credentials
        iclicker_username (str): University username for iClicker login
        iclicker_password (str): University password for iClicker login

        # Optional class selection
        class_name (Optional[str]): Specific class name to select automatically

        # Browser and monitoring settings
        headless (bool): Whether to run browser in headless mode
        polling_interval (int): Seconds between monitoring checks

        # Email notification settings
        notification_email (Optional[str]): Email to send question alerts to
        gmail_sender_email (Optional[str]): Gmail address to send from
        gmail_app_password (Optional[str]): Gmail app password for authentication

        # AI answer suggestions
        ai_answer_enabled (bool): Enable AI-powered answer suggestions
        openai_api_key (Optional[str]): OpenAI API key for GPT-4 Vision
        ai_model (str): AI model to use for suggestions

        # Application behavior
        debug_mode (bool): Enable debug logging and verbose output
    """

    # Required credentials
    iclicker_username: str
    iclicker_password: str

    # Optional settings
    class_name: Optional[str] = None
    headless: bool = True
    polling_interval: int = 5
    notification_email: Optional[str] = None
    gmail_sender_email: Optional[str] = None
    gmail_app_password: Optional[str] = None
    ai_answer_enabled: bool = False
    openai_api_key: Optional[str] = None
    ai_model: str = "gpt-4o"
    debug_mode: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        self._validate_required_fields()
        self._validate_email_config()
        self._validate_ai_config()
        self._validate_polling_interval()

    def _validate_required_fields(self) -> None:
        """Validate that required configuration fields are present.

        Raises:
            ValueError: If required fields are missing or empty
        """
        if not self.iclicker_username:
            raise ValueError("iClicker username is required")

        if not self.iclicker_password:
            raise ValueError("iClicker password is required")

    def _validate_email_config(self) -> None:
        """Validate email configuration if email notifications are requested.

        If notification_email is set, both gmail_sender_email and gmail_app_password
        must also be provided.

        Raises:
            ValueError: If email configuration is incomplete
        """
        if self.notification_email:
            if not self.gmail_sender_email:
                raise ValueError(
                    "GMAIL_SENDER_EMAIL must be set when using email notifications"
                )
            if not self.gmail_app_password:
                raise ValueError(
                    "GMAIL_APP_PASSWORD must be set when using email notifications"
                )

    def _validate_ai_config(self) -> None:
        """Validate AI configuration if AI answers are enabled.

        Raises:
            ValueError: If AI configuration is incomplete
        """
        if self.ai_answer_enabled:
            if not self.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY must be set when AI answers are enabled"
                )

    def _validate_polling_interval(self) -> None:
        """Validate polling interval is within reasonable bounds.

        Raises:
            ValueError: If polling interval is invalid
        """
        if self.polling_interval < 1:
            raise ValueError("Polling interval must be at least 1 second")
        if self.polling_interval > 300:  # 5 minutes
            raise ValueError("Polling interval should not exceed 300 seconds")

    @property
    def email_enabled(self) -> bool:
        """Check if email notifications are properly configured.

        Returns:
            True if all email settings are available, False otherwise
        """
        return bool(
            self.notification_email and
            self.gmail_sender_email and
            self.gmail_app_password
        )

    @property
    def ai_enabled(self) -> bool:
        """Check if AI answer suggestions are properly configured.

        Returns:
            True if AI settings are available, False otherwise
        """
        return bool(
            self.ai_answer_enabled and
            self.openai_api_key
        )

    def log_config_summary(self) -> None:
        """Log a summary of the current configuration.

        Logs key configuration values while masking sensitive information
        like passwords and email addresses.
        """
        logger = logging.getLogger(__name__)

        logger.info("=== iClicker Evade Configuration ===")
        logger.info(f"Username: {self.iclicker_username}")
        logger.info(f"Class: {self.class_name or 'Interactive selection'}")
        logger.info(f"Browser mode: {'Headless' if self.headless else 'Visible'}")
        logger.info(f"Polling interval: {self.polling_interval} seconds")

        if self.email_enabled:
            # Mask email addresses for privacy
            masked_sender = self._mask_email(self.gmail_sender_email)
            masked_recipient = self._mask_email(self.notification_email)
            logger.info(f"Email notifications: {masked_recipient} (from {masked_sender})")
        else:
            logger.info("Email notifications: Disabled")

        if self.ai_enabled:
            logger.info(f"AI answer suggestions: Enabled (model: {self.ai_model})")
        else:
            logger.info("AI answer suggestions: Disabled")

        logger.info(f"Debug mode: {self.debug_mode}")

    def _mask_email(self, email: Optional[str]) -> str:
        """Mask an email address for logging.

        Args:
            email: Email address to mask

        Returns:
            Masked email address (e.g., "u***@example.com")
        """
        if not email:
            return "None"

        try:
            local, domain = email.split('@', 1)
            if len(local) <= 2:
                masked_local = local
            else:
                masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
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
    ai_model: str = "gpt-4o",
    debug_mode: bool = False
) -> AppConfig:
    """Load and validate application configuration.

    Loads configuration from environment variables and combines with
    command-line arguments. Validates all settings and returns a
    complete configuration object.

    Args:
        headless: Whether to run browser in headless mode
        class_name: Specific class name to select (overrides env var)
        polling_interval: Seconds between monitoring checks
        notification_email: Email address for question alerts
        ai_answer_enabled: Enable AI-powered answer suggestions
        ai_model: AI model to use for suggestions
        debug_mode: Enable debug logging

    Returns:
        Validated AppConfig instance

    Raises:
        ConfigValidationError: If configuration is invalid or incomplete

    Example:
        >>> config = load_config(
        ...     headless=False,
        ...     class_name="CS 180",
        ...     notification_email="student@example.com"
        ... )
        >>> print(f"Username: {config.iclicker_username}")
        Username: john_doe
    """
    # Load environment variables from .env file
    load_dotenv()

    try:
        # Load required credentials from environment
        iclicker_username = os.getenv('ICLICKER_USERNAME')
        iclicker_password = os.getenv('ICLICKER_PASSWORD')

        # Load optional settings from environment
        class_name_env = os.getenv('ICLICKER_CLASS_NAME')
        gmail_sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
        openai_api_key = os.getenv('OPENAI_API_KEY')

        # Use command-line class name if provided, otherwise fall back to env
        final_class_name = class_name or class_name_env

        # Create and validate configuration
        config = AppConfig(
            iclicker_username=iclicker_username or "",
            iclicker_password=iclicker_password or "",
            class_name=final_class_name,
            headless=headless,
            polling_interval=polling_interval,
            notification_email=notification_email,
            gmail_sender_email=gmail_sender_email,
            gmail_app_password=gmail_app_password,
            ai_answer_enabled=ai_answer_enabled,
            openai_api_key=openai_api_key,
            ai_model=ai_model,
            debug_mode=debug_mode
        )

        return config

    except ValueError as e:
        raise ConfigValidationError(f"Configuration validation failed: {e}") from e
    except Exception as e:
        raise ConfigValidationError(f"Failed to load configuration: {e}") from e


def setup_logging(debug_mode: bool = False) -> None:
    """Set up application logging.

    Configures logging with appropriate levels and formatters for both
    console and file output.

    Args:
        debug_mode: If True, set DEBUG level; otherwise INFO level
    """
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Set up file handler
    file_handler = logging.FileHandler('iclicker_evade.log')
    file_handler.setLevel(logging.INFO)  # Always log INFO+ to file
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce noise from external libraries
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    if debug_mode:
        logging.info("Debug logging enabled")


def print_startup_banner(config: AppConfig) -> None:
    """Print a startup banner with configuration summary.

    Args:
        config: Application configuration to display
    """
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
        print(f"🤖 AI answer suggestions: Enabled ({config.ai_model})")
    else:
        print("🤖 AI answer suggestions: Disabled")

    if config.debug_mode:
        print("🐛 Debug mode: Enabled")

    print()  # Empty line for spacing