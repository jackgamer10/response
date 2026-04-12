# MagxxicVOT XII - Python Edition

This is the robust Python implementation of the MagxxicVOT XII Sender Suite.

## 📋 Prerequisites
*   Python 3.8.x or higher.
*   pip (Python package installer).

## 🚀 Quick Start
1.  Run `setup.bat` to install dependencies (uses `minify-html` for compatibility).
2.  Edit `smtp.txt` (format: `host|port|user|pass|fromEmail`).
3.  Edit `list.txt` with recipient email addresses.
4.  Place your HTML templates in the `letters/` directory.
5.  Run `start.bat`.

## 🛠️ Configuration
All major settings are managed through the interactive **Settings Dashboard** upon startup. This allows you to toggle proxies, attachments, encryption, and unique URL generation on-the-fly.

## 🛡️ Stealth Features
*   **Hide My IP**: Masks your originating IP in headers.
*   **User-Agent Rotation**: Randomizes headers using a pool of modern browser strings.
*   **SOCKS5 Tunneling**: Full SMTP traffic redirection through proxies using `socks.socksocket`.
