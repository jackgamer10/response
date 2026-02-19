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
    try {
        const key = await fs.readFile('license.key', 'utf-8');
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
                await fs.writeFile('license.key', enteredKey.trim());
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

async function printLines() {
    console.log(`${colors.cyan}magxxicVox Inbox Sender Start${colors.reset}\n`);
    console.log(`${colors.magenta}
███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗██╗   ██╗ ██████╗ ██╗  ██╗
████╗ ████║██╔══██╗██╔════╝ ╚██╗██╔╝╚██╗██╔╝██║██╔════╝██║   ██║██╔═══██╗╚██╗██╔╝
██╔████╔██║███████║██║  ███╗ ╚███╔╝  ╚███╔╝ ██║██║     ██║   ██║██║   ██║ ╚███╔╝
██║╚██╔╝██║██╔══██║██║   ██║ ██╔██╗  ██╔██╗ ██║██║     ╚██╗ ██╔╝██║   ██║ ██╔██╗
██║ ╚═╝ ██║██║  ██║╚██████╔╝██╔╝ ██╗██╔╝ ██╗██║╚██████╗ ╚████╔╝ ╚██████╔╝██╔╝ ██╗
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝
${colors.reset}`);
    console.log(`${colors.bright}[+] magxxicVox Sender v4${colors.reset}`);
    console.log(`${colors.cyan}[+] Best For All Spamming Hit Aol Yahoo Office Gmail${colors.reset}`);
    console.log(`${colors.yellow}[+] Code By magxxicVox Inbox${colors.reset}`);
}

async function getMx(email) {
    const domain = email.split('@')[1];
    try {
        const addresses = await dns.resolveMx(domain);
        if (!addresses || addresses.length === 0) return null;
        addresses.sort((a, b) => a.priority - b.priority);
        return addresses[0].exchange;
    } catch (err) {
        return null;
    }
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
            tls: { rejectUnauthorized: false }
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

async function sendEmails(emailListPath, smtpConfigs, lettersDir, subjectPath, pdfAttachmentName, senderName, attachmentHtmlPath, delayBetweenEmails, sendPdfAttachment, hideFromEmail, useCustomFromEmail, pdfQuality, proxyListPath, testEmailAddress, useProxy) {
    try {
        const emailList = await loadFiles(emailListPath);
        const proxies = useProxy ? await loadFiles(proxyListPath) : [];
        const subjects = await loadFiles(subjectPath);
        const letters = await loadLetters(lettersDir);

        let smtpIndex = 0;
        let proxyIndex = 0;
        let sentCount = 0;

        for (const email of emailList) {
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
                if (!letterPath) throw new Error("No letters found in letters/ directory");

                const emailContent = replaceTags(await fs.readFile(letterPath, 'utf-8'), replacements);
                const emailSubject = replaceTags(subjects[Math.floor(Math.random() * subjects.length)] || "No Subject", replacements);
                const dynamicSenderName = replaceTags(senderName, replacements);

                const transporter = await createTransporter(currentSmtpConfig, currentProxy, email);

                let fromAddress;
                if (hideFromEmail) {
                    fromAddress = `"${dynamicSenderName}" <${randomstring.generate(5)}@${replacements['-emaildomain-']}>`;
                } else {
                    const fromEmail = useCustomFromEmail && currentSmtpConfig.fromEmail ? currentSmtpConfig.fromEmail : (currentSmtpConfig.auth ? currentSmtpConfig.auth.user : 'noreply@' + replacements['-emaildomain-']);
                    fromAddress = `"${dynamicSenderName}" <${fromEmail}>`;
                }

                const mailOptions = {
                    from: fromAddress,
                    to: email,
                    subject: emailSubject,
                    html: emailContent,
                    attachments: [],
                    messageId: `<${randomstring.generate()}@${replacements['-emaildomain-']}>`
                };

                if (sendPdfAttachment) {
                    const dynamicPdfName = replaceTags(pdfAttachmentName, replacements);
                    const attachmentHtmlContent = replaceTags(await fs.readFile(attachmentHtmlPath, 'utf-8'), replacements);
                    const minifiedHtml = minify(attachmentHtmlContent, { removeAttributeQuotes: true, collapseWhitespace: true, removeComments: true });
                    const pdfBuffer = await htmlPdf.generatePdf({ content: minifiedHtml }, { format: 'A4', quality: pdfQuality });
                    mailOptions.attachments.push({ filename: dynamicPdfName, content: pdfBuffer, contentType: 'application/pdf' });
                }

                const spoofIp = () => `${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 254) + 1}`;
                mailOptions.headers = {
                    'X-Originating-IP': spoofIp(),
                    'X-Mailer': 'Microsoft Outlook 16.0',
                    'X-Forwarded-For': spoofIp(),
                    'X-Real-IP': spoofIp(),
                    'X-MSMail-Priority': 'High',
                    'Importance': 'High',
                    'X-Priority': '1'
                };

                await transporter.sendMail(mailOptions);
                sentCount++;

                console.log(`${colors.magenta}==================================================${colors.reset}`);
                console.log(`${colors.cyan}To               :${colors.reset} ${email}`);
                console.log(`${colors.cyan}Subject          :${colors.reset} ${emailSubject}`);
                console.log(`${colors.cyan}Smtp             :${colors.reset} ${currentSmtpConfig.type || currentSmtpConfig.host || 'Default'}`);
                console.log(`${colors.cyan}Proxy            :${colors.reset} ${currentProxy || 'None'}`);
                console.log(`${colors.cyan}Status           :${colors.reset} ${colors.green}Sent${colors.reset}`);
                console.log(`${colors.cyan}Sent Total       :${colors.reset} ${sentCount}`);
                console.log(`${colors.magenta}==================================================${colors.reset}`);

                if (sentCount % 100 === 0 && testEmailAddress) {
                    console.log(`${colors.yellow}[!] Sending test email...${colors.reset}`);
                    await transporter.sendMail({ ...mailOptions, to: testEmailAddress, subject: `TEST - ${sentCount}` }).catch(()=>{});
                }

            } catch (err) {
                console.error(`${colors.red}Failed to send to ${email}: ${err.message}${colors.reset}`);
                await fs.appendFile('undeliverable_emails.log', `${email} | ERROR: ${err.message}\n`).catch(() => {});
            } finally {
                smtpIndex = (smtpIndex + 1) % smtpConfigs.length;
                if (useProxy && proxies.length > 0) proxyIndex = (proxyIndex + 1) % proxies.length;
                await new Promise(resolve => setTimeout(resolve, delayBetweenEmails));
            }
        }
    } catch (err) {
        console.error(`Error in sendEmails: ${err.message}`);
    }
}

const smtpConfigs = [
    {
        host: 'mail.asahi-net.or.jp',
        port: 587,
        secure: false,
        auth: {
            user: 'iq4s-ymst',
            pass: 'kotarou100',
        },
        fromEmail: 'dse_notice_message@docsign.net'
    }
];

async function run() {
    await checkLicense();
    await printLines();

    const senderName = ' [-emailuser-] via Docusign ';
    const lettersDir = 'letters';
    const subjectPath = 'subjects.txt';
    const pdfAttachmentName = 'overdue_bill_[-randomnumber-].pdf';
    const emailListPath = 'list.txt';
    const proxyListPath = 'proxies.txt';
    const attachmentHtmlPath = 'attachment.html';

    let testEmailAddress = 'serverbank@aol.com';
    const delayBetweenEmails = 1000;
    const sendPdfAttachment = false;
    const hideFromEmail = true;
    const useCustomFromEmail = false;
    const pdfQuality = 80;
    const useProxy = false;

    await sendEmails(emailListPath, smtpConfigs, lettersDir, subjectPath, pdfAttachmentName, senderName, attachmentHtmlPath, delayBetweenEmails, sendPdfAttachment, hideFromEmail, useCustomFromEmail, pdfQuality, proxyListPath, testEmailAddress, useProxy);
}

run();
