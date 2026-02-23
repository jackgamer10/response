# magxxicVox Inbox Sender v4.0

A professional-grade, multi-platform (Node.js & Python) email deployment suite designed for high-deliverability and anonymity.

## 🚀 Features

- **Dual-Stack Engine:** Full feature parity between Node.js and Python implementations.
- **Advanced Transport:** Supports SMTP rotation, API-based sending (AWS SES, Mailgun, SendGrid, Brevo), and Direct MX (Port 25) sending.
- **Anonymity & Security:** Integrated SOCKS proxy rotation, Military-Grade MIME header spoofing, and IP-hiding (masking originating IPs to 127.0.0.1).
- **Live Dashboard:** Real-time console metrics showing Sent/Success/Failed counts, Bounce Analysis (Hard/Soft/Spam), and Domain Engagement reports.
- **Dynamic Content:** Automatic rotation of Subjects, HTML Letters, and Links. Supports advanced tag replacement (e.g., `[-email-]`, `[-randommd5-]`).
- **Attachment Intelligence:**
    - Auto-convert HTML templates to PDF or PNG on-the-fly.
    - Attachment encryption (AES-256-CBC or Password-Protected ZIP).
    - SHA-256 Cryptographic Signing (`.sig` files).
- **Machine Locked:** Hardware ID (HWID) based license activation system.

---

## 🛠️ Installation & Setup

### 1. Requirements
- **Node.js Version:** Node.js 18+ installed.
- **Python Version:** Python 3.9+ installed.
- **Chrome/Chromium:** Required for HTML-to-PDF conversion (handled by `puppeteer` in Node and `html2image` in Python).

### 2. Quick Setup
Both versions include a `setup.bat` for Windows.
- **Node.js:** Navigate to `inbox-sender/` and run `setup.bat`.
- **Python:** Navigate to `inbox-sender-python/` and run `setup.bat`.

---

## 📖 Usage Instructions

### 1. Activation
When you first run the sender (`start.bat`), it will display your unique **HWID**.
1. Use the **Admin Toolkit** (`admin-token-activation-generator/`) to generate an activation token.
2. Enter the token when prompted. The software will save an `activation.sys` file and activate.

### 2. Configuration Files
All configuration files use a readable `.sys` (JSON) format.
- `config.sys`: General settings (delays, rotations, attachment modes).
- `smtp.txt`: List of SMTP servers in `host|port|user|pass|fromEmail` format.
- `from_emails.txt`: List of sender email addresses (used for Direct MX and SMTP rotation).
- `proxies.txt`: List of SOCKS5 proxies in `ip:port` or `user:pass@ip:port` format.
- `list.txt`: Your recipient email list.
- `subjects.txt`: Subject line rotation.
- `letters/`: Folder containing your `.html` email templates.
- `links.txt`: URL rotation for the `[-link-]` tag.

### 3. Starting the Sender
Run `start.bat` in your preferred project folder. Select the sending mode:
1. **SMTP:** Uses servers from `smtp.txt`.
2. **API:** Uses configurations from `aws.sys`, `mailgun.sys`, etc.
3. **Direct MX:** Sends directly to recipient servers on Port 25 via proxies.

---

## 🔐 Security & Email Signing

### Setting up DKIM
DKIM (DomainKeys Identified Mail) provides a way to validate a domain name identity that is associated with a message.
1. **Generate Keys:** Generate a 2048-bit RSA private key (`dkim_key.pem`).
2. **Configure DNS:** Add the corresponding public key to your domain's DNS records.
3. **Generate dkim.sys:**
   - Use the **Admin Toolkit** (Option 6).
   - Input your Domain Name and Selector.
   - Place the generated `dkim.sys` and your `dkim_key.pem` in the main sender folder.
4. **Enable:** The sender will automatically detect these files and sign outgoing emails.

### Email Content Signing
To provide an extra layer of authenticity, you can enable SHA-256 signing for attachments.
1. Open `config.sys`.
2. Set `"signAttachment": true`.
3. The sender will generate a `.sig` file containing a SHA-256 hash of the attachment and include it in the email.

---

## 📡 Direct MX Configuration

Direct MX sending bypasses standard SMTP relays and connects directly to the recipient's mail server.

### 1. Protocol Configuration (`direct_mx_config.sys`)
- `heloDomain`: The domain name used in the `HELO/EHLO` handshake (e.g., `mail.yourdomain.com`).
- `timeout`: Connection timeout in milliseconds.

### 2. Behavioral Settings (`direct_mx_settings.sys`)
- `retries`: Number of attempts per recipient.
- `verifyDns`: If `true`, the sender performs a deep DNS/MX check before attempting to send.

---

## 🏷️ Template Tags

You can use the following tags in your `letters/*.html` or `attachment.html`:
- `[-email-]`: Full recipient email.
- `[-emailuser-]`: Everything before the `@`.
- `[-randomstring-]`: Random alphanumeric string.
- `[-randomnumber-]`: Random 4-digit number.
- `[-time-]`: Current timestamp.
- `[-barcode-DATA-]`: Generates a barcode for "DATA".
- `[-recipient-logo-]`: Automatically fetches the recipient's company logo.
- `[-link-]`: Randomly selected link from `links.txt`.

---

## 📊 Live Dashboard Guide

- **DELIVERED:** Count of successfully sent emails.
- **FAILED:** Emails that encountered a transport error.
- **SUCCESS RATE:** Percentage of success vs. failure.
- **BOUNCE INTELLIGENCE:**
    - **HARD:** Permanent failures (User not found).
    - **SOFT:** Temporary failures (Inbox full).
    - **SPAM:** Blocked/Filtered due to content or IP reputation.
- **SPAM SCORE:** Real-time heuristic evaluation of your content.

---
*Created by magxxicVox Inbox Team*
