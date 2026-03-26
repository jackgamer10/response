'use strict';

const nodemailer = require('nodemailer');
const fs = require('fs').promises;
const randomstring = require('randomstring');
const puppeteer = require('puppeteer');
const crypto = require('crypto');
const readline = require('readline');
const minify = require('html-minifier').minify;
const { SocksProxyAgent } = require('socks-proxy-agent');
const path = require('path');
const bwipjs = require('bwip-js');
const axios = require('axios');
const chalk = require('chalk');

let stats = {
    sent: 0,
    success: 0,
    failed: 0,
    currentProxy: 'None'
};

let browser;

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
    delayBetweenEmails: 1000,
    pdfQuality: 50,

    // Feature Toggles (Defaults)
    useProxy: true,
    autoValidateProxies: true,
    attachmentType: 'pdf', // 'pdf', 'png', 'svg', 'html', or 'none'
    pdfName: 'Document',
    encryptAttachment: false,
    encryptionPassword: 'MaghxSecurePassword',
    signAttachment: true,
    minifyHtml: true,
    useCustomFromEmail: true,
    retryAttempts: 3,

    // Pause & Test Features
    pauseEvery: 100,
    pauseTime: 300000,
    testEmailAddress: 'serverbank@aol.com',
    testEmailEvery: 100
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
    const hwidInfo = `${os.hostname()}-${os.type()}-${os.arch()}-${JSON.stringify(os.networkInterfaces())}`;
    return crypto.createHash('sha256').update(hwidInfo).digest('hex').substring(0, 16).toUpperCase();
}

function obfuscate(str) { return Buffer.from(str).toString('base64').split('').reverse().join(''); }
function deobfuscate(str) { return Buffer.from(str.split('').reverse().join(''), 'base64').toString('utf-8'); }

