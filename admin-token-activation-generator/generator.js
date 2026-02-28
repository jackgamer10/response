'use strict';

process.noDeprecation = true;

const crypto = require('crypto');
const fs = require('fs');
const readline = require('readline');

const colors = {
    reset: "\x1b[0m",
    bright: "\x1b[1m",
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    cyan: "\x1b[36m",
    magenta: "\x1b[35m",
    red: "\x1b[31m",
    white: "\x1b[37m"
};

const SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024';

const obf = {
    encode: (data) => {
        const json = JSON.stringify(data, null, 4);
        return Buffer.from(json).toString('base64').split('').reverse().join('');
    }
};

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function ask(query) {
    return new Promise(resolve => rl.question(`${colors.cyan}│ ${colors.reset}${query}`, resolve));
}

async function menu() {
    console.clear();
    console.log(`${colors.magenta}┌───────────────────────────────────────────────────┐${colors.reset}`);
    console.log(`${colors.magenta}│${colors.bright}${colors.cyan}      magxxicVox Admin Toolkit (Node.js)           ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}├───────────────────────────────────────────────────┤${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  1. Generate Activation Token (from HWID)         ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  2. Create AWS Config (aws.sys)                   ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  3. Create Brevo Config (brevo.sys)               ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  4. Create Mailgun Config (mailgun.sys)           ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  5. Create SendGrid Config (sendgrid.sys)         ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  6. Create DKIM Config (dkim.sys)                 ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  7. Create Direct MX Config (direct_mx.sys)       ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  8. Create App Config (config.sys)                ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  0. Exit                                          ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}└───────────────────────────────────────────────────┘${colors.reset}`);

    const choice = await ask('Select option: ');

    switch (choice) {
        case '1':
            const hwid = await ask('Enter User HWID: ');
            const token = crypto.createHash('sha256').update(hwid.trim() + SECRET_SALT).digest('hex').toUpperCase();
            console.log(`\n${colors.green}[+] Generated Token:${colors.reset} ${colors.bright}${token}${colors.reset}\n`);
            break;

        case '2':
            const aws = {
                region: await ask('Region (e.g. us-east-1): '),
                accessKeyId: await ask('Access Key ID: '),
                secretAccessKey: await ask('Secret Access Key: ')
            };
            fs.writeFileSync('aws.sys', obf.encode(aws));
            console.log(`\n${colors.green}[+] Created aws.sys${colors.reset}\n`);
            break;

        case '3':
            const brevo = {
                user: await ask('Brevo User Email: '),
                apiKey: await ask('Brevo API Key: ')
            };
            fs.writeFileSync('brevo.sys', obf.encode(brevo));
            console.log(`\n${colors.green}[+] Created brevo.sys${colors.reset}\n`);
            break;

        case '4':
            const mailgun = {
                apiKey: await ask('Mailgun API Key: '),
                domain: await ask('Mailgun Domain: ')
            };
            fs.writeFileSync('mailgun.sys', obf.encode(mailgun));
            console.log(`\n${colors.green}[+] Created mailgun.sys${colors.reset}\n`);
            break;

        case '5':
            const sendgrid = {
                apiKey: await ask('SendGrid API Key: ')
            };
            fs.writeFileSync('sendgrid.sys', obf.encode(sendgrid));
            console.log(`\n${colors.green}[+] Created sendgrid.sys${colors.reset}\n`);
            break;

        case '6':
            const dkim = {
                domainName: await ask('DKIM Domain: '),
                keySelector: await ask('DKIM Selector: ')
            };
            fs.writeFileSync('dkim.sys', obf.encode(dkim));
            console.log(`\n${colors.green}[+] Created dkim.sys${colors.reset}`);
            console.log(`${colors.yellow}[!] Remember to place dkim_key.pem in the same folder.${colors.reset}\n`);
            break;

        case '7':
            const dm_config = {
                heloDomain: await ask('HELO/EHLO Domain (e.g. mail.example.com): '),
                timeout: parseInt(await ask('Timeout in ms (default 10000): ')) || 10000
            };
            const dm_settings = {
                retries: parseInt(await ask('Max Retries (default 3): ')) || 3,
                verifyDns: (await ask('Verify DNS/MX before send? (y/n): ')).toLowerCase() === 'y'
            };
            fs.writeFileSync('direct_mx_config.sys', obf.encode(dm_config));
            fs.writeFileSync('direct_mx_settings.sys', obf.encode(dm_settings));
            console.log(`\n${colors.green}[+] Created direct_mx_config.sys and direct_mx_settings.sys${colors.reset}\n`);
            break;

        case '8':
            const sendAttachment = (await ask('Send Attachment? (y/n): ')).toLowerCase() === 'y';
            let attachmentType = 'None';
            if (sendAttachment) {
                console.log('\n  1. PDF');
                console.log('  2. Image');
                console.log('  3. SVG');
                const typeChoice = await ask('Select Attachment Format (1-3): ');
                attachmentType = typeChoice === '1' ? 'PDF' : (typeChoice === '2' ? 'Image' : 'SVG');
            }

            const config = {
                rotateLetters: (await ask('Rotate Letters? (y/n): ')).toLowerCase() === 'y',
                autoShortenLinks: (await ask('Auto Shorten Links? (y/n): ')).toLowerCase() === 'y',
                sendAttachment: sendAttachment,
                attachmentType: attachmentType,
                delayBetweenEmails: parseInt(await ask('Delay between emails (ms): ')) || 2000,
                pauseEvery: parseInt(await ask('Pause every X emails: ')) || 50,
                pauseTime: parseInt(await ask('Pause duration (ms): ')) || 30000,
                encryptionMethod: await ask('Encryption Method (None/AES-256-CBC/ZIP): ') || 'ZIP',
                encryptionPassword: await ask('Encryption Password: ') || 'secret',
                signAttachment: (await ask('Sign Attachment? (y/n): ')).toLowerCase() === 'y'
            };
            fs.writeFileSync('config.sys', obf.encode(config));
            console.log(`\n${colors.green}[+] Created config.sys${colors.reset}\n`);
            break;

        case '0':
            process.exit(0);

        default:
            console.log(`${colors.red}[!] Invalid selection.${colors.reset}`);
    }

    await ask('Press Enter to continue...');
    menu();
}

menu();
