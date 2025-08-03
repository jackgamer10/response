'use strict';

const nodemailer = require('nodemailer');
const fs = require('fs').promises;
const randomstring = require('randomstring');
const htmlPdf = require('html-pdf-node');

const VALID_KEYS = [
    'ACTIVATION-KEY-SAMPLE-12345',
    // Add more valid keys here
];

async function checkLicense() {
    try {
        const key = await fs.readFile('license.key', 'utf-8');
        if (!VALID_KEYS.includes(key.trim())) {
            throw new Error('Invalid license key.');
        }
        console.log('License key validated.');
    } catch (err) {
        console.error('Error: License key not found or is invalid.');
        console.error('Please contact the administrator for an activation key.');
        process.exit(1); // Exit the script
    }
}

function printWithDelay(text, color, delay) {
    return new Promise(resolve => {
        setTimeout(() => {
            console.log(text);
            resolve();
        }, delay);
    });
}

async function printLines() {
    await printWithDelay('Node Maghx Inbox Sender Start', null, 500);
    await printWithDelay('', null, 500);
    await printWithDelay(`
███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗    ██╗███╗   ██╗██████╗  ██████╗ ██╗  ██╗
████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝    ██║████╗  ██║██╔══██╗██╔═══██╗██║ ██╔╝
██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝     ██║██╔██╗ ██║██║  ██║██║   ██║█████╔╝
██║╚██╔╝██║██╔══██║██║   ██║██╔══██║ ██╔██╗     ██║██║╚██╗██║██║  ██║██║   ██║██╔═██╗
██║ ╚═╝ ██║██║  ██║╚██████╔╝██║  ██║██╔╝ ██╗    ██║██║ ╚████║██████╔╝╚██████╔╝██║  ██╗
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
`, null, 500);
    await printWithDelay('[+] Node Maghx Sender v1', null, 500);
    await printWithDelay('[+] Best For All Spamming Hit Aol Yahoo Office Gmail', null, 500);
    await printWithDelay('[+] Code By Maghx Inbox', null, 500);
    await printWithDelay('[+] Configuration Check', null, 500);
    await printWithDelay('[+] Smtp Connected', null, 500);
}

printLines();



async function checkSMTP(data) {
    try {
        const transporter = nodemailer.createTransport(data);
        await transporter.verify();
        return transporter;
    } catch(err) {
        throw new Error(`SMTP ERROR: ${err.message}`);
    }
}

function replaceTags(text, replacements, timezone) {
    let newText = text;
    // Replace email-related tags
    newText = newText.replace(/\[-email-\]/g, replacements['-email-']);
    newText = newText.replace(/\[-emailuser-\]/g, replacements['-emailuser-']);
    newText = newText.replace(/\[-emaildomain-\]/g, replacements['-emaildomain-']);

    // Replace time-related tag
    newText = newText.replace(/\[-time-\]/g, getCurrentTime(timezone, 'fulltime12'));

    // Replace random string tag
    newText = newText.replace(/\[-randomstring-\]/g, randomstring.generate());

    // Replace random number tag
    newText = newText.replace(/\[-randomnumber-\]/g, Math.floor(Math.random() * 10));

    // Replace random letters tag
    newText = newText.replace(/\[-randomletters-\]/g, randomstring.generate({ charset: 'alphabetic' }));

    // Replace random MD5 tag
    newText = newText.replace(/\[-randommd5-\]/g, require('crypto').createHash('md5').update(randomstring.generate()).digest('hex'));

    return newText;
}

async function readTemplate(templatePath, replacements, timezone) {
    try {
        const template = await fs.readFile(templatePath, 'utf-8');
        return replaceTags(template, replacements, timezone);
    } catch(err) {
        throw new Error(`Template Read Error: ${err.message}`);
    }
}

async function sendEmails(emailListPath, smtpConfig, templatePath, subject, timezone, pdfAttachmentName, senderName, attachmentHtmlPath) {
    try {
        const transporter = await checkSMTP(smtpConfig);
        const emailList = (await fs.readFile(emailListPath, 'utf-8')).split(/\r?\n/);

        for (const email of emailList) {
            if (validateEmail(email)) {
                const replacements = {
                    '-email-': email,
                    '-emailuser-': email.split('@')[0],
                    '-emaildomain-': email.split('@')[1],
                };

                const emailContent = await readTemplate(templatePath, replacements, timezone);
                const emailSubjectText = await fs.readFile(subject, 'utf-8');
                const emailSubject = replaceTags(emailSubjectText, replacements, timezone);

                const dynamicPdfName = replaceTags(pdfAttachmentName, replacements, timezone);
                const attachmentHtmlContent = await readTemplate(attachmentHtmlPath, replacements, timezone);

                const pdfBuffer = await htmlPdf.generatePdf({ content: attachmentHtmlContent }, { format: 'A4' });

                await transporter.sendMail({
                    from: `"${senderName}" <${smtpConfig.auth.user}>`, // Include sender name
                    to: email,
                    subject: emailSubject,
                    html: emailContent,
                    attachments: [
                        {
                            filename: dynamicPdfName,
                            content: pdfBuffer,
                            contentType: 'application/pdf'
                        }
                    ]
                });

                console.log('==================================================');
                console.log('To               : ' + email);
                console.log('Subject    : ' + emailSubject);
                console.log('Name       : ' + senderName);
                console.log('Smtp        : ' + smtpConfig.host);
                console.log('Status      : Sent');
                console.log('==================================================');
            } else {
                console.log(`Invalid email address: ${email}`);
            }
        }
    } catch (err) {
        console.error(`Error sending emails: ${err.message}`);
    }
}

function validateEmail(email) {
    // Implement proper email address validation logic
    return true;
}

function getCurrentTime(timezone, format) {
    // Implement logic to get current time in the specified timezone and format
    return '';
}

// Define SMTP configuration, template path, subject, and other parameters
const smtpConfig = {
    host: 'smtp.ionos.com',
    port: 587,
    secure: false,
    requireTLS: true,
    auth: {
        user: 'gbeasley@allagesvisioncare.com',
        pass: 'Aavc^@6917#100',
    },
};

async function run() {
    await checkLicense();

    const senderName = 'Docusign via Docusign';
    const templatePath = 'letter.html';
    const subject = 'subject.txt';
    const pdfAttachmentName = 'Docusign_[-emaildomain-]_[-randomstring-].pdf';
    const emailListPath = 'list.txt';
    const timezone = 'America/New_York'; // Example timezone
    const attachmentHtmlPath = 'attachment.html';

    // Define SMTP configuration just before sending emails
    const smtpConfig = {
        host: 'smtp.ionos.com',
        port: 587,
        secure: false,
        requireTLS: true,
        auth: {
            user: 'gbeasley@allagesvisioncare.com',
            pass: 'Aavc^@6917#100',
        },
    };

    await printLines();
    await sendEmails(emailListPath, smtpConfig, templatePath, subject, timezone, pdfAttachmentName, senderName, attachmentHtmlPath);
}

run();
