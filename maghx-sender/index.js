'use strict';

const nodemailer = require('nodemailer');
const fs = require('fs').promises;
const randomstring = require('randomstring');
const htmlPdf = require('html-pdf-node');
const crypto = require('crypto');
const readline = require('readline');
const minify = require('html-minifier').minify;
const { SocksProxyAgent } = require('socks-proxy-agent');
const path = require('path');
const bwipjs = require('bwip-js');
const nodeHtmlToImage = require('node-html-to-image');
const axios = require('axios');
const chalk = require('chalk');

let stats = {
    sent: 0,
    success: 0,
    failed: 0,
    currentProxy: 'None'
};

// Configuration & Toggles
const CONFIG = {
    senderName: 'IONOS Customer Service',
    lettersDir: 'letters',
    subjectsPath: 'subject.txt',
    linksPath: 'links.txt',
    proxiesPath: 'proxies.txt',
    emailListPath: 'list.txt',
    smtpPath: 'smtp.txt',
    attachmentHtmlPath: 'attachment.html',
    delayBetweenEmails: 6000,
    pdfQuality: 50,

    // Feature Toggles (Defaults)
    useProxy: true,
    autoValidateProxies: true,
    attachmentType: 'pdf', // 'pdf', 'png', or 'none'
    encryptAttachment: false, // AES-256-CBC
    encryptionPassword: 'MaghxSecurePassword',
    signAttachment: true, // SHA-256 .sig file
    minifyHtml: true,
    useCustomFromEmail: true,
    retryAttempts: 3
};

function askQuestion(query) {
    console.log(chalk.cyan('┌───────────────────────────────────────────────────┐'));
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        prompt: chalk.cyan('│ ') + chalk.yellow(query)
    });

    rl.prompt();

    return new Promise(resolve => rl.on('line', (line) => {
        rl.close();
        console.log(chalk.cyan('└───────────────────────────────────────────────────┘'));
        resolve(line);
    }));
}

function getHWID() {
    const os = require('os');
    const networkInterfaces = os.networkInterfaces();
    let mac = '';
    for (const name of Object.keys(networkInterfaces)) {
        for (const net of networkInterfaces[name]) {
            if (!net.internal && net.mac !== '00:00:00:00:00:00') {
                mac = net.mac;
                break;
            }
        }
        if (mac) break;
    }
    const hwidInfo = `${os.hostname()}-${os.type()}-${os.arch()}-${mac}`;
    return crypto.createHash('sha256').update(hwidInfo).digest('hex').substring(0, 16).toUpperCase();
}

function obfuscate(str) {
    return Buffer.from(str).toString('base64').split('').reverse().join('');
}

function deobfuscate(str) {
    return Buffer.from(str.split('').reverse().join(''), 'base64').toString('utf-8');
}

