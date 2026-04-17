# MagxxicVOT XII - Email Contact Fetcher

A professional tool for extracting and exporting contacts from any IMAP-enabled email account.

## Features
- **Auto-Discovery:** Automatically suggests IMAP settings based on the email domain.
- **Deep Scanning:** Scans multiple folders (INBOX, Sent, etc.) for unique contact addresses.
- **Clean Export:** Exports unique, cleaned email addresses to a text file.
- **TUI Interface:** Beautiful terminal user interface with progress bars and status updates.

## Setup
1. Ensure you have Python 3.6+ installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the script and follow the on-screen prompts:
```bash
python fetcher.py
```

## Security Note
If you are using Gmail or Outlook, you may need to:
1. Enable IMAP in your account settings.
2. Generate and use an **App Password** instead of your primary account password.
3. Enable 'Less Secure Apps' if applicable.

## Disclaimer
This tool is for professional security auditing and administrative use only. Always ensure you have permission before accessing any email account.
