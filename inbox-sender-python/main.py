import os
import sys
import time
import asyncio
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
from colorama import init, Fore, Style

# Initialize Colorama for beautiful cross-platform colors
init(autoreset=True)

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
    return json.dumps(data, indent=4)

def decode_obf(data):
    return json.loads(data)

async def check_license():
    activation_path = os.path.join(os.path.dirname(__file__), 'activation.sys')
    hidden_path = os.path.join(os.path.dirname(__file__), '.activation.sys')
    hwid = get_hwid()

    current_path = None
    if os.path.exists(activation_path): current_path = activation_path
    elif os.path.exists(hidden_path): current_path = hidden_path

    if current_path:
        try:
            with open(current_path, 'r') as f:
                data = decode_obf(f.read())
            if data.get('hwid') == hwid and data.get('token') == generate_token(hwid):
                print(Fore.GREEN + f"[+] License activated for HWID: {hwid[:8]}...")
                return True
        except Exception: pass
    print(Fore.YELLOW + "[!] Software not activated.")
    print(Fore.CYAN + f"Your HWID: " + Style.BRIGHT + f"{hwid}")
    token = input(Fore.WHITE + 'Enter Activation Token: ').strip().upper()
    if token == generate_token(hwid):
        data = {'hwid': hwid, 'token': token, 'installPath': os.path.dirname(__file__)}
        target_path = activation_path if os.name == 'nt' else hidden_path
        with open(target_path, 'w') as f: f.write(encode_obf(data))

        # Hide file on Windows
        if os.name == 'nt':
            import subprocess
            subprocess.run(['attrib', '+h', target_path], check=False)

        print(Fore.GREEN + "[+] Activation successful! Please restart.")
        sys.exit(0)
    else:
        print(Fore.RED + "[!] Invalid activation token.")
        sys.exit(1)

# --- Statistics & UI ---

stats = {
    'total': 0, 'sent': 0, 'failed': 0, 'invalid': 0,
    'start_time': time.time(), 'current_email': '', 'current_smtp': '',
    'current_proxy': 'None',
    'status': 'Idle', 'spam_score': 0.0,
    'bounces': {'hard': 0, 'soft': 0, 'spam': 0},
    'domains': {},
    'dns_verified': False,
    'proxies': {'live': 0, 'total': 0},
    'port25': 'Unknown'
}

def update_ui():
    total_delivered_failed = stats['sent'] + stats['failed']
    success_rate = round((stats['sent'] / total_delivered_failed * 100), 1) if total_delivered_failed > 0 else 0

    main_table = Table(show_header=False, box=None, expand=True)
    main_table.add_row(f"[bold white]DELIVERED[/bold white]", f"[bold green]{stats['sent']}", f"[bold white]STATUS[/bold white]", f"[cyan]{stats['status']}")
    main_table.add_row(f"[bold white]FAILED[/bold white]", f"[bold red]{stats['failed']}", f"[bold white]ELAPSED[/bold white]", f"{round(time.time() - stats['start_time'], 1)}s")
    main_table.add_row(f"[bold white]SUCCESS RATE[/bold white]", f"[bold yellow]{success_rate}%", f"[bold white]TOTAL[/bold white]", f"{stats['total']}")

    dns_status = "[bold green]ENABLED[/bold green]" if stats['dns_verified'] else "[bold red]DISABLED[/bold red]"
    diag_table = Table(show_header=False, box=None, expand=True)
    p25_col = "[green]Open[/green]" if stats['port25'] == 'Open' else ("[red]Blocked[/red]" if stats['port25'] == 'Blocked' else "[yellow]Proxied[/yellow]")
    diag_table.add_row(f"DNS VERIFY: {dns_status}", f"PORT 25: {p25_col}", f"PROXIES: [green]{stats['proxies']['live']}/{stats['proxies']['total']} Live[/green]")
    diag_table.add_row(f"CURRENT SMTP: [yellow]{stats['current_smtp']}", f"PROXY: [cyan]{stats['current_proxy']}", "")

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
        Layout(Panel(diag_table, title="[bold white]Diagnostic Intelligence", border_style="cyan")),
        Layout(Panel(bounce_table, title="[bold white]Bounce Intelligence", border_style="yellow")),
        Layout(Panel(domain_table, border_style="magenta")),
        Layout(Panel(f"[bold white]TARGET:[/bold white] [yellow]{stats['current_email']}[/yellow]  |  [bold white]SPAM SCORE:[/bold white] [red]{stats['spam_score']}[/red]", border_style="white"))
    )
    return layout

