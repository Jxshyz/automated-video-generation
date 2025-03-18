import os
import requests
import sys
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv("credentials.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure the API key is loaded
if not OPENAI_API_KEY:
    print("Error: OpenAI API key not found. Please set it in a .env file.")
    sys.exit(1)

def read_instructions(file_path):
    """Reads the instruction file and returns the text."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def query_gpt(prompt):
    """Sends the prompt to OpenAI's GPT API and returns the response."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "Follow the user's instructions carefully."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure a file path is provided
    if len(sys.argv) < 2:
        print("Usage: python gpt.py <instruction_file.txt>")
        sys.exit(1)

    instruction_file = sys.argv[1]
    instructions = read_instructions(instruction_file)
    
    print("\n[+] Sending instructions to ChatGPT...\n")
    response = query_gpt(instructions)

    print("\n[GPT Response]:\n")
    print(response)

    with open("./data/output_gpt.txt", "w", encoding="utf-8") as f:
        f.write(response)
        print("\n[+] Response saved to output_gpt.txt")
