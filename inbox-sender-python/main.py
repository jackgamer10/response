import os
import sys
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
import random
import json
import base64
import hashlib
import smtplib
import ssl
import socket
import dns.resolver
import requests
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.utils import formataddr, make_msgid
import dkim
import barcode
from barcode.writer import ImageWriter
try:
    from html2image import Html2Image
except ImportError:
    Html2Image = None
from Crypto.Cipher import AES
import zipfile
import io
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
import platform
import uuid

# --- Core Obfuscation & License ---

def get_hwid():
    try:
        system_info = f"{platform.node()}-{platform.processor()}-{uuid.getnode()}"
        return hashlib.sha256(system_info.encode()).hexdigest().upper()
    except Exception:
        return f"UNKNOWN-HWID-{hashlib.md5(socket.gethostname().encode()).hexdigest().upper()}"

SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024'

def generate_token(hwid):
    return hashlib.sha256((hwid + SECRET_SALT).encode()).hexdigest().upper()

def encode_obf(data):
    json_data = json.dumps(data, separators=(',', ':'))
    b64_data = base64.b64encode(json_data.encode()).decode()
    return b64_data[::-1]

def decode_obf(data):
    b64_data = data[::-1]
    json_data = base64.b64decode(b64_data).decode()
    return json.loads(json_data)

async def check_license():
    activation_path = os.path.join(os.path.dirname(__file__), 'activation.sys')
    hwid = get_hwid()
    if os.path.exists(activation_path):
        try:
            with open(activation_path, 'r') as f:
                data = decode_obf(f.read())
            if data.get('hwid') == hwid and data.get('token') == generate_token(hwid):
                print(f"\033[92m[+] License activated for HWID: {hwid[:8]}...\033[0m")
                return True
        except Exception: pass
    print("\033[93m[!] Software not activated.\033[0m")
    print(f"\033[96mYour HWID: \033[1m{hwid}\033[0m")
    token = input('Enter Activation Token: ').strip().upper()
    if token == generate_token(hwid):
        data = {'hwid': hwid, 'token': token, 'installPath': os.path.dirname(__file__)}
        with open(activation_path, 'w') as f: f.write(encode_obf(data))
        print("\033[92m[+] Activation successful! Please restart.\033[0m")
        sys.exit(0)
    else:
        print("\033[91m[!] Invalid activation token.\033[0m")
        sys.exit(1)

# --- Statistics & UI ---

stats = {'total': 0, 'sent': 0, 'failed': 0, 'invalid': 0, 'start_time': time.time(), 'current_email': '', 'current_smtp': '', 'status': 'Idle', 'spam_score': 0.0}

def update_ui():
    elapsed = round(time.time() - stats['start_time'], 1)
    remaining = stats['total'] - (stats['sent'] + stats['failed'] + stats['invalid'])
    table = Table(show_header=False, box=None)
    table.add_row(f"[white]Total Loaded: {stats['total']}", f"[white]Elapsed: {elapsed}s")
    table.add_row(f"[green]Sent: {stats['sent']}", f"[red]Failed: {stats['failed']}")
    table.add_row(f"[yellow]Invalid: {stats['invalid']}", f"[white]Remaining: {remaining}")
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"[cyan]magxxicVox Inbox Sender (Python) - Live Statistics[/cyan]", border_style="magenta")),
        Layout(Panel(table, border_style="magenta")),
        Layout(Panel(f"[cyan]Status: [white]{stats['status']}\n[cyan]Email : [white]{stats['current_email']}\n[cyan]SMTP  : [white]{stats['current_smtp']}\n[cyan]Spam Score: [white]{stats['spam_score']}", border_style="magenta"))
    )
    return layout

# --- Helpers ---

def get_mx(email):
    try:
        domain = email.split('@')[1]
        answers = dns.resolver.resolve(domain, 'MX')
        return sorted([(r.preference, r.exchange.to_text()) for r in answers])[0][1]
    except Exception: return None