# --- Helpers ---

def get_mx(email):
    try:
        domain = email.split('@')[1]
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            hosts = sorted([(r.preference, r.exchange.to_text().rstrip('.')) for r in answers])
            return hosts[0][1]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            # Fallback to A record if no MX
            return domain
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

def validate_proxies(proxy_list):
    print(Fore.CYAN + f"[+] Validating {len(proxy_list)} proxies...")
    stats['proxies']['total'] = len(proxy_list)
    valid_proxies = []
    import socks
    for proxy_url in proxy_list:
        try:
            url = requests.utils.urlparse(proxy_url if '://' in proxy_url else f'socks5://{proxy_url}')
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
            s.settimeout(5)
            s.connect(('1.1.1.1', 53))
            s.close()
            valid_proxies.append(proxy_url)
            stats['proxies']['live'] = len(valid_proxies)
            print(Fore.GREEN + f"  [ALIVE] {proxy_url}")
        except Exception as e:
            print(Fore.RED + f"  [DEAD] {proxy_url}: {str(e)[:30]}")
    return valid_proxies

def check_direct_mx_connectivity(proxy_url=None):
    print(Fore.CYAN + "[+] Checking Direct MX Connectivity (Port 25)...")
    test_host = 'mx1.emailsrvr.com'
    try:
        if proxy_url:
            import socks
            url = requests.utils.urlparse(proxy_url if '://' in proxy_url else f'socks5://{proxy_url}')
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
            s.settimeout(5)
            s.connect((test_host, 25))
            s.close()
            print(Fore.GREEN + f"  [OK] Port 25 is reachable via Proxy.")
            stats['port25'] = 'Proxied'
        else:
            socket.create_connection((test_host, 25), timeout=5)
            print(Fore.GREEN + "  [OK] Outbound Port 25 is open locally.")
            stats['port25'] = 'Open'
    except Exception as e:
        print(Fore.RED + f"  [FAIL] Port 25 is unreachable: {str(e)[:30]}")
        stats['port25'] = 'Blocked'
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
    tags = ['email', 'emailuser', 'emaildomain', 'emaildomainname', 'time', 'randomstring', 'randomnumber', 'randomletters', 'randommd5', 'link']
    for tag in tags:
        val = None
        if tag in replacements: val = replacements[tag]
        elif tag == 'time': val = time.strftime("%Y-%m-%d %H:%M:%S")
        elif tag == 'randomstring': val = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))
        elif tag == 'randomnumber': val = str(random.randint(1000, 9999))
        elif tag == 'randomletters': val = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))
        elif tag == 'randommd5': val = hashlib.md5(str(random.random()).encode()).hexdigest()

        if val is not None:
            text = text.replace(f"[-{tag}-]", str(val))
            text = text.replace(f"[{tag}]", str(val))
            text = text.replace(f"-{tag}-", str(val))
    return text

# --- Transport & Sending ---

def check_smtp_configs(configs, proxy=None):
    live = []
    print(Fore.CYAN + "[+] Checking SMTP configurations...")

    orig_socket = socket.socket
    if proxy:
        import socks
        url = requests.utils.urlparse(proxy if '://' in proxy else f'socks5://{proxy}')
        socks.set_default_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
        socket.socket = socks.socksocket

    try:
        for c in configs:
            try:
                if c.get('type') in ['aws', 'mailgun', 'sendgrid']:
                    print(Fore.YELLOW + f"  [SKIP] API Config: {c['type']}")
                    live.append(c); continue

                if c.get('type') == 'brevo':
                    c['host'] = 'smtp-relay.brevo.com'
                    c['port'] = 587
                    c['pass'] = c.get('apiKey')

                # Permissive SSL context
                context = ssl._create_unverified_context()

                if c['port'] == 465:
                    server = smtplib.SMTP_SSL(c['host'], c['port'], timeout=15, context=context)
                else:
                    server = smtplib.SMTP(c['host'], c['port'], timeout=15)
                    try:
                        server.starttls(context=context)
                    except Exception: pass

                with server:
                    server.login(c['user'], c['pass'])
                    live.append(c)
                    print(Fore.GREEN + f"  [LIVE] {c['host']}")
            except Exception as e:
                print(Fore.RED + f"  [DEAD] {c.get('host', 'API')}: {str(e)[:30]}")
    finally:
        if proxy:
            socket.socket = orig_socket

    return live

