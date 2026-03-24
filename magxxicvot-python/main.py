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
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box
import socks
from urllib.parse import urlparse

# Initialize Console
console = Console()

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
    "delay": 6.0,
    "use_proxy": True,
    "auto_validate_proxies": True,
    "attachment_type": "pdf",
    "pdf_name": "Document",
    "encrypt_attachment": False,
    "encryption_password": "MaghxSecurePassword",
    "sign_attachment": True,
    "minify_html": True,
    "use_custom_from": True,
    "retry_attempts": 3,
    "pause_every": 100,
    "pause_time": 300, # 5 minutes in seconds
    "test_email": "serverbank@aol.com",
    "test_every": 100
}

stats = {"sent": 0, "success": 0, "failed": 0, "current_proxy": "None"}

def get_hwid():
    import uuid
    hwid_info = f"{socket.gethostname()}-{sys.platform}-{uuid.getnode()}"
    return hashlib.sha256(hwid_info.encode()).hexdigest()[:16].upper()

def deobfuscate(s):
    try: return base64.b64decode(s[::-1].encode()).decode()
    except: return ""

def obfuscate(s): return base64.b64encode(s.encode()).decode()[::-1]

def check_activation():
    hwid, activation_file = get_hwid(), "activation.sys"
    expected = hashlib.sha256((hwid + "MAGXXICVOT-SALT").encode()).hexdigest()[:16].upper()
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
    console.print(Panel("[bold cyan]MagxxicVOT XII Python Edition v1.2[/bold cyan]\n[blue]Military-Grade MIME & Proxy Rotation\nAdvanced Content & Attachment Shield[/blue]", box=box.ROUNDED, style="bold blue"))

def generate_barcode(data):
    try:
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        fp = BytesIO()
        ean.write(fp)
        return base64.b64encode(fp.getvalue()).decode()
    except: return ""

def replace_tags(text, replacements):
    new_text = text
    new_text = new_text.replace("[-email-]", replacements.get("-email-", ""))
    new_text = new_text.replace("[-emailuser-]", replacements.get("-emailuser-", ""))
    new_text = new_text.replace("[-emaildomain-]", replacements.get("-emaildomain-", ""))
    new_text = new_text.replace("[-emaildomainname-]", replacements.get("-emaildomainname-", ""))
    new_text = new_text.replace("[-link-]", replacements.get("-link-", ""))
    new_text = re.sub(r'\[-randomstring-\]', lambda _: ''.join(random.choices(string.ascii_letters + string.digits, k=10)), new_text)
    new_text = re.sub(r'\[-randomnumber-\]', lambda _: str(random.randint(1000, 9999)), new_text)
    new_text = re.sub(r'\[-randomletters-\]', lambda _: ''.join(random.choices(string.ascii_letters, k=10)), new_text)
    new_text = re.sub(r'\[-randommd5-\]', lambda _: hashlib.md5(os.urandom(16)).hexdigest(), new_text)
    new_text = re.sub(r'\[-time-\]', lambda _: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), new_text)
    domain = replacements.get("-emaildomain-") or (replacements.get("-email-", "").split("@")[-1] if "@" in replacements.get("-email-", "") else "")
    logo_url = f"https://logo.clearbit.com/{domain}" if domain else ""
    new_text = new_text.replace("[-recipient-logo-]", f'<img src="{logo_url}" alt="Logo" style="max-height: 50px;">')
    matches = re.findall(r'\[-barcode-(.*?)-\]', new_text)
    for data in matches:
        b64 = generate_barcode(data)
        new_text = new_text.replace(f"[-barcode-{data}-]", f'<img src="data:image/png;base64,{b64}" alt="Barcode">')
    return new_text

def encrypt_attachment(data, password):
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        key = hashlib.scrypt(password.encode(), salt=b'salt', n=16384, r=8, p=1, dklen=32)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        pad_len = 16 - (len(data) % 16)
        padded_data = data + bytes([pad_len] * pad_len)
        return iv + encryptor.update(padded_data) + encryptor.finalize()
    except ImportError:
        console.print("[bold red]✘ Error: 'cryptography' module not found. Please run setup.bat.[/bold red]")
        return data

def get_stats_table():
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True, border_style="cyan")
    table.add_column("Metric", style="bold yellow")
    table.add_column("Value", style="bold white", justify="right")
    table.add_row("Total Sent", f"[bold yellow]{stats['sent']}[/bold yellow]")
    table.add_row("Success ✅", f"[bold green]{stats['success']}[/bold green]")
    table.add_row("Failed ❌", f"[bold red]{stats['failed']}[/bold red]")
    table.add_row("Proxy 🌐", f"[bold blue]{stats['current_proxy']}[/bold blue]")
    return Panel(table, title="[bold magenta]MagxxicVOT XII Live Dashboard[/bold magenta]", subtitle="[blue]Status: Mailing in progress...[/blue]", border_style="cyan")

def load_list(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: return [line.strip() for line in f if line.strip()]
    return []

def load_smtp(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            configs = []
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    configs.append({"host": parts[0], "port": int(parts[1]), "user": parts[2], "pass": parts[3], "from": parts[4] if len(parts) > 4 else parts[2]})
            return configs
    return []

def parse_proxy(proxy_str):
    if not proxy_str.startswith("socks"): proxy_str = "socks5://" + proxy_str
    parsed = urlparse(proxy_str)
    return {
        "addr": parsed.hostname,
        "port": parsed.port,
        "user": parsed.username,
        "pass": parsed.password,
        "type": socks.SOCKS5 if "socks5" in parsed.scheme else socks.SOCKS4
    }

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

def html_to_pdf(html_content):
    try:
        from xhtml2pdf import pisa
        result = BytesIO()
        pisa.CreatePDF(html_content, dest=result)
        return result.getvalue()
    except ImportError:
        console.print("[bold red]✘ Error: 'xhtml2pdf' module not found. Please run setup.bat.[/bold red]")
        return html_content.encode()

def html_to_png(html_content):
    try:
        from html2image import HtmlToImage
        hti = HtmlToImage()
        temp_html, out_png = "temp_att.html", "temp_att.png"
        with open(temp_html, "w", encoding="utf-8") as f: f.write(html_content)
        hti.screenshot(html_file=temp_html, save_as=out_png)
        with open(out_png, "rb") as f: data = f.read()
        if os.path.exists(temp_html): os.remove(temp_html)
        if os.path.exists(out_png): os.remove(out_png)
        return data
    except ImportError:
        console.print("[bold red]✘ Error: 'html2image' module not found. Please run setup.bat.[/bold red]")
        return html_content.encode()

def send_emails():
    emails, subjects, links = load_list(CONFIG["email_list_path"]), load_list(CONFIG["subjects_path"]), load_list(CONFIG["links_path"])
    smtps, letters, proxies = load_smtp(CONFIG["smtp_path"]), [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")], load_list(CONFIG["proxies_path"])
    if CONFIG["use_proxy"] and CONFIG["auto_validate_proxies"] and proxies: proxies = validate_proxies(proxies)
    if not smtps: console.print("[bold red]✘ No SMTP configurations found.[/bold red]"); return
    smtp_idx, subject_idx, link_idx, letter_idx, proxy_idx, success_since_test = 0, 0, 0, 0, 0, 0
    with Live(get_stats_table(), refresh_per_second=4) as live:
        for email in emails:
            attempts, sent = 0, False
            while attempts < CONFIG["retry_attempts"] and not sent:
                try:
                    smtp_cfg = smtps[smtp_idx]
                    current_proxy = proxies[proxy_idx] if CONFIG["use_proxy"] and proxies else None
                    stats["current_proxy"] = current_proxy or "Direct"; live.update(get_stats_table())
                    replacements = {"-email-": email, "-emailuser-": email.split("@")[0], "-emaildomain-": email.split("@")[1], "-emaildomainname-": email.split("@")[1].split(".")[0], "-link-": links[link_idx] if links else ""}
                    msg = MIMEMultipart()
                    msg["Subject"] = replace_tags(subjects[subject_idx] if subjects else "Security Update", replacements)
                    msg["From"] = f'"{replace_tags(CONFIG["sender_name"], replacements)}" <{CONFIG["use_custom_from"] and smtp_cfg["from"] or smtp_cfg["user"]}>'
                    msg["To"] = email
                    msg["X-Mailer"], msg["X-Priority"], msg["Importance"], msg["X-MSMail-Priority"], msg["X-Originating-IP"] = "Microsoft Outlook 16.0", "1 (Highest)", "High", "High", "127.0.0.1"
                    content = "Default Content"
                    if letters:
                        with open(os.path.join(CONFIG["letters_dir"], letters[letter_idx]), "r", encoding="utf-8") as f: content = f.read()
                    msg.attach(MIMEText(replace_tags(content, replacements), "html"))
                    if CONFIG["attachment_type"] != "none":
                        with open(CONFIG["attachment_html_path"], "r", encoding="utf-8") as f: att_html = replace_tags(f.read(), replacements)
                        try:
                            from htmlmin import minify
                            if CONFIG["minify_html"]: att_html = minify(att_html, remove_comments=True)
                        except ImportError: pass
                        filename = replace_tags(CONFIG["pdf_name"], replacements)
                        if CONFIG["attachment_type"] == "pdf": att_data, ext, c_type = html_to_pdf(att_html), ".pdf", "application/pdf"
                        elif CONFIG["attachment_type"] == "png": att_data, ext, c_type = html_to_png(att_html), ".png", "image/png"
                        else: att_data, ext, c_type = att_html.encode(), ".html", "text/html"
                        if CONFIG["encrypt_attachment"]: att_data, ext = encrypt_attachment(att_data, CONFIG["encryption_password"]), ext + ".enc"
                        part = MIMEBase(*c_type.split("/")); part.set_payload(att_data); encoders.encode_base64(part); part.add_header("Content-Disposition", f'attachment; filename="{filename}{ext}"'); msg.attach(part)
                        if CONFIG["sign_attachment"]: sig = hashlib.sha256(att_data).hexdigest(); part_sig = MIMEBase("text", "plain"); part_sig.set_payload(sig.encode()); part_sig.add_header("Content-Disposition", f'attachment; filename="{filename}{ext}.sig"'); msg.attach(part_sig)

                    def get_conn():
                        if current_proxy:
                            p = parse_proxy(current_proxy)
                            return socks.create_connection((smtp_cfg["host"], smtp_cfg["port"]), proxy_type=p["type"], proxy_addr=p["addr"], proxy_port=p["port"], proxy_username=p["user"], proxy_password=p["pass"], timeout=30)
                        return socket.create_connection((smtp_cfg["host"], smtp_cfg["port"]), timeout=30)

                    conn = get_conn(); server = smtplib.SMTP(timeout=30); server.sock, server._host = conn, smtp_cfg["host"]
                    server.ehlo_or_helo_if_needed()
                    if server.has_extn('starttls'): server.starttls(); server.ehlo_or_helo_if_needed()
                    server.login(smtp_cfg["user"], smtp_cfg["pass"]); server.send_message(msg); server.quit()
                    stats["sent"], stats["success"], sent, success_since_test = stats["sent"] + 1, stats["success"] + 1, True, success_since_test + 1
                    if success_since_test >= CONFIG["test_every"]:
                        try:
                            test_msg = MIMEMultipart(); test_msg["Subject"], test_msg["From"], test_msg["To"] = f"[TEST] {msg['Subject']}", msg["From"], CONFIG["test_email"]
                            for part in msg.get_payload(): test_msg.attach(part)
                            s = smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=30); s.starttls(); s.login(smtp_cfg["user"], smtp_cfg["pass"]); s.send_message(test_msg); s.quit()
                        except: pass
                        success_since_test = 0
                except:
                    attempts += 1
                    if attempts >= CONFIG["retry_attempts"]: stats["sent"], stats["failed"] = stats["sent"] + 1, stats["failed"] + 1
                    else: smtp_idx = (smtp_idx + 1) % len(smtps); proxy_idx = (proxy_idx + 1) % len(proxies) if proxies else 0; time.sleep(2)
            if stats["success"] > 0 and stats["success"] % CONFIG["pause_every"] == 0:
                console.print(f"\n[bold magenta][PAUSE][/bold magenta] Reached {stats['success']} successful sends. Pausing for {CONFIG['pause_time']}s..."); time.sleep(CONFIG["pause_time"])
            smtp_idx = (smtp_idx + 1) % len(smtps); proxy_idx = (proxy_idx + 1) % len(proxies) if proxies else 0; subject_idx = (subject_idx + 1) % len(subjects) if subjects else 0; link_idx = (link_idx + 1) % len(links) if links else 0; letter_idx = (letter_idx + 1) % len(letters) if letters else 0; time.sleep(CONFIG["delay"])

def run():
    check_activation(); print_banner()
    console.print(Panel("[bold magenta]Settings Dashboard[/bold magenta]", box=box.SQUARE, style="bold cyan"))
    CONFIG["use_custom_from"] = console.input("[bold blue]Use Custom From Email? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["use_proxy"] = console.input("[bold blue]Use SOCKS Proxy? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["attachment_type"] = console.input("[bold blue]Attachment Type (pdf/png/html/none): [/bold blue]").lower()
    if CONFIG["attachment_type"] != "none":
        CONFIG["pdf_name"] = console.input("[bold blue]Desired Attachment Filename (tags supported, e.g. [-emaildomainname-]_Report): [/bold blue]") or "Document"
    CONFIG["delay"] = float(console.input("[bold blue]Delay between emails (seconds): [/bold blue]") or 6.0)
    CONFIG["pause_every"] = int(console.input("[bold blue]Pause every X successful sends: [/bold blue]") or 100)
    CONFIG["pause_time"] = int(console.input("[bold blue]Pause time (seconds): [/bold blue]") or 300)
    CONFIG["test_every"] = int(console.input("[bold blue]Send test email every X successful sends: [/bold blue]") or 100)
    CONFIG["test_email"] = console.input("[bold blue]Test email address: [/bold blue]") or "serverbank@aol.com"
    if CONFIG["attachment_type"] != "none":
        CONFIG["encrypt_attachment"] = console.input("[bold blue]Encrypt Attachment? (y/n): [/bold blue]").lower() == 'y'
        CONFIG["sign_attachment"] = console.input("[bold blue]Sign Attachment? (y/n): [/bold blue]").lower() == 'y'
    console.print("\n[bold green]✔ Starting campaign with selected settings...[/bold green]\n"); time.sleep(2)
    if not os.path.exists(CONFIG["letters_dir"]): os.makedirs(CONFIG["letters_dir"])
    send_emails()

if __name__ == "__main__": run()
