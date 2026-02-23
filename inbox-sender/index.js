'use strict';

const nodemailer = require('nodemailer');
const fs = require('fs').promises;
const path = require('path');
const randomstring = require('randomstring');
const htmlPdf = require('html-pdf-node');
const crypto = require('crypto');
const readline = require('readline');
const minify = require('html-minifier').minify;
const { SocksProxyAgent } = require('socks-proxy-agent');
const socks = require('socks');
const ses = require('@aws-sdk/client-ses');
const mg = require('nodemailer-mailgun-transport');
const sg = require('nodemailer-sendgrid-transport');
const { NodeHttpHandler } = require("@smithy/node-http-handler");
const dns = require('dns').promises;
const bwipjs = require('bwip-js');
const axios = require('axios');
const nodeHtmlToImage = require('node-html-to-image');
const si = require('systeminformation');
const archiver = require('archiver');
const { Readable } = require('stream');

const colors = {
    reset: "\x1b[0m",
    bright: "\x1b[1m",
    green: "\x1b[32m",
    red: "\x1b[31m",
    yellow: "\x1b[33m",
    blue: "\x1b[34m",
    magenta: "\x1b[35m",
    cyan: "\x1b[36m",
    white: "\x1b[37m"
};

// --- Advanced Activation and Anti-Tamper ---
const SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024';

async function getHWID() {
    try {
        const uuid = await si.uuid();
        const cpu = await si.cpu();
        const baseboard = await si.baseboard();
        const raw = `${uuid.os}-${uuid.hardware}-${cpu.brand}-${baseboard.serial}`;
        return crypto.createHash('sha256').update(raw).digest('hex').toUpperCase();
    } catch (err) {
        return 'UNKNOWN-HWID-' + crypto.createHash('md5').update(require('os').hostname()).digest('hex');
    }
}

function generateToken(hwid) {
    return crypto.createHash('sha256').update(hwid + SECRET_SALT).digest('hex').toUpperCase();
}

// Obfuscation helper
const obf = {
    encode: (data) => Buffer.from(JSON.stringify(data)).toString('base64').split('').reverse().join(''),
    decode: (data) => JSON.parse(Buffer.from(data.split('').reverse().join(''), 'base64').toString('utf-8'))
};

async function checkLicense() {
    const activationPath = path.join(__dirname, 'activation.sys'); // Renamed to .sys
    const hwid = await getHWID();

    try {
        const rawData = await fs.readFile(activationPath, 'utf-8');
        const data = obf.decode(rawData);

        if (data.hwid !== hwid) {
            console.error(`${colors.red}[!] Anti-Tamper: Hardware mismatch detected!${colors.reset}`);
            process.exit(1);
        }

        if (data.token !== generateToken(hwid)) {
            throw new Error('Invalid token');
        }

        console.log(`${colors.green}[+] License activated for HWID: ${hwid.substring(0, 8)}...${colors.reset}`);
    } catch (err) {
        console.log(`${colors.yellow}[!] Software not activated.${colors.reset}`);
        console.log(`${colors.cyan}┌───────────────────────────────────────────────────┐${colors.reset}`);
        console.log(`${colors.cyan}│${colors.white} Your HWID: ${colors.bright}${hwid}${colors.reset}${colors.cyan} │${colors.reset}`);
        console.log(`${colors.cyan}└───────────────────────────────────────────────────┘${colors.reset}`);

        const token = (await askQuestion('Enter Activation Token: ')).trim().toUpperCase();
        if (token === generateToken(hwid)) {
            const data = { hwid, token, installPath: __dirname };
            await fs.writeFile(activationPath, obf.encode(data));
            console.log(`${colors.green}[+] Activation successful! Please restart.${colors.reset}`);
            process.exit(0);
        } else {
            console.error(`${colors.red}[!] Invalid activation token.${colors.reset}`);
            process.exit(1);
        }
    }
}

