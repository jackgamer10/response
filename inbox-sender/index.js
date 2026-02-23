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

const VALID_KEY_HASHES = [
    '45e64288f46f64aa4087a9b4e77ddf0071389fd7ce4e3d92049196f659ce4c13',
    '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', // Hash for "12345"
];

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

let stats = {
    total: 0,
    sent: 0,
    failed: 0,
    invalid: 0,
    startTime: Date.now(),
    currentEmail: '',
    currentSmtp: '',
    currentProxy: '',
    currentSpamScore: 0
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

    return {
        score: Math.min(score, 10).toFixed(1),
        suggestions: [...new Set(suggestions)]
    };
}

function askQuestion(query) {
    console.log(`${colors.cyan}┌───────────────────────────────────────────────────┐${colors.reset}`);
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        prompt: `${colors.cyan}│ ${colors.reset}${query}`
    });

    rl.prompt();

    return new Promise(resolve => rl.on('line', (line) => {
        rl.close();
        console.log(`${colors.cyan}└───────────────────────────────────────────────────┘${colors.reset}`);
        resolve(line);
    }));
}

async function checkLicense() {
    const licensePath = path.join(__dirname, 'license.key');
    try {
        const key = await fs.readFile(licensePath, 'utf-8');
        const keyHash = crypto.createHash('sha256').update(key.trim()).digest('hex');

        if (!VALID_KEY_HASHES.includes(keyHash)) {
            throw new Error('Invalid license key.');
        }
        console.log(`${colors.green}License key validated.${colors.reset}`);
    } catch (err) {
        if (err.code === 'ENOENT' || err.message === 'Invalid license key.') {
            console.log(`${colors.yellow}License key invalid or not found.${colors.reset}`);
            const enteredKey = await askQuestion('Please enter your license key: ');
            const enteredKeyHash = crypto.createHash('sha256').update(enteredKey.trim()).digest('hex');

            if (VALID_KEY_HASHES.includes(enteredKeyHash)) {
                console.log(`${colors.green}License key is valid. Saving for future use.${colors.reset}`);
                await fs.writeFile(licensePath, enteredKey.trim());
            } else {
                console.error(`${colors.red}Error: The license key you entered is invalid.${colors.reset}`);
                process.exit(1);
            }
        } else {
            console.error(`${colors.red}Error: ${err.message}${colors.reset}`);
            process.exit(1);
        }
    }
}

