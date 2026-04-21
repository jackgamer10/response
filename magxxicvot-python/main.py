import os
import sys
import time
import base64
import hashlib
import random
import string
import smtplib
import socket
import ssl
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import requests
from io import BytesIO
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box
import socks
from urllib.parse import urlparse
import mimetypes

# Initialize Console
console = Console()

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Configuration (Defaults)
CONFIG = {
    "sender_name": "IONOS Customer Service",
    "letters_dir": "letters",
    "subjects_path": "subject.txt",
    "links_path": "links.txt",
    "proxies_path": "proxies.txt",
    "email_list_path": "list.txt",
    "smtp_path": "smtp.txt",
    "attachment_html_path": "attachment.html",
    "delay": 1.0,
    "use_proxy": True,
    "auto_validate_proxies": True,
    "attachment_type": "pdf",
    "attachment_source": "convert",
    "attachment_pick_path": "",
    "pdf_name": "Document",
    "encrypt_attachment": False,
    "encryption_password": "MaghxSecurePassword",
    "sign_attachment": True,
    "minify_html": True,
    "use_custom_from": True,
    "retry_attempts": 3,
    "pause_every": 100,
    "pause_time": 300,
    "test_email": "serverbank@aol.com",
    "test_every": 100,
    "hide_my_ip": True,
    "unique_url": True,
    "base_url": "",
    "send_barcode_in_letter": True,
    "send_barcode_in_attachment": True,
    "stealth_from_name": True,
    "auto_translate": True
}

TLD_LANG_MAP = {
    'fr': 'fr', 'de': 'de', 'cn': 'zh-CN', 'in': 'hi', 'id': 'id',
    'pk': 'ur', 'br': 'pt', 'ru': 'ru', 'jp': 'ja', 'mx': 'es',
    'it': 'it', 'es': 'es', 'nl': 'nl', 'tr': 'tr'
}

def translate_text(text, target_lang):
    if not text or not target_lang or target_lang == 'en': return text
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={requests.utils.quote(text)}"
        res = requests.get(url, timeout=10)
        return "".join([part[0] for part in res.json()[0]])
    except: return text

def translate_html(html, target_lang):
    if not html or not target_lang or target_lang == 'en': return html
    try:
        parts = re.split(r'(<[^>]+>)', html)
        for i in range(len(parts)):
            if not parts[i].startswith('<') and parts[i].strip():
                parts[i] = translate_text(parts[i], target_lang)
        return "".join(parts)
    except: return html

stats = {"sent": 0, "success": 0, "failed": 0, "current_proxy": "None"}

def get_hwid():
    import uuid
    try:
        import psutil
        mac = "00:00:00:00:00:00"
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK and addr.address != "00:00:00:00:00:00":
                    mac = addr.address; break
            if mac != "00:00:00:00:00:00": break
    except:
        mac = hex(uuid.getnode())[2:].upper()

    hwid_info = f"{socket.gethostname()}-{mac.upper()}"
    return hashlib.sha256(hwid_info.encode()).hexdigest()[:16].upper()

def deobfuscate(s):
    try: return base64.b64decode(s[::-1].encode()).decode()
    except: return ""

def obfuscate(s): return base64.b64encode(s.encode()).decode()[::-1]

def decode_smart(s):
    if not s: return ""
    if s.startswith("base64:"): return base64.b64decode(s[7:]).decode("utf-8")
    if s.startswith("hex:"): return bytes.fromhex(s[4:]).decode("utf-8")
    return s

def inject_stealth(text):
    if not text: return ""
    inv_chars = ['\u200B', '\u200C', '\u200D', '\uFEFF']
    res = ""
    for char in text:
        res += char
        if random.random() > 0.7:
            res += random.choice(inv_chars)
    return res

