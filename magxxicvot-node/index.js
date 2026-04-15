'use strict';

const nodemailer = require('nodemailer');
const fs = require('fs').promises;
const randomstring = require('randomstring');
const puppeteer = require('puppeteer');
const crypto = require('crypto');
const readline = require('readline');
const minify = require('html-minifier').minify;
const { SocksClient } = require('socks');
const path = require('path');
const bwipjs = require('bwip-js');
const axios = require('axios');
const chalk = require('chalk');
const net = require('net');

let stats = { sent: 0, success: 0, failed: 0, currentProxy: 'None' };
let browser;

const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
];

const CONFIG = {
    senderName: 'IONOS Customer Service',
    lettersDir: 'letters',
    subjectsPath: 'subject.txt',
    linksPath: 'links.txt',
    proxiesPath: 'proxies.txt',
    emailListPath: 'list.txt',
    smtpPath: 'smtp.txt',
    attachmentHtmlPath: 'attachment.html',
    delayBetweenEmails: 1000,
    pdfQuality: 50,
    useProxy: true,
    autoValidateProxies: true,
    attachmentType: 'pdf',
    pdfName: 'Document',
    encryptAttachment: false,
    encryptionPassword: 'MaghxSecurePassword',
    signAttachment: true,
    minifyHtml: true,
    useCustomFromEmail: true,
    retryAttempts: 3,
    pauseEvery: 100,
    pauseTime: 300000,
    testEmailAddress: 'serverbank@aol.com',
    testEmailEvery: 100,
    hideMyIp: true,
    uniqueUrl: true,
    baseUrl: '',
    sendBarcodeInLetter: true,
    sendBarcodeInAttachment: true
};

function askQuestion(query) {
    console.log(chalk.cyan('┌───────────────────────────────────────────────────┐'));
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout, prompt: chalk.cyan('│ ') + chalk.yellow(query) });
    rl.prompt();
    return new Promise(resolve => rl.on('line', (line) => {
        rl.close(); console.log(chalk.cyan('└───────────────────────────────────────────────────┘')); resolve(line);
    }));
}

function getHWID() {
    const os = require('os');
    const networkInterfaces = os.networkInterfaces();
    let mac = '00:00:00:00:00:00';
    for (const name of Object.keys(networkInterfaces)) {
        for (const net of networkInterfaces[name]) {
            if (!net.internal && net.mac !== '00:00:00:00:00:00') { mac = net.mac; break; }
        }
        if (mac !== '00:00:00:00:00:00') break;
    }
    const hwidInfo = `${os.hostname()}-${mac.toUpperCase()}`;
    return crypto.createHash('sha256').update(hwidInfo).digest('hex').substring(0, 16).toUpperCase();
}

function obfuscate(str) { return Buffer.from(str).toString('base64').split('').reverse().join(''); }
function deobfuscate(str) { return Buffer.from(str.split('').reverse().join(''), 'base64').toString('utf-8'); }

async function checkLicense() {
    const hwid = getHWID(), activationFile = 'activation.sys';
    const expectedToken = crypto.createHash('sha256').update(hwid + 'MAGXXICVOT-XII-SALT').digest('hex').substring(0, 16).toUpperCase();
    try {
        const token = deobfuscate(await fs.readFile(activationFile, 'utf-8'));
        if (token !== expectedToken) throw new Error();
        console.log(chalk.green('✔ License activated successfully.'));
    } catch {
        console.log(chalk.yellow(`\nYour HWID: `) + chalk.cyan(hwid));
        const enteredToken = await askQuestion('Please enter your activation token: ');
        if (enteredToken.trim().toUpperCase() === expectedToken) {
            await fs.writeFile(activationFile, obfuscate(enteredToken.trim().toUpperCase()));
            if (process.platform === 'win32') require('child_process').exec(`attrib +h ${activationFile}`);
        } else { console.error(chalk.red('✘ Error: Invalid activation token.')); process.exit(1); }
    }
}

