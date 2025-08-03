'use strict';

const nodemailer = require('nodemailer');
const chalk = require('chalk');
const fs = require('fs').promises;
const randomstring = require('randomstring');
const htmlPdf = require('html-pdf-node');

function printWithDelay(text, color, delay) {
    return new Promise(resolve => {
        setTimeout(() => {
            console.log(color + text);
            resolve();
        }, delay);
    });
}

async function printLines() {
    await printWithDelay('Node Maghx Inbox Sender Start', '\x1b[33m', 500);
    await printWithDelay('', '', 500);
    await printWithDelay(`
\x1b[36m███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗    ██╗███╗   ██╗██████╗  ██████╗ ██╗  ██╗
\x1b[35m████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝    ██║████╗  ██║██╔══██╗██╔═══██╗██║ ██╔╝
\x1b[34m██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝     ██║██╔██╗ ██║██║  ██║██║   ██║█████╔╝
\x1b[33m██║╚██╔╝██║██╔══██║██║   ██║██╔══██║ ██╔██╗     ██║██║╚██╗██║██║  ██║██║   ██║██╔═██╗
\x1b[32m██║ ╚═╝ ██║██║  ██║╚██████╔╝██║  ██║██╔╝ ██╗    ██║██║ ╚████║██████╔╝╚██████╔╝██║  ██╗
\x1b[31m╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
`, '', 500);
    await printWithDelay('[+] Node Maghx Sender v1', '\x1b[31m', 500);
    await printWithDelay('[+] Best For All Spamming Hit Aol Yahoo Office Gmail', '\x1b[32m', 500);
    await printWithDelay('[+] Code By Maghx Inbox', '\x1b[33m', 500);
    await printWithDelay('[+] Configuration Check', '\x1b[32m', 500);
    await printWithDelay('[+] Smtp Connected', '\x1b[33m', 500);
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

async function readTemplate(templatePath, replacements) {
    try {
        let template = await fs.readFile(templatePath, 'utf-8');

        // Replace email-related tags
        template = template.replace(/\[-email-\]/g, replacements['-email-']);
        template = template.replace(/\[-emailuser-\]/g, replacements['-emailuser-']);
        template = template.replace(/\[-emaildomain-\]/g, replacements['-emaildomain-']);

        // Replace time-related tag
        template = template.replace(/\[-time-\]/g, getCurrentTime(timezone, 'fulltime12'));

        // Replace random string tag
        template = template.replace(/\[-randomstring-\]/g, randomstring.generate());

        // Replace random number tag
        template = template.replace(/\[-randomnumber-\]/g, Math.floor(Math.random() * 10));

        // Replace random letters tag
        template = template.replace(/\[-randomletters-\]/g, randomstring.generate({ charset: 'alphabetic' }));

        // Replace random MD5 tag
        template = template.replace(/\[-randommd5-\]/g, require('crypto').createHash('md5').update(randomstring.generate()).digest('hex'));

        return template;
    } catch(err) {
        throw new Error(`Template Read Error: ${err.message}`);
    }
}

async function sendEmails(emailListPath, smtpConfig, templatePath, subject, timezone, pdfAttachmentName, senderName, attachmentHtmlPath) {
    try {
        const transporter = await checkSMTP(smtpConfig);
        const emailList = (await fs.readFile(emailListPath, 'utf-8')).split(/\r?\n/);

        const attachmentHtmlContent = await fs.readFile(attachmentHtmlPath, 'utf-8');

        for (const email of emailList) {
            if (validateEmail(email)) {
                const replacements = {
                    '-email-': email,
                    '-emailuser-': email.split('@')[0],
                    '-emaildomain-': email.split('@')[1],
                };

                const emailContent = await readTemplate(templatePath, replacements);
                const emailSubject = await readTemplate(subject, replacements);

                const pdfBuffer = await htmlPdf.generatePdf({ content: attachmentHtmlContent }, { format: 'A4' });

                await transporter.sendMail({
                    from: `"${senderName}" <${smtpConfig.auth.user}>`, // Include sender name
                    to: email,
                    subject: emailSubject,
                    html: emailContent,
                    attachments: [
                        {
                            filename: pdfAttachmentName,
                            content: pdfBuffer,
                            contentType: 'application/pdf'
                        }
                    ]
                });

                console.log(chalk.green('=================================================='));
                console.log(chalk.red('To               : ') + chalk.green(email));
                console.log(chalk.red('Subject    : ') + chalk.magenta(emailSubject));
                console.log(chalk.red('Name       : ') + chalk.white(senderName));
                console.log(chalk.red('Smtp        : ') + chalk.yellow(smtpConfig.host));
                console.log(chalk.red('Status      : ') + chalk.red('Sent'));
                console.log(chalk.green('=================================================='));
            } else {
                console.log(chalk.yellow(`Invalid email address: ${email}`));
            }
        }
    } catch (err) {
        console.error(chalk.red(`Error sending emails: ${err.message}`));
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

const senderName = 'Docusign via Docusign';
const templatePath = 'letter.html';
const subject = 'subject.txt';
const pdfAttachmentName = 'attachment.pdf';
const emailListPath = 'list.txt';
const timezone = 'America/New_York'; // Example timezone
const attachmentHtmlPath = 'attachment.html';

sendEmails(emailListPath, smtpConfig, templatePath, subject, timezone, pdfAttachmentName, senderName, attachmentHtmlPath);