def check_activation():
    hwid, activation_file = get_hwid(), "activation.sys"
    expected = hashlib.sha256((hwid + "MAGXXICVOT-XII-SALT").encode()).hexdigest()[:16].upper()
    if os.path.exists(activation_file):
        with open(activation_file, "r") as f:
            if deobfuscate(f.read().strip()) == expected:
                console.print(Panel(f"[green]✔ License activated successfully.[/green]", box=box.ROUNDED, style="bold green"))
                return
    console.print(Panel(f"[bold yellow]Your HWID:[/bold yellow] [cyan]{hwid}[/cyan]", box=box.DOUBLE, title="Activation Required", style="bold magenta"))
    entered = console.input("[bold magenta]Please enter your activation token: [/bold magenta]").strip().upper()
    if entered == expected:
        console.print("[green]✔ Token validated. Activating...[/green]")
        with open(activation_file, "w") as f: f.write(obfuscate(entered))
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(activation_file, 0x02)
    else:
        console.print("[bold red]✘ Error: Invalid activation token. Please contact the administrator.[/bold red]"); sys.exit(1)

def print_banner():
    banner = """
███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗██╗   ██╗ ██████╗ ████████╗  ██╗  ██╗██╗██╗
████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝██║██╔════╝██║   ██║██╔═══██╗╚══██╔══╝  ╚██╗██╔╝██║██║
██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝ ██║██║     ██║   ██║██║   ██║   ██║      ╚███╔╝ ██║██║
██║╚██╔╝██║██╔══██║██║   ██║██╔══██║ ██╔██╗ ██║██║     ╚██╗ ██╔╝██║   ██║   ██║      ██╔██╗ ██║██║
██║ ╚═╝ ██║██║  ██║╚██████╔╝██║  ██║██╔╝ ██╗██║╚██████╗ ╚████╔╝ ╚██████╔╝   ██║     ██╔╝ ██╗██║██║
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝  ╚═══╝   ╚═════╝    ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝
"""
    console.print(banner, style="bold magenta")
    console.print(Panel("[bold cyan]MagxxicVOT XII Python Edition v4.6[/bold cyan]\n[blue]Ultra Speed & Multi-Language Edition[/blue]", box=box.ROUNDED, style="bold blue"))

def analyze_spam():
    console.print("\n[bold yellow]--- Campaign Spam Analysis ---[/bold yellow]")
    score = 0.0
    suggestions = []

    try:
        letters = [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")]
        if not letters:
            console.print("[red]No letters found. Skipping analysis.[/red]")
            return
        with open(os.path.join(CONFIG["letters_dir"], letters[0]), "r", encoding="utf-8") as f:
            html = f.read()

        keywords = ['free', 'money', 'urgent', 'winner', 'account', 'security', 'suspended', 'verify', 'click here']
        for word in keywords:
            if re.search(rf'\b{word}\b', html, re.IGNORECASE):
                score += 1.5
                suggestions.append(f"High-risk word found: '{word}'. Consider alternatives.")

        if '<img' in html and len(html) < 1000:
            score += 2.0
            suggestions.append("Low text-to-image ratio. Add more legitimate text to the body.")

        if 'javascript:' in html:
            score += 3.0
            suggestions.append("Avoid JavaScript in HTML letters; it triggers aggressive filters.")

        subjects = [l.strip() for l in open(CONFIG["subjects_path"]).readlines() if l.strip()]
        if subjects and any(s.isupper() for s in subjects):
            score += 1.0
            suggestions.append("ALL CAPS subject lines are often flagged as spam.")

        color = "green" if score <= 5 else "red"
        console.print(f"[cyan]Calculated Spam Score:[/cyan] [{color}]{score}[/{color}] [white]/ 10[/white]")

        if suggestions:
            console.print("[yellow]Improvement Suggestions:[/yellow]")
            for s in suggestions:
                console.print(f" - {s}")
        else:
            console.print("[green]Letter looks clean! Ready for high inboxing.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to analyze spam: {e}[/red]")
    console.print("-" * 30 + "\n")

def generate_barcode(data):
    try:
        import barcode
        from barcode.writer import ImageWriter
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        fp = BytesIO()
        ean.write(fp)
        return base64.b64encode(fp.getvalue()).decode()
    except: return ""

def replace_tags(text, replacements, is_attachment=False):
    new_text = text
    email = replacements.get("-email-", "")
    user = replacements.get("-emailuser-") or (email.split("@")[0] if "@" in email else "")
    domain = replacements.get("-emaildomain-") or (email.split("@")[1] if "@" in email else "")
    domainname = replacements.get("-emaildomainname-") or (domain.split(".")[0] if "." in domain else domain)

    tag_map = {
        r'\[-email-\]': email, r'\[email\]': email,
        r'\[-emailuser-\]': user, r'\[user\]': user,
        r'\[-emaildomain-\]': domain, r'\[domain\]': domain,
        r'\[-emaildomainname-\]': domainname, r'\[domainname\]': domainname,
        r'\[-time-\]': datetime.now().strftime("%H:%M:%S"), r'\[time\]': datetime.now().strftime("%H:%M:%S"),
        r'\[-date-\]': datetime.now().strftime("%Y-%m-%d"), r'\[date\]': datetime.now().strftime("%Y-%m-%d"),
        r'\[-randomnumber-\]': lambda: str(random.randint(1000, 9999)),
        r'\[randomnumber\]': lambda: str(random.randint(1000, 9999)),
        r'\[-randomstring-\]': lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
        r'\[randomstring\]': lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
        r'\[-randomhex-\]': lambda: os.urandom(4).hex(),
        r'\[randomhex\]': lambda: os.urandom(4).hex(),
        r'\[-randommd5-\]': lambda: hashlib.md5(os.urandom(8)).hexdigest(),
        r'\[-randomletters-\]': lambda: ''.join(random.choices(string.ascii_letters, k=8))
    }

    for tag, val in tag_map.items():
        if callable(val):
            new_text = re.sub(tag, lambda _: val(), new_text)
        else:
            new_text = re.sub(tag, val, new_text)

    # Unique URL generation
    final_link = replacements.get("-link-", "")
    if CONFIG["unique_url"] and CONFIG["base_url"]:
        sep = "&" if "?" in CONFIG["base_url"] else "?"
        final_link = f"{CONFIG['base_url']}{sep}v={''.join(random.choices(string.ascii_letters + string.digits, k=12))}"
    new_text = new_text.replace("[-link-]", final_link).replace("[link]", final_link)

    # Dynamic Logo
    logo_url = f"https://logo.clearbit.com/{domain}" if domain else ""
    new_text = new_text.replace("[-recipient-logo-]", f'<img src="{logo_url}" alt="Logo" style="max-height: 50px;">')
    new_text = new_text.replace("[recipient-logo]", f'<img src="{logo_url}" alt="Logo" style="max-height: 50px;">')

    def barcode_replace(match):
        should_replace = CONFIG["send_barcode_in_attachment"] if is_attachment else CONFIG["send_barcode_in_letter"]
        if should_replace:
            data = match.group(1)
            b64 = generate_barcode(data)
            return f'<img src="data:image/png;base64,{b64}" alt="Barcode">'
        return ""

    new_text = re.sub(r'\[-barcode-(.*?)-\]', barcode_replace, new_text)
    return new_text

def encrypt_attachment(data, password):
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        salt = os.urandom(16)
        key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        pad_len = 16 - (len(data) % 16)
        padded_data = data + bytes([pad_len] * pad_len)
        return salt + iv + encryptor.update(padded_data) + encryptor.finalize()
    except: return data

def get_stats_table():
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True, border_style="cyan")
    table.add_column("Metric", style="bold yellow")
    table.add_column("Value", style="bold white", justify="right")
    table.add_row("Total Attempts", f"[bold yellow]{stats['sent']}[/bold yellow]")
    table.add_row("Success ✅", f"[bold green]{stats['success']}[/bold green]")
    table.add_row("Failed ❌", f"[bold red]{stats['failed']}[/bold red]")
    table.add_row("Proxy 🌐", f"[bold blue]{stats['current_proxy']}[/bold blue]")
    return Panel(table, title="[bold magenta]MAGXXICVOT XII LIVE DASHBOARD[/bold magenta]", subtitle="[blue]Status: Fast Mailing...[/blue]", border_style="cyan")

