# AI Document Translator & Grammar Assistant

A Python AI assistant powered by **Google Gemini** that corrects English grammar and translates multi-format documents into different languages, exporting clean, ready-to-use files.

## Features
- **Multi-Format Support:** Reads **PDF (`.pdf`)**, **Word (`.docx`)**, and **PowerPoint (`.pptx`)** files.
- **Custom PDF Page Ranges:** Translate specific pages (e.g., `1-3` or `5`) or process an entire document.
- **Grammar & Spelling Correction:** Fixes English grammar and clarity before translating into your chosen target language (such as Swahili, French, or Spanish).
- **Formatted Word Export:** Outputs both the corrected English and translated sections neatly into a downloadable `.docx` document.
- **Resilient API Handling:** Automatically falls back across available Gemini models and paces requests to respect free-tier rate limits.

## Project Structure
```text
pius-first-ai-app/
├── app.py # Main document translation and grammar assistant script
├── .gitignore # Keeps API keys (.env) and generated outputs private
└── README.md # Setup and usage documentation
```

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd pius-first-ai-app
   ```

2. **Install required Python libraries:**
   ```bash
   pip install google-genai pypdf python-docx python-pptx
   ```

3. **Configure your Google Gemini API key:**
   Create a `.env` file in the root folder and add your key from [Google AI Studio](https://google.com):
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## How to Run

Run the script in your terminal:
```bash
python app.py
```

Follow the prompts:
1. Enter the filename (e.g., `sample.pdf`, `notes.docx`, or `slides.pptx`).
2. Enter your target language (e.g., `Swahili`, `French`).
3. *(For PDFs)* Enter a page range (e.g., `1-2`) or press **Enter** for all pages.
4. Open the generated `translated_<language>.docx` file to view your results.