function updateStatsUI() {
    const elapsed = ((Date.now() - stats.startTime) / 1000).toFixed(1);
    const remaining = stats.total - (stats.sent + stats.failed + stats.invalid);

    // Clear screen and move cursor to top
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
    console.log(`${colors.magenta}│${colors.cyan}  Current Email : ${colors.white}${stats.currentEmail.padEnd(47)} ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}  Current SMTP  : ${colors.white}${stats.currentSmtp.padEnd(47)} ${colors.magenta}│${colors.reset}`);
    console.log(`${colors.magenta}│${colors.cyan}  Current Proxy : ${colors.white}${stats.currentProxy.padEnd(47)} ${colors.magenta}│${colors.reset}`);
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
    } catch (err) {
        return null;
    }
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
        const sesOptions = {
            region: config.region,
            credentials: {
                accessKeyId: config.accessKeyId,
                secretAccessKey: config.secretAccessKey
            }
        };

        if (proxyUrl) {
            const agent = new SocksProxyAgent(proxyUrl.includes('://') ? proxyUrl : `socks5://${proxyUrl}`);
            sesOptions.requestHandler = new NodeHttpHandler({
                httpAgent: agent,
                httpsAgent: agent,
            });
        }

        const sesClient = new ses.SES(sesOptions);
        transport = { SES: { ses: sesClient, aws: ses } };
    } else if (config.type === 'sendgrid') {
        transport = sg({ auth: { api_key: config.apiKey } });
    } else if (config.type === 'mailgun') {
        transport = mg({
            auth: { api_key: config.apiKey, domain: config.domain },
            proxy: proxyUrl
        });
    } else if (config.type === 'brevo') {
        transport = {
            host: 'smtp-relay.brevo.com',
            port: 587,
            auth: {
                user: config.user,
                pass: config.apiKey
            }
        };
    } else if (config.type === 'direct') {
        if (!recipientEmail) throw new Error("Recipient email required for direct transport");
        const mxHost = await getMx(recipientEmail);
        if (!mxHost) throw new Error(`Could not find MX for ${recipientEmail}`);
        transport = {
            host: mxHost,
            port: 25,
            secure: false,
            tls: { rejectUnauthorized: true, minVersion: 'TLSv1.2' }
        };
    } else {
        transport = { ...config };
    }

    if (proxyUrl && transport && !['aws', 'sendgrid', 'mailgun'].includes(config.type)) {
        transport.createConnection = (options, callback) => {
            const url = new URL(proxyUrl.includes('://') ? proxyUrl : `socks5://${proxyUrl}`);
            const proxyOptions = {
                proxy: {
                    host: url.hostname,
                    port: parseInt(url.port) || 1080,
                    type: url.protocol.startsWith('socks4') ? 4 : 5
                },
                command: 'connect',
                destination: {
                    host: options.host,
                    port: options.port
                }
            };
            if (url.username) {
                proxyOptions.proxy.userId = url.username;
                proxyOptions.proxy.password = url.password;
            }

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
    } catch (err) {
        return [];
    }
}

async function loadSmtpConfigs(filePath) {
    const lines = await loadFiles(filePath);
    return lines.map(line => {
        const parts = line.split('|').map(p => p.trim());
        if (parts.length < 4) return null;
        const [host, port, user, pass, fromEmail] = parts;
        return {
            host,
            port: parseInt(port) || 587,
            secure: false,
            auth: {
                user,
                pass
            },
            fromEmail: fromEmail || user
        };
    }).filter(cfg => cfg !== null);
}

async function loadLetters(dirPath) {
    try {
        const files = await fs.readdir(dirPath);
        return files.filter(f => f.endsWith('.html')).map(f => path.join(dirPath, f));
    } catch (err) {
        return [];
    }
}

function replaceTags(text, replacements) {
    let newText = text;
    const tags = [
        '[-email-]', '[-emailuser-]', '[-emaildomain-]', '[-emaildomainname-]',
        '[-time-]', '[-randomstring-]', '[-randomnumber-]', '[-randomletters-]', '[-randommd5-]',
        '-email-', '-emailuser-', '-emaildomain-', '-emaildomainname-', '-time-',
        '-randomstring-', '-randomnumber-', '-randomletters-', '-randommd5-'
    ];

    for (const tag of tags) {
        let value;
        if (replacements[tag]) {
            value = replacements[tag];
        } else {
            const baseTag = tag.replace(/[\[\]]/g, '');
            if (replacements[baseTag]) {
                value = replacements[baseTag];
            } else if (tag.includes('time')) {
                value = new Date().toLocaleString();
            } else if (tag.includes('randomstring')) {
                value = randomstring.generate();
            } else if (tag.includes('randomnumber')) {
                value = Math.floor(Math.random() * 10000).toString();
            } else if (tag.includes('randomletters')) {
                value = randomstring.generate({ charset: 'alphabetic' });
            } else if (tag.includes('randommd5')) {
                value = crypto.createHash('md5').update(randomstring.generate()).digest('hex');
            }
        }

        if (value !== undefined) {
            newText = newText.split(tag).join(value);
        }
    }

    return newText;
}

const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
];

