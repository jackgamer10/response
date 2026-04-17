import imaplib
import email
import re
import os
import sys
import uuid
import socket
import hashlib
from email.header import decode_header
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.prompt import Prompt, Confirm
    from rich.table import Table

console = Console()

SALT = "MAGXXICVOT-XII-SALT"

class LicenseManager:
    def __init__(self):
        self.activation_file = "activation.sys"

    def get_hwid(self):
        try:
            hostname = socket.gethostname()
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            hwid_string = f"{hostname}{mac}{SALT}"
            return hashlib.sha256(hwid_string.encode()).hexdigest()[:16].upper()
        except:
            return "UNKNOWN-HWID-0000"

    def verify_token(self, hwid, token):
        # Activation logic: Base64 reverse obfuscation
        import base64
        try:
            expected = base64.b64encode(hwid[::-1].encode()).decode().replace('=', '')[:16].upper()
            return token == expected
        except:
            return False

    def is_activated(self):
        if not os.path.exists(self.activation_file):
            return False
        try:
            with open(self.activation_file, 'r') as f:
                token = f.read().strip()
                return self.verify_token(self.get_hwid(), token)
        except:
            return False

    def save_activation(self, token):
        try:
            with open(self.activation_file, 'w') as f:
                f.write(token)
            return True
        except:
            return False

    def run_activation_loop(self):
        if self.is_activated():
            return True

        hwid = self.get_hwid()
        console.print(Panel(
            f"[white]Your HWID:[/white] [bold cyan]{hwid}[/bold cyan]\n"
            f"[italic yellow]Please provide your HWID to the administrator to receive your activation token.[/italic yellow]",
            title="[bold red]MagxxicVOT XII - Activation Required[/bold red]",
            border_style="red"
        ))

        while True:
            token = Prompt.ask("[bold yellow]Enter Activation Token[/bold yellow]").strip()
            if self.verify_token(hwid, token):
                if self.save_activation(token):
                    console.print("[bold green]✓ Activation Successful! Restarting application...[/bold green]")
                    return True
                else:
                    console.print("[bold red]Error: Could not save activation file.[/bold red]")
            else:
                console.print("[bold red]Invalid Token. Please try again.[/bold red]")
                if not Confirm.ask("[yellow]Retry?[/yellow]", default=True):
                    sys.exit(0)

BANNER = r"""
[bold cyan]
  __  __                                  _____   _______
 |  \/  |                                |  __ \ |__   __|
 | \  / |  __ _   __ _ __  __ __  __  __ | |  | |   | |
 | |\/| | / _` | / _` |\ \/ / \ \/ / |  || |  | |   | |
 | |  | || (_| || (_| | >  <   >  <  |  || |__| |   | |
 |_|  |_| \__,_| \__, |/_/\_\ /_/\_\ |__||_____/    |_|
                  __/ |
                 |___/
[/bold cyan]
[bold white]MagxxicVOT XII - Email Contact Fetcher v1.0[/bold white]
[italic blue]Professional Email Intelligence & Extraction Tool[/italic blue]
"""

def get_imap_server(email_address):
    domain = email_address.split('@')[-1]
    # Common IMAP servers
    common_servers = {
        'gmail.com': 'imap.gmail.com',
        'outlook.com': 'outlook.office365.com',
        'hotmail.com': 'outlook.office365.com',
        'live.com': 'outlook.office365.com',
        'yahoo.com': 'imap.mail.yahoo.com',
        'icloud.com': 'imap.mail.me.com',
        'ionos.com': 'imap.ionos.com',
        'ionos.co.uk': 'imap.ionos.co.uk',
        'gmx.com': 'imap.gmx.com',
        'mail.com': 'imap.mail.com',
        'zoho.com': 'imap.zoho.com',
        'aol.com': 'imap.aol.com'
    }
    return common_servers.get(domain.lower(), f"imap.{domain}")

def extract_emails_from_text(text):
    if not text:
        return set()
    # Improved regex for email extraction supporting subdomains and complex TLDs
    return set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z0-9-]', text))

def parse_folder_line(line):
    # IMAP list returns something like '(\\HasNoChildren) "/" "INBOX"'
    # or '() "/" INBOX'
    pattern = re.compile(r'\((?P<flags>.*?)\)\s+"(?P<delimiter>.*?)"\s+"?(?P<name>.*?)"?$')
    match = pattern.match(line.decode())
    if match:
        return match.group('name')

    # Fallback for simpler formats
    try:
        parts = line.decode().split(' ')
        return parts[-1].strip().strip('"')
    except:
        return line.decode()