def send_email(transport_config, email, content, subject, attachments, dkim_options, config):
    msg = MIMEMultipart()
    msg['To'] = email
    msg['From'] = transport_config.get('from_email', transport_config.get('user', 'sender@example.com'))
    msg['Subject'] = subject
    msg['X-Priority'] = '1 (Highest)'
    msg['Importance'] = 'High'
    msg['X-MSMail-Priority'] = 'High'
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

    # Robust timeout conversion (ms to s)
    raw_timeout = transport_config.get('timeout', 10000)
    timeout_s = raw_timeout / 1000.0 if raw_timeout > 500 else raw_timeout

    if transport_config.get('type') == 'aws':
        client = boto3.client('ses', region_name=transport_config['region'], aws_access_key_id=transport_config['accessKeyId'], aws_secret_access_key=transport_config['secretAccessKey'])
        last_err = None
        for _ in range(3):
            try:
                client.send_raw_email(Source=msg['From'], Destinations=[msg['To']], RawMessage={'Data': msg.as_bytes()})
                return
            except Exception as e: last_err = e; time.sleep(1)
        if last_err: raise last_err
    elif transport_config.get('type') == 'mailgun':
        url = f"https://api.mailgun.net/v3/{transport_config['domain']}/messages.mime"
        auth = ("api", transport_config['apiKey'])
        files = {'to': (None, email), 'message': ('message.mime', msg.as_bytes())}
        last_err = None
        for _ in range(3):
            try:
                r = requests.post(url, auth=auth, files=files, timeout=30)
                r.raise_for_status()
                return
            except Exception as e: last_err = e; time.sleep(1)
        if last_err: raise last_err
    elif transport_config.get('type') == 'sendgrid':
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {"Authorization": f"Bearer {transport_config['apiKey']}"}
        data = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": transport_config.get('from_email', transport_config.get('user', 'sender@example.com'))},
            "subject": subject,
            "content": [{"type": "text/html", "value": content}]
        }
        if attachments:
            data["attachments"] = []
            for att in attachments:
                data["attachments"].append({
                    "content": base64.b64encode(att['content']).decode(),
                    "filename": att['filename'],
                    "disposition": "attachment",
                    "content_id": att.get('cid', '')
                })
        last_err = None
        for _ in range(3):
            try:
                r = requests.post(url, headers=headers, json=data, timeout=30)
                r.raise_for_status()
                return
            except Exception as e: last_err = e; time.sleep(1)
        if last_err: raise last_err
    elif transport_config.get('type') == 'direct':
        mx = get_mx(email)
        proxy = config.get('proxy')
        if proxy:
            import socks
            url = requests.utils.urlparse(proxy if '://' in proxy else f'socks5://{proxy}')
            socks.set_default_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
            socket.socket = socks.socksocket

        try:
            last_err = None
            for _ in range(transport_config.get('retries', 3)):
                try:
                    with smtplib.SMTP(mx, 25, timeout=timeout_s, local_hostname=transport_config.get('heloDomain')) as server:
                        try:
                            server.starttls(context=ssl._create_unverified_context())
                        except Exception: pass
                        server.send_message(msg)
                    return
                except Exception as e:
                    last_err = e
                    time.sleep(1)
            if last_err: raise last_err
        finally:
            if proxy:
                socket.socket = orig_socket
    else: # SMTP
        if transport_config.get('type') == 'brevo':
            transport_config['host'] = 'smtp-relay.brevo.com'
            transport_config['port'] = 587
            transport_config['pass'] = transport_config.get('apiKey')

        proxy = config.get('proxy')
        orig_socket = socket.socket
        if proxy:
            import socks
            url = requests.utils.urlparse(proxy if '://' in proxy else f'socks5://{proxy}')
            socks.set_default_proxy(socks.SOCKS5, url.hostname, url.port, True, url.username, url.password)
            socket.socket = socks.socksocket

        try:
            last_err = None
            for _ in range(config.get('directMxOptions', {}).get('retries', 3)):
                try:
                    helo = config.get('directMxOptions', {}).get('heloDomain', 'localhost')
                    context = ssl._create_unverified_context()
                    if transport_config.get('port') == 465:
                        server = smtplib.SMTP_SSL(transport_config['host'], transport_config['port'], timeout=timeout_s, local_hostname=helo, context=context)
                    else:
                        server = smtplib.SMTP(transport_config['host'], transport_config['port'], timeout=timeout_s, local_hostname=helo)
                        try:
                            server.starttls(context=context)
                        except Exception: pass

                    with server:
                        server.login(transport_config['user'], transport_config['pass'])
                        server.send_message(msg)
                    return # Success
                except Exception as e:
                    last_err = e
                    time.sleep(1)
            if last_err: raise last_err
        finally:
            if proxy:
                socket.socket = orig_socket

