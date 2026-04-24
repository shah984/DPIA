"""
app.py — DPIAgent (Streamlit UI)

UI only. All business logic delegated to src/.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Make src/ importable
sys.path.insert(0, str(Path(__file__).parent))

from src.document_reader import read_all, _read_docx
from src.extractor import extract_dpia_fields, DPIA_FIELDS, YESNO_FIELDS
from src.dpia_mapper import build_mapping_plan
from src.generator import generate_dpia_docx

logging.basicConfig(level=logging.INFO)

_DOCS_DIR = Path(__file__).parent / "dpia_docs"

# ── Load reference docs once ───────────────────────────────────────────────────

@st.cache_resource
def _load_reference_docs() -> tuple[str, str]:
    template_path = _DOCS_DIR / "dpia_template.docx"
    guidance_path = _DOCS_DIR / "dpia_guidance.docx"

    if not template_path.exists():
        st.error(f"Template file not found: {template_path}\nPlease add dpia_template.docx to dpia_docs/.")
        st.stop()

    template_text = _read_docx(template_path)
    guidance_text = _read_docx(guidance_path) if guidance_path.exists() else ""
    return template_text, guidance_text


# ── Field label lookup ─────────────────────────────────────────────────────────

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DPIA Document Extractor",
    page_icon=":page_facing_up:",
    layout="centered",
)

st.title("DPIAgent")
st.markdown(
    "Upload your project documents and this tool will extract any DPIA-relevant information "
    "and insert it into a pre-formatted Home Office DPIA template. "
    "Only information explicitly found in your documents will be populated."
)

st.divider()

# ── File uploader ──────────────────────────────────────────────────────────────

uploaded_files = st.file_uploader(
    "Upload project documents",
    type=["pdf", "docx", "pptx", "txt"],
    accept_multiple_files=True,
    help="Accepted formats: PDF, Word (.docx), PowerPoint (.pptx), plain text (.txt). Upload as many as needed.",
)

# ── Process button ─────────────────────────────────────────────────────────────

if st.button("Process Documents", type="primary", disabled=not uploaded_files):
    # ── Save uploads to disk ───────────────────────────────────────────────────

    uploads_dir = Path(__file__).parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    saved_paths: list[Path] = []
    for uf in uploaded_files:
        dest = uploads_dir / uf.name
        dest.write_bytes(uf.read())
        saved_paths.append(dest)

    # ── Step 1: Read documents ─────────────────────────────────────────────────

    with st.spinner("Reading uploaded documents…"):
        document_text, read_warnings = read_all(saved_paths)

    for warn in read_warnings:
        st.warning(warn)

    if not document_text.strip():
        st.error("No readable text found in the uploaded documents. Please check the files and try again.")
    else:
        # ── Step 2: LLM extraction ─────────────────────────────────────────────

        template_text, guidance_text = _load_reference_docs()

        with st.spinner("Extracting DPIA-relevant information (this may take a moment)…"):
            try:
                extracted = extract_dpia_fields(document_text, template_text, guidance_text)
            except ValueError as exc:
                st.error(f"Failed to parse the model's response:\n\n```\n{exc}\n```")
                extracted = None
            except Exception as exc:
                st.error(f"An error occurred while calling the AI model:\n\n```\n{exc}\n```")
                extracted = None

        if extracted is not None:
            # ── Step 3: Map and generate ───────────────────────────────────────

            plan = build_mapping_plan(extracted)
            stem = saved_paths[0].stem if saved_paths else "document"

            with st.spinner("Generating DPIA document…"):
                try:
                    output_path = generate_dpia_docx(plan, stem)
                    st.session_state["results"] = {
                        "extracted": extracted,
                        "plan": plan,
                        "output_path": str(output_path),
                    }
                except Exception as exc:
                    st.error(f"Failed to generate the document:\n\n```\n{exc}\n```")
elif not uploaded_files:
    st.info("Upload one or more documents above, then click **Process Documents**.")

# ── Step 4: Results (persisted across re-runs via session_state) ───────────────

def _colour_status(val: str) -> str:
    if val in ("Populated", "Yes", "No"):
        return "color: green; font-weight: bold"
    return "color: #888"

if "results" in st.session_state:
    extracted   = st.session_state["results"]["extracted"]
    plan        = st.session_state["results"]["plan"]
    output_path = st.session_state["results"]["output_path"]

    st.divider()
    st.subheader("Results")

    total_text      = len(DPIA_FIELDS)
    total_yesno     = len(YESNO_FIELDS)
    populated_text  = sum(1 for k, _, _ in DPIA_FIELDS if extracted.get(k) is not None)
    populated_yesno = sum(1 for k, _ in YESNO_FIELDS if extracted.get(k) is not None)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Text fields populated", f"{populated_text}/{total_text}")
    col2.metric("Yes/No answered",       f"{populated_yesno}/{total_yesno}")
    col3.metric("Checkboxes ticked",     len(plan.checkbox_ticks))
    col4.metric("Total fields",          total_text + total_yesno)

    st.markdown("**Text field summary**")

    rows = []
    for key, label, _ in DPIA_FIELDS:
        value = extracted.get(key)
        if value:
            preview = str(value)[:120] + ("…" if len(str(value)) > 120 else "")
            rows.append({"Field": label, "Status": "Populated", "Extracted value": preview})
        else:
            rows.append({"Field": label, "Status": "Blank", "Extracted value": ""})

    df_text = pd.DataFrame(rows)
    st.dataframe(
        df_text.style.map(_colour_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Yes/No question summary**")
    yesno_rows = []
    for key, label in YESNO_FIELDS:
        value = extracted.get(key)
        if value == "yes":
            yesno_rows.append({"Question": label, "Answer": "Yes"})
        elif value == "no":
            yesno_rows.append({"Question": label, "Answer": "No"})
        else:
            yesno_rows.append({"Question": label, "Answer": "Not found"})

    df_yesno = pd.DataFrame(yesno_rows)
    st.dataframe(
        df_yesno.style.map(_colour_status, subset=["Answer"]),
        use_container_width=True,
        hide_index=True,
    )

    # ── Download button ────────────────────────────────────────────────────────

    st.divider()

    output_filename = Path(output_path).name
    with open(output_path, "rb") as f:
        docx_bytes = f.read()

    st.download_button(
        label=f"Download {output_filename}",
        data=docx_bytes,
        file_name=output_filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )
