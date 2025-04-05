import tkinter as tk
from tkinter import filedialog, messagebox
import zipfile
from bs4 import BeautifulSoup
from lxml import etree
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import simpleSplit, ImageReader
import io
from PIL import Image

def get_spine_order(epub_path):
    with zipfile.ZipFile(epub_path, 'r') as z:
        opf_path = [f for f in z.namelist() if f.endswith('.opf')][0]
        opf_data = z.read(opf_path)
        tree = etree.fromstring(opf_data)

        ns = {'opf': 'http://www.idpf.org/2007/opf'}
        manifest = {item.get('id'): item.get('href') for item in tree.xpath('//opf:manifest/opf:item', namespaces=ns)}
        spine_ids = [item.get('idref') for item in tree.xpath('//opf:spine/opf:itemref', namespaces=ns)]
        base_path = opf_path.rsplit('/', 1)[0] + '/' if '/' in opf_path else ''

        ordered_files = [base_path + manifest[idref] for idref in spine_ids if idref in manifest]
        return ordered_files

def extract_sections_in_order(epub_path, ordered_files):
    sections = []
    with zipfile.ZipFile(epub_path, 'r') as z:
        for file in ordered_files:
            if file in z.namelist():
                with z.open(file) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    title_tag = soup.find(['h1', 'h2', 'title'])
                    title = title_tag.get_text().strip() if title_tag else file.split("/")[-1]
                    body = []
                    for element in soup.find_all(['p', 'img', 'div']):
                        if element.name == 'img':
                            img_src = element.get('src')
                            if img_src:
                                img_path = file.rsplit('/', 1)[0] + '/' + img_src if '/' in file else img_src
                                body.append(('img', img_path))
                        else:
                            body.append(('text', element.get_text().strip()))
                    sections.append((title, body))
    return sections

def draw_page_number(c, page_num, width, height):
    c.setFont("Times-Roman", 10)
    c.drawCentredString(width / 2, 0.5 * inch, f"Page {page_num}")

def sections_to_pdf(sections, pdf_path, epub_path):
    c = canvas.Canvas(pdf_path, pagesize=LETTER)
    c.setTitle("EPUB to PDF - Ordered and Formatted")

    width, height = LETTER
    margin = 1 * inch
    text_width = width - 2 * margin
    font_size = 12
    title_font_size = 16
    page_num = 1

    with zipfile.ZipFile(epub_path, 'r') as z:
        for i, (title, content_blocks) in enumerate(sections):
            c.bookmarkPage(f"section{i}")
            c.addOutlineEntry(title, f"section{i}", level=0, closed=False)
            c.setFont("Times-Bold", title_font_size)

            y = height - margin
            for line in simpleSplit(title, "Times-Bold", title_font_size, text_width):
                c.drawString(margin, y, line)
                y -= title_font_size + 2

            c.setFont("Times-Roman", font_size)

            for content_type, content in content_blocks:
                if content_type == 'text':
                    if not content:
                        y -= font_size
                        continue
                    for wrap_line in simpleSplit(content, "Times-Roman", font_size, text_width):
                        if y <= margin:
                            draw_page_number(c, page_num, width, height)
                            c.showPage()
                            page_num += 1
                            y = height - margin
                            c.setFont("Times-Roman", font_size)
                        c.drawString(margin, y, wrap_line)
                        y -= font_size + 2
                elif content_type == 'img':
                    if content in z.namelist():
                        try:
                            with z.open(content) as img_file:
                                img = Image.open(img_file)
                                img_width, img_height = img.size
                                aspect = img_height / img_width
                                display_width = text_width
                                display_height = display_width * aspect

                                if y - display_height < margin:
                                    draw_page_number(c, page_num, width, height)
                                    c.showPage()
                                    page_num += 1
                                    y = height - margin

                                img_reader = ImageReader(img)
                                c.drawImage(img_reader, margin, y - display_height, width=display_width, height=display_height)
                                y -= display_height + 10
                        except Exception as e:
                            print(f"Failed to load image {content}: {e}")

            draw_page_number(c, page_num, width, height)
            c.showPage()
            page_num += 1

    c.save()

def convert_epub_to_pdf_with_order(epub_path, pdf_path):
    try:
        ordered_files = get_spine_order(epub_path)
        sections = extract_sections_in_order(epub_path, ordered_files)
        sections_to_pdf(sections, pdf_path, epub_path)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Conversion failed: {e}")
        return False

def browse_file():
    epub_path = filedialog.askopenfilename(filetypes=[("EPUB files", "*.epub")])
    if epub_path:
        pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if pdf_path:
            success = convert_epub_to_pdf_with_order(epub_path, pdf_path)
            if success:
                messagebox.showinfo("Success", f"PDF saved to: {pdf_path}")

# GUI setup
root = tk.Tk()
root.title("EPUB to PDF Converter")
root.geometry("300x150")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

label = tk.Label(frame, text="Convert EPUB to PDF", font=("Arial", 14))
label.pack(pady=10)

button = tk.Button(frame, text="Select EPUB File", command=browse_file)
button.pack(pady=5)

root.mainloop()