// --- SMTP Checker ---
async function checkSmtpConfigs(configs) {
    console.log(`${colors.cyan}[+] Checking SMTP configurations...${colors.reset}`);
    const liveConfigs = [];
    for (const config of configs) {
        try {
            const transporter = nodemailer.createTransport(config);
            await transporter.verify();
            liveConfigs.push(config);
            console.log(`${colors.green}  [LIVE] ${config.host || config.type}${colors.reset}`);
        } catch (err) {
            console.log(`${colors.red}  [DEAD] ${config.host || config.type}: ${err.message}${colors.reset}`);
        }
    }
    return liveConfigs;
}

// --- Encryption Helpers ---
async function encryptBuffer(buffer, algorithm, password) {
    if (algorithm === 'AES-256-CBC') {
        const iv = crypto.randomBytes(16);
        const key = crypto.scryptSync(password, 'salt', 32);
        const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
        const encrypted = Buffer.concat([cipher.update(buffer), cipher.final()]);
        return Buffer.concat([iv, encrypted]);
    } else if (algorithm === 'ZIP') {
        return new Promise((resolve, reject) => {
            const chunks = [];
            const archive = archiver('zip', { zlib: { level: 9 }, password });
            archive.on('data', chunk => chunks.push(chunk));
            archive.on('end', () => resolve(Buffer.concat(chunks)));
            archive.on('error', reject);
            archive.append(buffer, { name: 'attachment.dat' });
            archive.finalize();
        });
    }
    return buffer;
}

// --- Main App Logic ---

let stats = {
    total: 0,
    sent: 0,
    failed: 0,
    invalid: 0,
    startTime: Date.now(),
    currentEmail: '',
    currentSmtp: '',
    currentProxy: '',
    currentSpamScore: 0,
    status: 'Idle'
};

const spamRules = [
    { name: 'Urgency Keywords', regex: /\b(urgent|immediate|action required|verify now|account suspended)\b/gi, score: 1.5, suggestion: 'Avoid high-urgency language in subject/body.' },
    { name: 'Money Keywords', regex: /\b(cash|money|dollars|euro|bitcoin|crypto|investment|profit|win|prize|winner|free)\b/gi, score: 2.0, suggestion: 'Reduce mentions of financial/monetary incentives.' },
    { name: 'Excessive Punctuation', regex: /[!?]{2,}/g, score: 1.0, suggestion: 'Avoid multiple exclamation or question marks.' },
    { name: 'All Caps Words', regex: /\b[A-Z]{5,}\b/g, score: 1.2, suggestion: 'Reduce use of all-caps words.' },
    { name: 'Suspicious Links', regex: /<a [^>]*href=["'](http|https):\/\/[^"'>]+["'][^>]*>/gi, weight: (matches) => matches.length > 5 ? 2.0 : 0, suggestion: 'Reduce the number of external links.' },
    { name: 'Unsubscribe Missing', check: (body) => !/unsubscribe/gi.test(body), score: 2.5, suggestion: 'Add a clear "unsubscribe" link or keyword to the body.' }
];

function evaluateSpamScore(subject, body) {
    let score = 0;
    let suggestions = [];
    const combinedText = subject + ' ' + body;
    for (const rule of spamRules) {
        if (rule.regex) {
            const matches = combinedText.match(rule.regex);
            if (matches) {
                const ruleScore = rule.weight ? rule.weight(matches) : rule.score;
                if (ruleScore > 0) {
                    score += ruleScore;
                    suggestions.push(rule.suggestion);
                }
            }
        } else if (rule.check) {
            if (rule.check(body)) {
                score += rule.score;
                suggestions.push(rule.suggestion);
            }
        }
    }
    return { score: Math.min(score, 10).toFixed(1), suggestions: [...new Set(suggestions)] };
}

function askQuestion(query) {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    return new Promise(resolve => rl.question(query, (answer) => { rl.close(); resolve(answer); }));
}