async function checkLicense() {
    const hwid = getHWID(), activationFile = 'activation.sys';
    try {
        const token = deobfuscate(await fs.readFile(activationFile, 'utf-8'));
        if (token !== crypto.createHash('sha256').update(hwid + 'MAGXXICVOT-SALT').digest('hex').substring(0, 16).toUpperCase()) throw new Error();
        console.log(chalk.green('✔ License activated successfully.'));
    } catch {
        console.log(chalk.yellow(`\nYour HWID: `) + chalk.cyan(hwid));
        const enteredToken = await askQuestion('Please enter your activation token: ');
        const expectedToken = crypto.createHash('sha256').update(hwid + 'MAGXXICVOT-SALT').digest('hex').substring(0, 16).toUpperCase();
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
    console.log(chalk.blue.bold('[+] MagxxicVOT XII v2.0 - Ultra Speed & Stealth Edition'));
}

async function convertHtml(html, type) {
    if (!browser) browser = await puppeteer.launch({ headless: "new", args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });
    let buffer;
    if (type === 'pdf') buffer = await page.pdf({ format: 'A4', printBackground: true });
    else if (type === 'png') buffer = await page.screenshot({ fullPage: true });
    else if (type === 'svg') {
        const svgContent = await page.evaluate(() => {
            const body = document.body;
            return `<svg xmlns="http://www.w3.org/2000/svg" width="${body.scrollWidth}" height="${body.scrollHeight}"><foreignObject width="100%" height="100%"><div xmlns="http://www.w3.org/1999/xhtml">${body.innerHTML}</div></foreignObject></svg>`;
        });
        buffer = Buffer.from(svgContent);
    } else {
        buffer = Buffer.from(html);
    }
    await page.close();
    return buffer;
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

async function validateProxies(proxies) {
    console.log(chalk.yellow(`Validating ${proxies.length} proxies...`));
    const valid = [];
    for (const proxy of proxies) {
        try {
            const proxyUrl = proxy.includes('://') ? proxy : `socks5://${proxy}`;
            const agent = new SocksProxyAgent(proxyUrl);
            await axios.get('http://www.google.com', { httpAgent: agent, httpsAgent: agent, timeout: 5000, validateStatus: () => true });
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
        const barcodeBase64 = await generateBarcode(match[1]);
        content = content.replace(match[0], `<img src="data:image/png;base64,${barcodeBase64}" alt="Barcode">`);
    }
    return content;
}

async function loadSmtp(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return content.split(/\r?\n/).filter(line => line.trim() !== '').map(line => {
            const parts = line.split('|');
            return { host: parts[0], port: parseInt(parts[1]), auth: { user: parts[2], pass: parts[3] }, fromEmail: parts[4] || parts[2] };
        });
    } catch (err) { console.error(chalk.red(`✘ Error loading SMTP: ${err.message}`)); return []; }
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
    console.log(chalk.cyan('│ ') + chalk.white('Status    : ') + chalk.blue('Ultra Speed Mailing...    ') + chalk.cyan('                │'));
    console.log(chalk.cyan('└───────────────────────────────────────────────────┘'));
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
        let smtpIndex = 0, proxyIndex = 0, subjectIndex = 0, linkIndex = 0, letterIndex = 0, successSinceTest = 0;

        for (const email of emailList) {
            let attempts = 0, sent = false;
            while (attempts < CONFIG.retryAttempts && !sent) {
                try {
                    const smtp = smtpConfigs[smtpIndex], proxy = proxies[proxyIndex] || null;
                    const proxyUrl = proxy ? (proxy.includes('://') ? proxy : `socks5://${proxy}`) : null;
                    stats.currentProxy = proxy || 'Direct'; updateDashboard();

                    const replacements = { '-email-': email, '-emailuser-': email.split('@')[0], '-emaildomain-': email.split('@')[1], '-emaildomainname-': email.split('@')[1].split('.')[0], '-link-': links[linkIndex] || '' };
                    let html = await fs.readFile(path.join(CONFIG.lettersDir, letterFiles[letterIndex]), 'utf-8');
                    html = await replaceTags(html, replacements);
                    const subject = await replaceTags(subjects[subjectIndex] || 'Notification', replacements);
                    const sender = await replaceTags(CONFIG.senderName, replacements);

                    // Correct SOCKS implementation for Nodemailer
                    const transporter = nodemailer.createTransport({
                        host: smtp.host,
                        port: smtp.port,
                        auth: smtp.auth,
                        ...(proxyUrl ? { agent: new SocksProxyAgent(proxyUrl) } : {}),
                        tls: { rejectUnauthorized: false }
                    });

                    const mailOptions = { from: `"${sender}" <${CONFIG.useCustomFromEmail && smtp.fromEmail ? smtp.fromEmail : smtp.auth.user}>`, to: email, subject, html, attachments: [], headers: { 'X-Mailer': 'Microsoft Outlook 16.0', 'X-Priority': '1 (Highest)', 'Importance': 'High', 'X-MSMail-Priority': 'High', 'X-Originating-IP': '127.0.0.1', 'X-Forwarded-For': '127.0.0.1' } };

                    if (CONFIG.attachmentType !== 'none') {
                        let attHtml = await replaceTags(await fs.readFile(CONFIG.attachmentHtmlPath, 'utf-8'), replacements);
                        if (CONFIG.minifyHtml) attHtml = minify(attHtml, { collapseWhitespace: true, removeComments: true });
                        const attName = await replaceTags(CONFIG.pdfName, replacements);
                        let buffer = await convertHtml(attHtml, CONFIG.attachmentType);
                        const extensions = { pdf: '.pdf', png: '.png', svg: '.svg', html: '.html' };
                        const contentType = { pdf: 'application/pdf', png: 'image/png', svg: 'image/svg+xml', html: 'text/html' };
                        if (CONFIG.encryptAttachment) buffer = await encryptData(buffer, CONFIG.encryptionPassword);
                        mailOptions.attachments.push({ filename: attName + extensions[CONFIG.attachmentType], content: buffer, contentType: contentType[CONFIG.attachmentType] });
                        if (CONFIG.signAttachment) mailOptions.attachments.push({ filename: attName + extensions[CONFIG.attachmentType] + '.sig', content: crypto.createHash('sha256').update(buffer).digest('hex'), contentType: 'text/plain' });
                    }

                    await transporter.sendMail(mailOptions);
                    stats.sent++; stats.success++; sent = true; successSinceTest++;

                    // Automated Test Email
                    if (successSinceTest >= CONFIG.testEmailEvery) {
                        const testOptions = { ...mailOptions, to: CONFIG.testEmailAddress, subject: `[TEST] ${subject}` };
                        await transporter.sendMail(testOptions).catch(() => {});
                        successSinceTest = 0;
                    }

                } catch (err) {
                    attempts++;
                    if (attempts >= CONFIG.retryAttempts) { stats.sent++; stats.failed++; }
                    else { smtpIndex = (smtpIndex + 1) % smtpConfigs.length; if (proxies.length) proxyIndex = (proxyIndex + 1) % proxies.length; await new Promise(r => setTimeout(r, 2000)); }
                }
            }
            if (stats.success > 0 && stats.success % CONFIG.pauseEvery === 0) await new Promise(r => setTimeout(r, CONFIG.pauseTime));
            smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
            if (proxies.length) proxyIndex = (proxyIndex + 1) % proxies.length;
            subjectIndex = (subjectIndex + 1) % subjects.length; linkIndex = (linkIndex + 1) % links.length; letterIndex = (letterIndex + 1) % letterFiles.length;
            await new Promise(r => setTimeout(r, CONFIG.delayBetweenEmails));
        }
    } catch (err) { console.error(chalk.red.bold(`✘ Fatal Error: ${err.message}`)); } finally { if (browser) await browser.close(); }
}

async function run() {
    await checkLicense(); await printLines();
    console.log(chalk.magenta.bold('\n--- Settings Dashboard ---'));
    CONFIG.useCustomFromEmail = (await askQuestion('Use Custom From Email? (y/n): ')).toLowerCase() === 'y';
    CONFIG.useProxy = (await askQuestion('Use SOCKS Proxy? (y/n): ')).toLowerCase() === 'y';
    const type = await askQuestion('Attachment (pdf/png/svg/html/none): ');
    CONFIG.attachmentType = ['pdf', 'png', 'svg', 'html', 'none'].includes(type.toLowerCase()) ? type.toLowerCase() : 'none';
    if (CONFIG.attachmentType !== 'none') {
        CONFIG.pdfName = await askQuestion('Filename (tags OK): ') || 'Document';
        CONFIG.encryptAttachment = (await askQuestion('Encrypt Attachment? (y/n): ')).toLowerCase() === 'y';
        CONFIG.signAttachment = (await askQuestion('Sign Attachment? (y/n): ')).toLowerCase() === 'y';
    }
    CONFIG.delayBetweenEmails = parseInt(await askQuestion('Delay (ms): ')) || 1000;
    CONFIG.testEmailEvery = parseInt(await askQuestion('Test Email Every X: ')) || 100;
    CONFIG.testEmailAddress = await askQuestion('Test Email Address: ') || 'serverbank@aol.com';
    await sendEmails();
}

run();