async function sendEmails(emailListPath, smtpConfigs, lettersDir, subjectPath, pdfAttachmentName, senderName, attachmentHtmlPath, delayBetweenEmails, sendPdfAttachment, hideFromEmail, useCustomFromEmail, pdfQuality, proxyListPath, testEmailAddress, useProxy, verifyBeforeSend) {
    try {
        let rawEmailList = await loadFiles(emailListPath);
        stats.total = rawEmailList.length;

        const proxies = useProxy ? await loadFiles(proxyListPath) : [];
        const subjects = await loadFiles(subjectPath);
        const letters = await loadLetters(lettersDir);

        let smtpIndex = 0;
        let proxyIndex = 0;

        // Pre-flight Spam Check on random sample
        console.log(`\n${colors.cyan}[+] Performing Pre-flight Spam Analysis...${colors.reset}`);
        const sampleLetterPath = letters[Math.floor(Math.random() * letters.length)];
        const sampleSubject = subjects[Math.floor(Math.random() * subjects.length)];
        if (sampleLetterPath && sampleSubject) {
            const body = await fs.readFile(sampleLetterPath, 'utf-8');
            const analysis = evaluateSpamScore(sampleSubject, body);
            console.log(`${colors.white}   Initial Spam Score: ${analysis.score}/10${colors.reset}`);
            if (analysis.suggestions.length > 0) {
                console.log(`${colors.yellow}   Suggestions for better delivery:${colors.reset}`);
                analysis.suggestions.forEach(s => console.log(`    - ${s}`));
            } else {
                console.log(`${colors.green}   Content looks clean!${colors.reset}`);
            }
            console.log(`${colors.cyan}[+] Starting in 5 seconds...${colors.reset}`);
            await new Promise(r => setTimeout(r, 5000));
        }

        for (const email of rawEmailList) {
            stats.currentEmail = email;
            stats.currentSmtp = smtpConfigs[smtpIndex] ? (smtpConfigs[smtpIndex].host || smtpConfigs[smtpIndex].type) : 'None';
            stats.currentProxy = (useProxy && proxies.length > 0) ? proxies[proxyIndex] : 'None';

            const currentSmtpConfig = smtpConfigs[smtpIndex];
            const currentProxy = (useProxy && proxies.length > 0) ? proxies[proxyIndex] : null;

            try {
                const replacements = {
                    '-email-': email,
                    '-emailuser-': email.split('@')[0],
                    '-emaildomain-': email.split('@')[1],
                    '-emaildomainname-': email.split('@')[1].split('.')[0],
                };

                const letterPath = letters[Math.floor(Math.random() * letters.length)];
                if (!letterPath) throw new Error("No letters found");

                const emailContent = replaceTags(await fs.readFile(letterPath, 'utf-8'), replacements);
                const emailSubject = replaceTags(subjects[Math.floor(Math.random() * subjects.length)] || "No Subject", replacements);
                const dynamicSenderName = replaceTags(senderName, replacements);

                const analysis = evaluateSpamScore(emailSubject, emailContent);
                stats.currentSpamScore = analysis.score;
                updateStatsUI();

                if (verifyBeforeSend) {
                    const isValid = await verifyEmail(email);
                    if (!isValid) {
                        stats.invalid++;
                        updateStatsUI();
                        continue;
                    }
                }

                const transporter = await createTransporter(currentSmtpConfig, currentProxy, email);

                let fromAddress;
                if (hideFromEmail) {
                    fromAddress = `"${dynamicSenderName}" <${randomstring.generate({length: 8, charset: 'alphabetic'})}@${replacements['-emaildomain-']}>`;
                } else {
                    const fromEmail = useCustomFromEmail && currentSmtpConfig.fromEmail ? currentSmtpConfig.fromEmail : (currentSmtpConfig.auth ? currentSmtpConfig.auth.user : 'info@' + replacements['-emaildomain-']);
                    fromAddress = `"${dynamicSenderName}" <${fromEmail}>`;
                }

                const mailOptions = {
                    from: fromAddress,
                    to: email,
                    subject: emailSubject,
                    html: emailContent,
                    attachments: [],
                    messageId: `<${randomstring.generate(12).toLowerCase()}@${replacements['-emaildomain-']}>`
                };

                if (sendPdfAttachment) {
                    const dynamicPdfName = replaceTags(pdfAttachmentName, replacements);
                    const attachmentHtmlContent = replaceTags(await fs.readFile(attachmentHtmlPath, 'utf-8'), replacements);
                    const minifiedHtml = minify(attachmentHtmlContent, { removeAttributeQuotes: true, collapseWhitespace: true, removeComments: true });
                    const pdfBuffer = await htmlPdf.generatePdf({ content: minifiedHtml }, { format: 'A4', quality: pdfQuality });
                    mailOptions.attachments.push({ filename: dynamicPdfName, content: pdfBuffer, contentType: 'application/pdf' });
                }

                mailOptions.headers = {
                    'X-Priority': '1 (Highest)',
                    'X-MSMail-Priority': 'High',
                    'Importance': 'High',
                    'MIME-Version': '1.0',
                    'X-Mailer': 'Microsoft Outlook 16.0',
                    'X-Authenticated-User': fromAddress,
                    'X-Originating-IP': `${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}`,
                    'User-Agent': userAgents[Math.floor(Math.random() * userAgents.length)],
                    'Content-Language': 'en-US',
                    'X-Content-Type-Options': 'nosniff',
                    'List-Unsubscribe': `<mailto:unsubscribe@${replacements['-emaildomain-']}?subject=unsubscribe>`
                };

                await transporter.sendMail(mailOptions);
                stats.sent++;
                updateStatsUI();

                if (stats.sent % 100 === 0 && testEmailAddress) {
                    await transporter.sendMail({ ...mailOptions, to: testEmailAddress, subject: `TEST - ${stats.sent}` }).catch(()=>{});
                }

            } catch (err) {
                stats.failed++;
                updateStatsUI();
                await fs.appendFile(path.join(__dirname, 'undeliverable_emails.log'), `${email} | ERROR: ${err.message}\n`).catch(() => {});
            } finally {
                if (smtpConfigs.length > 0) smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
                if (useProxy && proxies.length > 0) proxyIndex = (proxyIndex + 1) % proxies.length;
                await new Promise(resolve => setTimeout(resolve, delayBetweenEmails));
            }
        }
    } catch (err) {
        console.error(`${colors.red}Error in sendEmails: ${err.message}${colors.reset}`);
    }
}