function updateStatsUI() {
    const elapsed = ((Date.now() - stats.startTime) / 1000).toFixed(1);
    const remaining = stats.total - (stats.sent + stats.failed + stats.invalid);
    process.stdout.write('\x1B[2J\x1B[0f');
    let scoreColor = colors.green;
    if (stats.currentSpamScore > 5) scoreColor = colors.red;
    else if (stats.currentSpamScore > 2) scoreColor = colors.yellow;
    console.log(`${colors.magenta}┌─────────────────────────────────────────────────────────────────┐${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}         magxxicVox Inbox Sender - Live Statistics               ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}├─────────────────────────────────────────────────────────────────┤${colors.reset}`);
    console.log(`${colors.magenta}│${colors.white}  Total Loaded: ${stats.total.toString().padEnd(10)} | Elapsed Time: ${elapsed.toString().padEnd(10)}s ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.green}  Sent: ${stats.sent.toString().padEnd(10)}         ${colors.red}| Failed: ${stats.failed.toString().padEnd(10)}       ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.yellow}  Invalid: ${stats.invalid.toString().padEnd(10)}      ${colors.white}| Remaining: ${remaining.toString().padEnd(10)}    ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}├─────────────────────────────────────────────────────────────────┤${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}  Spam Score    : ${scoreColor}${stats.currentSpamScore.toString().padEnd(47)}${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}  Status        : ${colors.white}${stats.status.padEnd(47)} ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}  Current Email : ${colors.white}${stats.currentEmail.padEnd(47)} ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}  Current SMTP  : ${colors.white}${stats.currentSmtp.padEnd(47)} ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}└─────────────────────────────────────────────────────────────────┘${colors.reset}`);
}

async function getMx(email) {
    const domain = email.split('@')[1];
    if (!domain) return null;
    try {
        const addresses = await dns.resolveMx(domain);
        if (!addresses || addresses.length === 0) return null;
        addresses.sort((a, b) => a.priority - b.priority);
        return addresses[0].exchange;
    } catch (err) { return null; }
}

async function verifyEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    if (!re.test(String(email).toLowerCase())) return false;
    const mx = await getMx(email);
    return mx !== null;
}

async function createTransporter(config, proxy, recipientEmail = null) {
    let transport;
    let proxyUrl = proxy;
    if (config.type === 'aws') {
        const sesOptions = { region: config.region, credentials: { accessKeyId: config.accessKeyId, secretAccessKey: config.secretAccessKey } };
        if (proxyUrl) {
            const agent = new SocksProxyAgent(proxyUrl.includes('://') ? proxyUrl : `socks5://${proxyUrl}`);
            sesOptions.requestHandler = new NodeHttpHandler({ httpAgent: agent, httpsAgent: agent });
        }
        const sesClient = new ses.SES(sesOptions);
        transport = { SES: { ses: sesClient, aws: ses } };
    } else if (config.type === 'sendgrid') { transport = sg({ auth: { api_key: config.apiKey } }); }
    else if (config.type === 'mailgun') { transport = mg({ auth: { api_key: config.apiKey, domain: config.domain }, proxy: proxyUrl }); }
    else if (config.type === 'brevo') { transport = { host: 'smtp-relay.brevo.com', port: 587, auth: { user: config.user, pass: config.apiKey } }; }
    else if (config.type === 'direct') {
        if (!recipientEmail) throw new Error("Recipient email required");
        const mxHost = await getMx(recipientEmail);
        if (!mxHost) throw new Error(`No MX for ${recipientEmail}`);
        transport = { host: mxHost, port: 25, secure: false, tls: { rejectUnauthorized: true, minVersion: 'TLSv1.2' } };
    } else { transport = { ...config }; }

    if (proxyUrl && transport && !['aws', 'sendgrid', 'mailgun'].includes(config.type)) {
        transport.createConnection = (options, callback) => {
            const url = new URL(proxyUrl.includes('://') ? proxyUrl : `socks5://${proxyUrl}`);
            const proxyOptions = {
                proxy: { host: url.hostname, port: parseInt(url.port) || 1080, type: url.protocol.startsWith('socks4') ? 4 : 5 },
                command: 'connect', destination: { host: options.host, port: options.port }
            };
            if (url.username) { proxyOptions.proxy.userId = url.username; proxyOptions.proxy.password = url.password; }
            socks.SocksClient.createConnection(proxyOptions, (err, info) => {
                if (err) return callback(err);
                callback(null, info.socket);
            });
        };
    }
    return nodemailer.createTransport(transport);
}