def load_files(filepath):
    if not os.path.exists(filepath): return []
    with open(filepath, 'r', encoding='utf-8') as f: return [line.strip() for line in f if line.strip()]

def evaluate_spam_score(subject, body):
    score = 0.0
    triggers = ['urgent', 'money', 'free', 'winner', 'account suspended', 'bitcoin', 'prize', 'cash']
    for t in triggers:
        if t in subject.lower() or t in body.lower(): score += 1.2
    if 'unsubscribe' not in body.lower(): score += 2.0
    if body.isupper(): score += 1.5
    return round(min(score, 10.0), 1)

async def generate_barcode_buffer(data):
    ean = barcode.get('code128', data, writer=ImageWriter())
    buffer = io.BytesIO()
    ean.write(buffer)
    return buffer.getvalue()

async def get_recipient_logo(email):
    domain = email.split('@')[1]
    try:
        r = requests.get(f"https://logo.clearbit.com/{domain}", timeout=3)
        if r.status_code == 200: return r.content
    except Exception: pass
    return None

def encrypt_attachment(data, method, password):
    if method == 'ZIP':
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf: zf.writestr('attachment.dat', data)
        return buffer.getvalue()
    elif method == 'AES':
        key = hashlib.sha256(password.encode()).digest()
        cipher = AES.new(key, AES.MODE_CFB)
        return cipher.iv + cipher.encrypt(data)
    return data

def replace_tags(text, replacements):
    for k, v in replacements.items():
        text = text.replace(f"[-{k}-]", str(v)).replace(f"[{k}]", str(v))
    text = text.replace('[-randomstring-]', ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)))
    text = text.replace('[-randomnumber-]', str(random.randint(1000, 9999)))
    text = text.replace('[-time-]', time.strftime("%Y-%m-%d %H:%M:%S"))
    return text

# --- Transport & Sending ---

def check_smtp_configs(configs):
    live = []
    print(f"\033[96m[+] Checking SMTP configurations...\033[0m")
    for c in configs:
        try:
            if c.get('type') in ['aws', 'mailgun', 'sendgrid']:
                print(f"\033[93m  [SKIP] API Config: {c['type']}\033[0m")
                live.append(c); continue
            with smtplib.SMTP(c['host'], c['port'], timeout=10) as server:
                server.starttls()
                server.login(c['user'], c['pass'])
                live.append(c)
                print(f"\033[92m  [LIVE] {c['host']}\033[0m")
        except Exception as e:
            print(f"\033[91m  [DEAD] {c.get('host', 'API')}: {str(e)[:30]}\033[0m")
    return live

def send_email(transport_config, email, content, subject, attachments, dkim_options, config):
    msg = MIMEMultipart()
    msg['To'] = email
    msg['From'] = transport_config.get('from_email', transport_config.get('user', 'sender@example.com'))
    msg['Subject'] = subject
    msg['X-Priority'] = '1 (Highest)'
    msg['X-Mailer'] = 'Microsoft Outlook 16.0'
    msg['Message-ID'] = make_msgid(domain=email.split('@')[1])
    msg.attach(MIMEText(content, 'html'))

    for att in attachments:
        part = MIMEApplication(att['content'])
        part.add_header('Content-Disposition', 'attachment', filename=att['filename'])
        if att.get('cid'): part.add_header('Content-ID', f"<{att['cid']}>")
        msg.attach(part)

    if dkim_options:
        sig = dkim.sign(msg.as_bytes(), dkim_options['keySelector'].encode(), dkim_options['domainName'].encode(), dkim_options['privateKey'].encode())
        msg['DKIM-Signature'] = sig.decode().split('DKIM-Signature: ')[1]

    if transport_config.get('type') == 'aws':
        client = boto3.client('ses', region_name=transport_config['region'], aws_access_key_id=transport_config['accessKeyId'], aws_secret_access_key=transport_config['secretAccessKey'])
        client.send_raw_email(Source=msg['From'], Destinations=[msg['To']], RawMessage={'Data': msg.as_bytes()})
    elif transport_config.get('type') == 'direct':
        mx = get_mx(email)
        with smtplib.SMTP(mx, 25) as server: server.send_message(msg)
    else: # SMTP
        with smtplib.SMTP(transport_config['host'], transport_config['port']) as server:
            server.starttls()
            server.login(transport_config['user'], transport_config['pass'])
            server.send_message(msg)

