'use strict';
const crypto = require('crypto');

const key = process.argv[2];

if (!key) {
    console.error('Error: Please provide a key to hash.');
    console.error('Usage: node generate-hash.js YOUR_KEY_HERE');
    process.exit(1);
}

const hash = crypto.createHash('sha256').update(key.trim()).digest('hex');
console.log(`The SHA256 hash for "${key}" is:`);
console.log(hash);