async function loadFiles(filePath) {
    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return content.split(/\r?\n/).filter(line => line.trim() !== '');
    } catch (err) { return []; }
}

async function loadSmtpConfigs(filePath) {
    const lines = await loadFiles(filePath);
    return lines.map(line => {
        const parts = line.split('|').map(p => p.trim());
        if (parts.length < 4) return null;
        const [host, port, user, pass, fromEmail] = parts;
        return { host, port: parseInt(port) || 587, secure: false, auth: { user, pass }, fromEmail: fromEmail || user };
    }).filter(cfg => cfg !== null);
}

async function loadLetters(dirPath) {
    try {
        const files = await fs.readdir(dirPath);
        return files.filter(f => f.endsWith('.html')).map(f => path.join(dirPath, f));
    } catch (err) { return []; }
}

async function generateBarcode(data) {
    return new Promise((resolve, reject) => {
        bwipjs.toBuffer({ bcid: 'code128', text: data, scale: 3, height: 10, includetext: true, textxalign: 'center' }, (err, png) => {
            if (err) reject(err); else resolve(png);
        });
    });
}

async function getRecipientLogo(email) {
    const domain = email.split('@')[1];
    try {
        const logoUrl = `https://logo.clearbit.com/${domain}`;
        const response = await axios.get(logoUrl, { responseType: 'arraybuffer', timeout: 3000 });
        return Buffer.from(response.data, 'binary');
    } catch (err) { return null; }
}

async function shortenLinks(html) {
    return html.replace(/href=["'](https?:\/\/[^"']+)["']/gi, (match, url) => {
        if (url.length > 30) { return `href="https://tinyurl.com/y888888"`; }
        return match;
    });
}

function replaceTags(text, replacements) {
    let newText = text;
    const tags = ['[-email-]', '[-emailuser-]', '[-emaildomain-]', '[-emaildomainname-]', '[-time-]', '[-randomstring-]', '[-randomnumber-]', '[-randomletters-]', '[-randommd5-]', '-email-', '-emailuser-', '-emaildomain-', '-emaildomainname-', '-time-', '-randomstring-', '-randomnumber-', '-randomletters-', '-randommd5-', '[-link-]'];
    for (const tag of tags) {
        let value;
        if (replacements[tag]) { value = replacements[tag]; }
        else {
            const baseTag = tag.replace(/[\[\]]/g, '');
            if (replacements[baseTag]) { value = replacements[baseTag]; }
            else if (tag.includes('time')) { value = new Date().toLocaleString(); }
            else if (tag.includes('randomstring')) { value = randomstring.generate(); }
            else if (tag.includes('randomnumber')) { value = Math.floor(Math.random() * 10000).toString(); }
            else if (tag.includes('randomletters')) { value = randomstring.generate({ charset: 'alphabetic' }); }
            else if (tag.includes('randommd5')) { value = crypto.createHash('md5').update(randomstring.generate()).digest('hex'); }
            else if (tag === '[-link-]') { value = replacements['link'] || '#'; }
        }
        if (value !== undefined) { newText = newText.split(tag).join(value); }
    }
    return newText;
}

const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
];