async function checkLicense() {
    const hwid = getHWID();
    const activationFile = 'activation.sys';

    try {
        const obfuscatedToken = await fs.readFile(activationFile, 'utf-8');
        const token = deobfuscate(obfuscatedToken);
        const expectedToken = crypto.createHash('sha256').update(hwid + 'MAGXXICVOT-SALT').digest('hex').substring(0, 16).toUpperCase();

        if (token !== expectedToken) {
            throw new Error('Invalid activation token.');
        }
        console.log(chalk.green('✔ License activated successfully.'));
    } catch (err) {
        console.log(chalk.yellow(`\nYour HWID: `) + chalk.cyan(hwid));
        const enteredToken = await askQuestion('Please enter your activation token: ');
        const expectedToken = crypto.createHash('sha256').update(hwid + 'MAGXXICVOT-SALT').digest('hex').substring(0, 16).toUpperCase();

        if (enteredToken.trim().toUpperCase() === expectedToken) {
            console.log(chalk.green('✔ Token validated. Activating...'));
            await fs.writeFile(activationFile, obfuscate(enteredToken.trim().toUpperCase()));
            if (process.platform === 'win32') {
                const { exec } = require('child_process');
                exec(`attrib +h ${activationFile}`);
            }
        } else {
            console.error(chalk.red('✘ Error: Invalid activation token. Please contact the administrator.'));
            process.exit(1);
        }
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function printWithDelay(text, delayTime, color = chalk.white) {
    return new Promise(resolve => {
        setTimeout(() => {
            console.log(color(text));
            resolve();
        }, delayTime);
    });
}

async function printLines() {
    await printWithDelay('MagxxicVOT XII Sender Start', 500, chalk.cyan.bold);
    await printWithDelay('', 500);
    await printWithDelay(`
███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗██╗   ██╗ ██████╗ ████████╗  ██╗  ██╗██╗██╗
████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝██║██╔════╝██║   ██║██╔═══██╗╚══██╔══╝  ╚██╗██╔╝██║██║
██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝ ██║██║     ██║   ██║██║   ██║   ██║      ╚███╔╝ ██║██║
██║╚██╔╝██║██╔══██║██║   ██║██╔══██║ ██╔██╗ ██║██║     ╚██╗ ██╔╝██║   ██║   ██║      ██╔██╗ ██║██║
██║ ╚═╝ ██║██║  ██║╚██████╔╝██║  ██║██╔╝ ██╗██║╚██████╗ ╚████╔╝ ╚██████╔╝   ██║     ██╔╝ ██╗██║██║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═══╝   ╚═════╝    ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝
`, 500, chalk.magenta.bold);
    await printWithDelay('[+] MagxxicVOT XII v1.1', 500, chalk.blue.bold);
    await printWithDelay('[+] Military-Grade MIME & Proxy Rotation', 500, chalk.blue);
    await printWithDelay('[+] Advanced Content & Attachment Shield', 500, chalk.blue);
}

async function validateProxies(proxies) {
    console.log(chalk.yellow(`Validating ${proxies.length} proxies...`));
    const validProxies = [];
    for (const proxy of proxies) {
        try {
            const agent = new SocksProxyAgent(proxy);
            await axios.get('http://www.google.com', {
                httpAgent: agent,
                httpsAgent: agent,
                timeout: 5000,
                validateStatus: () => true
            });
            validProxies.push(proxy);
            console.log(chalk.green(`✔ Proxy ${proxy} OK.`));
        } catch (err) {
            console.log(chalk.red(`✘ Proxy ${proxy} FAILED.`));
        }
    }
    return validProxies;
}

async function generateBarcode(data) {
    return new Promise((resolve, reject) => {
        bwipjs.toBuffer({
            bcid: 'code128',
            text: data,
            scale: 3,
            height: 10,
            includetext: true,
            textxalign: 'center',
        }, function (err, png) {
            if (err) reject(err);
            else resolve(png.toString('base64'));
        });
    });
}

async function replaceTags(text, replacements) {
    let content = text;
    content = content.replace(/\[-email-\]/g, replacements['-email-'] || '');
    content = content.replace(/\[-emailuser-\]/g, replacements['-emailuser-'] || '');
    content = content.replace(/\[-emaildomain-\]/g, replacements['-emaildomain-'] || '');
    content = content.replace(/\[-emaildomainname-\]/g, replacements['-emaildomainname-'] || '');
    content = content.replace(/\[-link-\]/g, replacements['-link-'] || '');
    content = content.replace(/\[-randomstring-\]/g, () => randomstring.generate());
    content = content.replace(/\[-randomnumber-\]/g, () => Math.floor(1000 + Math.random() * 9000).toString());
    content = content.replace(/\[-randomletters-\]/g, () => randomstring.generate({ charset: 'alphabetic' }));
    content = content.replace(/\[-randommd5-\]/g, () => crypto.createHash('md5').update(randomstring.generate()).digest('hex'));
    content = content.replace(/\[-time-\]/g, () => new Date().toLocaleString());
    const domain = replacements['-emaildomain-'] || (replacements['-email-'] ? replacements['-email-'].split('@')[1] : '');
    const logoUrl = domain ? `https://logo.clearbit.com/${domain}` : '';
    content = content.replace(/\[-recipient-logo-\]/g, `<img src="${logoUrl}" alt="Logo" style="max-height: 50px;">`);
    const barcodeRegex = /\[-barcode-(.*?)-\]/g;
    const matches = [...content.matchAll(barcodeRegex)];
    for (const match of matches) {
        const barcodeData = match[1];
        const barcodeBase64 = await generateBarcode(barcodeData);
        content = content.replace(match[0], `<img src="data:image/png;base64,${barcodeBase64}" alt="Barcode">`);
    }
    return content;
}

async function encryptData(data, password) {
    const algorithm = 'aes-256-cbc';
    const key = crypto.scryptSync(password, 'salt', 32);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(algorithm, key, iv);
    let encrypted = cipher.update(data);
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    return Buffer.concat([iv, encrypted]);
}

async function signData(data) {
    return crypto.createHash('sha256').update(data).digest('hex');
}

async function loadList(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return content.split(/\r?\n/).filter(line => line.trim() !== '');
    } catch (err) {
        return [];
    }
}

async function loadSmtp(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return content.split(/\r?\n/).filter(line => line.trim() !== '').map(line => {
            const parts = line.split('|');
            return {
                host: parts[0],
                port: parseInt(parts[1]),
                auth: { user: parts[2], pass: parts[3] },
                fromEmail: parts[4] || parts[2]
            };
        });
    } catch (err) {
        console.error(chalk.red(`✘ Error loading SMTP: ${err.message}`));
        return [];
    }
}

