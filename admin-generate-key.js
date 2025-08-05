'use strict';
const crypto = require('crypto');

// Generate a new UUID (v4) as the license key
const newKey = crypto.randomUUID();

// Calculate the SHA256 hash of the new key
const hash = crypto.createHash('sha256').update(newKey.trim()).digest('hex');

console.log('New License Key (give this to your user):');
console.log(newKey);
console.log(''); // Add a blank line for readability
console.log('SHA256 Hash (add this to mailer.js):');
console.log(hash);