async function sendEmails(emailListPath, smtpConfigs, lettersDir, subjectPath, pdfAttachmentName, senderName, attachmentHtmlPath, delayBetweenEmails, sendPdfAttachment, hideFromEmail, useCustomFromEmail, pdfQuality, proxyListPath, testEmailAddress, useProxy, verifyBeforeSend, config) {
    try {
        let rawEmailList = await loadFiles(emailListPath);
        stats.total = rawEmailList.length;
        const proxies = useProxy ? await loadFiles(proxyListPath) : [];
        const subjects = await loadFiles(subjectPath);
        const letters = await loadLetters(lettersDir);
        const fromEmails = await loadFiles(path.join(__dirname, 'from_emails.txt'));
        const links = await loadFiles(path.join(__dirname, 'links.txt'));

        let smtpIndex = 0; let proxyIndex = 0; let fromIndex = 0; let letterIndex = 0; let linkIndex = 0;

        for (const email of rawEmailList) {
            stats.status = 'Processing';
            stats.currentEmail = email;
            stats.currentSmtp = smtpConfigs[smtpIndex] ? (smtpConfigs[smtpIndex].host || smtpConfigs[smtpIndex].type) : 'None';
            stats.currentProxy = (useProxy && proxies.length > 0) ? proxies[proxyIndex] : 'None';
            updateStatsUI();

            if (verifyBeforeSend) {
                stats.status = 'Verifying Email'; updateStatsUI();
                if (!(await verifyEmail(email))) { stats.invalid++; updateStatsUI(); continue; }
            }

            const currentSmtpConfig = smtpConfigs[smtpIndex];
            const currentProxy = (useProxy && proxies.length > 0) ? proxies[proxyIndex] : null;

            try {
                const currentLink = links.length > 0 ? links[linkIndex % links.length] : '';
                const replacements = { '-email-': email, '-emailuser-': email.split('@')[0], '-emaildomain-': email.split('@')[1], '-emaildomainname-': email.split('@')[1].split('.')[0], 'link': currentLink };
                const letterPath = config.rotateLetters ? letters[letterIndex % letters.length] : letters[0];
                if (!letterPath) throw new Error("No letters found");
                let emailContent = replaceTags(await fs.readFile(letterPath, 'utf-8'), replacements);
                const emailSubject = replaceTags(subjects[Math.floor(Math.random() * subjects.length)] || "No Subject", replacements);
                const dynamicSenderName = replaceTags(senderName, replacements);

                if (config.autoShortenLinks) { stats.status = 'Shortening Links'; updateStatsUI(); emailContent = await shortenLinks(emailContent); }

                const attachments = [];
                if (emailContent.includes('[-barcode-')) {
                    stats.status = 'Generating Barcode'; updateStatsUI();
                    const barcodeMatch = emailContent.match(/\[-barcode-(.*?)-\]/);
                    if (barcodeMatch) {
                        const barcodeBuffer = await generateBarcode(replaceTags(barcodeMatch[1], replacements));
                        attachments.push({ filename: 'barcode.png', content: barcodeBuffer, cid: 'barcode' });
                        emailContent = emailContent.replace(barcodeMatch[0], '<img src="cid:barcode"/>');
                    }
                }
                if (emailContent.includes('[-recipient-logo-]')) {
                    stats.status = 'Fetching Recipient Logo'; updateStatsUI();
                    const logoBuffer = await getRecipientLogo(email);
                    if (logoBuffer) { attachments.push({ filename: 'logo.png', content: logoBuffer, cid: 'recipientlogo' }); emailContent = emailContent.replace('[-recipient-logo-]', '<img src="cid:recipientlogo"/>'); }
                    else { emailContent = emailContent.replace('[-recipient-logo-]', ''); }
                }

                const transporter = await createTransporter(currentSmtpConfig, currentProxy, email);
                let fromAddress;
                if (fromEmails.length > 0) { fromAddress = `"${dynamicSenderName}" <${replaceTags(fromEmails[fromIndex % fromEmails.length], replacements)}>`; fromIndex++; }
                else if (hideFromEmail) { fromAddress = `"${dynamicSenderName}" <${randomstring.generate({length: 8, charset: 'alphabetic'})}@${replacements['-emaildomain-']}>`; }
                else { fromAddress = `"${dynamicSenderName}" <${useCustomFromEmail && currentSmtpConfig.fromEmail ? currentSmtpConfig.fromEmail : (currentSmtpConfig.auth ? currentSmtpConfig.auth.user : 'info@' + replacements['-emaildomain-'])}>`; }

                const mailOptions = { from: fromAddress, to: email, subject: emailSubject, html: emailContent, attachments, messageId: `<${randomstring.generate(12).toLowerCase()}@${replacements['-emaildomain-']}>` };

                if (sendPdfAttachment || config.sendImageAttachment) {
                    stats.status = 'Generating Attachment'; updateStatsUI();
                    const dynamicName = replaceTags(pdfAttachmentName, replacements);
                    const attachmentHtml = replaceTags(await fs.readFile(attachmentHtmlPath, 'utf-8'), replacements);
                    const minifiedHtml = minify(attachmentHtml, { removeAttributeQuotes: true, collapseWhitespace: true, removeComments: true });

                    let contentBuffer;
                    if (config.sendImageAttachment) { contentBuffer = await nodeHtmlToImage({ html: minifiedHtml, type: 'png' }); }
                    else { contentBuffer = await htmlPdf.generatePdf({ content: minifiedHtml }, { format: 'A4', quality: pdfQuality }); }

                    if (config.encryptionMethod && config.encryptionMethod !== 'None') {
                        stats.status = `Encrypting (${config.encryptionMethod})`; updateStatsUI();
                        contentBuffer = await encryptBuffer(contentBuffer, config.encryptionMethod, config.encryptionPassword || 'secret');
                    }
                    mailOptions.attachments.push({ filename: config.encryptionMethod === 'ZIP' ? dynamicName + '.zip' : dynamicName, content: contentBuffer });
                }

                stats.status = 'Sending Email'; updateStatsUI();
                await transporter.sendMail(mailOptions);
                stats.sent++; updateStatsUI();
            } catch (err) { stats.failed++; stats.status = 'Error: ' + err.message; updateStatsUI(); await fs.appendFile(path.join(__dirname, 'undeliverable_emails.log'), `${email} | ERROR: ${err.message}\n`).catch(() => {}); }
            finally { smtpIndex = (smtpIndex + 1) % smtpConfigs.length; if (useProxy && proxies.length > 0) proxyIndex = (proxyIndex + 1) % proxies.length; if (config.rotateLetters) letterIndex++; if (links.length > 0) linkIndex++; await new Promise(r => setTimeout(r, delayBetweenEmails)); }
        }
    } catch (err) { console.error(`${colors.red}Error in sendEmails: ${err.message}${colors.reset}`); }
}