# --- Main Flow ---

def show_settings_dashboard(app_config, direct_mx_options):
    console = Console()
    while True:
        table = Table(title="[bold cyan]Operation Configuration Dashboard[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Option", style="white")
        table.add_column("Current Value", style="yellow")
        table.add_column("Description", style="dim white")

        table.add_row("1. Delay (ms)", str(app_config.get('delayBetweenEmails', 2000)), "Wait time between each email")
        table.add_row("2. Rotate Letters", "ENABLED" if app_config.get('rotateLetters') else "DISABLED", "Use different templates for each email")
        table.add_row("3. Shorten Links", "ENABLED" if app_config.get('autoShortenLinks') else "DISABLED", "Automatically clean/shorten URLs")
        table.add_row("4. Encryption", app_config.get('encryptionMethod', 'ZIP'), "Attachment protection (ZIP/AES/None)")
        table.add_row("5. Sign Attachment", "ENABLED" if app_config.get('signAttachment') else "DISABLED", "Add cryptographic signature to files")
        table.add_row("6. HELO Domain", direct_mx_options.get('heloDomain', 'localhost'), "HELO/EHLO hostname for SMTP")
        table.add_row("7. DNS Verify", "ENABLED" if direct_mx_options.get('verifyDns') else "DISABLED", "Deep check recipient MX before sending")
        table.add_row("8. SMTP Timeout", str(direct_mx_options.get('timeout', 10000)), "Connection timeout in ms")
        table.add_row("9. SAVE & EXIT", "", "Apply changes and return to main menu")

        console.print(table)
        choice = input(Fore.WHITE + "\nSelect option to toggle/edit (1-9): ").strip()

        if choice == '1':
            val = input("Enter new delay (ms): ")
            if val.isdigit(): app_config['delayBetweenEmails'] = int(val)
        elif choice == '2': app_config['rotateLetters'] = not app_config.get('rotateLetters', True)
        elif choice == '3': app_config['autoShortenLinks'] = not app_config.get('autoShortenLinks', False)
        elif choice == '4':
            methods = ['ZIP', 'AES', 'None']
            curr = app_config.get('encryptionMethod', 'ZIP')
            app_config['encryptionMethod'] = methods[(methods.index(curr) + 1) % len(methods)]
        elif choice == '5': app_config['signAttachment'] = not app_config.get('signAttachment', True)
        elif choice == '6':
            val = input("Enter HELO domain: ")
            if val: direct_mx_options['heloDomain'] = val
        elif choice == '7': direct_mx_options['verifyDns'] = not direct_mx_options.get('verifyDns', True)
        elif choice == '8':
            val = input("Enter timeout (ms): ")
            if val.isdigit(): direct_mx_options['timeout'] = int(val)
        elif choice == '9':
            # Save to files
            with open(os.path.join(os.path.dirname(__file__), 'config.sys'), 'w') as f: f.write(encode_obf(app_config))
            with open(os.path.join(os.path.dirname(__file__), 'direct_mx_config.sys'), 'w') as f: f.write(encode_obf(direct_mx_options))
            break

