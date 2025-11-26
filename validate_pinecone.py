import os
from pathlib import Path
import hashlib
from pinecone import Pinecone
from dotenv import load_dotenv
import tiktoken

load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Validate environment variables
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in environment")

class PineconeValidator:
    def __init__(self, index_name="bangladesh-circulars-docs"):
        """
        Args:
            index_name: Name of the Pinecone index
        """
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = index_name
        self.index = self.pc.Index(self.index_name)
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

    def generate_file_id(self, file_path, chunk_num=0):
        """Generate unique ID for text file chunk"""
        file_hash = hashlib.md5(file_path.encode("utf-8")).hexdigest()[:8]
        filename = os.path.splitext(os.path.basename(file_path))[0]
        # Clean filename to avoid issues
        filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))[:50]
        
        if chunk_num > 0:
            return f"{file_hash}_{filename}_chunk_{chunk_num:03d}"
        return f"{file_hash}_{filename}"

    def chunk_text_by_tokens(self, text, max_tokens=6000, overlap_tokens=100):
        """Split text into overlapping chunks based on actual token count"""
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= max_tokens:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
            
            step = max_tokens - overlap_tokens
            start += step
            
            if step <= 0:
                 break
        
        return chunks
    
    def extract_text_from_file(self, file_path):
        """
        Extract text from a text file
        """
        try:
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    return text
                except UnicodeDecodeError:
                    continue
            return ""
            
        except Exception as e:
            return ""

    def validate_directory(self, directory_path):
        """Validate all text files in directory"""
        text_files = sorted(list(Path(directory_path).glob("*.txt")))
        print(f"Found {len(text_files)} text files to validate.\n")
        
        found_count = 0
        not_found_count = 0

        for idx, text_file in enumerate(text_files, 1):
            file_path = str(text_file)
            print(f"[{idx}/{len(text_files)}] Validating: {os.path.basename(file_path)}")
            
            full_text = self.extract_text_from_file(file_path)
            if not full_text.strip():
                print(f"  - No text extracted, skipping.\n")
                continue
            
            chunks = self.chunk_text_by_tokens(full_text)
            
            ids_to_check = []
            if len(chunks) > 1:
                for i in range(len(chunks)):
                    ids_to_check.append(self.generate_file_id(file_path, i + 1))
            else:
                ids_to_check.append(self.generate_file_id(file_path))

            try:
                fetch_response = self.index.fetch(ids=ids_to_check)
                if fetch_response['vectors']:
                    print(f"  - Found: {os.path.basename(file_path)}")
                    found_count += 1
                else:
                    print(f"  - Not Found: {os.path.basename(file_path)}")
                    not_found_count += 1

            except Exception as e:
                print(f"  - Error fetching file: {e}")
                not_found_count += 1
            print()

        print(f"\nValidation Complete.")
        print(f"Found: {found_count}")
        print(f"Not Found: {not_found_count}")


if __name__ == "__main__":
    validator = PineconeValidator(index_name="bangladesh-circulars-docs")
    validator.validate_directory(r"C:\Users\hasan\Downloads\Download file scripts\BB_Circulars_Downloads\extracted_text")
