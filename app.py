import os
import time
from google import genai
from pypdf import PdfReader
from docx import Document
from pptx import Presentation

# 1. Load your secret key safely
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1).pop()

client = genai.Client()

def clean_text(text):
    return text.encode("utf-8", "ignore").decode("utf-8").strip()

def call_gemini_with_fallback(prompt):
    models_to_try = ["gemini-4-argon", "gemini-4-carbon", "gemini-4-hydrogen", "gemini-3.8-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f" [{model_name} failed: {e}]")
            time.sleep(5)
    return None

def translate_section(text, target_language, label):
    cleaned = clean_text(text)
    prompt = f"""
    You are a helpful language assistant.
    1. Correct any English grammar, spelling, or punctuation mistakes in {label} below.
    2. Translate the corrected text into {target_language}.
    
    Format the output clearly with two headings:
    --- {label.upper()}: CORRECTED ENGLISH ---
    and
    --- {label.upper()}: {target_language.upper()} TRANSLATION ---
    
    Text:
    {cleaned}
    """
    result = call_gemini_with_fallback(prompt)
    return result if result else f"[Error: Could not translate {label}.]"

def process_powerpoint(filename, target_language):
    prs = Presentation(filename)
    total_slides = len(prs.slides)
    output_pptx = f"translated_{target_language.lower()}.pptx"
    print(f"\nLoaded PowerPoint '{filename}' ({total_slides} slides total).")

    for idx, slide in enumerate(prs.slides, start=1):
        print(f"Translating Slide {idx} of {total_slides}...")
        paragraphs_to_update = []
        original_texts = []

        # Collect all text boxes on this slide so they translate in ONE API call
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = clean_text(paragraph.text)
                    if text:
                        paragraphs_to_update.append(paragraph)
                        original_texts.append(text)

        if not original_texts:
            print(f" Slide {idx} has no text, skipping.")
            continue

        joined_text = "\n|||\n".join(original_texts)
        prompt = f"""
        Correct any English grammar or spelling mistakes in each item below, then translate each item into {target_language}.
        Keep the exact same number of items separated by ||| on its own line.
        Return ONLY the translated items separated by ||| (no numbering, headings, or extra notes).

        {joined_text}
        """
        response_text = call_gemini_with_fallback(prompt)
        if response_text:
            translated_items = [item.strip() for item in response_text.split("|||")]
            for paragraph, new_text in zip(paragraphs_to_update, translated_items):
                if paragraph.runs:
                    for i, run in enumerate(paragraph.runs):
                        run.text = new_text if i == 0 else ""
                else:
                    paragraph.text = new_text
        else:
            print(f" [Warning: Could not translate Slide {idx}, keeping original text.]")

        prs.save(output_pptx)
        if idx < total_slides:
            print(" Waiting 10s before next slide...")
            time.sleep(10)

    print(f"\nDone! Saved your translated PowerPoint deck to: {output_pptx}")

def get_sections_from_file(filename):
    lower_name = filename.lower()
    sections = []

    if lower_name.endswith(".pdf"):
        reader = PdfReader(filename)
        total_pages = len(reader.pages)
        print(f"\nLoaded PDF '{filename}' ({total_pages} pages total).")
        page_range = input(
            f"Enter page range (e.g., 1-3, 3, or press Enter for all {total_pages}): "
        ).strip()

        if not page_range:
            start_page, end_page = 1, total_pages
        elif "-" in page_range:
            parts = page_range.split("-")
            start_page = max(1, int(parts.pop(0).strip()))
            end_page = min(total_pages, int(parts.pop().strip()))
        else:
            start_page = end_page = min(total_pages, max(1, int(page_range)))

        for page_num in range(start_page, end_page + 1):
            text = reader.pages[page_num - 1].extract_text() or ""
            sections.append((f"Page {page_num}", text))

    elif lower_name.endswith(".docx"):
        doc = Document(filename)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        print(f"\nLoaded Word document '{filename}' ({len(paragraphs)} paragraphs).")
        
        chunk, chunk_num = [], 1
        for para in paragraphs:
            chunk.append(para)
            if len("\n".join(chunk)) >= 3000:
                sections.append((f"Section {chunk_num}", "\n\n".join(chunk)))
                chunk, chunk_num = [], chunk_num + 1
        if chunk:
            sections.append((f"Section {chunk_num}", "\n\n".join(chunk)))
    else:
        print("Unsupported file format! Please use a .pdf, .docx, or .pptx file.")
        exit()

    return sections

# 2. Ask user for file and target language
input_filename = input("Enter filename (e.g., sample.pdf, notes.docx, slides.pptx): ").strip()
target_lang = input("Enter the language to translate into (e.g., Swahili, French): ").strip()

# 3. Route PowerPoint files to .pptx slide export, and PDF/Word to .docx report export
if input_filename.lower().endswith(".pptx"):
    process_powerpoint(input_filename, target_lang)
else:
    sections = get_sections_from_file(input_filename)
    output_docx = f"translated_{target_lang.lower()}.docx"

    out_doc = Document()
    out_doc.add_heading(f"Corrected & Translated Document ({target_lang})", level=1)

    for idx, (label, text) in enumerate(sections):
        print(f"Processing {label}...")
        if not text.strip():
            print(f" {label} has no readable text, skipping.")
            continue

        result = translate_section(text, target_lang, label)
        for line in result.split("\n"):
            out_doc.add_paragraph(line)
        out_doc.add_page_break()
        out_doc.save(output_docx)

        if idx < len(sections) - 1:
            print(" Pausing 15s to stay within Free Tier per-minute limits...")
            time.sleep(15)

    print(f"\nDone! Saved your Word document to: {output_docx}")