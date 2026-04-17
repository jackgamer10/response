import imaplib
import email
import re
import os
import sys
from email.header import decode_header
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.prompt import Prompt, Confirm

console = Console()

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
    # Improved regex for email extraction
    return set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-]*[a-zA-Z0-9-]', text))

def clean_folder_name(folder_data):
    # IMAP list returns something like '(\\HasNoChildren) "/" "INBOX"'
    try:
        parts = folder_data.decode().split(' "/" ')
        if len(parts) > 1:
            return parts[-1].strip().strip('"')
        return folder_data.decode().split()[-1].strip().strip('"')
    except:
        return str(folder_data)

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

        all_folders = [clean_folder_name(f) for f in folder_list]

        # Priority folders to scan
        priority_folders = ['INBOX', 'Sent', 'Sent Items', 'Sent Messages', 'Drafts', 'Junk', 'Spam']
        folders_to_scan = [f for f in all_folders if f in priority_folders or any(p.lower() in f.lower() for p in priority_folders)]

        # If no common folders found, just use INBOX or all
        if not folders_to_scan:
            folders_to_scan = ['INBOX'] if 'INBOX' in all_folders else all_folders[:5]

        console.print(f"[blue]Targeting Folders:[/blue] [cyan]{', '.join(folders_to_scan)}[/cyan]\n")

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

                    # To avoid hanging on massive mailboxes, we can limit or just go through them
                    # For this tool, we'll scan up to 500 latest emails per folder
                    limit = 500
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
        fetch_contacts()
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")
        sys.exit(0)
