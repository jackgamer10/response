import re
import requests
from urllib.parse import urlparse, urljoin
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# Suppress insecure request warnings for cleaner output
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

console = Console()

# Statistics Globals
stats = {
    "urls_scanned": 0,
    "keys_found": 0,
    "errors": 0,
    "start_time": time.time(),
    "current_url": "Idle",
    "found_services": set()
}
stats_lock = threading.Lock()

# Expanded SMS API Patterns for better accuracy
PATTERNS = {
    "Twilio": [
        r"(AC[a-f0-9]{32})",  # Account SID
        r"(SK[a-f0-9]{32})",  # API Key SID
        r"twilio_account_sid\s*[:=]\s*['\"](AC[a-f0-9]{32})['\"]",
        r"twilio_auth_token\s*[:=]\s*['\"]([a-f0-9]{32})['\"]",
    ],
    "Textbelt": [
        r"(textbelt\.com/text)",
        r"['\"]textbelt_api_key['\"]\s*[:=]\s*['\"]([a-zA-Z0-9]+)['\"]",
    ],
    "AWS SNS": [
        r"(AKIA[0-9A-Z]{16})",  # Access Key ID
        r"secret_key\s*[:=]\s*['\"]([a-zA-Z0-9+/]{40})['\"]",
        r"(arn:aws:sns:[\w-]+:\d+:[\w-]+)",
    ],
    "Nexmo/Vonage": [
        r"api\.vonage\.com",
        r"rest\.nexmo\.com",
        r"nexmo_api_key\s*[:=]\s*['\"]([a-z0-9]{8})['\"]",
        r"nexmo_api_secret\s*[:=]\s*['\"]([a-zA-Z0-9]{16})['\"]",
    ],
    "Plivo": [
        r"api\.plivo\.com",
        r"auth_id\s*[:=]\s*['\"]([A-Z0-9]{20})['\"]",
        r"auth_token\s*[:=]\s*['\"]([a-zA-Z0-9]{40})['\"]",
    ],
    "MessageBird": [
        r"messagebird\.com/api",
        r"access_key\s*[:=]\s*['\"]([a-zA-Z0-9]{25})['\"]",
    ],
    "Infobip": [
        r"api\.infobip\.com",
        r"api_key\s*[:=]\s*['\"]([a-zA-Z0-9]{32,})['\"]",
    ],
    "Sinch": [
        r"sinch_app_key\s*[:=]\s*['\"]([a-f0-9-]{36})['\"]",
        r"sinch_app_secret\s*[:=]\s*['\"]([a-zA-Z0-9+/]{44})['\"]",
    ],
    "ClickSend": [
        r"clicksend_api_key\s*[:=]\s*['\"]([A-F0-9-]{36})['\"]",
        r"clicksend_username\s*[:=]\s*['\"]([^'\"]+)['\"]",
    ],
    "Generic API Key": [
        r"['\"](?:api_key|sms_key|secret|token)['\"]\s*[:=]\s*['\"]([a-zA-Z0-9-_]{20,})['\"]",
    ]
}

SENSITIVE_FILES = [
    ".env", "config.php", "settings.py", "app.js", "web.config",
    "firebase-config.json", "package.json", "composer.json",
    ".git/config", "config/database.php", "src/config.js"
]

def load_proxies(proxy_file="proxies.txt"):
    try:
        with open(proxy_file, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []

def scan_text(text):
    found = {}
    for service, regexes in PATTERNS.items():
        matches = []
        for regex in regexes:
            matches.extend(re.findall(regex, text, re.IGNORECASE))
        if matches:
            found[service] = list(set(matches))
            with stats_lock:
                stats["keys_found"] += len(found[service])
                stats["found_services"].add(service)
    return found

def merge_results(base, new):
    """Deep merge two result dictionaries where values are lists."""
    for key, val in new.items():
        if key in base:
            base[key] = list(set(base[key] + val))
        else:
            base[key] = val
    return base

def get_session(proxies=None):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    })
    if proxies:
        proxy = random.choice(proxies)
        session.proxies = {"http": proxy, "https": proxy}
    return session

def scan_url_worker(url, proxies=None, deep_scan=True, fuzzing=True):
    with stats_lock:
        stats["current_url"] = url
        stats["urls_scanned"] += 1

    results = {}
    try:
        session = get_session(proxies)
        response = session.get(url, timeout=10, verify=False)
        content = response.text

        results = scan_text(content)

        # Advanced Feature: Scan common sensitive files
        if deep_scan:
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}/"
            for s_file in SENSITIVE_FILES:
                try:
                    s_url = urljoin(base, s_file)
                    s_resp = session.get(s_url, timeout=5, verify=False)
                    if s_resp.status_code == 200:
                        results = merge_results(results, scan_text(s_resp.text))
                except:
                    pass

        # Advanced Feature: Fuzzing discovery
        if fuzzing:
            soup = BeautifulSoup(content, 'html.parser')
            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action')
                if action:
                    f_url = urljoin(url, action)
                    try:
                        f_resp = session.get(f_url, params={"debug": "true", "test": "1"}, timeout=5, verify=False)
                        results = merge_results(results, scan_text(f_resp.text))
                    except:
                        pass

        return url, results
    except Exception as e:
        with stats_lock:
            stats["errors"] += 1
        return url, {"Error": [str(e)]}

def generate_dashboard():
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )

    # Header Panel
    elapsed = int(time.time() - stats["start_time"])
    header_panel = Panel(
        f"[bold blue]MagxxicVOT SMS API Scanner[/bold blue] | Elapsed: {elapsed}s | Active Services: {len(stats['found_services'])}",
        box=box.ROUNDED, style="cyan"
    )
    layout["header"].update(header_panel)

    # Main Stats Table
    table = Table(expand=True, box=box.SIMPLE)
    table.add_column("Metric", style="magenta")
    table.add_column("Value", style="green")

    table.add_row("URLs Scanned", str(stats["urls_scanned"]))
    table.add_row("Keys Found", f"[bold red]{stats['keys_found']}[/bold red]")
    table.add_row("Errors encountered", str(stats["errors"]))
    table.add_row("Current Target", stats["current_url"][:50] + "..." if len(stats["current_url"]) > 50 else stats["current_url"])
    table.add_row("Found Services", ", ".join(list(stats["found_services"])[:5]))

    layout["main"].update(Panel(table, title="Live Statistics", border_style="blue"))

    # Footer
    footer_panel = Panel("[dim]Press Ctrl+C to terminate the scan safely[/dim]", box=box.ROUNDED, style="white")
    layout["footer"].update(footer_panel)

    return layout

def main():
    console.clear()
    console.print(Panel.fit("[bold cyan]MagxxicVOT SMS API Scanner v2.1[/bold cyan]\n[dim]Initializing advanced security scanner...[/dim]", border_style="cyan"))

    # Load targets from targets.txt or use defaults
    try:
        with open("targets.txt", "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        targets = ["http://example.com", "https://www.iana.org"]

    proxies = load_proxies()

    with Live(generate_dashboard(), refresh_per_second=4) as live:
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(scan_url_worker, url, proxies): url for url in targets}

            for future in as_completed(future_to_url):
                url, results = future.result()
                if results and not "Error" in results:
                    with open("found_keys.log", "a") as f:
                        f.write(f"--- {url} ---\n{str(results)}\n")
                live.update(generate_dashboard())

    console.print("\n[bold green]Scan Completed.[/bold green]")
    console.print(f"Total Keys Found: [bold yellow]{stats['keys_found']}[/bold yellow]")
    console.print("Check [cyan]found_keys.log[/cyan] for detailed results.")

if __name__ == "__main__":
    main()
