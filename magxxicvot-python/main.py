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
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from xhtml2pdf import pisa
from html2image import HtmlToImage
from htmlmin import minify

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
    "encrypt_attachment": False,
    "encryption_password": "MaghxSecurePassword",
    "sign_attachment": True,
    "minify_html": True,
    "use_custom_from": True,
    "retry_attempts": 3
}

stats = {"sent": 0, "success": 0, "failed": 0, "current_proxy": "None"}

def get_hwid():
    import uuid
    hwid_info = f"{socket.gethostname()}-{sys.platform}-{uuid.getnode()}"
    return hashlib.sha256(hwid_info.encode()).hexdigest()[:16].upper()

def deobfuscate(s):
    try:
        return base64.b64decode(s[::-1].encode()).decode()
    except:
        return ""

def obfuscate(s):
    return base64.b64encode(s.encode()).decode()[::-1]

def check_activation():
    hwid = get_hwid()
    activation_file = "activation.sys"
    expected_token = hashlib.sha256((hwid + "MAGXXICVOT-SALT").encode()).hexdigest()[:16].upper()

    if os.path.exists(activation_file):
        with open(activation_file, "r") as f:
            token = deobfuscate(f.read().strip())
            if token == expected_token:
                console.print(Panel(f"[green]✔ License activated successfully.[/green]", box=box.ROUNDED, style="bold green"))
                return

    console.print(Panel(f"[bold yellow]Your HWID:[/bold yellow] [cyan]{hwid}[/cyan]", box=box.DOUBLE, title="Activation Required", style="bold magenta"))
    entered_token = console.input("[bold magenta]Please enter your activation token: [/bold magenta]").strip().upper()

    if entered_token == expected_token:
        console.print("[green]✔ Token validated. Activating...[/green]")
        with open(activation_file, "w") as f:
            f.write(obfuscate(entered_token))
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(activation_file, 0x02)
    else:
        console.print("[bold red]✘ Error: Invalid activation token. Please contact the administrator.[/bold red]")
        sys.exit(1)

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
    console.print(Panel("[bold cyan]MagxxicVOT XII Python Edition v1.1[/bold cyan]\n[blue]Military-Grade MIME & Proxy Rotation\nAdvanced Content & Attachment Shield[/blue]", box=box.ROUNDED, style="bold blue"))

def generate_barcode(data):
    try:
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(data, writer=ImageWriter())
        fp = BytesIO()
        ean.write(fp)
        return base64.b64encode(fp.getvalue()).decode()
    except Exception as e:
        return ""

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
        tag = f"[-barcode-{data}-]"
        new_text = new_text.replace(tag, f'<img src="data:image/png;base64,{b64}" alt="Barcode">')
    return new_text

def encrypt_attachment(data, password):
    key = hashlib.scrypt(password.encode(), salt=b'salt', n=16384, r=8, p=1, dklen=32)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - (len(data) % 16)
    padded_data = data + bytes([pad_len] * pad_len)
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted

def get_stats_table():
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True, border_style="cyan")
    table.add_column("Metric", style="bold yellow")
    table.add_column("Value", style="bold white", justify="right")
    table.add_row("Total Sent", f"[bold yellow]{stats['sent']}[/bold yellow]")
    table.add_row("Success ✅", f"[bold green]{stats['success']}[/bold green]")
    table.add_row("Failed ❌", f"[bold red]{stats['failed']}[/bold red]")
    table.add_row("Proxy 🌐", f"[bold blue]{stats['current_proxy']}[/bold blue]")
    status_panel = Panel(table, title="[bold magenta]MagxxicVOT XII Live Dashboard[/bold magenta]", subtitle="[blue]Status: Mailing in progress...[/blue]", border_style="cyan")
    return status_panel