def parse_proxy(proxy_str):
    if not proxy_str.startswith("socks"): proxy_str = "socks5://" + proxy_str
    parsed = urlparse(proxy_str)
    return { "addr": parsed.hostname, "port": parsed.port, "user": parsed.username, "pass": parsed.password, "type": socks.SOCKS5 if "socks5" in parsed.scheme else socks.SOCKS4 }

def validate_proxies(proxies):
    console.print(f"[yellow]Validating {len(proxies)} proxies...[/yellow]")
    valid = []
    for proxy in proxies:
        try:
            p = parse_proxy(proxy)
            conn = socks.create_connection(("www.google.com", 80), proxy_type=p["type"], proxy_addr=p["addr"], proxy_port=p["port"], proxy_username=p["user"], proxy_password=p["pass"], timeout=5)
            conn.close(); valid.append(proxy)
            console.print(f"[green]✔ Proxy {proxy} OK.[/green]")
        except: console.print(f"[red]✘ Proxy {proxy} FAILED.[/red]")
    return valid

def validate_email(email):
    return bool(re.match(r'^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$', email))

def html_to_pdf(html_content):
    try:
        from xhtml2pdf import pisa
        result = BytesIO()
        pisa.CreatePDF(html_content, dest=result)
        return result.getvalue()
    except: return html_content.encode()

def html_to_png(html_content):
    try:
        from html2image import HtmlToImage
        hti = HtmlToImage()
        temp_h, out_p = "temp_att.html", "temp_att.png"
        with open(temp_h, "w", encoding="utf-8") as f: f.write(html_content)
        hti.screenshot(html_file=temp_h, save_as=out_p)
        with open(out_p, "rb") as f: data = f.read()
        for f in [temp_h, out_p]:
            if os.path.exists(f): os.remove(f)
        return data
    except: return html_content.encode()

def html_to_svg(html_content):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000"><foreignObject width="100%" height="100%"><div xmlns="http://www.w3.org/1999/xhtml">{html_content}</div></foreignObject></svg>'
    return svg.encode()

