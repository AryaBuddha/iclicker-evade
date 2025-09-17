# iClicker Evade

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automated iClicker access code retrieval and session management for university students. This tool streamlines the iClicker participation process by automating login, class selection, and session joining.

## Features

- 🔐 **Automated University Login**: Supports multiple university portal integrations
- 🎯 **Intelligent Class Selection**: Multiple matching strategies with fallback options
- ⏱️ **Session Monitoring**: Automatic detection of class start with configurable polling
- 🖱️ **Auto-Join**: Automatically clicks join button when instructor starts class
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
   ```

### Basic Usage

```bash
# Run with default settings (headless mode, interactive class selection)
python app.py

# Run with visible browser
python app.py --no-headless

# Specify class and polling interval
python app.py --class "CS 180" --polling_interval 3

# Full example
python app.py --no-headless --class "Math 161" --polling_interval 5
```

## Configuration

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--no-headless` | Run Chrome in visible mode | `False` (headless) |
| `--class "Name"` | Specify class name directly | Interactive selection |
| `--polling_interval N` | Seconds between session checks | `5` |

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
ICLICKER_USERNAME=your_username
ICLICKER_PASSWORD=your_password

# Optional
ICLICKER_CLASS_NAME=your_default_class_name
```

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