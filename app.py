#!/usr/bin/env python3
"""iClicker Access Code Generator.

This script automates the process of logging into iClicker through various university portals,
selecting classes, and waiting for sessions to start. It provides a complete automation solution
for iClicker participation.

Features:
    - Automated university portal login
    - Intelligent class selection with multiple strategies
    - Session monitoring with automatic join button clicking
    - Configurable polling intervals
    - Headless and visible browser modes

Example:
    $ python app.py --no-headless --class "CS 180" --polling_interval 3
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iclicker_signin import setup_chrome_driver
from class_functions import select_class_by_name, select_class_interactive, wait_for_button, monitor_for_questions

# Import Purdue login function directly
from school_logins.purdue_login import purdue_login

# Load environment variables
load_dotenv()

def main(headless: bool = True, class_name: Optional[str] = None, polling_interval: int = 5, notification_email: Optional[str] = None) -> None:
    """Main function to orchestrate the iClicker automation process.

    Coordinates the entire workflow:
    1. Loads credentials from environment
    2. Sets up Chrome WebDriver
    3. Performs university login
    4. Selects target class
    5. Waits for session to start and joins automatically
    6. Monitors for questions with optional email notifications

    Args:
        headless: Whether to run Chrome in headless mode. Default True.
        class_name: Name of the class to select. If None, uses interactive selection.
        polling_interval: Seconds between polling for the join button. Default 5.
        notification_email: Email address to send question screenshots to. Default None.

    Raises:
        SystemExit: If required environment variables are missing
    """
    
    # Get credentials from environment
    username = os.getenv('ICLICKER_USERNAME')
    password = os.getenv('ICLICKER_PASSWORD')
    class_name_env = os.getenv('ICLICKER_CLASS_NAME')

    # Get email configuration from environment
    sender_email = os.getenv('GMAIL_SENDER_EMAIL')
    sender_password = os.getenv('GMAIL_APP_PASSWORD')

    # Use class_name parameter if provided, otherwise fall back to environment variable
    selected_class = class_name or class_name_env
    
    if not username or not password:
        logging.error("Missing required environment variables: ICLICKER_USERNAME and ICLICKER_PASSWORD")
        print("❌ Error: ICLICKER_USERNAME and ICLICKER_PASSWORD environment variables must be set")
        print("Please create a .env file with your credentials.")
        return

    # Validate email configuration if notification email is requested
    if notification_email and (not sender_email or not sender_password):
        logging.error("Email notification requested but missing email credentials")
        print("❌ Error: GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD must be set in .env for email notifications")
        print("Please add these to your .env file or remove the --notif_email option.")
        return
    
    print("🚀 Starting iClicker Access Code Generator...")
    print(f"👤 Username: {username}")
    print(f"🎯 Class: {selected_class or 'Interactive selection'}")
    print(f"🖥️  Mode: {'Headless' if headless else 'Visible'}")
    print(f"⏱️  Polling interval: {polling_interval} seconds")
    if notification_email:
        print(f"📧 Email notifications: {notification_email}")
    else:
        print("📧 Email notifications: Disabled")
    
    # Set up the Chrome driver
    driver = setup_chrome_driver(headless=headless)
    
    try:
        logging.info("Starting Purdue login flow")
        # Execute Purdue login flow (gets access code)
        access_code = purdue_login(driver, username, password)
        
        if access_code:
            print(f"\n🎉 SUCCESS! Your iClicker access code is: {access_code}")
            
            # Now handle class selection
            print("\n🎯 CLASS SELECTION")
            if selected_class:
                print(f"Attempting to select class: {selected_class}")
                if not select_class_by_name(driver, selected_class):
                    print("❌ Failed to select specified class, falling back to interactive selection")
                    if not select_class_interactive(driver):
                        print("❌ Class selection failed")
                        return
            else:
                print("No class specified, using interactive selection...")
                if not select_class_interactive(driver):
                    print("❌ Class selection failed")
                    return
            
            print("✅ Class selected successfully!")

            # Wait for the join button to appear
            print("\n🔘 WAITING FOR CLASS TO START")
            if wait_for_button(driver, polling_interval=polling_interval):
                print("✅ Join button clicked! Ready for iClicker session.")
                print("🔒 Keeping browser open for your iClicker session...")

                # Start monitoring for questions using the same polling interval
                monitor_for_questions(driver, polling_interval=polling_interval,
                                    notification_email=notification_email,
                                    sender_email=sender_email,
                                    sender_password=sender_password)
            
        else:
            print("❌ Failed to retrieve access code")
            
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        print("Check the log for more details.")
    
    finally:
        try:
            driver.quit()
            logging.info("Browser closed successfully")
            print("🔒 Browser closed.")
        except Exception as e:
            logging.warning(f"Error closing browser: {e}")
            print("⚠️ Warning: Error closing browser")

def _create_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='iClicker Access Code Generator',
        epilog='Example: python app.py --no-headless --class "CS 180" --polling_interval 3 --notif_email example@gmail.com'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run Chrome in visible mode (not headless)'
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
        help='Seconds between polling for the join button (default: 5)'
    )
    parser.add_argument(
        '--notif_email',
        dest='notification_email',
        help='Email address to send question screenshots to (requires GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD in .env)'
    )
    return parser


def _setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('iclicker_evade.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Reduce selenium logging noise
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


if __name__ == "__main__":
    _setup_logging()

    parser = _create_parser()
    args = parser.parse_args()

    logging.info(f"Starting iClicker Evade v1.0.0")
    logging.info(f"Arguments: headless={not args.no_headless}, class={args.class_name}, polling_interval={args.polling_interval}, notification_email={args.notification_email}")

    # Run with headless=False if --no-headless flag is provided
    main(
        headless=not args.no_headless,
        class_name=args.class_name,
        polling_interval=args.polling_interval,
        notification_email=args.notification_email
    )