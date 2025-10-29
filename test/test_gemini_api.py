import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
print("Configuring Gemini API with provided API key...")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
print("Creating Gemini Generative Model instance...")
model = genai.GenerativeModel("gemini-2.0-flash")
print("Querying the model for a rock climbing joke...")
response = model.generate_content("Give me a hilarious joke about rock climbing")
if response.text:
    print(f"Success! Returned climbing joke:")
    print(response.text)