async function printLines() {
    await new Promise(r => setTimeout(r, 500));
    console.log(chalk.magenta.bold(`
███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗██╗   ██╗ ██████╗ ████████╗  ██╗  ██╗██╗██╗
████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝██║██╔════╝██║   ██║██╔═══██╗╚══██╔══╝  ╚██╗██╔╝██║██║
██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝ ██║██║     ██║   ██║██║   ██║   ██║      ╚███╔╝ ██║██║
██║╚██╔╝██║██╔══██║██║   ██║██╔══██║ ██╔██╗ ██║██║     ╚██╗ ██╔╝██║   ██║   ██║      ██╔██╗ ██║██║
██║ ╚═╝ ██║██║  ██║╚██████╔╝██║  ██║██╔╝ ██╗██║╚██████╗ ╚████╔╝ ╚██████╔╝   ██║     ██╔╝ ██╗██║██║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═══╝   ╚═════╝    ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝
`));
    console.log(chalk.blue.bold('[+] MagxxicVOT XII v4.2 - Ultra Speed & Dynamic Tag Edition'));
}

async function analyzeSpam() {
    console.log(chalk.yellow('\n--- Campaign Spam Analysis ---'));
    let score = 0;
    let suggestions = [];

    try {
        const letterFiles = (await fs.readdir(CONFIG.lettersDir)).filter(f => f.endsWith('.html'));
        if (letterFiles.length === 0) {
            console.log(chalk.red('No letters found. Skipping analysis.'));
            return;
        }
        const html = await fs.readFile(path.join(CONFIG.lettersDir, letterFiles[0]), 'utf-8');

        const keywords = ['free', 'money', 'urgent', 'winner', 'account', 'security', 'suspended', 'verify', 'click here'];
        keywords.forEach(word => {
            if (new RegExp(`\\b${word}\\b`, 'i').test(html)) {
                score += 1.5;
                suggestions.push(`High-risk word found: "${word}". Consider alternatives.`);
            }
        });

        if (html.includes('<img') && html.length < 1000) {
            score += 2;
            suggestions.push('Low text-to-image ratio. Add more legitimate text to the body.');
        }

        if (html.includes('javascript:')) {
            score += 3;
            suggestions.push('Avoid JavaScript in HTML letters; it triggers aggressive filters.');
        }

        const subjects = (await fs.readFile(CONFIG.subjectsPath, 'utf-8')).split(/\r?\n/).filter(l => l.trim() !== '');
        if (subjects.some(s => s.toUpperCase() === s)) {
            score += 1;
            suggestions.push('ALL CAPS subject lines are often flagged as spam.');
        }

        console.log(chalk.cyan(`Calculated Spam Score: `) + (score > 5 ? chalk.red(score) : chalk.green(score)) + chalk.white(' / 10'));
        if (suggestions.length > 0) {
            console.log(chalk.yellow('Improvement Suggestions:'));
            suggestions.forEach(s => console.log(chalk.white(' - ') + s));
        } else {
            console.log(chalk.green('Letter looks clean! Ready for high inboxing.'));
        }
    } catch (err) {
        console.error(chalk.red('Failed to analyze spam: ' + err.message));
    }
    console.log('------------------------------\n');
}

async function convertHtml(html, type) {
    if (!browser) browser = await puppeteer.launch({ headless: "new", args: ['--disable-setuid-sandbox', '--no-sandbox'] });
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });
    let buffer;
    if (type === 'pdf') {
        buffer = await page.pdf({ format: 'A4', printBackground: true, preferCSSPageSize: true });
    }
    else if (type === 'png') buffer = await page.screenshot({ fullPage: true });
    else if (type === 'svg') {
        const svgContent = await page.evaluate(() => {
            const body = document.body;
            return `<svg xmlns="http://www.w3.org/2000/svg" width="${body.scrollWidth}" height="${body.scrollHeight}"><foreignObject width="100%" height="100%"><div xmlns="http://www.w3.org/1999/xhtml">${body.innerHTML}</div></foreignObject></svg>`;
        });
        buffer = Buffer.from(svgContent);
    } else { buffer = Buffer.from(html); }
    await page.close();
    return buffer;
}

async function validateProxies(proxies) {
    console.log(chalk.yellow(`Validating ${proxies.length} proxies...`));
    const valid = [];
    for (const proxy of proxies) {
        try {
            const parsed = new URL(proxy.includes('://') ? proxy : `socks5://${proxy}`);
            await SocksClient.createConnection({
                proxy: { host: parsed.hostname, port: parseInt(parsed.port), type: 5 },
                command: 'connect',
                destination: { host: 'google.com', port: 80 },
                timeout: 5000
            });
            valid.push(proxy); console.log(chalk.green(`✔ Proxy ${proxy} OK.`));
        } catch { console.log(chalk.red(`✘ Proxy ${proxy} FAILED.`)); }
    }
    return valid;
}

