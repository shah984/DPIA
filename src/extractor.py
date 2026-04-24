"""
extractor.py — Extract DPIA-relevant information from uploaded documents.

Single public function: extract_dpia_fields(document_text, template_text, guidance_text)
All Azure OpenAI calls live here and nowhere else.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# ── Azure client ───────────────────────────────────────────────────────────────

def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_VERSION", "2025-04-01-preview"),
    )


_MODEL = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4")

# ── Field definitions ──────────────────────────────────────────────────────────
# Each entry: (json_key, human_label, description)
# These keys must match exactly what dpia_mapper.py expects.

DPIA_FIELDS: list[tuple[str, str, str]] = [
    # Section 1 — Background and contacts
    ("project_title",           "1.1 Proposal/Project/Activity title",
     "The name or title of the project, proposal, or activity being assessed."),
    ("information_asset_title", "1.2 Information Asset title(s)",
     "The title(s) of the information asset(s) involved in the processing."),
    ("iao_name",                "1.3 Information Asset Owner name",
     "Full name of the Information Asset Owner (IAO)."),
    ("iao_email",               "1.3 IAO email address",
     "Email address of the Information Asset Owner."),
    ("iao_phone",               "1.3 IAO telephone number",
     "Telephone number of the Information Asset Owner."),
    ("iao_asset_title",         "1.3 IAO Information Asset title/role",
     "The IAO's job title or role relating to the information asset."),
    ("person_name",             "1.4 Name of person completing DPIA",
     "Full name of the person completing this DPIA."),
    ("person_email",            "1.4 Email of person completing DPIA",
     "Email address of the person completing this DPIA."),
    ("person_phone",            "1.4 Telephone of person completing DPIA",
     "Telephone number of the person completing this DPIA."),
    ("person_team",             "1.4 Business Unit/Team",
     "The business unit or team of the person completing this DPIA."),
    ("person_directorate",      "1.4 Directorate",
     "The directorate of the person completing this DPIA."),
    ("date_commenced",          "1.5 Date DPIA commenced",
     "The date this DPIA work started (DD/MM/YYYY or similar)."),
    ("processing_start_date",   "1.6 Date processing activity will start",
     "The date the data processing activity will start or has started."),
    ("iar_reference",           "1.7 Information Asset Register reference",
     "The reference number from the Information Asset Register, if known."),
    ("dpia_version",            "1.8 DPIA version number",
     "Version number of this DPIA document, e.g. Draft 0.1."),
    ("linked_dpias",            "1.9 Linked DPIAs",
     "Titles of any other DPIAs linked to this one."),
    ("publication_date",        "1.10 Proposed DPIA publication date",
     "The proposed date for publishing this DPIA, if applicable."),

    # Stage 1 / Section 3 — Purpose
    ("purpose_summary",         "Stage 1 Q2 / Purpose summary",
     "A brief plain-English summary (up to 100 words) of the processing activity and its purpose."),
    ("purpose_detailed",        "3.1 Detailed purpose of processing",
     "A detailed explanation of what the processing is for."),
    ("reason_for_proceeding",   "Stage 1 Q3 / Reason for proceeding",
     "The reason why proceeding with this processing is justified despite any risks."),

    # Section 2 — Personal data details
    ("personal_data",           "2.1 What personal data is being processed?",
     "Description of all personal data involved, including any special category data."),
    ("safeguards",              "2.5 Additional safeguards for special category data",
     "Any additional safeguards required for special category or sensitive personal data."),
    ("informed_why_not",        "2.6 Why data subjects are not / cannot be informed",
     "Explanation for why data subjects are not being informed, if applicable."),
    ("notification_method",     "2.7 How data subjects will be informed/notified",
     "Method by which data subjects will be informed about the processing."),
    ("access_who",              "2.8 Who will have access to the data?",
     "Which staff, roles, or external persons will have access to the personal data."),
    ("access_control",          "2.8a How access will be controlled",
     "Description of access control measures in place."),
    ("storage_location",        "2.9 Where will the data be stored?",
     "System(s) or location(s) where the personal data will be stored."),
    ("data_rights_no_reason",   "2.10 Reason data subject rights cannot be fulfilled",
     "If data subject rights cannot be fulfilled, the reason why."),
    ("data_rights_how",         "2.11 How data subject rights requirements will be met",
     "Explanation of how the organisation will fulfil data subject rights."),
    ("law_enf_logging",         "2.12 Law enforcement logging arrangements",
     "Details of logging arrangements for law enforcement processing, if applicable."),
    ("law_enf_categories",      "2.13 Law enforcement special categories",
     "Details of special category data processed under law enforcement provisions."),
    ("retention_period",        "2.14 Retention period for the data",
     "How long the personal data will be retained before deletion."),
    ("deletion_method",         "2.15 How data will be deleted",
     "The method by which data will be deleted in line with the retention period."),
    ("transfer_method",         "2.16 Method for physically moving/sharing/transferring data",
     "How personal data will be moved, shared, or transferred if applicable."),
    ("security_measures",       "2.17 Security measures",
     "Technical and organisational security measures protecting the personal data."),
    ("new_data_details",        "2.18 Details of new personal data being created",
     "If new personal data is being created or derived, provide details."),
    ("cookies_consent",         "2.20a Cookies — categories 2 or 3 consent details",
     "Details of cookie consent arrangements for category 2 or 3 cookies."),

    # Section 3 — Legal basis
    ("common_law_detail",       "3.3 Common law power details",
     "Details of the common law power relied on, if applicable."),
    ("explicit_statute",        "3.3 Explicit statute/power",
     "The explicit statutory power or legislation authorising the processing."),
    ("implied_statute",         "3.3 Implied statute/power",
     "The implied statutory power or legislation authorising the processing."),
    ("replacing_existing",      "3.x Replacing or enhancing existing activity",
     "Whether this processing replaces or enhances an existing activity or system, and details."),
    ("records_volume",          "Annual records/transactions volume",
     "Approximate number of individual records or transactions processed annually."),
    ("processing_frequency",    "Processing frequency",
     "Whether the processing is a one-off activity or ongoing, and how frequent."),
    ("processor_details",       "Processor details",
     "Details of any processors (non-public bodies) acting on behalf of the Home Office."),
    ("international_transfer",  "4.x International data transfer details",
     "Details of any international transfers of personal data, including destination countries."),
    ("new_technology_details",  "4.x New technology details",
     "Description of any new technology being used and its privacy implications."),
    ("privacy_enhancing",       "4.x Privacy-enhancing technology details",
     "Details of any privacy-enhancing technologies being deployed."),

    # Section 5 — Legal basis (full assessment)
    ("legal_basis_full",        "5.2 Full legal basis for processing",
     "The complete legal basis and relevant legislation for the processing activity."),
    ("explicit_statute_5",      "5.2 Explicit statute (section 5)",
     "Explicit statute or power listed in Section 5 legal basis."),
    ("implied_statute_5",       "5.2 Implied statute (section 5)",
     "Implied statute or power listed in Section 5 legal basis."),
]

# ── Yes/No fields ──────────────────────────────────────────────────────────────
# Each entry: (json_key, question_label)
# LLM must return "yes", "no", or null for each.
# These map to checkbox pairs in dpia_mapper.py.

YESNO_FIELDS: list[tuple[str, str]] = [
    # Stage 1 screening questions
    ("q1_personal_data",         "Stage 1 Q1: Does the proposal involve the processing of personal data?"),
    ("q3_automated_decisions",   "Stage 1 Q3: Does the processing involve automated decision-making with legal or similar significant effects?"),
    ("q4_systematic_monitoring", "Stage 1 Q4: Does the processing involve systematic monitoring of individuals?"),
    ("q5_sensitive_data",        "Stage 1 Q5: Does the processing involve mostly sensitive or special category personal data?"),
    ("q6_large_scale",           "Stage 1 Q6: Does the processing involve personal data on a large scale?"),
    ("q7_data_matching",         "Stage 1 Q7: Does the processing involve matching or combining datasets processed for different purposes?"),
    ("q8_vulnerable_subjects",   "Stage 1 Q8: Does the processing involve mostly data concerning vulnerable data subjects or children?"),
    ("q9_new_technology",        "Stage 1 Q9: Does the processing involve innovative use of new technological or organisational solutions?"),
    ("q10_rights_prevention",    "Stage 1 Q10: Will the processing prevent data subjects from exercising a right or accessing a service?"),
    # Section 2
    ("q2_3_special_category",    "2.3: Does the processing include any special category or criminal conviction data?"),
    ("q2_4_children_data",       "2.4: Does the processing include data relating to an individual aged 13 or younger?"),
    ("q2_6_subjects_informed",   "2.6: Will data subjects be informed of the processing?"),
    ("q2_10_storage_rights",     "2.10: Does the electronic storage system have capacity to meet data subject rights?"),
    ("q2_12_law_enf_logging",    "2.12: For law enforcement processing: does the electronic storage system log all access?"),
    ("q2_13_law_enf_categories", "2.13: For law enforcement processing: will it be possible to distinguish between different categories of data subjects?"),
    ("q2_18_new_data",           "2.18: Is there any new or additional personal data being processed?"),
    ("q2_20_cookies",            "2.20: Will the processing include the use of cookies?"),
    # Section 3/4
    ("q3_same_purpose",          "3.x: Is the purpose for processing the same as the original purpose for which the data was collected?"),
    ("q4_replacing_existing",    "4.x: Is the processing replacing or enhancing an existing activity or system?"),
    ("q4_new_activity",          "4.x: Is the processing a new activity?"),
    ("q4_involves_other_party",  "4.x: Does the processing involve another party (other directorates, external orgs)?"),
    ("q4_international_transfer","4.x: Will any personal data be transferred outside the UK?"),
    ("q4_profiling",             "4.x: Does the proposal involve profiling that could produce legal or significant effects?"),
    ("q4_automated_decision",    "4.x: Does the proposal involve automated decision-making?"),
    ("q4_new_technology",        "4.x: Does the processing involve the use of new technology?"),
    ("q4_subjects_consulted",    "4.x: Are the views of impacted data subjects being sought directly?"),
    # Section 5
    ("q5_5_mou",                 "5.5: Is the data sharing process underpinned by a non-binding arrangement (MOU)?"),
    ("q5_7_third_party",         "5.7: Will the other party share any HO data with a third party?"),
    ("q5_9_feasibility_testing", "5.9: Has any analysis or feasibility testing been carried out?"),
    ("q5_10_dev_required",       "5.10: Is development work required to ensure systems are Data Protection compliant?"),
    ("q5_11_security_satisfied", "5.11: Are you satisfied with the proposed security of the data?"),
    ("q5_14_off_site",           "5.14: Will the data be stored and accessible off-site?"),
    # Section 6
    ("q6_1_international",       "6.1: Does the activity involve transferring data to a country outside the UK?"),
    # Section 7
    ("q7_3_risks_balanced",      "7.3: Can you demonstrate that the risks to individuals are sufficiently balanced by the perceived benefits?"),
    ("q7_4_risk_register",       "7.4: Are these risks included within a risk register?"),
    ("q7_5_eia_completed",       "7.5: Has an Equality Impact Assessment been completed?"),
]

# Build the fields block for the system prompt
_FIELDS_BLOCK = "\n".join(
    f'  "{key}": {label} — {desc}'
    for key, label, desc in DPIA_FIELDS
)

_YESNO_BLOCK = "\n".join(
    f'  "{key}": {label}'
    for key, label in YESNO_FIELDS
)

_JSON_SHAPE = (
    "{"
    + ", ".join(f'"{k}": "..."' for k, _, _ in DPIA_FIELDS[:6])
    + ', "q1_personal_data": "yes/no/null", ... }'
)


# ── System prompt ──────────────────────────────────────────────────────────────

def _build_system_prompt(template_text: str, guidance_text: str) -> str:
    guidance_block = (
        f"\n=== HOME OFFICE DPIA GUIDANCE ===\n{guidance_text}\n=== END OF GUIDANCE ===\n"
        if guidance_text.strip()
        else ""
    )

    return f"""\
