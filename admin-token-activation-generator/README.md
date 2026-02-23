# magxxicVox Admin Toolkit

This folder contains tools for administrators to generate activation tokens and obfuscated configuration files for the `inbox-sender` and `inbox-sender-python` tools.

## Features

- **Activation Token Generation**: Generate a machine-specific token based on the user's HWID.
- **API Config Creation**: Generate obfuscated `.sys` files for AWS, Brevo, Mailgun, and SendGrid.
- **DKIM Config Creation**: Generate obfuscated `dkim.sys` files.

## How to Use (Node.js)

1. Navigate to this folder.
2. Run `node generator.js`.
3. Follow the interactive menu.

## How to Use (Python)

1. Navigate to this folder.
2. Run `python generator.py`.
3. Follow the interactive menu.

## Files Produced

- `aws.sys`: Place in the sender's root directory if using AWS SES.
- `brevo.sys`: Place in the sender's root directory if using Brevo API.
- `mailgun.sys`: Place in the sender's root directory if using Mailgun API.
- `sendgrid.sys`: Place in the sender's root directory if using SendGrid API.
- `dkim.sys`: Place in the sender's root directory for DKIM signing.

**Note**: For DKIM, you must also provide the `dkim_key.pem` (private key) file in the same folder as the sender.