async function generateBarcode(data) {
    return new Promise((resolve, reject) => {
        bwipjs.toBuffer({ bcid: 'code128', text: data, scale: 3, height: 10, includetext: true, textxalign: 'center' }, (err, png) => {
            if (err) reject(err); else resolve(png.toString('base64'));
        });
    });
}

async function replaceTags(text, replacements, isAttachment = false) {
    let content = text;
    content = content.replace(/\[-email-\]/g, replacements['-email-'] || '');
    content = content.replace(/\[-emailuser-\]/g, replacements['-emailuser-'] || '');
    content = content.replace(/\[-emaildomain-\]/g, replacements['-emaildomain-'] || '');
    content = content.replace(/\[-emaildomainname-\]/g, replacements['-emaildomainname-'] || '');

    let finalLink = replacements['-link-'] || '';
    if (CONFIG.uniqueUrl && CONFIG.baseUrl) {
        const sep = CONFIG.baseUrl.includes('?') ? '&' : '?';
        finalLink = `${CONFIG.baseUrl}${sep}v=${randomstring.generate(12)}`;
    }
    content = content.replace(/\[-link-\]/g, finalLink);

    content = content.replace(/\[-randomstring-\]/g, () => randomstring.generate());
    content = content.replace(/\[-randomnumber-\]/g, () => Math.floor(1000 + Math.random() * 9000).toString());
    content = content.replace(/\[-randomletters-\]/g, () => randomstring.generate({ charset: 'alphabetic' }));
    content = content.replace(/\[-randommd5-\]/g, () => crypto.createHash('md5').update(randomstring.generate()).digest('hex'));
    content = content.replace(/\[-randomhex-\]/g, () => crypto.randomBytes(8).toString('hex'));
    content = content.replace(/\[-time-\]/g, () => new Date().toLocaleString());
    content = content.replace(/\[-date-\]/g, () => new Date().toLocaleDateString());

    const domain = replacements['-emaildomain-'] || (replacements['-email-'] ? replacements['-email-'].split('@')[1] : '');
    const logoUrl = domain ? `https://logo.clearbit.com/${domain}` : '';
    content = content.replace(/\[-recipient-logo-\]/g, `<img src="${logoUrl}" alt="Logo" style="max-height: 50px;">`);

    const barcodeRegex = /\[-barcode-(.*?)-\]/g;
    const matches = [...content.matchAll(barcodeRegex)];
    for (const match of matches) {
        const shouldReplace = isAttachment ? CONFIG.sendBarcodeInAttachment : CONFIG.sendBarcodeInLetter;
        if (shouldReplace) {
            const barcodeBase64 = await generateBarcode(match[1]);
            content = content.replace(match[0], `<img src="data:image/png;base64,${barcodeBase64}" alt="Barcode">`);
        } else {
            content = content.replace(match[0], '');
        }
    }
    return content;
}

async function loadSmtp(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return content.split(/\r?\n/).filter(line => line.trim() !== '').map(line => {
            const parts = line.split('|');
            const fromEmail = parts[4] || parts[2];
            const ehlo = parts[5] || (fromEmail.includes('@') ? fromEmail.split('@')[1] : 'localhost');
            return { host: parts[0], port: parseInt(parts[1]), auth: { user: parts[2], pass: parts[3] }, fromEmail: fromEmail, name: ehlo };
        });
    } catch (err) { console.error(chalk.red(`✘ Error loading SMTP: ${err.message}`)); return []; }
}

