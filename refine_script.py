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

def break_down_script(script):
    """Uses GPT to break down the script into four sections for Beautiful.ai."""
    # Define the prompt for GPT to break down the script
    prompt = f"""
    I have a presentation script that I want to break down into four sections to create a 12-slide presentation in Beautiful.ai. The sections should be as follows:

    - Section 1: Introduction and Recurrent Neural Networks (RNNs) - 3 slides
    - Section 2: Long Short-Term Memory Networks (LSTMs) and Gated Recurrent Units (GRUs) - 3 slides
    - Section 3: Attention Mechanisms and Applications (Sports, Medical, Autonomous Driving) - 4 slides
    - Section 4: Transformers and Conclusion - 2 slides

    Here is the script:

    {script}

    Please break down the script into these four sections. For each section, provide the relevant text and include any visual cues (e.g., illustrations, diagrams, equations, animations) mentioned in the script. Label each section clearly (e.g., "Section 1: Introduction and RNNs"). Output the sections in a format that I can use as prompts for Beautiful.ai.
    """

    print("\n[+] Sending script breakdown request to ChatGPT...\n")
    response = query_gpt(prompt)

    return response

def save_sections(response):
    """Parses the GPT response and saves each section as a separate file."""
    # Create a directory to store the sections
    output_dir = "./data/script_sections"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Split the response into sections based on labels
    sections = response.split("Section ")[1:]  # Split after the first "Section "
    for section in sections:
        # Extract section number and title
        lines = section.split("\n", 1)
        if len(lines) < 2:
            print(f"Warning: Could not parse section: {section}")
            continue
        section_header = lines[0].strip()
        section_content = lines[1].strip()

        # Create a filename based on the section number
        section_number = section_header.split(":")[0].strip()
        filename = f"section_{section_number}.txt"
        filepath = os.path.join(output_dir, filename)

        # Save the section content to a file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(section_content)
        print(f"[+] Saved Section {section_number} to {filepath}")

if __name__ == "__main__":
    # Step 1: Read the script from ./data/output_gpt.txt
    script_file = "./data/output_gpt.txt"
    script = read_instructions(script_file)

    # Step 2: Break down the script using GPT
    breakdown_response = break_down_script(script)

    print("\n[GPT Response - Script Breakdown]:\n")
    print(breakdown_response)

    # Save the response to a file for reference
    with open("./data/script_breakdown.txt", "w", encoding="utf-8") as f:
        f.write(breakdown_response)
        print("\n[+] Script breakdown saved to script_breakdown.txt")

    # Step 3: Parse the response and save each section as a separate file
    save_sections(breakdown_response)

    print("\n[+] Script has been broken down into sections. You can now use these sections as prompts in Beautiful.ai.")
    print("\nInstructions for Beautiful.ai:")
    print("1. Go to Beautiful.ai and sign in or create an account (start with the free trial if needed).")
    print("2. Use the DesignerBot feature to create a presentation for each section:")
    print("   - Section 1 (3 slides): Introduction and RNNs")
    print("   - Section 2 (3 slides): LSTMs and GRUs")
    print("   - Section 3 (4 slides): Attention Mechanisms and Applications")
    print("   - Section 4 (2 slides): Transformers and Conclusion")
    print("3. For each section:")
    print("   - Copy the content from the corresponding section file (e.g., ./data/script_sections/section_1.txt).")
    print("   - Paste the content into DesignerBot as a prompt or upload the file as context.")
    print("   - Upload your custom images (e.g., diagrams, illustrations) as context to ensure they are included.")
    print("   - Generate the presentation and edit the slides as needed.")
    print("   - Export the presentation as a PDF (e.g., section_1.pdf).")
    print("4. Combine the PDFs into a single 12-slide PDF using a tool like Adobe Acrobat, Smallpdf, or a Python script (e.g., PyPDF2).")
    print("5. Use the final PDF in your video editing software to add your spoken text, avatar, and additional images/animations.")