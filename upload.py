import os
from pathlib import Path
import time
import hashlib
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_REGION = os.getenv("PINECONE_REGION") or os.getenv("PINECONE_ENVIRONMENT") or "us-east-1"

# Validate environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in environment")

print(f"Using Pinecone region: {PINECONE_REGION}")

# Configure OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072
BATCH_SIZE = 100

# Token limits - keep well under the 8191 limit
MAX_TOKENS = 6000  # Safe limit for embeddings
OVERLAP_TOKENS = 100


class TextUploader:
    def __init__(self, index_name="bangladesh-circulars-docs"):
        """
        Args:
            index_name: Name of the Pinecone index
        """
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = index_name
        self.index = None
        
        # Initialize tokenizer for accurate token counting
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

    def create_index(self):
        existing = self.pc.list_indexes().names()
        if self.index_name not in existing:
            print(f"Creating new index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_REGION),
            )
            self._wait_until_ready(timeout=15) # Increased timeout for index creation
        else:
            print(f"Connecting to existing index: {self.index_name}")
            
        self.index = self.pc.Index(self.index_name)
        print("Index is ready.")

    def _wait_until_ready(self, timeout=15, poll=2.0):
        start = time.time()
        while True:
            try:
                desc = self.pc.describe_index(self.index_name)
                status = getattr(desc, "status", None)
                ready = getattr(status, "ready", None)
                state = getattr(status, "state", None)
                
                if ready is True or state == "Ready":
                    print(f"Index {self.index_name} is ready.")
                    return
                    
            except Exception as e:
                print(f"Error describing index (will retry): {e}")

            if time.time() - start > timeout:
                raise TimeoutError(f"Index {self.index_name} not ready after {timeout}s")
                
            print(f"Waiting for index... (State: {state}, Ready: {ready})")
            time.sleep(poll)

    def extract_text_from_file(self, file_path):
        """
        Extract text from a text file
        """
        print(f" Extracting text from file...")
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                    print(f"  Successfully read with {encoding} encoding")
                    return text
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail
            print(f"  Could not decode file with standard encodings")
            return ""
            
        except Exception as e:
            print(f"  CRITICAL file reading error: {e}")
            return ""

    def count_tokens(self, text):
        """Accurately count tokens using tiktoken"""
        try:
            return len(self.tokenizer.encode(text, disallowed_special=()))
        except Exception as e:
            # Fallback to rough estimate for problematic text
            return len(text) // 3  # Conservative estimate

    def get_embedding(self, text):
        """Get embedding using OpenAI with token validation"""
        # Check token count before making API call
        token_count = self.count_tokens(text)
        if token_count > 8190: # Use 8190 as a hard limit
            print(f" Warning: Text has {token_count} tokens, truncating...")
            # Truncate to safe length
            tokens = self.tokenizer.encode(text)[:8190]
            text = self.tokenizer.decode(tokens)
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                response = client.embeddings.create(
                    input=text,
                    model=EMBEDDING_MODEL
                )
                return response.data[0].embedding
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f" Rate limit hit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f" Embedding error after {max_retries} attempts: {e}")
                        return None
                elif "400" in str(e) or "maximum context length" in str(e):
                    print(f" Token limit error: {e}")
                    return None
                else:
                    print(f" Embedding error: {e}")
                    return None
        
        return None

    def chunk_text_by_tokens(self, text, max_tokens=MAX_TOKENS, overlap_tokens=OVERLAP_TOKENS):
        """Split text into overlapping chunks based on actual token count"""
        # Tokenize the entire text
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= max_tokens:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get chunk of tokens
            end = min(start + max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
            
            # Move start position with overlap
            # Ensure start + step is less than end to avoid re-processing same chunk
            step = max_tokens - overlap_tokens
            start += step
            
            # Prevent infinite loop if step is 0 or negative
            if step <= 0:
                 break
        
        return chunks

    def generate_file_id(self, file_path, chunk_num=0):
        """Generate unique ID for text file chunk"""
        file_hash = hashlib.md5(file_path.encode("utf-8")).hexdigest()[:8]
        filename = os.path.splitext(os.path.basename(file_path))[0]
        # Clean filename to avoid issues
        filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))[:50]
        
        if chunk_num > 0:
            return f"{file_hash}_{filename}_chunk_{chunk_num:03d}"
        return f"{file_hash}_{filename}"

    def upload_text_file(self, file_path):
        """Upload text file with chunking and overlap"""
        print(f"Processing: {os.path.basename(file_path)}")
        
        full_text = self.extract_text_from_file(file_path)
        if not full_text.strip():
            print(f" No text extracted\n")
            return
        
        # Count tokens in full text
        total_tokens = self.count_tokens(full_text)
        print(f" Extracted text ({len(full_text)} chars, ~{total_tokens} tokens)")
        
        # Split into overlapping chunks by tokens
        chunks = self.chunk_text_by_tokens(full_text)
        print(f" Created {len(chunks)} chunk{'s' if len(chunks) > 1 else ''}")
        
        vectors = []
        successful_chunks = 0
        
        for chunk_idx, chunk in enumerate(chunks):
            # Verify chunk size
            chunk_tokens = self.count_tokens(chunk)
            if chunk_tokens == 0:
                print(f"  Chunk {chunk_idx + 1} is empty, skipping...")
                continue
            if chunk_tokens > 8190:
                print(f"  Chunk {chunk_idx + 1} too large ({chunk_tokens} tokens), skipping...")
                continue
            
            emb = self.get_embedding(chunk)
            if emb is None:
                print(f"  Chunk {chunk_idx + 1} embedding failed, skipping...")
                continue
            
            # Generate unique ID for each chunk
            if len(chunks) > 1:
                vid = self.generate_file_id(file_path, chunk_idx + 1)
            else:
                vid = self.generate_file_id(file_path)
            
            # Metadata with chunk text (limit metadata size)
            metadata = {
                "source": os.path.basename(file_path),
                "text": chunk[:10000]  # Limit metadata text size
            }
            
            if len(chunks) > 1:
                metadata["chunk"] = chunk_idx + 1
                metadata["total_chunks"] = len(chunks)
            
            vectors.append({
                "id": vid,
                "values": emb,
                "metadata": metadata
            })
            
            successful_chunks += 1
            
            # Batch upload
            if len(vectors) >= BATCH_SIZE:
                try:
                    self.index.upsert(vectors=vectors)
                    print(f"  → Uploaded {len(vectors)} vectors")
                    vectors = []
                except Exception as e:
                    print(f"  Upload error: {e}")
                    vectors = []
        
        # Upload remaining vectors
        if vectors:
            try:
                self.index.upsert(vectors=vectors)
                print(f"  → Uploaded {len(vectors)} vectors")
            except Exception as e:
                print(f"  Upload error: {e}")
        
        print(f" Completed ({successful_chunks}/{len(chunks)} chunks uploaded)\n")

    def upload_directory(self, directory_path):
        """Upload all text files in directory"""
        text_files = sorted(list(Path(directory_path).glob("*.txt")))
        print(f"Found {len(text_files)} text files\n")
        
        for idx, text_file in enumerate(text_files, 1):
            print(f"[{idx}/{len(text_files)}] ", end="")
            try:
                self.upload_text_file(str(text_file))
            except KeyboardInterrupt:
                print("\n\nUpload interrupted by user")
                break
            except Exception as e:
                print(f" Error: {e}\n")
                continue


if __name__ == "__main__":
    uploader = TextUploader(index_name="bangladesh-circulars-docs")
    uploader.create_index()
    uploader.upload_directory(r"C:\Users\hasan\Downloads\Download file scripts\BB_Circulars_Downloads\extracted_text")