"""
dpia_mapper.py — Maps extracted field dict to template insertion points.

No I/O. Returns a MappingPlan consumed by generator.py.

Template insertion points:
  - SDT_MAP: field_key → sequential index of text-input SDT in document body
  - DATE_SDT_MAP: field_key → sequential index of date-picker SDT in document body
  - TABLE_CELL_MAP: field_key → (table_index, row_index, col_index)

SDT indices are zero-based positions among all <w:sdt> elements containing
the placeholder text "Click or tap here to enter text." (for text SDTs) or
"Click or tap to enter a date." (for date SDTs), walked sequentially through
the document body.

The cover table uses plain cell text replacement (Table 0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── SDT positional map (text-input SDTs) ──────────────────────────────────────
# Index → sequential position among body SDTs whose placeholder = "Click or tap here to enter text."
# Derived from full document walk (see project notes).

SDT_MAP: dict[str, int] = {
    "purpose_summary":          0,   # Stage 1 Q2
    "reason_for_proceeding":    1,   # Stage 1 Q2/Q3
    "project_title":            2,   # 1.1
    "information_asset_title":  3,   # 1.2
    # IAO 1
    "iao_email":                4,   # 1.3 IAO-1 email
    "iao_name":                 5,   # 1.3 IAO-1 name
    "iao_phone":                6,   # 1.3 IAO-1 telephone
    "iao_asset_title":          7,   # 1.3 IAO-1 asset title
    # Person completing DPIA
    "person_email":             16,  # 1.4 email
    "person_name":              17,  # 1.4 name
    "person_phone":             18,  # 1.4 telephone
    "person_team":              19,  # 1.4 business unit/team
    "person_directorate":       20,  # 1.4 directorate
    # Section 1 continued
    "processing_start_date":    21,  # 1.6 (text input after date picker + NB)
    "iar_reference":            22,  # 1.7
    "dpia_version":             23,  # 1.8
    "linked_dpias":             24,  # 1.9
    # Section 2
    "personal_data":            25,  # 2.1
    "safeguards":               26,  # 2.5
    "informed_why_not":         27,  # 2.6
    "notification_method":      28,  # 2.7
    "access_who":               29,  # 2.8
    "access_control":           30,  # 2.8a
    "storage_location":         31,  # 2.9
    "data_rights_no_reason":    32,  # 2.10
    "data_rights_how":          33,  # 2.11
    "law_enf_logging":          34,  # 2.12/2.13 (inline parent=p)
    "retention_period":         35,  # 2.14
    "deletion_method":          36,  # 2.15
    "transfer_method":          37,  # 2.16
    "security_measures":        38,  # 2.17
    "new_data_details":         39,  # 2.18
    "cookies_consent":          40,  # 2.20a
    # Section 3
    "purpose_detailed":         41,  # 3.1
    "common_law_detail":        42,  # 3.3 common law
    "explicit_statute":         43,  # 3.3 explicit statute
    "implied_statute":          44,  # 3.3 implied statute
    "replacing_existing":       46,  # 3.x replacing/enhancing (SDT[45]=inline "Original purpose:")
    "records_volume":           47,  # annual records volume
    "processing_frequency":     48,  # one-off vs ongoing frequency
    "processor_details":        50,  # 4.x processor details
    "international_transfer":   51,  # 4.x international transfer countries
    "new_technology_details":   54,  # 4.x new technology description
    "privacy_enhancing":        55,  # 4.x privacy-enhancing tech
    # Section 5
    "legal_basis_full":         69,  # 5.2 legal basis text
    "explicit_statute_5":       70,  # 5.2 explicit statute
    "implied_statute_5":        71,  # 5.2 implied statute
}

# ── Date-picker SDT map ────────────────────────────────────────────────────────
# Index → sequential position among body SDTs whose placeholder = "Click or tap to enter a date."

DATE_SDT_MAP: dict[str, int] = {
    "date_commenced":       0,   # 1.5
    # processing_start_date date picker = DATE_SDT[1], but we also write to SDT[21] above
    "publication_date":     2,   # 1.10
}

# ── Table cell map ─────────────────────────────────────────────────────────────
# (table_index, row_index, col_index) — zero-based

TABLE_CELL_MAP: dict[str, tuple[int, int, int]] = {
    "project_title":    (0, 0, 1),   # Cover table row 0 col 1 (replaces "INSERT NAME")
    "iao_name":         (0, 1, 1),   # Cover table row 1 col 1
}

# ── Checkbox pair map ─────────────────────────────────────────────────────────
# Maps yes/no field key → (yes_checkbox_index, no_checkbox_index)
# Indices are sequential positions among all ☐ SDTs in the document body.
# Derived from full positional walk (see project notes).

CHECKBOX_PAIR_MAP: dict[str, tuple[int, int]] = {
    # Stage 1 screening questions
    "q1_personal_data":          (0,   2),
    "q3_automated_decisions":    (17,  20),
    "q4_systematic_monitoring":  (23,  26),
    "q5_sensitive_data":         (29,  31),
    "q6_large_scale":            (34,  37),
    "q7_data_matching":          (40,  43),
    "q8_vulnerable_subjects":    (46,  49),
    "q9_new_technology":         (52,  55),
    "q10_rights_prevention":     (58,  61),
    # Section 2
    "q2_3_special_category":     (83,  87),
    "q2_4_children_data":        (115, 117),
    "q2_6_subjects_informed":    (119, 121),
    "q2_10_storage_rights":      (123, 125),
    "q2_12_law_enf_logging":     (127, 129),
    "q2_13_law_enf_categories":  (131, 133),
    "q2_18_new_data":            (135, 137),
    "q2_20_cookies":             (144, 145),
    # Section 3/4
    "q3_same_purpose":           (228, 230),
    "q4_replacing_existing":     (244, 246),
    "q4_new_activity":           (248, 250),
    "q4_involves_other_party":   (255, 257),
    "q4_international_transfer": (268, 270),
    "q4_profiling":              (272, 274),
    "q4_automated_decision":     (276, 278),
    "q4_new_technology":         (279, 281),
    "q4_subjects_consulted":     (282, 284),
    # Section 5
    "q5_5_mou":                  (294, 296),
    "q5_7_third_party":          (298, 300),
    "q5_9_feasibility_testing":  (323, 325),
    "q5_10_dev_required":        (327, 329),
    "q5_11_security_satisfied":  (331, 333),
    "q5_14_off_site":            (335, 337),
    # Section 6
    "q6_1_international":        (344, 346),
    # Section 7
    "q7_3_risks_balanced":       (411, 413),
    "q7_4_risk_register":        (415, 417),
    "q7_5_eia_completed":        (419, 421),
}


# ── MappingPlan dataclass ──────────────────────────────────────────────────────

@dataclass
class MappingPlan:
    """
    Resolved insertion instructions for generator.py.

    sdt_insertions:       list of (sdt_index, value)
    date_sdt_insertions:  list of (date_sdt_index, value)
    table_insertions:     list of (table_idx, row_idx, col_idx, value)
    checkbox_ticks:       list of checkbox_sdt_index to tick (☐ → ☒)
    populated_fields:     keys that have a non-null value
    blank_fields:         keys that are null / not found
    """
    sdt_insertions: list[tuple[int, str]] = field(default_factory=list)
    date_sdt_insertions: list[tuple[int, str]] = field(default_factory=list)
    table_insertions: list[tuple[int, int, int, str]] = field(default_factory=list)
    checkbox_ticks: list[int] = field(default_factory=list)
    populated_fields: list[str] = field(default_factory=list)
    blank_fields: list[str] = field(default_factory=list)


def build_mapping_plan(extracted: dict[str, Any]) -> MappingPlan:
    """
    Convert the extracted field dict into a MappingPlan.

    Args:
        extracted: dict of field_key → value (None if not found).
                   Yes/no fields contain "yes", "no", or None.

    Returns:
        MappingPlan ready for generator.py to consume.
    """
    plan = MappingPlan()
    seen_sdt_indices: set[int] = set()

    for key, value in extracted.items():
        if value is None:
            plan.blank_fields.append(key)
            continue

        # ── Yes/No checkbox fields ────────────────────────────────────────────
        if key in CHECKBOX_PAIR_MAP:
            yes_idx, no_idx = CHECKBOX_PAIR_MAP[key]
            answer = str(value).strip().lower()
            if answer == "yes":
                plan.checkbox_ticks.append(yes_idx)
                plan.populated_fields.append(key)
            elif answer == "no":
                plan.checkbox_ticks.append(no_idx)
                plan.populated_fields.append(key)
            else:
                plan.blank_fields.append(key)
            continue

        text = str(value).strip()
        if not text:
            plan.blank_fields.append(key)
            continue

        plan.populated_fields.append(key)

        # Table cell insertion (cover table)
        if key in TABLE_CELL_MAP:
            t_idx, r_idx, c_idx = TABLE_CELL_MAP[key]
            plan.table_insertions.append((t_idx, r_idx, c_idx, text))

        # Text-input SDT insertion
        if key in SDT_MAP:
            sdt_idx = SDT_MAP[key]
            if sdt_idx not in seen_sdt_indices:
                plan.sdt_insertions.append((sdt_idx, text))
                seen_sdt_indices.add(sdt_idx)

        # Date-picker SDT insertion
        if key in DATE_SDT_MAP:
            date_idx = DATE_SDT_MAP[key]
            plan.date_sdt_insertions.append((date_idx, text))

    return plan