You are a data protection specialist at the UK Home Office.
Your task is to read a set of uploaded project documents and extract ONLY the information
that is relevant to populating a Data Protection Impact Assessment (DPIA).

You have access to the full DPIA template and guidance below. Study them carefully so you
understand what each field is asking for and what a good answer looks like.

=== HOME OFFICE DPIA TEMPLATE ===
{template_text}
=== END OF TEMPLATE ===
{guidance_block}
───────────────────────────────────────────────────────────────────────────────
PART A — TEXT FIELDS TO EXTRACT:

{_FIELDS_BLOCK}

───────────────────────────────────────────────────────────────────────────────
PART B — YES/NO QUESTIONS:

For each question below, return exactly "yes", "no", or null (if the documents
do not contain enough information to answer it).

{_YESNO_BLOCK}

───────────────────────────────────────────────────────────────────────────────
EXTRACTION RULES — follow these strictly:

1. Read ALL uploaded documents carefully before extracting anything.
2. Extract ONLY information that is explicitly stated in the uploaded documents.
   Do NOT invent, infer, or guess any values.
3. For text fields: if relevant information exists, extract it verbatim or
   summarised accurately. If not found, use null.
4. For yes/no fields: only answer "yes" or "no" if the documents explicitly
   state or clearly imply the answer. Otherwise use null.
