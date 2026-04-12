'use strict';

const crypto = require('crypto');
const readline = require('readline');

function obfuscate(str) {
    return Buffer.from(str).toString('base64').split('').reverse().join('');
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

console.log('--- MagxxicVOT XII Admin Activation Generator ---');
rl.question('Enter User HWID: ', (hwid) => {
    const salt = 'MAGXXICVOT-XII-SALT';
    const token = crypto.createHash('sha256').update(hwid.trim().toUpperCase() + salt).digest('hex').substring(0, 16).toUpperCase();

    console.log('\n-----------------------------------');
    console.log('Activation Token: ' + token);
    console.log('Obfuscated Token (for manual entry if needed): ' + obfuscate(token));
    console.log('-----------------------------------\n');

    rl.close();
});
