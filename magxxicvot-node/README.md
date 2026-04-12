# MagxxicVOT XII - Node.js Edition

This is the high-performance Node.js implementation of the MagxxicVOT XII Sender Suite.

## 📋 Prerequisites
*   Node.js 16.x or higher.
*   npm (installed with Node.js).

## 🚀 Quick Start
1.  Run `setup.bat` to install dependencies (including Puppeteer).
2.  Edit `smtp.txt` (format: `host|port|user|pass|fromEmail`).
3.  Edit `list.txt` with recipient email addresses.
4.  Place your HTML templates in the `letters/` directory.
5.  Run `start.bat`.

## 🛠️ Configuration
All major settings are managed through the interactive **Settings Dashboard** upon startup. This allows you to toggle proxies, attachments, encryption, and unique URL generation on-the-fly.

## 🛡️ Stealth Features
*   **Hide My IP**: Masks your originating IP in headers.
*   **User-Agent Rotation**: Randomizes headers using a pool of modern browser strings.
*   **SOCKS5 Tunneling**: Full SMTP traffic redirection through proxies.
