import os
import time
import argparse
import PyPDF2
import google.generativeai as genai

# --- Instructions for Use ---
# 1. Set your Gemini API key as an environment variable:
#    export GEMINI_API_KEY='your_api_key_here'
#
# 2. Run the script from your terminal, providing the path to the PDF file:
#    python main.py /path/to/your/document.pdf
# --------------------------

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    if not os.path.exists(pdf_path):
        return f"Error: The file '{pdf_path}' was not found."

    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            # Check if the PDF is encrypted
            if reader.is_encrypted:
                return "Error: The provided PDF is encrypted and cannot be read."

            for page in reader.pages:
                # Ensure page.extract_text() doesn't return None
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    except FileNotFoundError:
        return f"Error: PDF file not found at '{pdf_path}'."
    except Exception as e:
        return f"An unexpected error occurred while reading the PDF: {e}"
    return text

def summarize_text_with_gemini(api_key, text):
    """Summarizes text using the Gemini API."""
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set. Please set it before running the script."

    try:
        genai.configure(api_key=api_key)

        # Find a suitable model that supports content generation
        model_name = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name:
                    model_name = m.name
                    break
                if model_name is None:
                    model_name = m.name

        if not model_name:
            return "Error: No suitable model found for content generation."

        print(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name)

        prompt = f"Provide a concise and structured summary of the following research paper review:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        if "API key not valid" in str(e):
            return "An error occurred with the Gemini API: The provided API key is not valid."
        if "429" in str(e):
            return "Rate limit exceeded. Please wait a moment and try again."
        return f"An error occurred with the Gemini API: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize a PDF document using the Gemini API.")
    parser.add_argument("pdf_path", type=str, help="The full path to the PDF file you want to summarize.")
    args = parser.parse_args()

    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if not gemini_api_key:
        print("Error: The GEMINI_API_KEY environment variable is not set.")
        print("Please set it before running: export GEMINI_API_KEY='your_api_key'")
    else:
        print("Extracting text from PDF...")
        pdf_text = extract_text_from_pdf(args.pdf_path)

        if "Error:" not in pdf_text and pdf_text:
            # Truncate text to a safe limit for the API
            truncated_text = pdf_text[:32000]
            print(f"Text extracted successfully. Summarizing the first {len(truncated_text)} characters...")

            summary = summarize_text_with_gemini(gemini_api_key, truncated_text)

            print("\n--- Summary ---")
            print(summary)
            print("----------------")
        elif not pdf_text:
            print("No text could be extracted from the PDF. It might be empty or image-based.")
        else:
            # Print the specific error message from the extraction function
            print(pdf_text)