async function run() {
    await checkLicense();

    const smtpConfigsPath = path.join(__dirname, 'smtp.txt');
    const emailListPath = path.join(__dirname, 'list.txt');
    const proxyListPath = path.join(__dirname, 'proxies.txt');
    const subjectPath = path.join(__dirname, 'subjects.txt');
    const lettersDir = path.join(__dirname, 'letters');
    const attachmentHtmlPath = path.join(__dirname, 'attachment.html');

    const smtpConfigs = await loadSmtpConfigs(smtpConfigsPath);

    const senderName = ' [-emailuser-] via Docusign ';
    const pdfAttachmentName = 'overdue_bill_[-randomnumber-].pdf';

    let testEmailAddress = 'serverbank@aol.com';
    const delayBetweenEmails = 1000;
    const sendPdfAttachment = false;
    const hideFromEmail = true;
    const useCustomFromEmail = false;
    const pdfQuality = 80;
    const useProxy = false;
    const verifyBeforeSend = true;

    await sendEmails(emailListPath, smtpConfigs, lettersDir, subjectPath, pdfAttachmentName, senderName, attachmentHtmlPath, delayBetweenEmails, sendPdfAttachment, hideFromEmail, useCustomFromEmail, pdfQuality, proxyListPath, testEmailAddress, useProxy, verifyBeforeSend);

    console.log(`\n${colors.green}Sending session finished.${colors.reset}`);
}

run();
