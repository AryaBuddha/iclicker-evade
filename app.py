#!/usr/bin/env python3
"""iClicker Access Code Generator - Refactored Version.

This script automates the process of logging into iClicker through various university portals,
selecting classes, and waiting for sessions to start. It provides a complete automation solution
for iClicker participation with question monitoring and email notifications.

Features:
    - Automated university portal login
    - Intelligent class selection with multiple strategies
    - Session monitoring with automatic join button clicking
    - Real-time question detection and screenshot capture
    - Email notifications with question alerts
    - Automated answer selection and clicking
    - Configurable polling intervals and browser modes

Example:
    $ python app.py --no-headless --class "CS 180" --polling_interval 3 --notif_email alert@example.com
"""

import argparse
import logging
import sys
from typing import Optional

# Import our refactored modules
from config import load_config, setup_logging, print_startup_banner, ConfigValidationError
from notifications import EmailNotificationService
from monitoring import QuestionMonitor
from utils import setup_chrome_driver, safe_quit_driver
from ai_services import OpenAIAnswerService
from class_functions import select_class_by_name, select_class_interactive, wait_for_button
from school_logins.purdue_login import purdue_login


def main(
    headless: bool = True,
    class_name: Optional[str] = None,
    polling_interval: int = 5,
    notification_email: Optional[str] = None,
    ai_answer_enabled: bool = False,
    ai_model: str = "gpt-4o",
    debug_mode: bool = False
) -> None:
    """Main function to orchestrate the iClicker automation process.

    Coordinates the entire workflow using the modular architecture:
    1. Loads and validates configuration
    2. Sets up logging and email services
    3. Initializes browser and performs university login
    4. Handles class selection
    5. Waits for session to start and joins automatically
    6. Monitors for questions with automated responses

    Args:
        headless: Whether to run Chrome in headless mode
        class_name: Name of the class to select (overrides environment)
        polling_interval: Seconds between polling checks
        notification_email: Email address for question notifications
        ai_answer_enabled: Enable AI-powered answer suggestions
        ai_model: AI model to use for suggestions
        debug_mode: Enable debug logging and verbose output

    Raises:
        ConfigValidationError: If configuration is invalid
        SystemExit: If critical errors occur during execution
    """
    # Load and validate configuration
    try:
        config = load_config(
            headless=headless,
            class_name=class_name,
            polling_interval=polling_interval,
            notification_email=notification_email,
            ai_answer_enabled=ai_answer_enabled,
            ai_model=ai_model,
            debug_mode=debug_mode
        )
    except ConfigValidationError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)

    # Set up logging
    setup_logging(config.debug_mode)
    logger = logging.getLogger(__name__)

    # Display startup information
    print_startup_banner(config)
    config.log_config_summary()

    # Initialize email service if configured
    email_service = None
    if config.email_enabled:
        try:
            # Ensure the values are not None before passing
            if config.gmail_sender_email and config.gmail_app_password:
                email_service = EmailNotificationService(
                    config.gmail_sender_email,
                    config.gmail_app_password
                )
                # Test email connection
                if email_service.test_connection():
                    logger.info("Email notification service initialized and tested")
                else:
                    logger.warning("Email service initialized but connection test failed")
            else:
                logger.warning("Email configuration incomplete")
                print("⚠️ Warning: Email configuration incomplete")
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
            print(f"⚠️ Warning: Email service unavailable: {e}")
            email_service = None

    # Initialize AI service if configured
    ai_service = None
    if config.ai_enabled and config.openai_api_key:
        try:
            ai_service = OpenAIAnswerService(
                config.openai_api_key,
                config.ai_model
            )
            # Test AI connection
            if ai_service.test_connection():
                logger.info("AI answer service initialized and tested")
            else:
                logger.warning("AI service initialized but connection test failed")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            print(f"⚠️ Warning: AI service unavailable: {e}")
            ai_service = None

    # Set up the Chrome driver
    driver = None
    try:
        logger.info("Initializing Chrome WebDriver")
        driver = setup_chrome_driver(headless=config.headless)

        # Execute Purdue login flow
        logger.info("Starting Purdue login flow")
        access_code = purdue_login(driver, config.iclicker_username, config.iclicker_password)

        if access_code:
            print(f"\n🎉 SUCCESS! Your iClicker access code is: {access_code}")
            logger.info(f"iClicker access code retrieved: {access_code}")

            # Handle class selection
            print("\n🎯 CLASS SELECTION")
            class_selected = False

            if config.class_name:
                print(f"Attempting to select class: {config.class_name}")
                if select_class_by_name(driver, config.class_name):
                    class_selected = True
                else:
                    print("❌ Failed to select specified class, falling back to interactive selection")

            if not class_selected:
                print("Using interactive class selection...")
                if not select_class_interactive(driver):
                    print("❌ Class selection failed")
                    return

            print("✅ Class selected successfully!")
            logger.info("Class selection completed")

            # Wait for the join button to appear and join class
            print("\n🔘 WAITING FOR CLASS TO START")
            if wait_for_button(driver, polling_interval=config.polling_interval):
                print("✅ Join button clicked! Ready for iClicker session.")
                print("🔒 Starting question monitoring...")
                logger.info("Class joined, starting question monitoring")

                # Initialize and start question monitoring
                question_monitor = QuestionMonitor(
                    driver=driver,
                    polling_interval=config.polling_interval,
                    email_service=email_service,
                    ai_service=ai_service,
                    recipient_email=config.notification_email
                )

                # Start monitoring (this will run until interrupted)
                question_monitor.start_monitoring()

            else:
                logger.warning("Failed to join class session")
                print("❌ Failed to join class session")

        else:
            logger.error("Failed to retrieve access code")
            print("❌ Failed to retrieve access code")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=config.debug_mode)
        print(f"❌ Unexpected error: {e}")
        if config.debug_mode:
            import traceback
            traceback.print_exc()
    finally:
        # Clean up resources
        if driver:
            logger.info("Cleaning up WebDriver")
            safe_quit_driver(driver)
            print("🔒 Browser closed.")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser.

    Returns:
        Configured ArgumentParser instance with all supported options
    """
    parser = argparse.ArgumentParser(
        description='iClicker Access Code Generator with Question Monitoring',
        epilog='Example: python app.py --no-headless --class "CS 180" --polling_interval 3 --notif_email alert@example.com',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run Chrome in visible mode (default: headless)'
    )

    parser.add_argument(
        '--class',
        dest='class_name',
        help='Name of the class to select (overrides environment variable)'
    )

    parser.add_argument(
        '--polling_interval',
        type=int,
        default=5,
        metavar='SECONDS',
        help='Seconds between polling checks (default: 5, range: 1-300)'
    )

    parser.add_argument(
        '--notif_email',
        dest='notification_email',
        help='Email address to send question screenshots to (requires Gmail credentials in .env)'
    )

    parser.add_argument(
        '--ai_answer',
        action='store_true',
        help='Enable AI-powered answer suggestions (requires OPENAI_API_KEY in .env)'
    )

    parser.add_argument(
        '--ai_model',
        default='gpt-4o',
        help='AI model to use for answer suggestions (default: gpt-4o)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging and verbose output'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='iClicker Evade v2.0.0'
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments.

    Args:
        args: Parsed command line arguments

    Raises:
        SystemExit: If arguments are invalid
    """
    # Validate polling interval
    if not (1 <= args.polling_interval <= 300):
        print("❌ Error: Polling interval must be between 1 and 300 seconds")
        sys.exit(1)

    # Validate email format if provided
    if args.notification_email:
        from utils.validators import validate_email_address
        if not validate_email_address(args.notification_email):
            print(f"❌ Error: Invalid email address format: {args.notification_email}")
            sys.exit(1)


if __name__ == "__main__":
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    # Log startup information
    print("=" * 60)
    print("🚀 iClicker Evade v2.0.0 - Question Monitoring Edition")
    print("=" * 60)

    try:
        # Run the main application
        main(
            headless=not args.no_headless,
            class_name=args.class_name,
            polling_interval=args.polling_interval,
            notification_email=args.notification_email,
            ai_answer_enabled=args.ai_answer,
            ai_model=args.ai_model,
            debug_mode=args.debug
        )
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)