def load_list(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def load_smtp(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            configs = []
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    configs.append({
                        "host": parts[0], "port": int(parts[1]), "user": parts[2], "pass": parts[3], "from": parts[4] if len(parts) > 4 else parts[2]
                    })
            return configs
    return []

def validate_proxies(proxies):
    console.print(f"[yellow]Validating {len(proxies)} proxies...[/yellow]")
    valid = []
    for proxy in proxies:
        try:
            proxy_parts = re.split(r'[:@/]+', proxy)
            test_conn = socks.create_connection(("www.google.com", 80), proxy_type=socks.SOCKS5, proxy_addr=proxy_parts[-2], proxy_port=int(proxy_parts[-1]), timeout=5)
            test_conn.close()
            valid.append(proxy)
            console.print(f"[green]✔ Proxy {proxy} OK.[/green]")
        except:
            console.print(f"[red]✘ Proxy {proxy} FAILED.[/red]")
    return valid

def html_to_pdf(html_content):
    result = BytesIO()
    pisa.CreatePDF(html_content, dest=result)
    return result.getvalue()

def html_to_png(html_content):
    hti = HtmlToImage()
    temp_html, out_png = "temp_att.html", "temp_att.png"
    with open(temp_html, "w", encoding="utf-8") as f: f.write(html_content)
    hti.screenshot(html_file=temp_html, save_as=out_png)
    with open(out_png, "rb") as f: data = f.read()
    if os.path.exists(temp_html): os.remove(temp_html)
    if os.path.exists(out_png): os.remove(out_png)
    return data

def send_emails():
    emails = load_list(CONFIG["email_list_path"])
    subjects = load_list(CONFIG["subjects_path"])
    links = load_list(CONFIG["links_path"])
    smtps = load_smtp(CONFIG["smtp_path"])
    letters = [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")]
    proxies = load_list(CONFIG["proxies_path"])

    if CONFIG["use_proxy"] and CONFIG["auto_validate_proxies"] and proxies:
        proxies = validate_proxies(proxies)
    if not smtps:
        console.print("[bold red]✘ No SMTP configurations found.[/bold red]")
        return

    smtp_idx, subject_idx, link_idx, letter_idx, proxy_idx = 0, 0, 0, 0, 0

    with Live(get_stats_table(), refresh_per_second=4) as live:
        for email in emails:
            attempts = 0
            sent = False

            while attempts < CONFIG["retry_attempts"] and not sent:
                try:
                    smtp_cfg = smtps[smtp_idx]
                    current_proxy = proxies[proxy_idx] if CONFIG["use_proxy"] and proxies else None
                    stats["current_proxy"] = current_proxy or "Direct"
                    live.update(get_stats_table())

                    subject_raw = subjects[subject_idx] if subjects else "Security Update"
                    link = links[link_idx] if links else ""
                    letter_file = os.path.join(CONFIG["letters_dir"], letters[letter_idx]) if letters else None

                    replacements = {"-email-": email, "-emailuser-": email.split("@")[0], "-emaildomain-": email.split("@")[1], "-emaildomainname-": email.split("@")[1].split(".")[0], "-link-": link}

                    msg = MIMEMultipart()
                    msg["Subject"] = replace_tags(subject_raw, replacements)
                    from_email = CONFIG["use_custom_from"] and smtp_cfg["from"] or smtp_cfg["user"]
                    msg["From"] = f'"{replace_tags(CONFIG["sender_name"], replacements)}" <{from_email}>'
                    msg["To"] = email
                    msg["X-Mailer"], msg["X-Priority"], msg["Importance"], msg["X-MSMail-Priority"], msg["X-Originating-IP"] = "Microsoft Outlook 16.0", "1 (Highest)", "High", "High", "127.0.0.1"

                    content = "Default Content"
                    if letter_file:
                        with open(letter_file, "r", encoding="utf-8") as f: content = f.read()
                    msg.attach(MIMEText(replace_tags(content, replacements), "html"))

                    if CONFIG["attachment_type"] != "none":
                        with open(CONFIG["attachment_html_path"], "r", encoding="utf-8") as f: att_html = replace_tags(f.read(), replacements)
                        if CONFIG["minify_html"]: att_html = minify(att_html, remove_comments=True)
                        filename = f"Document_{random.randint(1000,9999)}"
                        if CONFIG["attachment_type"] == "pdf":
                            att_data, ext, c_type = html_to_pdf(att_html), ".pdf", "application/pdf"
                        elif CONFIG["attachment_type"] == "png":
                            att_data, ext, c_type = html_to_png(att_html), ".png", "image/png"
                        else:
                            att_data, ext, c_type = att_html.encode(), ".html", "text/html"
                        if CONFIG["encrypt_attachment"]:
                            att_data, ext = encrypt_attachment(att_data, CONFIG["encryption_password"]), ext + ".enc"
                        part = MIMEBase(*c_type.split("/"))
                        part.set_payload(att_data)
                        encoders.encode_base64(part)
                        part.add_header("Content-Disposition", f'attachment; filename="{filename}{ext}"')
                        msg.attach(part)
                        if CONFIG["sign_attachment"]:
                            sig = hashlib.sha256(att_data).hexdigest()
                            part_sig = MIMEBase("text", "plain")
                            part_sig.set_payload(sig.encode())
                            part_sig.add_header("Content-Disposition", f'attachment; filename="{filename}{ext}.sig"')
                            msg.attach(part_sig)

                    def get_proxy_conn():
                        if current_proxy:
                            parts = re.split(r'[:@/]+', current_proxy)
                            return socks.create_connection((smtp_cfg["host"], smtp_cfg["port"]), proxy_type=socks.SOCKS5, proxy_addr=parts[-2], proxy_port=int(parts[-1]), timeout=30)
                        return socket.create_connection((smtp_cfg["host"], smtp_cfg["port"]), timeout=30)

                    conn = get_proxy_conn()
                    server = smtplib.SMTP(timeout=30)
                    server.sock, server._host = conn, smtp_cfg["host"]
                    server.ehlo_or_helo_if_needed()
                    if server.has_extn('starttls'):
                        server.starttls()
                        server.ehlo_or_helo_if_needed()
                    server.login(smtp_cfg["user"], smtp_cfg["pass"])
                    server.send_message(msg)
                    server.quit()
                    stats["sent"], stats["success"], sent = stats["sent"] + 1, stats["success"] + 1, True
                except:
                    attempts += 1
                    if attempts >= CONFIG["retry_attempts"]:
                        stats["sent"], stats["failed"] = stats["sent"] + 1, stats["failed"] + 1
                    else:
                        smtp_idx = (smtp_idx + 1) % len(smtps)
                        if proxies: proxy_idx = (proxy_idx + 1) % len(proxies)
                        time.sleep(2)

            smtp_idx = (smtp_idx + 1) % len(smtps)
            if subjects: subject_idx = (subject_idx + 1) % len(subjects)
            if links: link_idx = (link_idx + 1) % len(links)
            if letters: letter_idx = (letter_idx + 1) % len(letters)
            if proxies: proxy_idx = (proxy_idx + 1) % len(proxies)
            time.sleep(CONFIG["delay"])

def run():
    check_activation()
    print_banner()
    console.print(Panel("[bold magenta]Settings Dashboard[/bold magenta]", box=box.SQUARE, style="bold cyan"))
    CONFIG["use_custom_from"] = console.input("[bold blue]Use Custom From Email? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["use_proxy"] = console.input("[bold blue]Use SOCKS Proxy? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["attachment_type"] = console.input("[bold blue]Attachment Type (pdf/png/html/none): [/bold blue]").lower()
    if CONFIG["attachment_type"] != "none":
        CONFIG["encrypt_attachment"] = console.input("[bold blue]Encrypt Attachment? (y/n): [/bold blue]").lower() == 'y'
        CONFIG["sign_attachment"] = console.input("[bold blue]Sign Attachment? (y/n): [/bold blue]").lower() == 'y'
    console.print("\n[bold green]✔ Starting campaign with selected settings...[/bold green]\n")
    time.sleep(2)
    if not os.path.exists(CONFIG["letters_dir"]): os.makedirs(CONFIG["letters_dir"])
    send_emails()

if __name__ == "__main__":
    run()