def send_single_email(target_email, smtp, proxy, reps, letter_path, subject_line):
    msg = MIMEMultipart()

    letter_html = open(letter_path, "r", encoding="utf-8").read()
    final_subject = subject_line

    if CONFIG["auto_translate"]:
        tld = target_email.split('.')[-1].lower()
        target_lang = TLD_LANG_MAP.get(tld)
        if target_lang:
            letter_html = translate_html(letter_html, target_lang)
            final_subject = translate_text(final_subject, target_lang)

    msg["Subject"] = replace_tags(final_subject, reps, False)

    sender_name = replace_tags(CONFIG["sender_name"], reps, False)
    if CONFIG["stealth_from_name"]:
        sender_name = inject_stealth(sender_name)

    msg["From"] = f'"{sender_name}" <{CONFIG["use_custom_from"] and smtp["from"] or smtp["user"]}>'
    msg["To"] = target_email

    msg["X-Mailer"] = "Microsoft Outlook 16.0"
    msg["X-Priority"] = "1 (Highest)"
    msg["Importance"] = "High"
    msg["X-MSMail-Priority"] = "High"
    msg["User-Agent"] = random.choice(USER_AGENTS)

    if CONFIG["hide_my_ip"]:
        msg["X-Originating-IP"] = "127.0.0.1"
        msg["X-Forwarded-For"] = "127.0.0.1"
        msg["X-Real-IP"] = "127.0.0.1"
        msg["X-Remote-IP"] = "127.0.0.1"
        msg["X-Client-IP"] = "127.0.0.1"

    msg.attach(MIMEText(replace_tags(letter_html, reps, False), "html"))

    if CONFIG["attachment_type"] != "none":
        if CONFIG["attachment_source"] == "convert":
            att_html = replace_tags(open(CONFIG["attachment_html_path"]).read(), reps, True)
            try:
                import minify_html
                if CONFIG["minify_html"]:
                    att_html = minify_html.minify(att_html, minify_js=True, remove_processing_instructions=True, ensure_spec_compliant_unquoted_attribute_values=True, keep_comments=False)
            except: pass

            att_name = replace_tags(CONFIG["pdf_name"], reps, True)
            if CONFIG["attachment_type"] == "pdf": data, ext, ctype = html_to_pdf(att_html), ".pdf", "application/pdf"
            elif CONFIG["attachment_type"] == "png": data, ext, ctype = html_to_png(att_html), ".png", "image/png"
            elif CONFIG["attachment_type"] == "svg": data, ext, ctype = html_to_svg(att_html), ".svg", "image/svg+xml"
            else: data, ext, ctype = att_html.encode(), ".html", "text/html"
            filename = f"{att_name}{ext}"
        else:
            with open(CONFIG["attachment_pick_path"], "rb") as f: data = f.read()
            ext = os.path.splitext(CONFIG["attachment_pick_path"])[1]
            ctype = mimetypes.guess_type(CONFIG["attachment_pick_path"])[0] or "application/octet-stream"
            att_name = replace_tags(CONFIG["pdf_name"], reps, True)
            filename = f"{att_name}{ext}"

        if CONFIG["encrypt_attachment"]: data = encrypt_attachment(data, CONFIG["encryption_password"]); filename += ".enc"

        part = MIMEBase(*ctype.split("/")); part.set_payload(data); encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

        if CONFIG["sign_attachment"]:
            sig = hashlib.sha256(data).hexdigest()
            part_sig = MIMEBase("text", "plain"); part_sig.set_payload(sig.encode())
            part_sig.add_header("Content-Disposition", f'attachment; filename="{filename}.sig"')
            msg.attach(part_sig)

    def get_conn():
        if proxy:
            p = parse_proxy(proxy)
            s = socks.socksocket()
            s.set_proxy(p["type"], p["addr"], p["port"], username=p["user"], password=p["pass"])
            s.settimeout(30)
            s.connect((smtp["host"], smtp["port"]))
            return s
        return socket.create_connection((smtp["host"], smtp["port"]), timeout=30)

    conn = get_conn()
    server = smtplib.SMTP(timeout=30, local_hostname=smtp['ehlo'])
    server.sock = conn
    server.file = conn.makefile('rb')
    server.helo_or_helo_if_needed()
    if server.has_extn('starttls'):
        server.starttls()
        server.helo_or_helo_if_needed()
    server.login(smtp["user"], smtp["pass"])
    server.send_message(msg)
    server.quit()

