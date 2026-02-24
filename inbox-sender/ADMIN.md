# magxxicVox Inbox Sender - Administrator Guide

## Generating Activation Tokens

To generate an activation token for a user, use the following Node.js snippet:

```javascript
const crypto = require('crypto');

const SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024';
const hwid = 'USER_HWID_HERE'; // The HWID the user sends you

const token = crypto.createHash('sha256')
    .update(hwid + SECRET_SALT)
    .digest('hex')
    .toUpperCase();

console.log('Activation Token:', token);
```

## Setting up DKIM

To enable DKIM signing, create two files in the script directory:

1. `dkim_key.pem`: Your private RSA key (standard PEM format).
2. `dkim.sys`: Obfuscated configuration.

Generate `dkim.sys` using this snippet:

```javascript
const dkimConfig = {
    domainName: 'yourdomain.com',
    keySelector: 'default' // your DKIM selector
};
// Use the obfuscation helper from index.js to encode dkimConfig and save to dkim.sys
```

## Creating API Config Files

Use the following snippet to generate obfuscated config files for AWS, Mailgun, etc.

```javascript
// Example for AWS (aws.sys)
const awsConfig = {
    region: 'us-east-1',
    accessKeyId: 'YOUR_KEY',
    secretAccessKey: 'YOUR_SECRET'
};
// obf.encode(awsConfig) -> save to aws.sys

// Example for Mailgun (mailgun.sys)
const mailgunConfig = {
    apiKey: 'YOUR_API_KEY',
    domain: 'yourdomain.com'
};
// obf.encode(mailgunConfig) -> save to mailgun.sys

// Example for SendGrid (sendgrid.sys)
const sendgridConfig = {
    apiKey: 'YOUR_SENDGRID_KEY'
};
// obf.encode(sendgridConfig) -> save to sendgrid.sys

// Example for Brevo (brevo.sys)
const brevoConfig = {
    user: 'your-email',
    apiKey: 'your-brevo-api-key'
};
// obf.encode(brevoConfig) -> save to brevo.sys
```

## Anti-Tamper Notes
- The activation is locked to the specific hardware identifiers (CPU, UUID, Baseboard).
- If the user moves the files to another machine, they will be prompted for a new activation.
- The `activation.sys` file stores the paired HWID and Token.
