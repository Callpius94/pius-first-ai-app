import os
import io
import time
import streamlit as st
from google import genai
from pypdf import PdfReader
from docx import Document
from pptx import Presentation

# 1. Load your secret key safely
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1).pop()

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
                return response.text.strip()
        except Exception as e:
            time.sleep(5)
    return f"[Error: Could not translate {label}. Check your API quota.]"

def extract_sections(uploaded_file, page_range_str=""):
    name = uploaded_file.name.lower()
    sections = []

    if name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        total = len(reader.pages)
        if not page_range_str.strip():
            start_p, end_p = 1, total
        elif "-" in page_range_str:
            parts = page_range_str.split("-")
            start_p = max(1, int(parts.pop(0).strip()))
            end_p = min(total, int(parts.pop().strip()))
        else:
            start_p = end_p = min(total, max(1, int(page_range_str.strip())))

        for p in range(start_p, end_p + 1):
            text = reader.pages[p - 1].extract_text() or ""
            sections.append((f"Page {p}", text))

    elif name.endswith(".docx"):
        doc = Document(uploaded_file)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        chunk, num = [], 1
        for para in paragraphs:
            chunk.append(para)
            if len("\n".join(chunk)) >= 3000:
                sections.append((f"Section {num}", "\n\n".join(chunk)))
                chunk, num = [], num + 1
        if chunk:
            sections.append((f"Section {num}", "\n\n".join(chunk)))

    elif name.endswith(".pptx"):
        prs = Presentation(uploaded_file)
        for idx, slide in enumerate(prs.slides, start=1):
            texts = [sh.text_frame.text.strip() for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
            sections.append((f"Slide {idx}", "\n".join(texts)))

    return sections

# --- STREAMLIT WEB UI ---
st.set_page_config(page_title="AI Document Translator", page_icon="🌍")
st.title("🌍 AI Document Translator & Grammar Assistant")
st.write("Upload a **PDF**, **Word (.docx)**, or **PowerPoint (.pptx)** file to fix English grammar and translate it into your chosen language.")

uploaded_file = st.file_uploader("Choose a document", type=["pdf", "docx", "pptx"])

col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Target Language", ["Swahili", "French", "Spanish", "German", "Arabic", "Other"])
    if target_lang == "Other":
        target_lang = st.text_input("Enter custom language", value="Portuguese")
with col2:
    page_range = st.text_input("PDF Page Range (optional, e.g. 1-2)", value="")

if uploaded_file and st.button("✨ Correct Grammar & Translate", type="primary"):
    sections = extract_sections(uploaded_file, page_range)
    if not sections:
        st.warning("No readable text found in this file.")
    else:
        out_doc = Document()
        out_doc.add_heading(f"Corrected & Translated Document ({target_lang})", level=1)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        preview_box = st.expander("Preview Translated Output", expanded=True)

        for idx, (label, text) in enumerate(sections):
            status_text.text(f"Processing {label} ({idx + 1}/{len(sections)})...")
            if text.strip():
                result = translate_section(text, target_lang, label)
                for line in result.split("\n"):
                    out_doc.add_paragraph(line)
                out_doc.add_page_break()
                with preview_box:
                    st.markdown(f"### {label}")
                    st.text(result)
            progress_bar.progress((idx + 1) / len(sections))
            if idx < len(sections) - 1:
                time.sleep(10)

        status_text.success("Done! Your translated Word document is ready.")
        
        # Save Word doc into memory for instant browser download
        buffer = io.BytesIO()
        out_doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label=f"📥 Download translated_{target_lang.lower()}.docx",
            data=buffer,
            file_name=f"translated_{target_lang.lower()}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )