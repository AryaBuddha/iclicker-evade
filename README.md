# iClicker Evade

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automated iClicker access code retrieval and session management for university students. This tool streamlines the iClicker participation process by automating login, class selection, and session joining.

## Features

- 🔐 **Automated University Login**: Supports multiple university portal integrations
- 🎯 **Intelligent Class Selection**: Multiple matching strategies with fallback options
- ⏱️ **Session Monitoring**: Automatic detection of class start with configurable polling
- 🖱️ **Auto-Join**: Automatically clicks join button when instructor starts class
- 📋 **Question Detection**: Real-time monitoring for iClicker questions during sessions
- 📸 **Screenshot Capture**: Automatic full-page screenshots when questions appear
- 📧 **Email Notifications**: Send question screenshots via Gmail when detected
- 🤖 **AI Answer Suggestions**: GPT-4 Vision powered answer analysis and suggestions
- 🎯 **Auto-Answer**: User-guided answer selection with automatic button clicking
- 🔄 **Smart Polling**: Detects answered questions and waits for new ones
- 🖥️ **Flexible Modes**: Headless or visible browser operation
- 🔧 **Configurable**: Command-line options and environment variable support

## Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/username/iclicker-evade.git
   cd iclicker-evade
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up credentials** in `.env`:
   ```env
   ICLICKER_USERNAME=your_username
   ICLICKER_PASSWORD=your_password
   ICLICKER_CLASS_NAME=your_class_name  # Optional

   # Optional: For email notifications
   GMAIL_SENDER_EMAIL=your_gmail@gmail.com
   GMAIL_APP_PASSWORD=your_app_password

   # Optional: For AI answer suggestions
   OPENAI_API_KEY=your_openai_api_key
   ```

### Basic Usage

```bash
# Run with default settings (headless mode, interactive class selection)
python app.py

# Run with visible browser
python app.py --no-headless

# Specify class and polling interval
python app.py --class "CS 180" --polling_interval 3

# Full example with email and AI
python app.py --no-headless --class "Math 161" --polling_interval 5 --notif_email student@example.com --ai_answer
```

## Configuration

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--no-headless` | Run Chrome in visible mode | `False` (headless) |
| `--class "Name"` | Specify class name directly | Interactive selection |
| `--polling_interval N` | Seconds between session checks | `5` |
| `--notif_email EMAIL` | Email address for question notifications | `None` (disabled) |
| `--ai_answer` | Enable AI-powered answer suggestions | `False` (disabled) |
| `--ai_model MODEL` | AI model to use for suggestions | `gpt-4o` |

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
ICLICKER_USERNAME=your_username
ICLICKER_PASSWORD=your_password

# Optional
ICLICKER_CLASS_NAME=your_default_class_name

# Email notifications (both required for email functionality)
GMAIL_SENDER_EMAIL=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password

# AI answer suggestions (optional)
OPENAI_API_KEY=your_openai_api_key
```

#### Setting up Gmail App Password

To use email notifications, you need to set up a Gmail App Password:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate a password
3. **Use the generated password** as `GMAIL_APP_PASSWORD` in your `.env` file

#### Setting up OpenAI API Key

To use AI-powered answer suggestions, you need an OpenAI API key:

