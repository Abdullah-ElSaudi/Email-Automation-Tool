"""
Gmail Routine Activity & Keep-Alive Script
===========================================
Automates sending periodic routine emails across multiple Gmail backup accounts
using SMTP and Google App Passwords to maintain account activity.

Author: Abdullah El Saudi
License: MIT
"""

import argparse
import csv
import logging
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# SMTP Server configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

DEFAULT_SUBJECT = "Routine security procedures"
DEFAULT_BODY = """Hello,
This is an automated security routine to verify and keep backup Gmail accounts active.
Best regards,
Account Management Routine
"""
DEFAULT_WAIT_TIME = 180  # seconds between each account


def setup_logger(log_file: str = "gmail_activity.log") -> logging.Logger:
    """Configures logging to both console and a log file."""
    logger = logging.getLogger("GmailKeeper")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if re-initialized
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s")

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def load_accounts(file_path: Path, logger: logging.Logger) -> list[dict[str, str]]:
    """
    Loads email accounts and app passwords from an Excel (.xlsx) or CSV (.csv) file.
    Expected columns: 'gmail' (or 'email') and 'password'.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Accounts file not found: {file_path}")

    suffix = file_path.suffix.lower()
    accounts: list[dict[str, str]] = []

    if suffix in [".xlsx", ".xls"]:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                raise ValueError("Excel file is empty.")

            headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
            email_idx = next((i for i, h in enumerate(headers) if h in ["gmail", "email", "account"]), None)
            pass_idx = next((i for i, h in enumerate(headers) if h in ["password", "pass", "app_password"]), None)

            if email_idx is None or pass_idx is None:
                raise ValueError(
                    f"Excel file must contain 'gmail' and 'password' columns. Found columns: {headers}"
                )

            for row in rows[1:]:
                if not row or len(row) <= max(email_idx, pass_idx):
                    continue
                email_val = str(row[email_idx] or "").replace("\xa0", " ").strip()
                pass_val = str(row[pass_idx] or "").replace("\xa0", " ").strip()
                if email_val and pass_val and email_val.lower() != "none":
                    accounts.append({"email": email_val, "password": pass_val})

        except ImportError:
            raise ImportError(
                "openpyxl is required to read Excel files. "
                "Install it via: pip install openpyxl"
            )

    elif suffix == ".csv":
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or missing headers.")

            col_map = {c.strip().lower(): c for c in reader.fieldnames}
            email_col = next((c for c in ["gmail", "email", "account"] if c in col_map), None)
            pass_col = next((c for c in ["password", "pass", "app_password"] if c in col_map), None)

            if not email_col or not pass_col:
                raise ValueError(
                    f"CSV file must contain 'gmail' and 'password' headers. Found: {reader.fieldnames}"
                )

            real_email_col = col_map[email_col]
            real_pass_col = col_map[pass_col]

            for row in reader:
                email_val = row[real_email_col].replace("\xa0", " ").strip()
                pass_val = row[real_pass_col].replace("\xa0", " ").strip()
                if email_val and pass_val:
                    accounts.append({"email": email_val, "password": pass_val})
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Please provide a .xlsx or .csv file.")

    logger.info(f"Loaded {len(accounts)} valid accounts from {file_path.name}")
    return accounts


def build_message(sender: str, recipients: list[str], subject: str, body: str) -> MIMEMultipart:
    """Builds an RFC-compliant MIME email message."""
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg


def run_routine(
    accounts: list[dict[str, str]],
    wait_time: int,
    subject: str,
    body: str,
    dry_run: bool,
    test_auth_only: bool,
    logger: logging.Logger,
) -> None:
    """Iterates through accounts and executes SMTP login & email delivery."""
    all_emails = [acc["email"] for acc in accounts]
    total = len(accounts)

    logger.info(f"Starting routine with {total} accounts. Wait interval: {wait_time}s.")
    if dry_run:
        logger.info("[DRY RUN MODE] No network connections or emails will be initiated.")
    elif test_auth_only:
        logger.info("[AUTH TEST MODE] Credentials will be tested; no emails will be sent.")

    for idx, acc in enumerate(accounts, start=1):
        sender = acc["email"]
        password = acc["password"]

        logger.info(f"[{idx}/{total}] Processing account: {sender}")

        if dry_run:
            logger.info(f"[DRY RUN] Would login as {sender} and dispatch email to {len(all_emails)} recipients.")
            continue

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(sender, password)
                logger.info(f"✓ Authentication successful for {sender}")

                if not test_auth_only:
                    message = build_message(sender, all_emails, subject, body)
                    server.sendmail(sender, all_emails, message.as_string())
                    logger.info(f"✓ Message dispatched successfully from {sender} to {len(all_emails)} recipients.")

        except smtplib.SMTPAuthenticationError:
            logger.error(
                f"✗ Authentication failed for {sender}. "
                "Ensure 2-Factor Authentication is active and a valid Google App Password is used."
            )
        except smtplib.SMTPException as e:
            logger.error(f"✗ SMTP error occurred for {sender}: {e}")
        except Exception as e:
            logger.error(f"✗ Unexpected error for {sender}: {e}")

        # Sleep between accounts if not the last account and not in dry-run
        if idx < total and not dry_run and wait_time > 0:
            logger.info(f"Pausing for {wait_time} seconds before processing the next account...")
            time.sleep(wait_time)

    logger.info("=" * 50)
    logger.info("Routine execution finished.")
    logger.info("=" * 50)


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Gmail Routine Activity & Keep-Alive Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        default=None,
        help="Path to Excel (.xlsx) or CSV (.csv) containing 'gmail' and 'password' columns.",
    )
    parser.add_argument(
        "-d", "--delay",
        type=int,
        default=DEFAULT_WAIT_TIME,
        help=f"Delay in seconds between processing accounts (default: {DEFAULT_WAIT_TIME}s).",
    )
    parser.add_argument(
        "-s", "--subject",
        type=str,
        default=DEFAULT_SUBJECT,
        help=f"Email subject line (default: '{DEFAULT_SUBJECT}').",
    )
    parser.add_argument(
        "-b", "--body",
        type=str,
        default=DEFAULT_BODY,
        help="Custom body message for the email.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the workflow without authenticating or sending emails.",
    )
    parser.add_argument(
        "--test-auth",
        action="store_true",
        help="Test SMTP login credentials without sending emails.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="gmail_activity.log",
        help="Filename for storing activity logs (default: gmail_activity.log).",
    )
    return parser.parse_args()


def find_default_accounts_file() -> Path | None:
    """Searches for default candidate account files in current directory."""
    candidates = [
        "gmails pass.XLSX",
        "gmails pass.xlsx",
        "accounts.xlsx",
        "accounts.csv",
        "accounts_template.xlsx",
        "accounts_template.csv",
    ]
    for c in candidates:
        p = Path(c)
        if p.exists():
            return p
    return None


def main() -> None:
    args = parse_arguments()
    logger = setup_logger(args.log_file)

    accounts_file = args.file
    if accounts_file is None:
        accounts_file = find_default_accounts_file()
        if accounts_file is None:
            logger.error(
                "No accounts file found! Please specify a file via: "
                "python main.py --file your_accounts.xlsx (or .csv)"
            )
            sys.exit(1)

    logger.info(f"Target accounts file: {accounts_file}")

    try:
        accounts = load_accounts(accounts_file, logger)
        if not accounts:
            logger.warning("No valid accounts found in the file.")
            sys.exit(0)

        run_routine(
            accounts=accounts,
            wait_time=args.delay,
            subject=args.subject,
            body=args.body,
            dry_run=args.dry_run,
            test_auth_only=args.test_auth,
            logger=logger,
        )
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user. Exiting cleanly.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
