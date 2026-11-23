import os
import time
from google import genai
from pypdf import PdfReader
from docx import Document

# 1. Load your secret key safely without unpacking
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = line.strip().partition("=").pop(2)

client = genai.Client()

def clean_text(text):
    return text.encode("utf-8", "ignore").decode("utf-8").strip()

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
    models_to_try = ["gemini-4-argon", "gemini-4-carbon", "gemini-4-hydrogen", "gemini-3.8-flash"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                return response.text
        except Exception as e:
            print(f" [{model_name} error: {e}]")
            time.sleep(3)
            
    return f"[Error: Could not translate {label}.]"

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
        print("Unsupported file format! Please use a .pdf or .docx file.")
        exit()

    return sections

# 2. Ask user for file and target language
input_filename = input("Enter filename (e.g., sample.pdf or notes.docx): ").strip()
target_lang = input("Enter the language to translate into (e.g., Swahili, French): ").strip()

sections = get_sections_from_file(input_filename)
output_docx = f"translated_{target_lang.lower()}.docx"

# 3. Translate and save directly into a new Word (.docx) document
out_doc = Document()
out_doc.add_heading(f"Corrected & Translated Document ({target_lang})", level=1)

for label, text in sections:
    print(f"Processing {label}...")
    if not text.strip():
        print(f" {label} has no readable text, skipping.")
        continue

    result = translate_section(text, target_lang, label)
    for line in result.split("\n"):
        out_doc.add_paragraph(line)
    out_doc.add_page_break()
    out_doc.save(output_docx)

print(f"\nDone! Saved your Word document to: {output_docx}")