function updateDashboard() {
    process.stdout.write('\x1Bc');
    console.log(chalk.cyan('┌───────────────────────────────────────────────────┐'));
    console.log(chalk.cyan('│             ') + chalk.magenta.bold('MAGXXICVOT XII LIVE DASHBOARD') + chalk.cyan('         │'));
    console.log(chalk.cyan('├───────────────────────────────────────────────────┤'));
    console.log(chalk.cyan('│ ') + chalk.white('Sent      : ') + chalk.yellow(stats.sent.toString().padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('│ ') + chalk.white('Success   : ') + chalk.green(stats.success.toString().padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('│ ') + chalk.white('Failed    : ') + chalk.red(stats.failed.toString().padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('│ ') + chalk.white('Proxy     : ') + chalk.blue(stats.currentProxy.padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('├───────────────────────────────────────────────────┤'));
    console.log(chalk.cyan('│ ') + chalk.white('Status    : ') + chalk.blue('Mailing in progress...') + chalk.cyan('                │'));
    console.log(chalk.cyan('└───────────────────────────────────────────────────┘'));
}

async function sendEmails() {
    try {
        const emailList = await loadList(CONFIG.emailListPath);
        const subjects = await loadList(CONFIG.subjectsPath);
        const links = await loadList(CONFIG.linksPath);
        const smtpConfigs = await loadSmtp(CONFIG.smtpPath);
        let proxies = await loadList(CONFIG.proxiesPath);

        if (smtpConfigs.length === 0) throw new Error('No SMTP configurations found.');

        if (CONFIG.useProxy && CONFIG.autoValidateProxies && proxies.length > 0) {
            proxies = await validateProxies(proxies);
        }

        const letterFiles = (await fs.readdir(CONFIG.lettersDir)).filter(file => file.endsWith('.html'));

        let smtpIndex = 0;
        let proxyIndex = 0;
        let subjectIndex = 0;
        let linkIndex = 0;
        let letterIndex = 0;

        for (const email of emailList) {
            let attempts = 0;
            let sent = false;

            while (attempts < CONFIG.retryAttempts && !sent) {
                try {
                    const currentSmtpConfig = smtpConfigs[smtpIndex];
                    const currentProxy = proxies.length > 0 ? proxies[proxyIndex] : null;
                    stats.currentProxy = currentProxy || 'Direct';
                    updateDashboard();

                    const currentSubject = subjects.length > 0 ? subjects[subjectIndex] : 'Security Update';
                    const currentLink = links.length > 0 ? links[linkIndex] : '';
                    const currentLetterFile = letterFiles.length > 0 ? path.join(CONFIG.lettersDir, letterFiles[letterIndex]) : null;

                    const replacements = {
                        '-email-': email,
                        '-emailuser-': email.split('@')[0],
                        '-emaildomain-': email.split('@')[1],
                        '-emaildomainname-': email.split('@')[1].split('.')[0],
                        '-link-': currentLink
                    };

                    let htmlContent = currentLetterFile ? await fs.readFile(currentLetterFile, 'utf-8') : 'Default Content';
                    htmlContent = await replaceTags(htmlContent, replacements);
                    const subject = await replaceTags(currentSubject, replacements);
                    const senderName = await replaceTags(CONFIG.senderName, replacements);

                    const transportOptions = { ...currentSmtpConfig };
                    if (CONFIG.useProxy && currentProxy) {
                        transportOptions.agent = new SocksProxyAgent(currentProxy);
                    }
                    const transporter = nodemailer.createTransport(transportOptions);

                    const fromEmail = CONFIG.useCustomFromEmail && currentSmtpConfig.fromEmail ? currentSmtpConfig.fromEmail : currentSmtpConfig.auth.user;
                    const fromAddress = `"${senderName}" <${fromEmail}>`;

                    const mailOptions = {
                        from: fromAddress,
                        to: email,
                        subject: subject,
                        html: htmlContent,
                        attachments: [],
                        headers: {
                            'X-Mailer': 'Microsoft Outlook 16.0',
                            'X-Priority': '1 (Highest)',
                            'Importance': 'High',
                            'X-MSMail-Priority': 'High',
                            'X-Originating-IP': '127.0.0.1',
                            'X-Forwarded-For': '127.0.0.1',
                            'X-Real-IP': '127.0.0.1'
                        }
                    };

                    if (CONFIG.attachmentType !== 'none') {
                        let attachmentHtml = await fs.readFile(CONFIG.attachmentHtmlPath, 'utf-8');
                        attachmentHtml = await replaceTags(attachmentHtml, replacements);
                        if (CONFIG.minifyHtml) attachmentHtml = minify(attachmentHtml, { collapseWhitespace: true, removeComments: true });

                        let buffer;
                        let filename = `Document_${randomstring.generate(7)}`;
                        let contentType;

                        if (CONFIG.attachmentType === 'pdf') {
                            buffer = await htmlPdf.generatePdf({ content: attachmentHtml }, { format: 'A4', quality: CONFIG.pdfQuality });
                            filename += '.pdf';
                            contentType = 'application/pdf';
                        } else if (CONFIG.attachmentType === 'png') {
                            buffer = await nodeHtmlToImage({ html: attachmentHtml });
                            filename += '.png';
                            contentType = 'image/png';
                        }

                        if (CONFIG.encryptAttachment) {
                            buffer = await encryptData(buffer, CONFIG.encryptionPassword);
                            filename += '.enc';
                        }

                        mailOptions.attachments.push({ filename, content: buffer, contentType });
                        if (CONFIG.signAttachment) {
                            const signature = await signData(buffer);
                            mailOptions.attachments.push({ filename: filename + '.sig', content: signature, contentType: 'text/plain' });
                        }
                    }

                    await transporter.sendMail(mailOptions);
                    stats.sent++;
                    stats.success++;
                    sent = true;

                } catch (err) {
                    attempts++;
                    if (attempts >= CONFIG.retryAttempts) {
                        console.error(chalk.red(`✘ Failed to send to ${email} after ${attempts} attempts: ${err.message}`));
                        stats.sent++;
                        stats.failed++;
                    } else {
                        // Rotate on failure
                        smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
                        if (proxies.length > 0) proxyIndex = (proxyIndex + 1) % proxies.length;
                        await delay(2000);
                    }
                }
            }

            // Normal rotation
            smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
            if (proxies.length > 0) proxyIndex = (proxyIndex + 1) % proxies.length;
            if (subjects.length > 0) subjectIndex = (subjectIndex + 1) % subjects.length;
            if (links.length > 0) linkIndex = (linkIndex + 1) % links.length;
            if (letterFiles.length > 0) letterIndex = (letterIndex + 1) % letterFiles.length;
            await delay(CONFIG.delayBetweenEmails);
        }
    } catch (err) {
        console.error(chalk.red.bold(`✘ Fatal Error: ${err.message}`));
    }
}

async function run() {
    await checkLicense();
    await printLines();

    console.log(chalk.magenta.bold('\n--- Settings Dashboard ---'));
    const customFrom = await askQuestion('Use Custom From Email? (y/n): ');
    CONFIG.useCustomFromEmail = customFrom.toLowerCase() === 'y';
    const useProxy = await askQuestion('Use SOCKS Proxy? (y/n): ');
    CONFIG.useProxy = useProxy.toLowerCase() === 'y';
    const attachment = await askQuestion('Attachment Type (pdf/png/none): ');
    CONFIG.attachmentType = ['pdf', 'png', 'none'].includes(attachment.toLowerCase()) ? attachment.toLowerCase() : 'none';
    if (CONFIG.attachmentType !== 'none') {
        const encrypt = await askQuestion('Encrypt Attachment (AES-256-CBC)? (y/n): ');
        CONFIG.encryptAttachment = encrypt.toLowerCase() === 'y';
        const sign = await askQuestion('SHA-256 Sign Attachment (.sig)? (y/n): ');
        CONFIG.signAttachment = sign.toLowerCase() === 'y';
    }

    console.log(chalk.blue('\nStarting campaign with selected settings...\n'));
    await delay(2000);
    try { await fs.mkdir(CONFIG.lettersDir); } catch (err) { if (err.code !== 'EEXIST') throw err; }
    await sendEmails();
}

run();