# --- Main Flow ---

async def main():
    if not await check_license(): return

    print("\n1. SMTP (from smtp.txt)\n2. API (aws.sys, brevo.sys, etc.)\n3. Direct MX (Port 25)")
    mode = input("Select mode (1-3): ").strip()

    configs = []
    if mode == '1':
        for l in load_files(os.path.join(os.path.dirname(__file__), 'smtp.txt')):
            p = l.split('|')
            if len(p) >= 4: configs.append({'host':p[0], 'port':int(p[1]), 'user':p[2], 'pass':p[3]})
    elif mode == '2':
        for f in ['aws.sys', 'brevo.sys', 'mailgun.sys', 'sendgrid.sys']:
            p_ = os.path.join(os.path.dirname(__file__), f)
            if os.path.exists(p_):
                with open(p_, 'r') as file:
                    data = decode_obf(file.read())
                    data['type'] = f.split('.')[0]
                    configs.append(data)
    elif mode == '3': configs = [{'type': 'direct'}]

    if not configs: print("No configurations found!"); return
    if mode != '3': configs = check_smtp_configs(configs)
    if not configs: print("No live configurations!"); return

    email_list = load_files(os.path.join(os.path.dirname(__file__), 'list.txt'))
    stats['total'] = len(email_list)
    subjects = load_files(os.path.join(os.path.dirname(__file__), 'subjects.txt'))
    letters = [os.path.join(os.path.dirname(__file__), 'letters', f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'letters')) if f.endswith('.html')]
    links = load_files(os.path.join(os.path.dirname(__file__), 'links.txt'))
    from_emails = load_files(os.path.join(os.path.dirname(__file__), 'from_emails.txt'))

    with Live(update_ui(), refresh_per_second=4) as live:
        for idx, email in enumerate(email_list):
            stats['current_email'] = email
            stats['status'] = 'Verifying'
            live.update(update_ui())

            if not get_mx(email):
                stats['invalid'] += 1; continue

            try:
                repls = {'email': email, 'emailuser': email.split('@')[0], 'emaildomain': email.split('@')[1]}
                if links: repls['link'] = random.choice(links)

                content = replace_tags(open(random.choice(letters)).read(), repls)
                subject = replace_tags(random.choice(subjects), repls)
                stats['spam_score'] = evaluate_spam_score(subject, content)
                stats['current_smtp'] = configs[idx % len(configs)].get('host', configs[idx % len(configs)].get('type'))

                atts = []
                if '[-barcode-]' in content:
                    stats['status'] = 'Barcoding'
                    live.update(update_ui())
                    bc = await generate_barcode_buffer(email)
                    atts.append({'filename': 'barcode.png', 'content': bc, 'cid': 'barcode'})
                    content = content.replace('[-barcode-]', '<img src="cid:barcode"/>')

                if '[-recipient-logo-]' in content:
                    stats['status'] = 'Fetching Logo'
                    live.update(update_ui())
                    logo = await get_recipient_logo(email)
                    if logo:
                        atts.append({'filename': 'logo.png', 'content': logo, 'cid': 'logo'})
                        content = content.replace('[-recipient-logo-]', '<img src="cid:logo"/>')

                stats['status'] = 'Sending'
                live.update(update_ui())

                conf = configs[idx % len(configs)].copy()
                if from_emails: conf['from_email'] = replace_tags(random.choice(from_emails), repls)

                send_email(conf, email, content, subject, atts, None, {})
                stats['sent'] += 1
            except Exception as e:
                stats['failed'] += 1
                stats['status'] = f"Error: {str(e)[:20]}"

            live.update(update_ui())
            time.sleep(2)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
