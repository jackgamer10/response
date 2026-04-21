# MagxxicVOT XII - Professional Stealth Sender Suite

MagxxicVOT XII is a high-performance, multi-platform mailing suite designed for advanced deliverability, anonymity, and content automation. Available in both Node.js and Python, it features a robust TUI and a comprehensive diagnostic engine.

## 🚀 Key Features

*   **Dual-Platform Support**: Full feature parity between Node.js and Python implementations.
*   **Advanced Anonymity**:
    *   SOCKS5 Proxy Rotation with automatic validation.
    *   "Hide My IP" Header Masking (X-Originating-IP, X-Forwarded-For, etc.).
    *   User-Agent Rotation from a modern browser pool.
    *   **Stealth Headers**: Invisible Unicode character injection for From Names.
*   **Dynamic Content Engine**:
    *   Unique URL generation per recipient.
    *   Code128 Barcode generation (`[-barcode-DATA-]`).
    *   Automatic Recipient Logo detection via Clearbit API (`[-recipient-logo-]`).
    *   Robust Tag Support: `[-email-]`, `[-time-]`, `[-date-]`, `[-randomnumber-]`, `[-randomhex-]`, etc.
*   **Auto Language Translation**:
    *   **Geo-Detection**: Automatically detects recipient's native language via Email TLD (e.g., .fr -> French, .de -> German).
    *   **On-the-fly Localization**: Translates letter body and subject while preserving HTML tags and dynamic data.
*   **Multi-Attachment Pipeline**:
    *   **Convert**: On-the-fly conversion from HTML to PDF, PNG, or SVG with source minification.
    *   **Pick**: Send any existing file directly (DOCX, ZIP, PDF, HTML, etc.).
    *   **Personalization**: Every attachment receives a **unique name** using the dynamic tag engine.
    *   Optional AES-256-CBC Encryption and SHA-256 Cryptographic Signing.
*   **Diagnostic & Testing Tools**:
    *   Heuristic Spam Score evaluation with deliverability suggestions.
    *   Multiple SMTP Connectivity & Inboxing Test.
    *   Single Email Setup verification mode.
*   **Live Dashboard**: Real-time tracking of attempts, successes, failures, and active proxies.
*   **Security**:
    *   HWID-based activation system with SHA-256 machine identification.
    *   **Smart Decoding**: Support for `base64:` and `hex:` prefixes in config files for obfuscated credentials.

## 🛠️ Installation

### Node.js Version
1.  Navigate to `magxxicvot-node/`.
2.  Run `setup.bat`.
3.  Configure `smtp.txt`, `list.txt`, and `letters/`.
4.  Run `start.bat`.

### Python Version
1.  Navigate to `magxxicvot-python/`.
2.  Run `setup.bat`.
3.  Configure `smtp.txt`, `list.txt`, and `letters/`.
4.  Run `start.bat`.

## 📂 Project Structure
*   `magxxicvot-node/`: Node.js implementation (requires Node.js 16+).
*   `magxxicvot-python/`: Python implementation (requires Python 3.8+).
*   `admin-activation-kit/`: Tools for administrators to generate license tokens.
*   `DISCLAIMER.md`: Legal and ethical usage information.

## ⚖️ License & Usage
Usage of this software is subject to the terms outlined in [DISCLAIMER.md](DISCLAIMER.md).
