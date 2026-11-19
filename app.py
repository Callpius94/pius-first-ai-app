import os
from google import genai

# Load your secret key from the .env file
with open(".env") as f:
    for line in f:
        if line.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]

# Connect to Gemini
client = genai.Client()

def translate_and_fix(text, target_language):
    prompt = f"""
    You are a helpful language assistant.
    1. Correct any grammar or spelling mistakes in the original text.
    2. Translate the corrected text into {target_language}.
    
    Return both clearly labeled.
    
    Original text: {text}
    """
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
    )
    return response.text

# Test with a sample sentence
sample_text = "Hello friend, i is very excited to building my first AI app today!"
print("Processing...\n")
result = translate_and_fix(sample_text, "Swahili")
print(result)