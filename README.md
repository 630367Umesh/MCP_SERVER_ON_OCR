# OCR MCP Server

A FastAPI-based server for Optical Character Recognition (OCR) and document processing, supporting Tesseract, Nougat, and translation tools. Includes endpoints for extraction, summarization, and translation, with CORS enabled for easy integration with web frontends.

---

## Features

- **OCR Extraction**: Extract text from images using Tesseract or Nougat.
- **Summarization**: Summarize extracted text using Groq LLM.
- **Translation**: Translate extracted or summarized text to a target language using Groq LLM.

---

## Getting Started

### Prerequisites

- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (if using Tesseract engine)
- (Optional) Nougat model dependencies

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd ocr_mcp_server
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Install Tesseract:**
   - On Ubuntu: `sudo apt-get install tesseract-ocr`
   - On Windows: Download from [here](https://github.com/tesseract-ocr/tesseract/wiki)

---

## Running the Server

Start the FastAPI server with:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/docs`

---

## API Endpoints

### 1. Extract Text

**POST** `/tools/extract`

- **Form Data:**
  - `image_base64` (str, required): Base64-encoded image.
  - `engine` (str, optional): `"tesseract"` (default) or `"nougat"`.

**Response:**
```json
{ "result": "Extracted text..." }
```

---

### 2. Summarize File

**POST** `/tools/summarise`

- **Form Data:**
  - `uploaded_file` (file, required): File to summarize.
  - `engine` (str, optional): `"tesseract"` or `"nougat"`.

**Response:**
```json
{ "result": "Summary..." }
```

---

### 3. Translate File

**POST** `/tools/translate`

- **Form Data:**
  - `uploaded_file` (file, required): File to translate (image or PDF).
  - `target_language` (str, required): Target language (e.g., 'French', 'es', 'zh').
  - `engine` (str, optional): `"tesseract"`, `"nougat"`, or `"mistral"`.

**Response:**
```json
{ "result": "Translated summary..." }
```

---

## Example: Extract Text with cURL

```bash
curl -X POST http://localhost:8000/tools/extract \
  -F "image_base64=$(base64 -w 0 sample_data/test_ocr.png)" \
  -F "engine=nougat"
```

---

## Notes

- For best results, ensure images are clear and high-resolution.
- The summarization and translation endpoints use Groq LLM; ensure API keys/configuration are set if required.

---

## Using Images and PDFs

### Using Images
- The `/tools/extract` endpoint expects an image in base64 format.
- You can use PNG, JPG, or other common image formats.
- Example (Linux/macOS):
  ```bash
  base64 -w 0 sample_data/test_ocr.png > image.b64
  # Or directly in cURL:
  curl -X POST http://localhost:8000/tools/extract \
    -F "image_base64=$(base64 -w 0 sample_data/test_ocr.png)" \
    -F "engine=tesseract"
  ```
- Example (Windows PowerShell):
  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes('sample_data/test_ocr.png')) > image.b64
  # Or directly in cURL (PowerShell):
  curl -X POST http://localhost:8000/tools/extract `
    -F "image_base64=$(Get-Content -Raw -Path sample_data/test_ocr.png | [Convert]::ToBase64String([IO.File]::ReadAllBytes('sample_data/test_ocr.png')))" `
    -F "engine=tesseract"
  ```

### Using PDFs
- The API does not process PDFs directly for extraction; you must first convert PDF pages to images.
- You can use tools like `pdfimages` (Linux), `pdftoppm`, or Python libraries like `PyMuPDF` or `pdf2image`.
- Example using Python (`PyMuPDF`):
  ```python
  import fitz  # PyMuPDF
  doc = fitz.open('sample.pdf')
  for page_num in range(len(doc)):
      page = doc.load_page(page_num)
      pix = page.get_pixmap()
      pix.save(f'page_{page_num+1}.png')
  ```
- After conversion, use the resulting image(s) as shown above.

### Summarizing PDFs or Images
- For `/tools/summarise`, upload the image or PDF file directly as `uploaded_file`.
- The server will handle the file and return a summary.
- Example cURL:
  ```bash
  curl -X POST http://localhost:8000/tools/summarise \
    -F "uploaded_file=@sample_data/test_ocr.png" \
    -F "engine=tesseract"
  # For PDF:
  curl -X POST http://localhost:8000/tools/summarise \
    -F "uploaded_file=@sample_data/sample.pdf" \
    -F "engine=tesseract"
  ```

### Translating PDFs or Images
- For `/tools/translate`, upload the image or PDF file directly as `uploaded_file` and specify the `target_language`.
- The server will extract and summarize the text, then translate it to the target language using the LLM.
- Example cURL:
  ```bash
  curl -X POST http://localhost:8000/tools/translate \
    -F "uploaded_file=@sample_data/test_ocr.png" \
    -F "target_language=French" \
    -F "engine=nougat"
  # For PDF:
  curl -X POST http://localhost:8000/tools/translate \
    -F "uploaded_file=@sample_data/sample.pdf" \
    -F "target_language=French" \
    -F "engine=nougat"
  ```

Work_Flow:-

+------------------+         +------------------------+
| Streamlit UI     |         | FastAPI OCR MCP Server|
|------------------|         |------------------------|
| User uploads     |         | Receives base64       |
| image/pdf        +-------->+ or UploadFile         |
| Selects tool     |         | depending on endpoint |
| + OCR engine     |         +----------+------------+
+------------------+                    |
                                        |
                      +-----------------v----------------------+
                      | Tool Dispatcher (FastAPI Endpoints)    |
                      |----------------------------------------|
                      | /tools/extract   -> OCR (image/pdf)    |
                      | /tools/summarise -> OCR + LLM summary  |
                      | /tools/translate -> OCR + LLM translate|
                      +-----------------+----------------------+
                                        |
                +-----------------------v--------------------+
                | OCR Engine Logic                            |
                |---------------------------------------------|
                | If PDF: convert to image (fitz)             |
                | If image: open with PIL                     |
                | OCR Engine:                                 |
                |   - Tesseract (via pytesseract)             |
                |   - Nougat (via HuggingFace Transformers)   |
                +------------------------+--------------------+
                                         |
           +-----------------------------v---------------------+
           |  Result: extracted_text (plain)                   |
           +-----------------------------+---------------------+
                                         |
                  +----------------------v-------------------+
                  | If summarise:                            |
                  |   → Send extracted_text to Groq LLM      |
                  |   → Get summary                          |
                  +----------------------^-------------------+
                                         |
                  +----------------------v-------------------+
                  | If translate:                            |
                  |   → Send extracted_text or summary       |
                  |     to Groq LLM for translation          |
                  |   → Get translation                      |
                  +----------------------^-------------------+
                                         
