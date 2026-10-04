# 📬 Gmail Keep-Alive & Activity Routine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated Python utility designed to maintain account activity across multiple Google (Gmail) backup accounts using SMTP and Google App Passwords.

Google may deactivate or flag dormant accounts after extended periods of inactivity. This script runs scheduled routine security checks and sends keep-alive emails between your backup accounts to ensure they stay active.

---

## 🔒 Security Notice

> **IMPORTANT:**
> - **Never** commit your personal email addresses or App Passwords to GitHub or any public repository!
> - The included `.gitignore` is pre-configured to block `*.xlsx`, `*.csv` (except templates), `.env`, and log files.
> - Always use [Google App Passwords](https://myaccount.google.com/apppasswords), **never** use your master Google account password.

---

## ✨ Features

- 🔄 **Multi-Account Batch Processing**: Cycles through any number of accounts automatically.
- ⏱️ **Rate Limiting / Sleep Delay**: Configurable interval (default: 180 seconds) between accounts to comply with Gmail sending limits and prevent spam flags.
- 📊 **Flexible Formats**: Supports both Excel (`.xlsx`) and CSV (`.csv`) account files.
- 🧪 **Safety Modes**:
  - `--dry-run`: Test file parsing without connecting to the network.
  - `--test-auth`: Validate login credentials without sending emails.
- 📝 **Dual Logging**: Real-time terminal progress with persistent logging to file (`gmail_activity.log`).
- 🛑 **Graceful Shutdown**: Safely stop execution anytime using `Ctrl + C`.

---

## 📋 Prerequisites & Requirements

1. **Python 3.10+**
2. **Google 2-Step Verification & App Password**:
   - Go to your [Google Account](https://myaccount.google.com/).
   - Navigate to **Security** → **2-Step Verification**.
   - Scroll down to **App passwords** (or search "App passwords").
   - Create an app password (e.g., named "Mail Routine").
   - Google will provide a 16-letter password (e.g., `abcd efgh ijkl mnop`). Use this in your accounts list.

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/gmail-keep-alive.git
   cd gmail-keep-alive
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your accounts file:**
   - Copy `accounts_template.xlsx` or `accounts_template.csv` to `accounts.xlsx` or `accounts.csv`:
     ```bash
     cp accounts_template.xlsx accounts.xlsx
     ```
   - Fill in your Gmail addresses and 16-letter App Passwords.

| gmail | password |
| :--- | :--- |
| `backup1@gmail.com` | `abcd efgh ijkl mnop` |
| `backup2@gmail.com` | `qrst uvwx yzab cdef` |

---

## 💻 Usage

### 1. Test in Dry-Run Mode (Simulation)
Verify your accounts file can be read without sending any emails:
```bash
python main.py --file accounts.xlsx --dry-run
```

### 2. Test Credentials Only
Verify your App Passwords connect successfully without sending emails:
```bash
python main.py --file accounts.xlsx --test-auth
```

### 3. Run the Full Routine
```bash
python main.py --file accounts.xlsx
```

### 4. Custom Delay and Message
```bash
python main.py --file accounts.xlsx --delay 120 --subject "Weekly Keep-Alive"
```

---

## ⚙️ Command-Line Arguments

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--file` | `-f` | Auto-detect | Path to `.xlsx` or `.csv` accounts file |
| `--delay` | `-d` | `180` | Delay in seconds between accounts |
| `--subject` | `-s` | `Routine security procedures` | Email subject header |
| `--body` | `-b` | Default notice | Email body content |
| `--dry-run` | | `False` | Simulate run without network connections |
| `--test-auth`| | `False` | Authenticate accounts without sending mail |
| `--log-file` | | `gmail_activity.log` | Target file for logging output |

---

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
