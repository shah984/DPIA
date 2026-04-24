# DPIAgent

A Streamlit web application that extracts DPIA-relevant information from uploaded project documents and populates a Home Office DPIA template Word document.

## What it does

Upload a mix of project documents (business cases, technical designs, data sharing notes, etc.) and the tool will:

1. Read and parse all uploaded files
2. Use an LLM to extract only DPIA-relevant information
3. Populate a pre-formatted Home Office DPIA template `.docx`
4. Present a summary of which fields were populated
5. Provide a download link for the completed document

Only information explicitly found in the uploaded documents is populated — nothing is invented or inferred.

## Supported file formats

- PDF (`.pdf`)
- Word (`.docx`)
- PowerPoint (`.pptx`)
- Plain text (`.txt`)

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/shah984/DPIA.git
   cd DPIA
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Fill in your Azure OpenAI credentials in `.env`:
   ```
   AZURE_OPENAI_API_KEY=
   AZURE_OPENAI_ENDPOINT=
   AZURE_OPENAI_DEPLOYMENT=
   AZURE_OPENAI_VERSION=
   ```

4. **Add the DPIA reference documents**

   Place the following files in `dpia_docs/` (not included in the repo):
   - `dpia_template.docx`
   - `dpia_guidance.docx`

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Project structure

```
dpia-web/
├── app.py                  # Streamlit entry point (UI only)
├── requirements.txt
├── dpia_docs/              # Reference docs — add manually, gitignored
├── uploads/                # Temp storage for uploaded files (gitignored)
├── outputs/                # Generated DPIA documents (gitignored)
└── src/
    ├── document_reader.py  # Parses uploaded files into plain text
    ├── extractor.py        # LLM extraction logic
    ├── dpia_mapper.py      # Maps extracted fields to template positions
    └── generator.py        # Populates and saves the .docx output
```
