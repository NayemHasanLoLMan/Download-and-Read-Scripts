import os
import google.generativeai as genai
from pathlib import Path
import time
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Replace with your API key
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini 2.0 Flash model
model = genai.GenerativeModel('gemini-2.0-flash')

# Directories
INPUT_DIR = r"C:\Users\hasan\Downloads\Download file scripts\BB_Circulars_Downloads"
OUTPUT_TEXT_DIR = os.path.join(INPUT_DIR, "extracted_text")
OUTPUT_PDF_DIR = os.path.join(INPUT_DIR, "converted_pdfs")

# Create output directory
os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using Gemini 2.0 Flash with enhanced vision"""
    try:
        print(f"Processing: {os.path.basename(pdf_path)}")
        
        # Upload PDF to Gemini
        uploaded_file = genai.upload_file(pdf_path)
        
        # Wait for file processing
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            raise ValueError(f"File processing failed: {uploaded_file.state.name}")
        
        # Enhanced prompt for exact text extraction with OCR capabilities
        prompt = """You are an expert OCR and document extraction system. Extract ALL text from this PDF document with PERFECT accuracy.

        CRITICAL REQUIREMENTS:
        1. Extract text EXACTLY as it appears - word for word, character for character
        2. Preserve the EXACT language - if text is in Bengali (বাংলা), keep it in Bengali. If English, keep in English
        3. Maintain all formatting: paragraph breaks, line breaks, indentation, spacing
        4. Include ALL content: headers, footers, tables, lists, annotations, page numbers
        5. For scanned/image-based PDFs, use OCR to read every word accurately
        6. For tables, preserve the structure using plain text formatting
        7. Do NOT translate, summarize, or modify ANY text
        8. Do NOT skip any content - extract everything visible

        Return ONLY the extracted text with no commentary, no explanations, just the pure document content."""
        
        response = model.generate_content([uploaded_file, prompt])
        
        # Clean up uploaded file
        genai.delete_file(uploaded_file.name)
        
        return response.text
    
    except Exception as e:
        print(f" Error: {str(e)}")
        return None


def save_text_to_file(text, output_path):
    """Save extracted text to a text file with UTF-8 encoding"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f" Saved: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f" Error saving: {str(e)}")
        return False


def process_all_pdfs():
    """Process all PDFs in the input directory"""
    # Find all PDF files
    pdf_files = list(Path(INPUT_DIR).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process\n")
    
    successful = 0
    failed = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\n[{idx}/{len(pdf_files)}] {pdf_path.name}")
            
            filename = pdf_path.stem
            
            # Extract text using Gemini Vision
            extracted_text = extract_text_from_pdf(str(pdf_path))
            
            if extracted_text:
                # Save to text file
                text_output_path = os.path.join(OUTPUT_TEXT_DIR, f"{filename}.txt")
                if save_text_to_file(extracted_text, text_output_path):
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        except Exception as e:
            print(f" Error processing: {str(e)}")
            failed += 1
    
    print("PROCESSING COMPLETE!")
    print(f"Successfully extracted: {successful}")
    print(f"Failed: {failed}")
    print(f"\nText files saved in:\n   {OUTPUT_TEXT_DIR}")


if __name__ == "__main__":    
    process_all_pdfs()