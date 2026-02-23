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

## Anti-Tamper Notes
- The activation is locked to the specific hardware identifiers (CPU, UUID, Baseboard).
- If the user moves the files to another machine, they will be prompted for a new activation.
- The `activation.dat` file stores the paired HWID and Token.
