
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    print("Listing models via google.genai...")
    # The list method might return an iterator
    pager = client.models.list()
    for m in pager:
        print(f"Model: {m.name}")
        # print(f"  - Supported methods: {m.supported_generation_methods}") 
except Exception as e:
    print(f"Error with google.genai: {e}")

# Fallback check with langchain if possible, but skipping for now