def fetch_contacts():
    console.print(BANNER)

    email_user = Prompt.ask("[bold yellow]Enter Email Address[/bold yellow]")
    password = Prompt.ask("[bold yellow]Enter Password[/bold yellow]", password=True)

    suggested_imap = get_imap_server(email_user)
    console.print(f"[blue]Auto-detected IMAP Server:[/blue] [cyan]{suggested_imap}[/cyan]")

    use_suggested = Confirm.ask(f"Use [cyan]{suggested_imap}[/cyan]?", default=True)

    if use_suggested:
        imap_server = suggested_imap
    else:
        imap_server = Prompt.ask("[bold yellow]Enter IMAP Server[/bold yellow]")

    imap_port = Prompt.ask("[bold yellow]Enter IMAP Port[/bold yellow]", default="993")

    try:
        console.print(f"\n[bold yellow]Attempting connection to {imap_server}...[/bold yellow]")
        mail = imaplib.IMAP4_SSL(imap_server, int(imap_port))
        mail.login(email_user, password)
        console.print("[bold green]✓ Authentication Successful![/bold green]\n")

        contacts = set()

        status, folder_list = mail.list()
        if status != 'OK':
            console.print("[red]Error: Could not retrieve folder list.[/red]")
            return

        all_folders = sorted(list(set([parse_folder_line(f) for f in folder_list])))

        console.print("[bold cyan]Available Folders:[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Folder Name")

        for i, folder in enumerate(all_folders):
            table.add_row(str(i+1), folder)

        console.print(table)

        selection = Prompt.ask(
            "\n[bold yellow]Select folders to scan[/bold yellow] (IDs separated by comma, e.g., 1,2,5 or 'all')",
            default="all"
        )

        if selection.lower() == 'all':
            folders_to_scan = all_folders
        else:
            try:
                indices = [int(i.strip()) - 1 for i in selection.split(',')]
                folders_to_scan = [all_folders[i] for i in indices if 0 <= i < len(all_folders)]
            except:
                console.print("[red]Invalid selection. Scanning all folders as default.[/red]")
                folders_to_scan = all_folders

        if not folders_to_scan:
            console.print("[red]No folders selected. Exiting.[/red]")
            return

        console.print(f"\n[blue]Selected Folders:[/blue] [cyan]{', '.join(folders_to_scan)}[/cyan]\n")

        with Progress() as progress:
            folder_task = progress.add_task("[cyan]Scanning folders...", total=len(folders_to_scan))

            for folder in folders_to_scan:
                try:
                    # Some folders might need quotes if they have spaces
                    select_name = f'"{folder}"' if ' ' in folder else folder
                    status, _ = mail.select(select_name, readonly=True)
                    if status != 'OK':
                        continue

                    status, messages = mail.search(None, 'ALL')
                    if status != 'OK':
                        continue

                    msg_ids = messages[0].split()
                    msg_count = len(msg_ids)

                    # To ensure performance, we scan the most recent emails first
                    # User can select scan depth
                    limit = 1000
                    target_ids = msg_ids[-limit:]

                    msg_task = progress.add_task(f"  [white]Processing {folder}...", total=len(target_ids))

                    for msg_id in target_ids:
                        try:
                            # Fetch headers only to be fast
                            status, msg_data = mail.fetch(msg_id, '(BODY[HEADER.FIELDS (FROM TO CC)])')
                            for response_part in msg_data:
                                if isinstance(response_part, tuple):
                                    msg = email.message_from_bytes(response_part[1])
                                    for header in ['From', 'To', 'Cc']:
                                        val = msg.get(header)
                                        if val:
                                            # Decode header if encoded
                                            decoded_parts = decode_header(val)
                                            decoded_val = ""
                                            for part, encoding in decoded_parts:
                                                if isinstance(part, bytes):
                                                    decoded_val += part.decode(encoding or 'utf-8', errors='ignore')
                                                else:
                                                    decoded_val += str(part)
                                            contacts.update(extract_emails_from_text(decoded_val))
                        except:
                            continue
                        progress.update(msg_task, advance=1)

                    progress.remove_task(msg_task)
                    progress.update(folder_task, advance=1)
                except Exception as e:
                    console.print(f"[red]Error scanning {folder}: {e}[/red]")

        # Remove the user's own email from the list
        contacts.discard(email_user.lower())
        # Basic cleanup: remove invalid/system emails if needed
        contacts = {c.lower() for c in contacts if len(c) > 5 and '.' in c.split('@')[-1]}

        if contacts:
            if not os.path.exists('exports'):
                os.makedirs('exports')

            safe_email = re.sub(r'[^a-zA-Z0-9]', '_', email_user)
            filename = f"exports/contacts_{safe_email}.txt"

            with open(filename, "w") as f:
                for contact in sorted(contacts):
                    f.write(contact + "\n")

            console.print("\n" + Panel(
                f"[bold green]Extraction Complete![/bold green]\n\n"
                f"[white]Total Unique Contacts:[/white] [bold cyan]{len(contacts)}[/bold cyan]\n"
                f"[white]Saved to:[/white] [bold yellow]{filename}[/bold yellow]",
                title="Success",
                border_style="green"
            ))
        else:
            console.print("\n[bold red]No contacts were found in the scanned folders.[/bold red]")

        mail.logout()
    except imaplib.IMAP4.error as e:
        console.print(f"\n[bold red]IMAP Error:[/bold red] {e}")
        console.print("[yellow]Hint: Check if 'Less Secure Apps' is enabled or use an App Password if using Gmail/Outlook.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")

if __name__ == "__main__":
    try:
        lm = LicenseManager()
        if lm.run_activation_loop():
            fetch_contacts()
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")
        sys.exit(0)
