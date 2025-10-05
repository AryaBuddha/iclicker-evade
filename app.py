#!/usr/bin/env python3
"""iClicker Access Code Generator - Refactored Version.

This script automates the process of logging into iClicker through various university portals,
selecting classes, and waiting for sessions to start. It provides a complete automation solution
for iClicker participation with question monitoring and email notifications.
"""

import argparse
import logging
import sys
from typing import Optional

from config import load_config, setup_logging, print_startup_banner, ConfigValidationError, AIProvider
from notifications import EmailNotificationService
from monitoring import QuestionMonitor
from utils import setup_chrome_driver, safe_quit_driver
from ai_services import (
    create_openai_service,
    create_gemini_service,
    create_claude_service,
    BaseAIService
)
from class_functions import select_class_by_name, select_class_interactive, wait_for_button
from school_logins.purdue_login import purdue_login


def main(
    headless: bool,
    class_name: Optional[str],
    polling_interval: int,
    notification_email: Optional[str],
    ai_answer_enabled: bool,
    ai_provider: AIProvider,
    ai_model: Optional[str],
    ai_show_console: bool,
    ai_show_notification: bool,
    ai_auto_answer: bool,
    debug_mode: bool
) -> None:
    """Main function to orchestrate the iClicker automation process."""
    try:
        config = load_config(
            headless=headless,
            class_name=class_name,
            polling_interval=polling_interval,
            notification_email=notification_email,
            ai_answer_enabled=ai_answer_enabled,
            ai_provider=ai_provider,
            ai_model=ai_model,
            ai_show_console=ai_show_console,
            ai_show_notification=ai_show_notification,
            ai_auto_answer=ai_auto_answer,
            debug_mode=debug_mode
        )
    except ConfigValidationError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)

    setup_logging(config.debug_mode)
    logger = logging.getLogger(__name__)

    print_startup_banner(config)
    config.log_config_summary()

    email_service = None
    if config.email_enabled:
        try:
            email_service = EmailNotificationService(config.gmail_sender_email, config.gmail_app_password)
            if email_service.test_connection():
                logger.info("Email notification service initialized and tested")
            else:
                logger.warning("Email service initialized but connection test failed")
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
            print(f"⚠️ Warning: Email service unavailable: {e}")

    ai_service: Optional[BaseAIService] = None
    if config.ai_enabled:
        try:
            service_map = {
                "openai": create_openai_service,
                "gemini": create_gemini_service,
                "claude": create_claude_service,
            }
            create_service = service_map.get(config.ai_provider)

            if create_service:
                ai_service = create_service(config.current_ai_api_key, config.ai_model)
                if ai_service and ai_service.test_connection():
                    logger.info(f"{ai_service.service_name} service initialized and tested")
                else:
                    logger.warning(f"{config.ai_provider} service initialized but connection test failed")
            else:
                logger.error(f"Unknown AI provider: {config.ai_provider}")

        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            print(f"⚠️ Warning: AI service unavailable: {e}")

    driver = None
    try:
        logger.info("Initializing Chrome WebDriver")
        driver = setup_chrome_driver(headless=config.headless)

        logger.info("Starting Purdue login flow")
        access_code = purdue_login(driver, config.iclicker_username, config.iclicker_password)

        if not access_code:
            logger.error("Failed to retrieve access code")
            print("❌ Failed to retrieve access code")
            return

        print(f"\n🎉 SUCCESS! Your iClicker access code is: {access_code}")
        logger.info(f"iClicker access code retrieved: {access_code}")

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

        print("\n🔘 WAITING FOR CLASS TO START")
        if wait_for_button(driver, polling_interval=config.polling_interval):
            print("✅ Join button clicked! Ready for iClicker session.")
            print("🔒 Starting question monitoring...")
            logger.info("Class joined, starting question monitoring")

            question_monitor = QuestionMonitor(
                driver=driver,
                polling_interval=config.polling_interval,
                email_service=email_service,
                ai_service=ai_service,
                recipient_email=config.notification_email,
                config=config
            )
            question_monitor.start_monitoring()
        else:
            logger.warning("Failed to join class session")
            print("❌ Failed to join class session")

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
        if driver:
            logger.info("Cleaning up WebDriver")
            safe_quit_driver(driver)
            print("🔒 Browser closed.")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        description='iClicker Access Code Generator with Question Monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # General options
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='Run Chrome in visible mode')
    parser.add_argument('--class', dest='class_name', help='Name of the class to select')
    parser.add_argument('--polling_interval', type=int, default=5, metavar='SEC', help='Seconds between checks (default: 5)')
    parser.add_argument('--notif_email', dest='notification_email', help='Email for notifications (req. Gmail creds in .env)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='version', version='iClicker Evade v2.1.0')

    # AI options
    ai_group = parser.add_argument_group('AI Answer Suggestions')
    ai_group.add_argument('--ai', action='store_true', dest='ai_answer_enabled', help='Enable AI answer suggestions')
    ai_group.add_argument('--ai-provider', choices=['openai', 'gemini', 'claude'], default='openai', help='AI provider to use (default: openai)')
    ai_group.add_argument('--ai-model', help='Specific AI model to use (e.g., gpt-4o, gemini-1.5-pro-latest)')

    # AI behavior flags
    ai_behavior_group = parser.add_argument_group('AI Behavior Flags')
    ai_behavior_group.add_argument('--ai-show-console', action='store_true', default=True, help='Show AI answer in console (default)')
    ai_behavior_group.add_argument('--ai-hide-console', action='store_false', dest='ai_show_console', help='Hide AI answer in console')
    ai_behavior_group.add_argument('--ai-show-notification', action='store_true', default=True, help='Include AI answer in email notifications (default)')
    ai_behavior_group.add_argument('--ai-hide-notification', action='store_false', dest='ai_show_notification', help='Exclude AI answer from email notifications')
    ai_behavior_group.add_argument('--ai-auto-answer', action='store_true', default=False, help='Let AI automatically answer questions')

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if not (1 <= args.polling_interval <= 300):
        print("❌ Error: Polling interval must be between 1 and 300 seconds")
        sys.exit(1)
    if args.notification_email:
        from utils.validators import validate_email_address
        if not validate_email_address(args.notification_email):
            print(f"❌ Error: Invalid email address format: {args.notification_email}")
            sys.exit(1)


if __name__ == "__main__":
    parser = create_argument_parser()
    args = parser.parse_args()

    validate_arguments(args)

    print("=" * 60)
    print("🚀 iClicker Evade v2.1.0 - Multi-AI Edition")
    print("=" * 60)

    try:
        main(
            headless=args.headless,
            class_name=args.class_name,
            polling_interval=args.polling_interval,
            notification_email=args.notification_email,
            ai_answer_enabled=args.ai_answer_enabled,
            ai_provider=args.ai_provider,
            ai_model=args.ai_model,
            ai_show_console=args.ai_show_console,
            ai_show_notification=args.ai_show_notification,
            ai_auto_answer=args.ai_auto_answer,
            debug_mode=args.debug
        )
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)