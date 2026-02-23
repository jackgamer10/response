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

stats = {
    'total': 0, 'sent': 0, 'failed': 0, 'invalid': 0,
    'start_time': time.time(), 'current_email': '', 'current_smtp': '',
    'status': 'Idle', 'spam_score': 0.0,
    'bounces': {'hard': 0, 'soft': 0, 'spam': 0},
    'domains': {}
}

def update_ui():
    total_delivered_failed = stats['sent'] + stats['failed']
    success_rate = round((stats['sent'] / total_delivered_failed * 100), 1) if total_delivered_failed > 0 else 0

    main_table = Table(show_header=False, box=None, expand=True)
    main_table.add_row(f"[bold white]DELIVERED[/bold white]", f"[bold green]{stats['sent']}", f"[bold white]STATUS[/bold white]", f"[cyan]{stats['status']}")
    main_table.add_row(f"[bold white]FAILED[/bold white]", f"[bold red]{stats['failed']}", f"[bold white]ELAPSED[/bold white]", f"{round(time.time() - stats['start_time'], 1)}s")
    main_table.add_row(f"[bold white]SUCCESS RATE[/bold white]", f"[bold yellow]{success_rate}%", f"[bold white]TOTAL[/bold white]", f"{stats['total']}")

    bounce_table = Table(show_header=False, box=None, expand=True)
    bounce_table.add_row(f"HARD: [red]{stats['bounces']['hard']}", f"SOFT: [yellow]{stats['bounces']['soft']}", f"SPAM: [red]{stats['bounces']['spam']}")

    domain_table = Table(title="Top Domain Performance", show_header=True, header_style="bold magenta", box=None, expand=True)
    domain_table.add_column("Domain", style="white")
    domain_table.add_column("Progress", justify="center")
    domain_table.add_column("Ratio", justify="right")

    sorted_domains = sorted(stats['domains'].items(), key=lambda x: (x[1]['sent'] + x[1]['failed']), reverse=True)[:3]
    for dom, dstats in sorted_domains:
        dtotal = dstats['sent'] + dstats['failed']
        drate = (dstats['sent'] / dtotal) if dtotal > 0 else 0
        bar = "█" * int(drate * 10) + "░" * (10 - int(drate * 10))
        domain_table.add_row(dom, f"[green]{bar}[/green] {int(drate*100)}%", f"{dstats['sent']}/{dtotal}")

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"[bold cyan]magxxicVox Inbox Sender[/bold cyan] [magenta]v4.0[/magenta]", border_style="cyan", subtitle="[white]Military Grade Email Deployment")),
        Layout(Panel(main_table, title="[bold white]Delivery Metrics", border_style="green")),
        Layout(Panel(bounce_table, title="[bold white]Bounce Intelligence", border_style="yellow")),
        Layout(Panel(domain_table, border_style="magenta")),
        Layout(Panel(f"[bold white]TARGET:[/bold white] [yellow]{stats['current_email']}[/yellow]  |  [bold white]SPAM SCORE:[/bold white] [red]{stats['spam_score']}[/red]", border_style="white"))
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

def load_direct_mx_config():
    cfg_path = os.path.join(os.path.dirname(__file__), 'direct_mx_config.sys')
    set_path = os.path.join(os.path.dirname(__file__), 'direct_mx_settings.sys')
    try:
        res = {'retries': 3, 'timeout': 10000, 'verifyDns': True, 'heloDomain': 'localhost'}
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r') as f: res.update(decode_obf(f.read()))
        if os.path.exists(set_path):
            with open(set_path, 'r') as f: res.update(decode_obf(f.read()))
        return res
    except Exception: return {'retries': 3, 'timeout': 10000, 'verifyDns': True, 'heloDomain': 'localhost'}

def load_app_config():
    path = os.path.join(os.path.dirname(__file__), 'config.sys')
    try:
        if os.path.exists(path):
            with open(path, 'r') as f: return decode_obf(f.read())
    except Exception: pass
    return {
        'rotateLetters': True, 'autoShortenLinks': False, 'sendImageAttachment': True,
        'delayBetweenEmails': 2000, 'pauseEvery': 50, 'pauseTime': 30000,
        'encryptionMethod': 'ZIP', 'encryptionPassword': 'military_grade_password', 'signAttachment': True
    }

def load_dkim_config():
    dkim_path = os.path.join(os.path.dirname(__file__), 'dkim.sys')
    key_path = os.path.join(os.path.dirname(__file__), 'dkim_key.pem')
    try:
        if os.path.exists(dkim_path) and os.path.exists(key_path):
            with open(dkim_path, 'r') as f: config = decode_obf(f.read())
            with open(key_path, 'r') as f: private_key = f.read()
            return {**config, 'privateKey': private_key}
    except Exception: pass
    return None