5. Do not mix information between fields.
6. Return ONLY a single valid JSON object containing ALL Part A and Part B keys.
   No markdown fences, no explanation, no text before or after the JSON.
7. Use null (JSON null, not the string "null") for any field not found.

Example output shape (keys only):
{_JSON_SHAPE}
"""


# ── Public function ────────────────────────────────────────────────────────────

def extract_dpia_fields(
    document_text: str,
    template_text: str,
    guidance_text: str,
) -> dict[str, Any]:
    """
    Send all uploaded document text to the LLM and extract DPIA-relevant fields.

    Returns:
        dict mapping each DPIA field key to its extracted value (or None).

    Raises:
        ValueError: if the LLM response cannot be parsed as valid JSON.
        Exception: propagates Azure OpenAI errors.
    """
    client = _get_client()
    system_prompt = _build_system_prompt(template_text, guidance_text)

    user_message = (
        "Here are the uploaded project documents. "
        "Extract all DPIA-relevant information and return the JSON object.\n\n"
        f"{document_text}"
    )

    response = client.chat.completions.create(
        model=_MODEL,
        max_completion_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )

    raw = (response.choices[0].message.content or "").strip()
    logger.debug("LLM raw response (first 200 chars): %s", raw[:200])

    # Strip markdown fences if the model added them despite instructions
    if raw.startswith("```"):
        parts = raw.split("```", 2)
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not parse the model's JSON response: {exc}\n\n"
            f"Raw output (first 500 chars):\n{raw[:500]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object but got {type(data).__name__}."
        )

    # Normalise text fields: ensure every defined key exists (missing → None)
    result: dict[str, Any] = {}
    for key, _, _ in DPIA_FIELDS:
        value = data.get(key)
        if value in (None, "", "null", "N/A", "n/a"):
            result[key] = None
        else:
            result[key] = value

    # Normalise yes/no fields: only accept "yes" or "no", anything else → None
    for key, _ in YESNO_FIELDS:
        value = data.get(key)
        if isinstance(value, str) and value.strip().lower() in ("yes", "no"):
            result[key] = value.strip().lower()
        else:
            result[key] = None

    return result