async def main():
    if not await check_license(): return

    app_config = load_app_config()
    direct_mx_options = load_direct_mx_config()
    dkim_options = load_dkim_config()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.RED + """
      @@@@          @@@@@@@@@@@@@@@@@@@@@@@@          @@@@
      @@@@          @@@@@@@@@@@@@@@@@@@@@@@@          @@@@
                    @@@@@@@@@@@@@@@@@@@@@@@@
                          @@@@@@@@@@
                      @@@@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@@@@@@@
                  @@@@@@@@@@@@@@@@@@@@@@@@@@""")
        print(Fore.BLUE + r"""
  __  __    _    ____ __  __ __  __ __  __ ___  ____  _  _  _____
 |  \/  |  / \  / ___|\ \/ / \ \/ / \ \/ /|_ _|| ___|| \/ ||_   _|
 | |\/| | / _ \| |  _  \  /   \  /   \  /  | | | |   |    |  | |
 | |  | |/ ___ \ |_| | /  \   /  \   /  \  | | | |__ | |\ |  | |
 |_|  |_/_/   \_\____|/_/\_\ /_/\_\ /_/\_\|___| \___||_| \_|  |_|  """)
        print(Fore.YELLOW + """
      >>> PROXY-ONLY DIRECT-TO-MX DELIVERY SYSTEM - STATUS: ARMED <<<
      [RFC-2822] [DKIM-SIGNED] [SOCKS5-CHAIN] [ZERO-SMTP-RELAY]
      VERSION 4.0.0 | BUILD 2024-05-20 | SCORPION PROTOCOL
        """)
        print(Fore.CYAN + "1. SMTP (from smtp.txt)")
        print(Fore.CYAN + "2. API (aws.sys, brevo.sys, etc.)")
        print(Fore.CYAN + "3. Direct MX (Port 25)")
        print(Fore.YELLOW + "4. Settings / Configuration Dashboard")
        print(Fore.YELLOW + "5. Run Connectivity & Proxy Diagnostic")
        print(Fore.RED + "6. Exit")

        mode = input(Fore.WHITE + "\nSelect mode (1-6): ").strip()

        if mode == '4':
            show_settings_dashboard(app_config, direct_mx_options)
            continue
        elif mode == '5':
            proxies = load_files(os.path.join(os.path.dirname(__file__), 'proxies.txt'))
            validate_proxies(proxies)
            check_direct_mx_connectivity(proxies[0] if proxies else None)
            input(Fore.WHITE + "\nDiagnostic complete. Press Enter to return to menu...")
            continue
        elif mode == '6':
            sys.exit(0)
        elif mode in ['1', '2', '3']:
            break
        else:
            print(Fore.RED + "Invalid selection!")
            time.sleep(1)

    configs = []
    if mode == '1':
        import re
        for l in load_files(os.path.join(os.path.dirname(__file__), 'smtp.txt')):
            p = l.split('|')
            if len(p) >= 4:
                port_match = re.search(r'\d+', p[1])
                port = int(port_match.group()) if port_match else 587
                cfg = {'host': p[0].strip(), 'port': port, 'user': p[2].strip(), 'pass': p[3].strip()}
                if len(p) >= 5:
                    cfg['from_email'] = p[4].strip()
                configs.append(cfg)
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

    if not configs: print("No configurations found!"); return

    proxies = load_files(os.path.join(os.path.dirname(__file__), 'proxies.txt'))
    if proxies:
        proxies = validate_proxies(proxies)
        if not proxies and mode == '3':
            print(Fore.RED + "[!] No live proxies found for Direct MX!")
            return

    if mode != '3':
        check_proxy = proxies[0] if proxies else None
        configs = check_smtp_configs(configs, check_proxy)
    if not configs: print("No live configurations!"); return

    email_list = load_files(os.path.join(os.path.dirname(__file__), 'list.txt'))
    stats['total'] = len(email_list)
    subjects = load_files(os.path.join(os.path.dirname(__file__), 'subjects.txt'))
    letters = [os.path.join(os.path.dirname(__file__), 'letters', f) for f in os.listdir(os.path.join(os.path.dirname(__file__), 'letters')) if f.endswith('.html')]
    links = load_files(os.path.join(os.path.dirname(__file__), 'links.txt'))
    from_emails = load_files(os.path.join(os.path.dirname(__file__), 'from_emails.txt'))


    if mode == '3':
        check_direct_mx_connectivity(proxies[0] if proxies else None)

    print(Fore.CYAN + "\nAttachment Settings:")
    send_att = input(Fore.WHITE + "Send Attachment this session? (y/n): ").lower() == 'y'
    att_type = app_config.get('attachmentType', 'PDF')
    if send_att:
        print("  1. PDF")
        print("  2. Image")
        print("  3. SVG")
        choice = input("Select Attachment Format (1-3): ")
        att_type = 'PDF' if choice == '1' else ('Image' if choice == '2' else 'SVG')

    app_config['sendAttachment'] = send_att
    app_config['attachmentType'] = att_type

    with Live(update_ui(), refresh_per_second=4) as live:
        from_idx = 0
        stats['dns_verified'] = direct_mx_options.get('verifyDns', False)
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
                domain_parts = email.split('@')[1].split('.')
                repls = {
                    'email': email,
                    'emailuser': email.split('@')[0],
                    'emaildomain': email.split('@')[1],
                    'emaildomainname': domain_parts[0] if domain_parts else ''
                }
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

                # Attachment Auto-Convert
                if app_config.get('sendAttachment'):
                    attachment_html_path = os.path.join(os.path.dirname(__file__), 'attachment.html')
                    if os.path.exists(attachment_html_path):
                        stats['status'] = f"Generating {app_config.get('attachmentType')}"
                        live.update(update_ui())
                        with open(attachment_html_path, 'r', encoding='utf-8') as f:
                            att_html = replace_tags(f.read(), repls)

                        att_type = app_config.get('attachmentType', 'PDF')
                        if att_type == 'Image':
                            if Html2Image:
                                hti = Html2Image(output_path=os.path.dirname(__file__))
                                hti.screenshot(html_str=att_html, save_as='temp_att.png')
                                with open(os.path.join(os.path.dirname(__file__), 'temp_att.png'), 'rb') as f:
                                    atts.append({'filename': 'attachment.png', 'content': f.read()})
                                os.remove(os.path.join(os.path.dirname(__file__), 'temp_att.png'))
                        elif att_type == 'SVG':
                            svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000"><foreignObject width="100%" height="100%"><div xmlns="http://www.w3.org/1999/xhtml">{att_html}</div></foreignObject></svg>'
                            atts.append({'filename': 'attachment.svg', 'content': svg_content.encode('utf-8')})
                        else: # PDF
                            if Html2Image:
                                hti = Html2Image(output_path=os.path.dirname(__file__))
                                hti.screenshot(html_str=att_html, save_as='temp_att.png')
                                from PIL import Image
                                img = Image.open(os.path.join(os.path.dirname(__file__), 'temp_att.png'))
                                pdf_buffer = io.BytesIO()
                                img.save(pdf_buffer, format='PDF')
                                atts.append({'filename': 'attachment.pdf', 'content': pdf_buffer.getvalue()})
                                os.remove(os.path.join(os.path.dirname(__file__), 'temp_att.png'))

                stats['status'] = 'Sending'
                live.update(update_ui())

                conf = configs[idx % len(configs)].copy()
                if from_emails:
                    conf['from_email'] = replace_tags(from_emails[from_idx % len(from_emails)], repls)
                    from_idx += 1

                proxy = proxies[idx % len(proxies)] if proxies else None
                stats['current_proxy'] = proxy if proxy else 'None'
                send_email(conf, email, content, subject, atts, dkim_options, {**app_config, 'proxy': proxy, 'directMxOptions': direct_mx_options})
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
            await asyncio.sleep(app_config.get('delayBetweenEmails', 2000) / 1000)

if __name__ == "__main__":
    asyncio.run(main())