def check_direct_mx_connectivity(proxy_url=None):
    print(f"\033[96m[+] Checking Direct MX Connectivity (Port 25)...\033[0m")
    if proxy_url:
        print(f"\033[93m  [INFO] Proxy check not implemented in this Python helper, but will be used in transport.\033[0m")

    try:
        socket.create_connection(('mx1.emailsrvr.com', 25), timeout=5)
        print(f"\033[92m  [OK] Outbound Port 25 is open.\033[0m")
    except Exception:
        if proxy_url:
            print(f"\033[93m  [INFO] Outbound Port 25 blocked locally, but will use Proxy.\033[0m")
        else:
            print(f"\033[91m  [WARN] Outbound Port 25 seems blocked. Direct sending might fail without proxy.\033[0m")
    return True

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
        text = text.replace(f"-{k}-", str(v))

    text = text.replace('[-randomstring-]', ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)))
    text = text.replace('[-randomnumber-]', str(random.randint(1000, 9999)))
    text = text.replace('[-randomletters-]', ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)))
    text = text.replace('[-randommd5-]', hashlib.md5(str(random.random()).encode()).hexdigest())
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
    msg['X-Originating-IP'] = '127.0.0.1'
    msg['X-Forwarded-For'] = '127.0.0.1'
    msg['X-Real-IP'] = '127.0.0.1'
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
        proxy = config.get('proxy')
        if proxy:
            import socks
            url = requests.utils.urlparse(proxy if '://' in proxy else f'socks5://{proxy}')
            socks.set_default_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
            socket.socket = socks.socksocket

        try:
            with smtplib.SMTP(mx, 25, timeout=transport_config.get('timeout', 10), local_hostname=transport_config.get('heloDomain')) as server:
                server.send_message(msg)
        finally:
            if proxy:
                import socket
                import importlib
                importlib.reload(socket) # Reset socket after proxy use
    else: # SMTP
        proxy = config.get('proxy')
        if proxy:
            import socks
            url = requests.utils.urlparse(proxy if '://' in proxy else f'socks5://{proxy}')
            socks.set_default_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
            socket.socket = socks.socksocket

        try:
            with smtplib.SMTP(transport_config['host'], transport_config['port'], timeout=transport_config.get('timeout', 10)) as server:
                server.starttls()
                server.login(transport_config['user'], transport_config['pass'])
                server.send_message(msg)
        finally:
            if proxy:
                import socket
                import importlib
                importlib.reload(socket)

# --- Main Flow ---

async def main():
    if not await check_license(): return

    print("\n1. SMTP (from smtp.txt)\n2. API (aws.sys, brevo.sys, etc.)\n3. Direct MX (Port 25)")
    mode = input("Select mode (1-3): ").strip()

    configs = []
    direct_mx_options = load_direct_mx_config()
    app_config = load_app_config()
    dkim_options = load_dkim_config()

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
    elif mode == '3':
        configs = [{'type': 'direct', **direct_mx_options}]
        proxies = load_files(os.path.join(os.path.dirname(__file__), 'proxies.txt'))
        check_direct_mx_connectivity(proxies[0] if proxies else None)

    if not configs: print("No configurations found!"); return
    if mode != '3': configs = check_smtp_configs(configs)
    if not configs: print("No live configurations!"); return

    email_list = load_files(os.path.join(os.path.dirname(__file__), 'list.txt'))
    stats['total'] = len(email_list)
    subjects = load_files(os.path.join(os.path.dirname(__file__), 'subjects.txt'))
    letters = [os.path.join(os.path.dirname(__file__), 'letters', f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'letters')) if f.endswith('.html')]
    links = load_files(os.path.join(os.path.dirname(__file__), 'links.txt'))
    from_emails = load_files(os.path.join(os.path.dirname(__file__), 'from_emails.txt'))
    proxies = load_files(os.path.join(os.path.dirname(__file__), 'proxies.txt'))

    with Live(update_ui(), refresh_per_second=4) as live:
        for idx, email in enumerate(email_list):
            domain = email.split('@')[1]
            if domain not in stats['domains']: stats['domains'][domain] = {'sent': 0, 'failed': 0}

            stats['current_email'] = email

            if direct_mx_options.get('verifyDns'):
                stats['status'] = 'Verifying'
                live.update(update_ui())
                if not get_mx(email):
                    stats['invalid'] += 1; continue

            stats['status'] = 'Processing'
            live.update(update_ui())

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

                # PDF Attachment Auto-Convert
                attachment_html_path = os.path.join(os.path.dirname(__file__), 'attachment.html')
                if os.path.exists(attachment_html_path):
                    stats['status'] = 'Generating PDF'
                    live.update(update_ui())
                    with open(attachment_html_path, 'r', encoding='utf-8') as f:
                        att_html = replace_tags(f.read(), repls)

                    if Html2Image:
                        hti = Html2Image(output_path=os.path.dirname(__file__))
                        img_path = hti.screenshot(html_str=att_html, save_as='temp_att.png')
                        from PIL import Image
                        img = Image.open(os.path.join(os.path.dirname(__file__), 'temp_att.png'))
                        pdf_buffer = io.BytesIO()
                        img.save(pdf_buffer, format='PDF')
                        atts.append({'filename': 'attachment.pdf', 'content': pdf_buffer.getvalue()})
                        os.remove(os.path.join(os.path.dirname(__file__), 'temp_att.png'))

                stats['status'] = 'Sending'
                live.update(update_ui())

                conf = configs[idx % len(configs)].copy()
                if from_emails: conf['from_email'] = replace_tags(random.choice(from_emails), repls)

                proxy = proxies[idx % len(proxies)] if proxies else None
                send_email(conf, email, content, subject, atts, dkim_options, {**app_config, 'proxy': proxy})
                stats['sent'] += 1
                stats['domains'][domain]['sent'] += 1
            except Exception as e:
                stats['failed'] += 1
                stats['domains'][domain]['failed'] += 1
                stats['status'] = f"Error: {str(e)[:20]}"

                msg = str(e).lower()
                if any(x in msg for x in ['spam', 'blocked', 'blacklisted']): stats['bounces']['spam'] += 1
                elif any(x in msg for x in ['not found', 'unavailable', '550']): stats['bounces']['hard'] += 1
                else: stats['bounces']['soft'] += 1

            live.update(update_ui())
            time.sleep(app_config.get('delayBetweenEmails', 2000) / 1000)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
