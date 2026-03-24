'use strict';

const crypto = require('crypto');
const readline = require('readline');

function askQuestion(query) {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });
    return new Promise(resolve => rl.question(query, (answer) => {
        rl.close();
        resolve(answer);
    }));
}

function obfuscate(str) {
    return Buffer.from(str).toString('base64').split('').reverse().join('');
}

async function run() {
    console.log('--- MagxxicVOT XII Admin Activation Kit ---');
    const hwid = await askQuestion('Enter User HWID: ');

    if (!hwid) {
        console.error('Error: HWID is required.');
        process.exit(1);
    }

    const token = crypto.createHash('sha256').update(hwid.trim().toUpperCase() + 'MAGXXICVOT-SALT').digest('hex').substring(0, 16).toUpperCase();
    const obfuscatedToken = obfuscate(token);

    console.log('\n--- Activation Details ---');
    console.log(`User HWID: ${hwid.trim().toUpperCase()}`);
    console.log(`Raw Token: ${token}`);
    console.log(`Obfuscated Token (activation.sys content): ${obfuscatedToken}`);
    console.log('\nCopy the obfuscated token into a file named "activation.sys" in the sender root directory.');
}

run();
