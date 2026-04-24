# dpia-web — Claude Code Instructions

## Project Overview
A Streamlit web application that allows users to upload project documents (mix of relevant
and irrelevant content), uses an LLM to extract only DPIA-relevant information from them,
and outputs a partially populated DPIA template Word document.

This is a standalone project, separate from dpia-chatbot. It lives in its own repo: `dpia-web/`

## Repo Structure
dpia-web/
├── CLAUDE.md
├── README.md
├── .env.example
├── requirements.txt
├── app.py                        ← Streamlit entry point
├── dpia_docs/
│   ├── dpia_template.docx        ← Added manually — do not create or modify
│   └── dpia_guidance.docx        ← Added manually — do not create or modify
├── uploads/                      ← Temp storage for user-uploaded files (gitignored)
├── outputs/                      ← Populated DPIA documents land here (gitignored)
└── src/
    ├── extractor.py              ← LLM extraction logic
    ├── document_reader.py        ← Reads uploaded files into plain text
    ├── dpia_mapper.py            ← Maps extracted info to DPIA template fields
    └── generator.py              ← Populates and saves the .docx output

## LLM
Use the OpenAI Python SDK.
Model: gpt-5.4  — no other model is acceptable.

## Reference Documents
Before writing any code, read both files in dpia_docs/:
- dpia_template.docx — understand every section, field, and heading
- dpia_guidance.docx — understand what each field is asking for and what a good answer looks like

These files will be added manually by the developer. If they are not present when you start,
halt and ask for them before proceeding.

## Environment Variables
All secrets and config come from .env (loaded via python-dotenv).
Required variable: ANTHROPIC_API_KEY
Generate a .env.example with this key blank. Never hardcode keys.

## Tech Stack
- Python 3.11+
- streamlit
- openai (Python SDK)
- python-docx
- python-dotenv
- pypdf2 or pdfplumber (for reading uploaded PDFs)
- python-docx (for reading uploaded .docx files too)

## What the App Does — Step by Step

### Step 1 — Upload
User lands on the Streamlit app and uploads one or more files.
Accepted formats: .pdf, .docx, .txt
Files are saved temporarily to uploads/

### Step 2 — Document Reading
src/document_reader.py reads each uploaded file and converts it to plain text.
Handle all three formats. If a file cannot be parsed, show a warning and skip it — do not crash.

### Step 3 — LLM Extraction
src/extractor.py sends the full text of all uploaded documents to the LLM in a single call.

System prompt must:
- Include the full content of dpia_template.docx and dpia_guidance.docx so the model
  knows exactly what fields exist and what each one requires
- Instruct the model to read through all uploaded content and extract ONLY information
  that is relevant to populating a DPIA
- Instruct the model to ignore anything that is not relevant to a DPIA
- Ask the model to return a structured JSON object where each key is a DPIA field name
  (matching the template exactly) and each value is the extracted content for that field,
  or null if nothing relevant was found
- Tell the model to never invent or infer information — only extract what is explicitly
  stated in the uploaded documents

The JSON response must be parsed and validated before passing downstream.
If parsing fails, surface a clear error in the Streamlit UI.

### Step 4 — Template Population
src/dpia_mapper.py takes the extracted JSON and maps values to the correct locations
in the DPIA template.

src/generator.py opens dpia_docs/dpia_template.docx using python-docx, inserts the
extracted values into the correct fields, and saves the result to:
outputs/DPIA_<original_filename_stem>_<YYYY-MM-DD>.docx

Fields with null values are left blank — do not insert placeholder text.
Do not alter the template structure, formatting, fonts, or layout in any way.

### Step 5 — Download
Streamlit displays:
- A summary table showing which DPIA fields were populated and which remain blank
- A download button for the populated .docx file

## Streamlit UI Requirements
- Clean, single-page layout
- Clear heading: "DPIA Document Extractor"
- Brief plain-English explanation of what the tool does (2-3 sentences max)
- File uploader (multi-file, accepts .pdf .docx .txt)
- A "Process Documents" button — nothing runs until this is clicked
- A progress indicator while the LLM is working
- Results section: summary table + download button
- Error messages shown inline, never crash the app

## Hard Constraints
- Never invent DPIA content — extraction only, strictly from uploaded documents
- Never modify files in dpia_docs/
- uploads/ and outputs/ must be in .gitignore
- All LLM logic lives in src/extractor.py — do not scatter API calls elsewhere
- Keep app.py thin — UI only, delegates everything to src/

## Definition of Done
1. `streamlit run app.py` starts without errors
2. Uploading a mix of relevant and irrelevant documents results in only relevant
   DPIA information being extracted
3. The output .docx matches the template layout exactly, with populated fields only
   where information was found
4. A blank field in the output means nothing relevant was found — not an error