async function run() {
    await checkLicense();
    await printLines();

    const smtpConfigs = await checkSmtpConfigs(await loadSmtpConfigs(path.join(__dirname, 'smtp.txt')));
    if (smtpConfigs.length === 0) { console.error(`${colors.red}[!] No live SMTPs found!${colors.reset}`); process.exit(1); }

    const config = {
        rotateLetters: true,
        autoShortenLinks: false,
        sendImageAttachment: true,
        pauseEvery: 50, pauseTime: 30000, delayBetweenEmails: 2000,
        encryptionMethod: 'ZIP', // Options: 'None', 'AES-256-CBC', 'ZIP'
        encryptionPassword: 'military_grade_password'
    };

    await sendEmails(path.join(__dirname, 'list.txt'), smtpConfigs, path.join(__dirname, 'letters'), path.join(__dirname, 'subjects.txt'), 'overdue_bill_[-randomnumber-].pdf', ' [-emailuser-] via Docusign ', path.join(__dirname, 'attachment.sys'), config.delayBetweenEmails, false, true, false, 80, path.join(__dirname, 'proxies.txt'), '', false, true, config);
}

async function printLines() {
    console.log(`${colors.magenta}
███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗██╗   ██╗ ██████╗ ██╗  ██╗
████╗ ████║██╔══██╗██╔════╝ ╚██╗██╔╝╚██╗██╔╝██║██╔════╝██║   ██║██╔═══██╗╚██╗██╔╝
██╔████╔██║███████║██║  ███╗ ╚███╔╝  ╚███╔╝ ██║██║     ██║   ██║██║   ██║ ╚███╔╝
██║╚██╔╝██║██╔══██║██║   ██║ ██╔██╗  ██╔██╗ ██║██║     ╚██╗ ██╔╝██║   ██║ ██╔██╗
██║ ╚═╝ ██║██║  ██║╚██████╔╝██╔╝ ██╗██╔╝ ██╗██║╚██████╗ ╚████╔╝ ╚██████╔╝██╔╝ ██╗
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝
${colors.reset}`);
}

run();