def send_emails():
    try:
        emails = [l.strip() for l in open(CONFIG["email_list_path"]).readlines() if l.strip()]
        links = [l.strip() for l in open(CONFIG["links_path"]).readlines() if l.strip()]
        subjects = [l.strip() for l in open(CONFIG["subjects_path"]).readlines() if l.strip()]
        smtps = []
        for line in open(CONFIG["smtp_path"]).readlines():
            parts = line.strip().split("|")
            if len(parts) >= 4:
                from_email = decode_smart(parts[4] if len(parts) > 4 else parts[2])
                user = decode_smart(parts[2])
                passw = decode_smart(parts[3])
                ehlo = parts[5] if len(parts) > 5 else (from_email.split('@')[1] if '@' in from_email else 'localhost')
                smtps.append({"host": parts[0], "port": int(parts[1]), "user": user, "pass": passw, "from": from_email, "ehlo": ehlo})
        letters = [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")]
        proxies = [l.strip() for l in open(CONFIG["proxies_path"]).readlines() if l.strip()]

        if not emails or not smtps or not letters:
            console.print("[bold red]✘ Fatal Error: Missing email list, SMTPs, or letters.[/bold red]")
            return

        if CONFIG["use_proxy"] and CONFIG["auto_validate_proxies"] and proxies: proxies = validate_proxies(proxies)
        smtp_idx, link_idx, let_idx, prx_idx, sub_idx, test_count = 0, 0, 0, 0, 0, 0

        with Live(get_stats_table(), refresh_per_second=4) as live:
            for email in emails:
                stats["sent"] += 1
                if not validate_email(email):
                    stats["failed"] += 1; live.update(get_stats_table()); continue

                attempts, sent = 0, False
                while attempts < CONFIG["retry_attempts"] and not sent:
                    try:
                        smtp, proxy = smtps[smtp_idx], proxies[prx_idx] if CONFIG["use_proxy"] and proxies else None
                        stats["current_proxy"] = proxy or "Direct"; live.update(get_stats_table())
                        reps = {"-email-": email}
                        letter_path = os.path.join(CONFIG["letters_dir"], letters[let_idx])
                        current_subject = subjects[sub_idx] if subjects else "Notification"

                        send_single_email(email, smtp, proxy, reps, letter_path, current_subject)

                        stats["success"] += 1; sent = True; test_count += 1
                        if test_count >= CONFIG["test_every"]:
                            try:
                                send_single_email(CONFIG["test_email"], smtp, proxy, reps, letter_path, current_subject)
                            except: pass
                            test_count = 0
                    except Exception:
                        attempts += 1
                        if attempts >= CONFIG["retry_attempts"]: stats["failed"] += 1
                        else: smtp_idx = (smtp_idx + 1) % len(smtps); prx_idx = (prx_idx + 1) % (len(proxies) or 1); time.sleep(1)
                    live.update(get_stats_table())

                if stats["success"] > 0 and stats["success"] % CONFIG["pause_every"] == 0: time.sleep(CONFIG["pause_time"])
                smtp_idx, prx_idx, link_idx, let_idx, sub_idx = (smtp_idx + 1) % len(smtps), (prx_idx + 1) % (len(proxies) or 1), (link_idx + 1) % len(links), (let_idx + 1) % len(letters), (sub_idx + 1) % len(subjects)
                time.sleep(CONFIG["delay"])
    except Exception as e:
        console.print(f"[bold red]✘ Fatal Error: {e}[/bold red]")

def run():
    check_activation(); print_banner()
    analyze_spam()
    console.print(Panel("[bold magenta]Settings Dashboard[/bold magenta]", box=box.SQUARE, style="bold cyan"))
    CONFIG["use_custom_from"] = console.input("[bold blue]Use Custom From Email? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["use_proxy"] = console.input("[bold blue]Use SOCKS Proxy? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["hide_my_ip"] = console.input("[bold blue]Enable Hide My IP (Header Masking)? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["stealth_from_name"] = console.input("[bold blue]Enable Stealth From Name (Invisible Chars)? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["auto_translate"] = console.input("[bold blue]Enable Auto Language Translation (Geo-TLD)? (y/n): [/bold blue]").lower() == 'y'

    CONFIG["unique_url"] = console.input("[bold blue]Enable Unique URL per Recipient? (y/n): [/bold blue]").lower() == 'y'
    if CONFIG["unique_url"]:
        CONFIG["base_url"] = console.input("[bold blue]Base URL for Unique Generation: [/bold blue]")

    has_att = console.input("[bold blue]Include Attachment? (y/n): [/bold blue]").lower() == 'y'
    if has_att:
        source = console.input("[bold blue]Attachment Source (1: Convert HTML, 2: Pick Existing File): [/bold blue]")
        if source == "2":
            CONFIG["attachment_source"] = "pick"
            CONFIG["attachment_pick_path"] = console.input("[bold blue]Path to File: [/bold blue]")
        else:
            CONFIG["attachment_source"] = "convert"
            CONFIG["attachment_type"] = console.input("[bold blue]Convert to (pdf/png/svg/html): [/bold blue]").lower()

        CONFIG["pdf_name"] = console.input("[bold blue]Unique Filename (tags OK): [/bold blue]") or "Document"
        CONFIG["encrypt_attachment"] = console.input("[bold blue]Encrypt Attachment? (y/n): [/bold blue]").lower() == 'y'
        CONFIG["sign_attachment"] = console.input("[bold blue]Sign Attachment? (y/n): [/bold blue]").lower() == 'y'
        CONFIG["send_barcode_in_attachment"] = console.input("[bold blue]Send Barcode in Attachment? (y/n): [/bold blue]").lower() == 'y'
    else:
        CONFIG["attachment_type"] = "none"

    CONFIG["send_barcode_in_letter"] = console.input("[bold blue]Send Barcode in Letter Body? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["delay"] = float(console.input("[bold blue]Delay (seconds): [/bold blue]") or 1.0)
    CONFIG["test_every"] = int(console.input("[bold blue]Test Email Every X: [/bold blue]") or 100)
    CONFIG["test_email"] = console.input("[bold blue]Test Email Address: [/bold blue]") or "serverbank@aol.com"

    run_smtp_test = console.input("[bold yellow]Run Multiple SMTP Connectivity Test? (y/n): [/bold yellow]").lower() == 'y'
    if run_smtp_test:
        try:
            smtps = []
            for line in open(CONFIG["smtp_path"]).readlines():
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    from_email = decode_smart(parts[4] if len(parts) > 4 else parts[2])
                    user = decode_smart(parts[2])
                    passw = decode_smart(parts[3])
                    ehlo = parts[5] if len(parts) > 5 else (from_email.split('@')[1] if '@' in from_email else 'localhost')
                    smtps.append({"host": parts[0], "port": int(parts[1]), "user": user, "pass": passw, "from": from_email, "ehlo": ehlo})
            if not smtps: raise Exception("smtp.txt is empty.")
            console.print(f"\n[yellow]Testing {len(smtps)} SMTPs...[/yellow]")
            for i, smtp in enumerate(smtps):
                try:
                    letters = [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")]
                    if not letters: raise Exception("letters/ is empty.")
                    reps = {"-email-": CONFIG["test_email"]}
                    send_single_email(CONFIG["test_email"], smtp, None, reps, os.path.join(CONFIG["letters_dir"], letters[0]), "SMTP Verification [randomnumber] [date]")
                    console.print(f"[bold green][OK] SMTP {i+1}: {smtp['host']} - Sent.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red][FAIL] SMTP {i+1}: {smtp['host']} - {e}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]SMTP Test failed: {e}[/bold red]")

    run_test = console.input("[bold yellow]Run a Setup Test Send before Campaign? (y/n): [/bold yellow]").lower() == 'y'
    if run_test:
        console.print(f"\n[yellow]Sending test email with full setup...[/yellow]")
        try:
            smtps = []
            for line in open(CONFIG["smtp_path"]).readlines():
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    from_email = decode_smart(parts[4] if len(parts) > 4 else parts[2])
                    user = decode_smart(parts[2])
                    passw = decode_smart(parts[3])
                    ehlo = parts[5] if len(parts) > 5 else (from_email.split('@')[1] if '@' in from_email else 'localhost')
                    smtps.append({"host": parts[0], "port": int(parts[1]), "user": user, "pass": passw, "from": from_email, "ehlo": ehlo})
            letters = [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")]
            links = [l.strip() for l in open(CONFIG["links_path"]).readlines() if l.strip()]
            if not smtps or not letters: raise Exception("Missing SMTP or Letter.")
            reps = {"-email-": CONFIG["test_email"]}
            send_single_email(CONFIG["test_email"], smtps[0], None, reps, os.path.join(CONFIG["letters_dir"], letters[0]), "Final Verification [randomnumber] [date]")
            console.print("[bold green]Test email sent successfully! Check your inbox.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Test email failed: {e}[/bold red]")

    start_mailing = console.input("[bold magenta]Start Campaign now? (y/n): [/bold magenta]").lower() == 'y'
    if start_mailing:
        console.print("\n[bold green]✔ Starting Ultra Speed campaign...[/bold green]\n")
        time.sleep(1)
        send_emails()
    else:
        console.print("[bold blue]Exiting. Have a great day![/bold blue]")

if __name__ == "__main__": run()