function validateEmail(email) {
    if (!email || typeof email !== 'string') return false;
    const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function updateDashboard() {
    process.stdout.write('\x1Bc');
    console.log(chalk.cyan('┌───────────────────────────────────────────────────┐'));
    console.log(chalk.cyan('│             ') + chalk.magenta.bold('MAGXXICVOT XII LIVE DASHBOARD') + chalk.cyan('         │'));
    console.log(chalk.cyan('├───────────────────────────────────────────────────┤'));
    console.log(chalk.cyan('│ ') + chalk.white('Total     : ') + chalk.yellow(stats.sent.toString().padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('│ ') + chalk.white('Success   : ') + chalk.green(stats.success.toString().padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('│ ') + chalk.white('Failed    : ') + chalk.red(stats.failed.toString().padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('│ ') + chalk.white('Proxy     : ') + chalk.blue(stats.currentProxy.padEnd(38)) + chalk.cyan(' │'));
    console.log(chalk.cyan('├───────────────────────────────────────────────────┤'));
    console.log(chalk.cyan('│ ') + chalk.white('Status    : ') + chalk.blue('Ultra Speed Mailing...    ') + chalk.cyan('                │'));
    console.log(chalk.cyan('└───────────────────────────────────────────────────┘'));
}

async function encryptData(data, password) {
    const salt = crypto.randomBytes(16);
    const key = crypto.scryptSync(password, salt, 32);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    const encrypted = Buffer.concat([cipher.update(data), cipher.final()]);
    return Buffer.concat([salt, iv, encrypted]);
}

async function sendSingleEmail(targetEmail, smtp, proxy, replacements, letterPath, subjectLine) {
    const proxyUrl = proxy ? (proxy.includes('://') ? proxy : `socks5://${proxy}`) : null;
    const transporter = nodemailer.createTransport({
        host: smtp.host, port: smtp.port, auth: smtp.auth, name: smtp.name,
        tls: { rejectUnauthorized: false },
        createConnection: (options, callback) => {
            if (proxyUrl) {
                const parsed = new URL(proxyUrl);
                SocksClient.createConnection({
                    proxy: { host: parsed.hostname, port: parseInt(parsed.port), type: 5, userId: parsed.username, password: parsed.password },
                    command: 'connect', destination: { host: options.host, port: options.port }
                }, (err, info) => {
                    if (err) return callback(err);
                    callback(null, info.socket);
                });
            } else {
                return net.connect(options.port, options.host, callback);
            }
        }
    });

    let html = await fs.readFile(letterPath, 'utf-8');
    html = await replaceTags(html, replacements, false);
    const subject = await replaceTags(subjectLine || 'Notification', replacements, false);
    const sender = await replaceTags(CONFIG.senderName, replacements, false);

    const headers = {
        'X-Mailer': 'Microsoft Outlook 16.0', 'X-Priority': '1 (Highest)', 'Importance': 'High', 'X-MSMail-Priority': 'High',
        'User-Agent': USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)]
    };
    if (CONFIG.hideMyIp) {
        headers['X-Originating-IP'] = '127.0.0.1'; headers['X-Forwarded-For'] = '127.0.0.1'; headers['X-Real-IP'] = '127.0.0.1'; headers['X-Remote-IP'] = '127.0.0.1'; headers['X-Client-IP'] = '127.0.0.1';
    }

    const mailOptions = {
        from: `"${sender}" <${CONFIG.useCustomFromEmail && smtp.fromEmail ? smtp.fromEmail : smtp.auth.user}>`,
        to: targetEmail, subject, html, attachments: [], headers: headers
    };

    if (CONFIG.attachmentType !== 'none') {
        let attHtml = await replaceTags(await fs.readFile(CONFIG.attachmentHtmlPath, 'utf-8'), replacements, true);
        if (CONFIG.minifyHtml) {
            attHtml = minify(attHtml, { collapseWhitespace: true, removeComments: true, minifyCSS: true, minifyJS: true, removeAttributeQuotes: true, removeOptionalTags: true });
        }
        const attName = await replaceTags(CONFIG.pdfName, replacements, true);
        let buffer = await convertHtml(attHtml, CONFIG.attachmentType);
        const extensions = { pdf: '.pdf', png: '.png', svg: '.svg', html: '.html' };
        const contentType = { pdf: 'application/pdf', png: 'image/png', svg: 'image/svg+xml', html: 'text/html' };
        if (CONFIG.encryptAttachment) buffer = await encryptData(buffer, CONFIG.encryptionPassword);
        mailOptions.attachments.push({ filename: attName + extensions[CONFIG.attachmentType], content: buffer, contentType: contentType[CONFIG.attachmentType] });
        if (CONFIG.signAttachment) mailOptions.attachments.push({ filename: attName + extensions[CONFIG.attachmentType] + '.sig', content: crypto.createHash('sha256').update(buffer).digest('hex'), contentType: 'text/plain' });
    }

    await transporter.sendMail(mailOptions);
}

async function sendEmails() {
    try {
        const emailList = (await fs.readFile(CONFIG.emailListPath, 'utf-8')).split(/\r?\n/).filter(l => l.trim() !== '');
        const subjects = (await fs.readFile(CONFIG.subjectsPath, 'utf-8')).split(/\r?\n/).filter(l => l.trim() !== '');
        const links = (await fs.readFile(CONFIG.linksPath, 'utf-8')).split(/\r?\n/).filter(l => l.trim() !== '');
        const smtpConfigs = await loadSmtp(CONFIG.smtpPath);
        let proxies = (await fs.readFile(CONFIG.proxiesPath, 'utf-8')).split(/\r?\n/).filter(l => l.trim() !== '');
        if (CONFIG.useProxy && CONFIG.autoValidateProxies && proxies.length > 0) proxies = await validateProxies(proxies);
        const letterFiles = (await fs.readdir(CONFIG.lettersDir)).filter(file => file.endsWith('.html'));

        if (!emailList.length || !smtpConfigs.length || !letterFiles.length) {
            throw new Error('Crucial mailing data is missing (list.txt, smtp.txt, or letters/).');
        }

        let smtpIndex = 0, proxyIndex = 0, linkIndex = 0, letterIndex = 0, subjectIndex = 0, successSinceTest = 0;

        for (const email of emailList) {
            stats.sent++;
            if (!validateEmail(email.trim())) {
                stats.failed++;
                updateDashboard();
                continue;
            }

            let attempts = 0, sent = false;
            while (attempts < CONFIG.retryAttempts && !sent) {
                try {
                    const smtp = smtpConfigs[smtpIndex], proxy = proxies[proxyIndex] || null;
                    stats.currentProxy = proxy || 'Direct'; updateDashboard();

                    const replacements = { '-email-': email, '-emailuser-': email.split('@')[0], '-emaildomain-': email.split('@')[1], '-emaildomainname-': email.split('@')[1].split('.')[0], '-link-': links[linkIndex] || '' };
                    const letterPath = path.join(CONFIG.lettersDir, letterFiles[letterIndex]);
                    const currentSubject = subjects[subjectIndex] || 'Notification';

                    await sendSingleEmail(email, smtp, proxy, replacements, letterPath, currentSubject);
                    stats.success++; sent = true; successSinceTest++;
                    if (successSinceTest >= CONFIG.testEmailEvery) {
                        await sendSingleEmail(CONFIG.testEmailAddress, smtp, proxy, replacements, letterPath, currentSubject).catch(() => {});
                        successSinceTest = 0;
                    }
                } catch (err) {
                    attempts++;
                    smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
                    if (proxies.length) proxyIndex = (proxyIndex + 1) % proxies.length;
                    if (attempts >= CONFIG.retryAttempts) stats.failed++;
                    updateDashboard();
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
            if (stats.success > 0 && stats.success % CONFIG.pauseEvery === 0) {
                console.log(chalk.magenta(`\n[PAUSE] reached ${stats.success}. waiting ${CONFIG.pauseTime/1000}s...`));
                await new Promise(r => setTimeout(r, CONFIG.pauseTime));
            }
            smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
            if (proxies.length) proxyIndex = (proxyIndex + 1) % proxies.length;
            linkIndex = (linkIndex + 1) % links.length;
            letterIndex = (letterIndex + 1) % letterFiles.length;
            subjectIndex = (subjectIndex + 1) % subjects.length;
            await new Promise(r => setTimeout(r, CONFIG.delayBetweenEmails));
        }
    } catch (err) { console.error(chalk.red.bold(`✘ Fatal Error: ${err.message}`)); } finally { if (browser) await browser.close(); }
}

async function run() {
    await checkLicense(); await printLines();
    await analyzeSpam();
    console.log(chalk.magenta.bold('\n--- Settings Dashboard ---'));
    CONFIG.useCustomFromEmail = (await askQuestion('Use Custom From Email? (y/n): ')).toLowerCase() === 'y';
    CONFIG.useProxy = (await askQuestion('Use SOCKS Proxy? (y/n): ')).toLowerCase() === 'y';
    CONFIG.hideMyIp = (await askQuestion('Enable Hide My IP (Header Masking)? (y/n): ')).toLowerCase() === 'y';

    CONFIG.uniqueUrl = (await askQuestion('Enable Unique URL per Recipient? (y/n): ')).toLowerCase() === 'y';
    if (CONFIG.uniqueUrl) {
        CONFIG.baseUrl = await askQuestion('Base URL for Unique Generation: ');
    }

    const type = await askQuestion('Attachment (pdf/png/svg/html/none): ');
    CONFIG.attachmentType = ['pdf', 'png', 'svg', 'html', 'none'].includes(type.toLowerCase()) ? type.toLowerCase() : 'none';
    if (CONFIG.attachmentType !== 'none') {
        CONFIG.pdfName = await askQuestion('Filename (tags OK): ') || 'Document';
        CONFIG.encryptAttachment = (await askQuestion('Encrypt Attachment? (y/n): ')).toLowerCase() === 'y';
        CONFIG.signAttachment = (await askQuestion('Sign Attachment? (y/n): ')).toLowerCase() === 'y';
        CONFIG.sendBarcodeInAttachment = (await askQuestion('Send Barcode in Attachment? (y/n): ')).toLowerCase() === 'y';
    }
    CONFIG.sendBarcodeInLetter = (await askQuestion('Send Barcode in Letter Body? (y/n): ')).toLowerCase() === 'y';

    CONFIG.delayBetweenEmails = parseInt(await askQuestion('Delay (ms): ')) || 1000;
    CONFIG.testEmailEvery = parseInt(await askQuestion('Test Email Every X: ')) || 100;
    CONFIG.testEmailAddress = await askQuestion('Test Email Address: ') || 'serverbank@aol.com';

    const runSmtpTest = (await askQuestion('Run Multiple SMTP Connectivity Test? (y/n): ')).toLowerCase() === 'y';
    if (runSmtpTest) {
        try {
            const smtps = await loadSmtp(CONFIG.smtpPath);
            if (!smtps.length) throw new Error('smtp.txt is empty.');
            console.log(chalk.yellow(`\nTesting ${smtps.length} SMTPs...`));
            for (let i = 0; i < smtps.length; i++) {
                const smtp = smtps[i];
                try {
                    const reps = { '-email-': CONFIG.testEmailAddress, '-emailuser-': CONFIG.testEmailAddress.split('@')[0], '-emaildomain-': CONFIG.testEmailAddress.split('@')[1], '-emaildomainname-': CONFIG.testEmailAddress.split('@')[1].split('.')[0], '-link-': 'http://test.com' };
                    const letterFiles = (await fs.readdir(CONFIG.lettersDir)).filter(file => file.endsWith('.html'));
                    if (!letterFiles.length) throw new Error('letters/ directory is empty.');
                    await sendSingleEmail(CONFIG.testEmailAddress, smtp, null, reps, path.join(CONFIG.lettersDir, letterFiles[0]), 'SMTP Verification [-randomnumber-] [-date-]');
                    console.log(chalk.green(`[OK] SMTP ${i+1}: ${smtp.host} - Message Sent.`));
                } catch (err) {
                    console.log(chalk.red(`[FAIL] SMTP ${i+1}: ${smtp.host} - Error: ${err.message}`));
                }
            }
        } catch (err) {
            console.log(chalk.red('SMTP Test failed: ' + err.message));
        }
    }

    const runTest = (await askQuestion('Run a Final Setup Test Send? (y/n): ')).toLowerCase() === 'y';
    if (runTest) {
        console.log(chalk.yellow('\nSending test email with full setup...'));
        try {
            const smtps = await loadSmtp(CONFIG.smtpPath);
            const letterFiles = (await fs.readdir(CONFIG.lettersDir)).filter(file => file.endsWith('.html'));
            const links = (await fs.readFile(CONFIG.linksPath, 'utf-8')).split(/\r?\n/).filter(l => l.trim() !== '');
            if (!smtps.length || !letterFiles.length) throw new Error('Missing SMTP or Letter for test.');
            const reps = { '-email-': CONFIG.testEmailAddress, '-emailuser-': CONFIG.testEmailAddress.split('@')[0], '-emaildomain-': CONFIG.testEmailAddress.split('@')[1], '-emaildomainname-': CONFIG.testEmailAddress.split('@')[1].split('.')[0], '-link-': links[0] || '' };
            await sendSingleEmail(CONFIG.testEmailAddress, smtps[0], null, reps, path.join(CONFIG.lettersDir, letterFiles[0]), 'Final Verification [-randomnumber-] [-date-]');
            console.log(chalk.green('Final Test email sent successfully!'));
        } catch (err) {
            console.log(chalk.red('Test email failed: ' + err.message));
        }
    }

    const startMailing = (await askQuestion('Start Full Campaign now? (y/n): ')).toLowerCase() === 'y';
    if (startMailing) await sendEmails();
    else console.log(chalk.blue('Exiting. Have a great day!'));
}

run();
