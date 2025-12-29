# Download and Read Scripts

<div align="center">

**Automated document processing pipeline for Bangladesh Bank circulars with OCR and vector database integration**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-orange.svg)](https://www.pinecone.io/)
[![OCR](https://img.shields.io/badge/OCR-Enabled-green.svg)](https://github.com/tesseract-ocr/tesseract)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Module Documentation](#module-documentation)
- [Data Pipeline](#data-pipeline)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

Download and Read Scripts is a comprehensive automation framework designed to process Bangladesh Bank circulars and regulatory documents. The system downloads documents, performs OCR on scanned PDFs, extracts structured information, and uploads the processed data to Pinecone vector database for intelligent search and retrieval.

This solution streamlines the traditionally manual process of tracking, reading, and searching through banking circulars, making regulatory compliance and information retrieval significantly more efficient.

## Features

### Core Capabilities

- **Automated Download**: Fetch Bangladesh Bank circulars automatically from official sources
- **OCR Processing**: Extract text from scanned PDF documents with high accuracy
- **Structured Data Extraction**: Parse and organize circular metadata and content
- **Vector Database Integration**: Upload processed documents to Pinecone for semantic search
- **Data Validation**: Verify data integrity and upload success
- **JSON Storage**: Maintain a local JSON database of all processed circulars

### Advanced Features

- **Batch Processing**: Handle multiple documents efficiently
- **Error Recovery**: Robust error handling and retry mechanisms
- **Metadata Extraction**: Capture circular numbers, dates, subjects, and categories
- **Progress Tracking**: Monitor download and processing status
- **Duplicate Detection**: Prevent redundant processing of existing circulars

## Architecture

```
┌─────────────────┐
│  Bangladesh     │
│  Bank Website   │
└────────┬────────┘
         │
         ▼
  ┌──────────────┐
  │   main.py    │  ◄── Download circulars
  │  (Downloader)│
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   ocr.py     │  ◄── Extract text from PDFs
  │ (OCR Engine) │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │   JSON       │  ◄── Store structured data
  │  Database    │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  upload.py   │  ◄── Upload to Pinecone
  │  (Uploader)  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  validate_   │  ◄── Verify uploads
  │  pinecone.py │
  └──────────────┘
         │
         ▼
  ┌──────────────┐
  │   Pinecone   │
  │  Vector DB   │
  └──────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR is installed on your system
- Pinecone account and API key
- Stable internet connection

### System Dependencies

**For Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

**For macOS:**
```bash
brew install tesseract
```

**For Windows:**
Download and install from [Tesseract GitHub releases](https://github.com/tesseract-ocr/tesseract)

### Python Dependencies

```bash
# Core dependencies
pip install requests>=2.28.0
pip install beautifulsoup4>=4.11.0
pip install lxml>=4.9.0

# PDF and OCR processing
pip install PyPDF2>=3.0.0
pip install pdf2image>=1.16.0
pip install pytesseract>=0.3.10
pip install Pillow>=9.0.0

# Vector database
pip install pinecone-client>=2.2.0

# Utilities
pip install python-dotenv>=1.0.0
pip install tqdm>=4.65.0
```

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/NayemHasanLoLMan/Download-and-Read-Scripts.git
   cd Download-and-Read-Scripts
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Pinecone Configuration
PINECONE_API_KEY=your_api_key_here
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=bb-circulars

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
OCR_LANGUAGE=ben+eng  # Bengali and English

# Download Configuration
DOWNLOAD_PATH=./downloads
MAX_RETRIES=3
TIMEOUT=30

# Processing Configuration
BATCH_SIZE=10
ENABLE_PARALLEL_PROCESSING=true
```

### Directory Structure

```
Download-and-Read-Scripts/
├── main.py                    # Main download script
├── ocr.py                     # OCR processing module
├── upload.py                  # Pinecone upload module
├── validate_pinecone.py       # Validation script
├── bb_circulars.json         # Local circular database
├── downloads/                 # Downloaded PDF files
├── processed/                 # Processed documents
├── logs/                      # Application logs
└── .env                       # Environment configuration
```

## Quick Start

### Basic Workflow

```bash
# Step 1: Download circulars from Bangladesh Bank
python main.py --download --start-date 2024-01-01 --end-date 2024-12-31

# Step 2: Process downloaded PDFs with OCR
python ocr.py --input downloads/ --output processed/

# Step 3: Upload processed data to Pinecone
python upload.py --source bb_circulars.json

# Step 4: Validate uploads
python validate_pinecone.py --index bb-circulars
```

### Advanced Usage

```bash
# Download specific circular categories
python main.py --category "Foreign Exchange" --download

# Process single PDF file
python ocr.py --file downloads/circular_123.pdf

# Batch upload with custom settings
python upload.py --batch-size 50 --namespace production

# Validate specific date range
python validate_pinecone.py --start-date 2024-01-01 --end-date 2024-12-31
```

## Module Documentation

### `main.py` - Circular Downloader

Downloads Bangladesh Bank circulars from the official website and maintains a JSON database of all circulars.

**Key Functions:**
```python
def download_circular(url, output_dir):
    """Download a single circular PDF"""
    
def scrape_circulars(start_date, end_date):
    """Scrape circular metadata from website"""
    
def update_json_database(circulars):
    """Update local JSON database with new circulars"""
```

**Command Line Arguments:**
- `--download`: Enable download mode
- `--start-date`: Start date for circular search (YYYY-MM-DD)
- `--end-date`: End date for circular search (YYYY-MM-DD)
- `--category`: Filter by circular category
- `--output-dir`: Specify download directory

**Example:**
```bash
python main.py --download --start-date 2024-01-01 --category "Monetary Policy"
```

### `ocr.py` - OCR Processing Engine

Extracts text from scanned PDF documents using Tesseract OCR with support for Bengali and English languages.

**Key Functions:**
```python
def extract_text_from_pdf(pdf_path, language='ben+eng'):
    """Extract text from PDF using OCR"""
    
def preprocess_image(image):
    """Enhance image quality for better OCR results"""
    
def batch_process_pdfs(input_dir, output_dir):
    """Process multiple PDFs in batch"""
```

**Features:**
- Image preprocessing for better accuracy
- Multi-language support (Bengali + English)
- Batch processing capabilities
- Progress tracking with tqdm
- Error handling and logging

**Example:**
```python
from ocr import extract_text_from_pdf

text = extract_text_from_pdf('circular.pdf', language='ben+eng')
print(text)
```

### `upload.py` - Pinecone Uploader

Uploads processed circular data to Pinecone vector database with metadata and embeddings for semantic search.

**Key Functions:**
```python
def initialize_pinecone(api_key, environment, index_name):
    """Initialize Pinecone connection"""
    
def generate_embeddings(text):
    """Generate vector embeddings for text"""
    
def upload_to_pinecone(circulars, batch_size=100):
    """Upload circulars to Pinecone in batches"""
```

**Metadata Structure:**
```python
metadata = {
    'circular_no': '123/2024',
    'date': '2024-01-15',
    'subject': 'Foreign Exchange Guidelines',
    'category': 'Foreign Exchange',
    'text': 'Full circular text...'
}
```

**Example:**
```bash
python upload.py --source bb_circulars.json --batch-size 50 --namespace production
```

### `validate_pinecone.py` - Data Validator

Validates that all uploaded circulars are correctly stored in Pinecone with proper metadata and embeddings.

**Key Functions:**
```python
def validate_index(index_name):
    """Check if index exists and is accessible"
    
def verify_uploads(circular_ids):
    """Verify specific circulars are uploaded"""
    
def generate_validation_report():
    """ Generate comprehensive validation report"""
```

**Validation Checks:**
- Index existence and accessibility
- Document count verification
- Metadata completeness
- Embedding quality
- Search functionality test

**Example:**
```bash
python validate_pinecone.py --index bb-circulars --detailed-report
```

### `bb_circulars.json` - Circular Database

JSON database storing all processed circulars with metadata.

**Structure:**
```json
{
  "circulars": [
    {
      "id": "circular_123_2024",
      "circular_no": "123/2024",
      "date": "2024-01-15",
      "subject": "Foreign Exchange Guidelines",
      "category": "Foreign Exchange",
      "pdf_url": "https://...",
      "pdf_path": "./downloads/circular_123.pdf",
      "text": "Full extracted text...",
      "processed_date": "2024-01-20",
      "status": "uploaded"
    }
  ],
  "last_updated": "2024-12-29T10:30:00Z",
  "total_circulars": 1
}
```

## Data Pipeline

### End-to-End Workflow

1. **Discovery Phase**
   - Scrape the Bangladesh Bank website for new circulars
   - Extract circular metadata (number, date, subject, category)
   - Generate download URLs

2. **Download Phase**
   - Download PDF files to local storage
   - Verify file integrity
   - Update JSON database with download status

3. **Processing Phase**
   - Convert PDF pages to images
   - Preprocess images for OCR
   - Extract text using Tesseract OCR
   - Clean and structure extracted text

4. **Upload Phase**
   - Generate vector embeddings from text
   - Prepare metadata for Pinecone
   - Batch upload to vector database
   - Track upload progress

5. **Validation Phase**
   - Verify all documents uploaded successfully
   - Check metadata completeness
   - Test search functionality
   - Generate validation reports

### Error Handling

The system includes comprehensive error handling:
- **Network Errors**: Automatic retry with exponential backoff
- **OCR Failures**: Fallback to alternative extraction methods
- **Upload Errors**: Transaction logging and retry mechanisms
- **Validation Failures**: Detailed error reports with remediation steps

## Use Cases

### Regulatory Compliance
Monitor and track Bangladesh Bank circulars for compliance requirements in real-time.

### Banking Research
Build searchable knowledge bases of banking regulations and guidelines for research purposes.

### Legal Services
Provide law firms with rapid access to banking circulars for legal consultation and case preparation.

### Financial Consulting
Enable consultants to reference relevant circulars when advising clients on banking matters quickly.

### Automated Alerts
Set up notification systems for new circulars in specific categories or topics.

### Semantic Search
Implement intelligent search systems that understand context and intent, not just keywords.

## Troubleshooting

### Common Issues

**OCR Not Working**
```bash
# Verify Tesseract installation
tesseract --version

# Set correct path in .env
TESSERACT_PATH=/usr/bin/tesseract
```

**Pinecone Connection Errors**
```python
# Check API key and environment
import pinecone
pinecone.init(api_key="your-key", environment="your-env")
print(pinecone.whoami())
```

**Low OCR Accuracy**
- Ensure high-quality PDF source
- Adjust image preprocessing parameters
- Use appropriate language models
- Enable GPU acceleration if available

**Memory Issues with Large PDFs**
```python
# Process PDFs page by page instead of all at once
def process_large_pdf(pdf_path):
    for page_num in range(pdf_page_count):
        process_single_page(pdf_path, page_num)
```

## Contributing

We welcome contributions from the community!

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Download-and-Read-Scripts.git
   cd Download-and-Read-Scripts
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Code Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all functions and classes
- Add unit tests for new features
- Update documentation as needed

### Pull Request Process

1. Ensure all tests pass
2. Update README.md with details of changes
3. Update CHANGELOG.md with a note describing your changes
4. Submit PR with a clear description of changes

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=. tests/

# Run specific test file
python -m pytest tests/test_ocr.py
```

## License

This project is licensed under the MIT License. Please take a look at the [LICENSE](LICENSE) file for details.

## Contact

**Nayem Hasan**

- GitHub: [@NayemHasanLoLMan](https://github.com/NayemHasanLoLMan)
- Project Link: [https://github.com/NayemHasanLoLMan/Download-and-Read-Scripts](https://github.com/NayemHasanLoLMan/Download-and-Read-Scripts)

## Acknowledgments

- **Bangladesh Bank** for providing public access to circulars
- **Tesseract OCR** for open-source OCR capabilities
- **Pinecone** for vector database infrastructure
- **Open Source Community** for continuous support and contributions

## Roadmap

- [ ] Add support for multilingual OCR (Arabic, Hindi)
- [ ] Implement real-time circular monitoring
- [ ] Create REST API for programmatic access
- [ ] Build a web dashboard for visualization
- [ ] Add support for other central banks
- [ ] Implement change detection for circular updates
- [ ] Add export functionality (CSV, Excel, PDF)

---

<div align="center">

**Built for the Bangladesh banking and finance community**

⭐ Star this repository if you find it helpful!

</div>
