import os
from google import genai
from pypdf import PdfReader

# 1. Load your secret key from the .env file
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]

client = genai.Client()

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    print(f"Found {len(reader.pages)} page(s) in PDF.")
    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)
    return "\n".join(full_text)

# 2. Ask the user for the PDF file name and target language
pdf_filename = input("Enter the PDF filename (e.g., sample.pdf): ").strip()
target_lang = input("Enter the language to translate into (e.g., Swahili, French): ").strip()

print("\nReading PDF...")
extracted_text = extract_text_from_pdf(pdf_filename)

# Check if the PDF actually had readable text
if not extracted_text.strip():
    print("Error: No readable text was found! Your PDF might be a scanned image.")
    exit()

print(f"Extracted {len(extracted_text)} characters. Sending to Gemini...\n")

prompt = f"""
You are a helpful language assistant.
1. Correct any English grammar, spelling, or punctuation mistakes in the document text below.
2. Translate the corrected text into {target_lang}.

Format the output with two clear headings:
--- CORRECTED ENGLISH ---
and
--- {target_lang.upper()} TRANSLATION ---

Document text:
{extracted_text}
"""

# 3. Stream the response with automatic fallback if a model is busy
models_to_try = ["gemini-3.8-flash", "gemini-3.1-pro-preview", "gemini-3-flash-preview"]
output_filename = f"translated_{target_lang.lower()}.txt"

for model_name in models_to_try:
    try:
        print(f"Trying {model_name}...\n")
        with open(output_filename, "w", encoding="utf-8") as out_file:
            for chunk in client.models.generate_content_stream(
                model=model_name,
                contents=prompt,
            ):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    out_file.write(chunk.text)
        print(f"\n\nDone! Saved your corrected and translated document to: {output_filename}")
        break
    except Exception as e:
        print(f"\n{model_name} is currently busy ({e}). Switching to next model...\n")