1. **Sign up at OpenAI**: Visit [OpenAI Platform](https://platform.openai.com/)
2. **Create API Key**:
   - Go to API Keys section
   - Click "Create new secret key"
   - Copy the generated key
3. **Add to .env file**: Use the key as `OPENAI_API_KEY` in your `.env` file

**Note**: GPT-4 Vision access may require a paid OpenAI account. Check [OpenAI pricing](https://openai.com/pricing) for current rates.

### Class Selection Methods

The application supports multiple class selection methods in order of priority:

1. **Command Line**: `--class "Class Name"`
2. **Environment Variable**: `ICLICKER_CLASS_NAME` in `.env`
3. **Interactive Selection**: Choose from available classes at runtime

The class matching system includes:
- Exact name matching
- Partial name matching
- Case-insensitive search
- Multiple fallback strategies

## Architecture

### Project Structure

```
iclicker-evade/
├── app.py                 # Main entry point and orchestrator
├── class_functions.py     # Class selection and session utilities
├── iclicker_signin.py     # Base iClicker navigation utilities
├── school_logins/         # University-specific login modules
│   └── purdue_login.py   # Purdue University implementation
├── questions/             # Auto-generated screenshot folder
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
└── README.md             # This file
```

### Core Modules

#### `app.py`
Main application orchestrator that:
- Handles command-line arguments
- Manages environment configuration
- Coordinates the login and session workflow

#### `class_functions.py`
Class selection and session management:
- `select_class_by_name()`: Intelligent class selection with multiple strategies
- `list_available_classes()`: Scans and displays available classes
- `select_class_interactive()`: User-guided class selection
- `wait_for_button()`: Session monitoring with auto-join functionality
- `monitor_for_questions()`: Real-time question detection with screenshot capture and auto-answer

#### `school_logins/`
University-specific authentication modules. Each module provides a complete login flow for a specific university.

## Session Monitoring

The application includes sophisticated session monitoring:

1. **Continuous Polling**: Checks for "Your instructor started class." text
2. **Visual Feedback**: Displays spinning progress indicator
3. **Automatic Joining**: Clicks join button when class starts
4. **No Timeout**: Runs indefinitely until class starts or manually stopped

```bash
# Monitor with 3-second intervals
python app.py --polling_interval 3
```

## Question Monitoring & Auto-Answer

After joining a class, the application automatically begins monitoring for iClicker questions:

### Features

- **Real-time Detection**: Monitors for question elements using iClicker's DOM structure
- **Screenshot Capture**: Takes full-page screenshots when questions appear
- **Smart Answer Selection**: Prompts user to choose answers (A, B, C, D, E)
- **Automatic Clicking**: Finds and clicks the selected answer button
- **Answered Question Detection**: Skips questions that have already been answered
- **Continuous Monitoring**: Seamlessly transitions between questions

### How It Works

1. **Question Detection**: Monitors for elements at `/html/body/app-root/ng-component/div/ng-component/app-poll/main/div/app-multiple-choice-question/div[3]`

2. **Screenshot Capture**:
   - Creates `questions/` folder automatically
   - Saves full-page screenshots as `question_YYYYMMDD_HHMMSS.png`
   - Captures entire page content for complete question context

3. **User Interaction**:
   ```
   🚨 QUESTION DETECTED! 🚨
   📋 An iClicker question has appeared on the page!
   📸 Full page screenshot saved: questions/question_20240918_143052.png
   🤖 Getting AI answer suggestion...
   ✅ AI analysis completed
   📧 Sending email notification...
   ✅ Email sent to student@example.com
   ❓ Question content: [question text and options]

   🤖 AI SUGGESTION:
      Answer: B
      Confidence: 85.2%
      Reasoning: Based on the diagram, option B correctly identifies...
      Model: gpt-4o
      Processing time: 2.34s

   ⚡ Select your answer (A, B, C, D, E) [AI suggests: B]:
   Using AI suggestion: B
   🖱️  Attempting to click answer B...
   ✅ Successfully clicked answer B!
   🔄 Waiting for next question...
   ```

4. **Smart State Management**:
   - Detects when questions are already answered (via `btn-selected` class)
   - Only processes new questions
   - Continues monitoring seamlessly

### Answer Selection Strategies

The system uses multiple strategies to locate and click answer buttons:

1. **Text-based matching**: Buttons containing answer letters
2. **Class-based matching**: Elements with answer-specific CSS classes
3. **Aria-label matching**: Accessibility labels
4. **Radio button detection**: Input elements with answer values
5. **Fallback clicking**: Any clickable element with answer text

### Generated Files

Screenshots are automatically saved to the `questions/` directory:
```
questions/
├── question_20240918_143052.png
├── question_20240918_143245.png
└── question_20240918_144010.png
```

## Email Notifications

When enabled with `--notif_email`, the application automatically sends email notifications with question screenshots:

### Email Features

- **Automatic Sending**: Emails sent immediately when questions are detected
- **Gmail Integration**: Uses Gmail SMTP with app password authentication
- **Screenshot Attachments**: Full-page screenshots attached to each email
- **Detailed Content**: Email includes timestamp, question text, and visual context
- **Secure Authentication**: Uses app passwords instead of main account password

### Email Content

Each notification email includes:

```
Subject: iClicker Question Alert - 14:30:52

🚨 iClicker Question Detected! 🚨

Time: 2024-09-18 14:30:52

Question Content:
[extracted question text and options]

Please see the attached screenshot for the complete question and answer options.

---
Sent automatically by iClicker Evade
```

### Usage Examples

```bash
# Enable email notifications
python app.py --notif_email your.email@example.com

# With all options including AI
python app.py --no-headless --class "CS 180" --polling_interval 3 --notif_email notify@gmail.com --ai_answer --ai_model gpt-4o
```

## AI Answer Suggestions

The application now includes powerful AI-driven answer suggestions using OpenAI's GPT-4 Vision model:

### Features

- **Visual Analysis**: Analyzes question screenshots using GPT-4 Vision
- **Smart Suggestions**: Provides answer recommendations with confidence scores
- **Detailed Reasoning**: Explains the logic behind each suggestion
- **Multiple Models**: Support for different OpenAI models (gpt-4o, gpt-4-vision-preview, gpt-4o-mini)
- **Email Integration**: AI suggestions included in email notifications
- **Easy Selection**: Press Enter to accept AI suggestion or choose your own answer

### How It Works

1. **Question Detection**: When a question appears, a screenshot is captured
2. **AI Analysis**: Screenshot is sent to OpenAI GPT-4 Vision for analysis
3. **Suggestion Display**: AI provides answer choice, confidence, and reasoning
4. **User Choice**: Accept AI suggestion (press Enter) or choose your own answer
5. **Email Notification**: AI suggestion included in email alerts

### Supported Models

| Model | Description | Best For |
|-------|-------------|----------|
| `gpt-4o` | Latest GPT-4 Omni model | General questions, fast responses |
| `gpt-4o-mini` | Smaller, faster model | Simple questions, cost efficiency |
| `gpt-4-vision-preview` | Original vision model | Complex visual analysis |

### Usage Examples

```bash
# Enable AI with default model
python app.py --ai_answer

# Use specific AI model
python app.py --ai_answer --ai_model gpt-4o-mini

# Full configuration with AI
python app.py --no-headless --class "Physics 101" --ai_answer --notif_email alerts@example.com
```

### AI Response Format

The AI provides structured responses including:
- **Answer Choice**: A, B, C, D, or E
- **Confidence Score**: 0-100% certainty level
- **Reasoning**: Explanation of the logic
- **Processing Time**: Time taken for analysis
- **Model Used**: Which AI model provided the answer

### Cost Considerations

- AI analysis uses OpenAI API credits
- GPT-4 Vision typically costs ~$0.01-0.03 per question
- Consider using `gpt-4o-mini` for cost efficiency
- Set spending limits in your OpenAI account

## Adding University Support

To add support for a new university:

1. **Create login module**:
   ```python
   # school_logins/new_university_login.py
   def new_university_login(driver, username, password):
       # Implement university-specific authentication
       # Return access code on success
       pass
   ```

2. **Update main application**:
   ```python
   # app.py
   from school_logins.new_university_login import new_university_login

   # Replace existing login call
   access_code = new_university_login(driver, username, password)
   ```

3. **Test thoroughly** with university-specific requirements

### Implementation Guidelines

- **Self-contained**: Each login module should handle the complete flow
- **Error handling**: Robust error handling with meaningful messages
- **Consistent interface**: Follow the established function signature
- **Documentation**: Include comprehensive docstrings and type hints

## Development

### Requirements

- **Python 3.7+**
- **Chrome Browser**: Latest stable version recommended
- **ChromeDriver**: Automatically managed by Selenium WebDriver Manager

### Testing

```bash
# Run with visible browser for debugging
python app.py --no-headless

# Test specific class selection
python app.py --no-headless --class "Test Class"

# Test with fast polling for development
python app.py --no-headless --polling_interval 1
```

### Code Quality

The project follows Python best practices:
- **Type hints**: Full type annotation support
- **Docstrings**: Comprehensive documentation for all functions
- **Error handling**: Graceful degradation and meaningful error messages
- **Modular design**: Clean separation of concerns

## Troubleshooting

### Common Issues

**Login Failures**:
- Verify credentials in `.env` file
- Check university portal availability
- Ensure Chrome and ChromeDriver compatibility

**Class Selection Issues**:
- Use `--no-headless` to visually debug
- Try partial class name matching
- Use interactive selection to see available options

**Session Monitoring**:
- Verify the class page is correctly loaded
- Check if instructor has actually started the session
- Use lower polling intervals for faster detection

**Question Monitoring**:
- Questions not appearing: Verify the DOM structure matches the expected XPath
- Answer clicking fails: Check browser console for JavaScript errors
- Screenshots not saving: Ensure write permissions in the project directory
- Already answered questions still appearing: Clear browser cache or restart session

**Email Notifications**:
- Emails not sending: Verify Gmail credentials and app password in `.env`
- Authentication failed: Ensure 2FA is enabled and app password is correct
- SMTP errors: Check internet connection and Gmail SMTP access
- Missing attachments: Verify screenshot was saved successfully before email attempt

**AI Answer Suggestions**:
- AI not working: Verify `OPENAI_API_KEY` is set correctly in `.env`
- API errors: Check OpenAI account status and billing
- Slow responses: Try using `gpt-4o-mini` for faster processing
- Poor suggestions: Ensure questions are clearly visible in screenshots

### Debug Mode

Run with visible browser to troubleshoot:

```bash
python app.py --no-headless --class "Your Class" --polling_interval 1
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run type checking
mypy *.py

# Run code formatting
black *.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes and personal use. Users are responsible for complying with their institution's technology policies and terms of service. The authors are not responsible for any misuse or violations of institutional policies.

## Support

- 📖 **Documentation**: This README and inline code documentation
- 🐛 **Issues**: Report bugs and request features via GitHub Issues
- 💡 **Discussions**: Share ideas and ask questions in GitHub Discussions

---

**Note**: This project is not affiliated with iClicker or any educational institution. It is an independent automation tool created for convenience and learning purposes.