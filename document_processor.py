"""Module 3: Identity and Insurance Document Processor.

Features:
- Multi-document upload (PDF, Images, TXT).
- Classification of 10 Identity & Insurance document types:
  Aadhaar, PAN, Driving Licence, Passport, NACH/ECS, FATCA,
  Benefit Illustration Declaration, Moral Hazard Questionnaire,
  Multiple Policies Consent, and Suitability Profiler.
- Field extraction with individual confidence scores.
- Low-confidence flagging for human review.
- OCR support for scanned documents & clear handwriting disclaimer.
- Strict null handling for unextracted fields (no hallucinations).
- Sensitive PII masking and structured JSON generation.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st
from PIL import Image

from utils.doc_reader import extract_text_from_file
from utils.ocr_engine import is_tesseract_available, perform_ocr_on_image
from utils.pii_protector import mask_field_value, redact_document_data

# Classification keywords and document signatures
DOC_SIGNATURES = {
    "Aadhaar": [
        "aadhaar", "uidai", "unique identification authority", "enrolment no",
        "government of india", "mera aadhaar", "vid:", "help@uidai.gov.in"
    ],
    "PAN": [
        "income tax department", "permanent account number", "pan card",
        "govt. of india", "father's name", "date of birth", "incometaxindia"
    ],
    "Driving Licence": [
        "driving licence", "driving license", "union of india", "motor vehicles act",
        "licence no", "dl no", "transport department", "authorisation to drive", "mcwg", "lmv"
    ],
    "Passport": [
        "passport", "republic of india", "given name", "surname", "nationality",
        "type p", "country code ind", "place of issue", "passport no"
    ],
    "NACH/ECS": [
        "nach", "ecs", "mandate", "national automated clearing", "umrn",
        "sponsor bank", "utility code", "ifsc", "maximum amount", "frequency", "debit type"
    ],
    "FATCA": [
        "fatca", "crs", "foreign account tax compliance", "tax residency",
        "tin", "tax identification number", "us person", "country of tax residence"
    ],
    "Benefit Illustration Declaration": [
        "benefit illustration", "guaranteed benefits", "non-guaranteed", "bi declaration",
        "sum assured", "policy term", "premium paying term", "illustrative returns", "modal premium"
    ],
    "Moral Hazard Questionnaire": [
        "moral hazard", "mhq", "confidential report", "financial underwriting",
        "proposer's income", "justification for insurance", "insured reputation", "agent's confidential"
    ],
    "Multiple Policies Consent": [
        "multiple policies", "existing policies", "previous insurance", "other policies consent",
        "concurrent policies", "total sum assured across insurers", "insurer consent"
    ],
    "Suitability Profiler": [
        "suitability profiler", "risk appetite", "investment horizon", "risk tolerance",
        "product suitability", "financial goals", "conservative", "aggressive", "moderate risk"
    ]
}


def classify_document(text: str) -> Tuple[str, float]:
    """Classifies document into one of the 10 target document types.

    Returns (document_type, classification_confidence).
    """
    if not text or len(text.strip()) < 10:
        return "Unknown / Unclassified", 0.0

    text_lower = text.lower()
    scores = {}

    for doc_type, keywords in DOC_SIGNATURES.items():
        score = 0
        for kw in keywords:
            if kw in text_lower:
                score += 1
        if score > 0:
            scores[doc_type] = score / len(keywords)

    if not scores:
        return "Unknown / Unclassified", 0.0

    best_type = max(scores, key=scores.get)
    raw_conf = scores[best_type]
    # Normalize confidence
    conf = min(0.99, max(0.40, raw_conf * 1.5))
    return best_type, round(conf, 2)


def extract_regex_with_confidence(
    pattern: str, text: str, group: int = 1, default_conf: float = 0.95
) -> Tuple[Optional[str], float]:
    """Extracts value using regex pattern and assigns a confidence score."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        val = match.group(group).strip()
        val = re.sub(r"[\r\n\t]+", " ", val)
        return val, default_conf
    return None, 0.0


def extract_key_value(
    key_pattern: str, text: str, default_conf: float = 0.85
) -> Tuple[Optional[str], float]:
    """Extracts line following a key indicator, e.g., 'Name: John Doe'."""
    pattern = rf"(?:{key_pattern})[:\s-]+([^\n\r,;|]+)"
    return extract_regex_with_confidence(pattern, text, default_conf=default_conf)


def extract_aadhaar_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Aadhaar document fields."""
    fields = {}

    # Aadhaar Number: 12 digits (often 4 4 4)
    val, conf = extract_regex_with_confidence(r"\b(\d{4}\s\d{4}\s\d{4})\b", text, default_conf=0.98)
    if not val:
        val, conf = extract_regex_with_confidence(r"\b(\d{12})\b", text, default_conf=0.85)
        if val:
            val = f"{val[:4]} {val[4:8]} {val[8:]}"
    fields["aadhaar_number"] = {"value": val, "confidence": conf}

    # Date of Birth / Year of Birth
    val, conf = extract_regex_with_confidence(r"(?:DOB|Date of Birth|Year of Birth)[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4}|[0-9]{4})", text, default_conf=0.92)
    fields["dob_or_yob"] = {"value": val, "confidence": conf}

    # Gender
    val, conf = extract_regex_with_confidence(r"\b(Male|Female|Transgender)\b", text, default_conf=0.95)
    fields["gender"] = {"value": val, "confidence": conf}

    # Name
    val, conf = extract_key_value(r"Name|To|Resident Name", text, default_conf=0.85)
    fields["name"] = {"value": val, "confidence": conf}

    # Address / Care of
    val, conf = extract_key_value(r"Address|C/O|S/O|W/O|D/O", text, default_conf=0.75)
    fields["address_or_care_of"] = {"value": val, "confidence": conf}

    return fields


def extract_pan_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts PAN card fields."""
    fields = {}

    # PAN Number: 5 letters + 4 digits + 1 letter
    val, conf = extract_regex_with_confidence(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b", text.upper(), default_conf=0.99)
    fields["pan_number"] = {"value": val, "confidence": conf}

    # Name
    val, conf = extract_key_value(r"Name|Cardholder Name", text, default_conf=0.88)
    fields["name"] = {"value": val, "confidence": conf}

    # Father's Name
    val, conf = extract_key_value(r"Father'?s?\s+Name", text, default_conf=0.88)
    fields["fathers_name"] = {"value": val, "confidence": conf}

    # Date of Birth
    val, conf = extract_regex_with_confidence(r"(?:DOB|Date of Birth)[:\s]*([0-9]{2}/[0-9]{2}/[0-9]{4})", text, default_conf=0.94)
    fields["date_of_birth"] = {"value": val, "confidence": conf}

    return fields


def extract_dl_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Driving Licence fields."""
    fields = {}

    # DL Number: usually State Code (2 letters) + digits/format
    val, conf = extract_regex_with_confidence(r"(?:DL\s*No|Licence\s*No)[:\s]*([A-Z0-9/-]{10,20})", text, default_conf=0.95)
    if not val:
        val, conf = extract_regex_with_confidence(r"\b([A-Z]{2}[0-9]{2}[0-9A-Z/-]{8,15})\b", text, default_conf=0.85)
    fields["dl_number"] = {"value": val, "confidence": conf}

    # Name
    val, conf = extract_key_value(r"Name|Driver'?s?\s+Name", text, default_conf=0.88)
    fields["name"] = {"value": val, "confidence": conf}

    # Date of Issue
    val, conf = extract_key_value(r"Date of Issue|Issue Date|Issued", text, default_conf=0.85)
    fields["date_of_issue"] = {"value": val, "confidence": conf}

    # Expiry Date / Valid Till
    val, conf = extract_key_value(r"Valid Till|Validity|Expiry Date|Expires", text, default_conf=0.85)
    fields["valid_till"] = {"value": val, "confidence": conf}

    # Vehicle Class
    val, conf = extract_regex_with_confidence(r"\b(MCWG|LMV|TRANS|MCWOG|3W-CAB)\b", text, default_conf=0.90)
    fields["vehicle_class"] = {"value": val, "confidence": conf}

    return fields


def extract_passport_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Passport fields."""
    fields = {}

    # Passport Number: 1 letter + 7 digits
    val, conf = extract_regex_with_confidence(r"\b([A-Z]{1}[0-9]{7})\b", text.upper(), default_conf=0.98)
    fields["passport_number"] = {"value": val, "confidence": conf}

    # Given Name
    val, conf = extract_key_value(r"Given Name|First Name", text, default_conf=0.88)
    fields["given_name"] = {"value": val, "confidence": conf}

    # Surname
    val, conf = extract_key_value(r"Surname|Last Name", text, default_conf=0.88)
    fields["surname"] = {"value": val, "confidence": conf}

    # Nationality
    val, conf = extract_key_value(r"Nationality", text, default_conf=0.90)
    if not val and "indian" in text.lower():
        val, conf = "INDIAN", 0.75
    fields["nationality"] = {"value": val, "confidence": conf}

    # Date of Birth
    val, conf = extract_key_value(r"Date of Birth|DOB", text, default_conf=0.90)
    fields["date_of_birth"] = {"value": val, "confidence": conf}

    # Date of Expiry
    val, conf = extract_key_value(r"Date of Expiry|Expiry Date", text, default_conf=0.90)
    fields["date_of_expiry"] = {"value": val, "confidence": conf}

    # Place of Issue
    val, conf = extract_key_value(r"Place of Issue", text, default_conf=0.85)
    fields["place_of_issue"] = {"value": val, "confidence": conf}

    return fields


def extract_nach_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts NACH/ECS Mandate fields."""
    fields = {}

    # Bank Name
    val, conf = extract_key_value(r"Bank Name|To Bank", text, default_conf=0.85)
    fields["bank_name"] = {"value": val, "confidence": conf}

    # Account Number
    val, conf = extract_regex_with_confidence(r"(?:Account Number|A/C No)[:\s]*([0-9]{9,18})", text, default_conf=0.92)
    fields["account_number"] = {"value": val, "confidence": conf}

    # IFSC Code: 4 letters + 0 + 6 alphanumeric
    val, conf = extract_regex_with_confidence(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", text.upper(), default_conf=0.98)
    fields["ifsc_code"] = {"value": val, "confidence": conf}

    # Account Type
    val, conf = extract_regex_with_confidence(r"\b(SB|Savings|Current|CA|CC)\b", text, default_conf=0.88)
    fields["account_type"] = {"value": val, "confidence": conf}

    # Maximum Amount
    val, conf = extract_key_value(r"Maximum Amount|Limit Amount|Amount ₹?|Amount Rs\.?", text, default_conf=0.85)
    fields["maximum_amount"] = {"value": val, "confidence": conf}

    # Frequency
    val, conf = extract_regex_with_confidence(r"\b(Monthly|Quarterly|Half Yearly|Yearly|As and when presented)\b", text, default_conf=0.90)
    fields["frequency"] = {"value": val, "confidence": conf}

    # Customer Name / Signatory
    val, conf = extract_key_value(r"Customer Name|Account Holder|Name of Account Holder", text, default_conf=0.85)
    fields["customer_name"] = {"value": val, "confidence": conf}

    return fields


def extract_fatca_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts FATCA Declaration fields."""
    fields = {}

    # Country of Tax Residency
    val, conf = extract_key_value(r"Country of Tax Residency|Tax Residence Country|Country of Residence", text, default_conf=0.88)
    fields["tax_residency_country"] = {"value": val, "confidence": conf}

    # Tax Identification Number (TIN)
    val, conf = extract_key_value(r"TIN|Tax Identification Number|Functional Equivalent", text, default_conf=0.90)
    fields["tin_number"] = {"value": val, "confidence": conf}

    # Place of Birth
    val, conf = extract_key_value(r"Place of Birth|City of Birth", text, default_conf=0.85)
    fields["place_of_birth"] = {"value": val, "confidence": conf}

    # Country of Birth
    val, conf = extract_key_value(r"Country of Birth", text, default_conf=0.85)
    fields["country_of_birth"] = {"value": val, "confidence": conf}

    # Occupation
    val, conf = extract_key_value(r"Occupation|Profession", text, default_conf=0.82)
    fields["occupation"] = {"value": val, "confidence": conf}

    # Politically Exposed Person (PEP)
    val, conf = extract_regex_with_confidence(r"(?:PEP|Politically Exposed Person)[:\s]*(Yes|No)", text, default_conf=0.90)
    fields["pep_status"] = {"value": val, "confidence": conf}

    return fields


def extract_benefit_illustration_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Benefit Illustration Declaration fields."""
    fields = {}

    # Policy / Plan Name
    val, conf = extract_key_value(r"Plan Name|Product Name|Policy Name", text, default_conf=0.88)
    fields["plan_name"] = {"value": val, "confidence": conf}

    # Sum Assured
    val, conf = extract_key_value(r"Sum Assured|Basic Sum Assured", text, default_conf=0.90)
    fields["sum_assured"] = {"value": val, "confidence": conf}

    # Premium Amount
    val, conf = extract_key_value(r"Installment Premium|Modal Premium|Annualised Premium|Premium Amount", text, default_conf=0.90)
    fields["premium_amount"] = {"value": val, "confidence": conf}

    # Policy Term
    val, conf = extract_key_value(r"Policy Term|PT|Term", text, default_conf=0.85)
    fields["policy_term"] = {"value": val, "confidence": conf}

    # Client / Proposer Name
    val, conf = extract_key_value(r"Client Name|Proposer Name|Life Assured", text, default_conf=0.85)
    fields["client_name"] = {"value": val, "confidence": conf}

    # Declaration Date
    val, conf = extract_key_value(r"Date|Signing Date|Illustration Date", text, default_conf=0.85)
    fields["declaration_date"] = {"value": val, "confidence": conf}

    return fields


def extract_moral_hazard_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Moral Hazard Questionnaire fields."""
    fields = {}

    # Proposer Name
    val, conf = extract_key_value(r"Proposer Name|Name of Proposer", text, default_conf=0.88)
    fields["proposer_name"] = {"value": val, "confidence": conf}

    # Life to be Assured
    val, conf = extract_key_value(r"Life to be Assured|Name of Insured|Insured Person", text, default_conf=0.88)
    fields["insured_name"] = {"value": val, "confidence": conf}

    # Annual Income
    val, conf = extract_key_value(r"Annual Income|Gross Income|Income per Annum", text, default_conf=0.90)
    fields["annual_income"] = {"value": val, "confidence": conf}

    # Occupation / Business Nature
    val, conf = extract_key_value(r"Occupation|Nature of Business|Employment", text, default_conf=0.85)
    fields["occupation"] = {"value": val, "confidence": conf}

    # Justification for Insurance
    val, conf = extract_key_value(r"Justification|Need for Insurance|Purpose of Policy", text, default_conf=0.75)
    fields["insurance_justification"] = {"value": val, "confidence": conf}

    # Underwriter Remarks
    val, conf = extract_key_value(r"Underwriter Remarks|Recommendation|Agent Remarks", text, default_conf=0.75)
    fields["underwriter_remarks"] = {"value": val, "confidence": conf}

    return fields


def extract_multiple_policies_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Multiple Policies Consent fields."""
    fields = {}

    # Existing Policy Numbers
    val, conf = extract_key_value(r"Policy Numbers?|Existing Policy Nos?|Previous Policy Numbers?", text, default_conf=0.85)
    fields["existing_policy_numbers"] = {"value": val, "confidence": conf}

    # Total Existing Sum Assured
    val, conf = extract_key_value(r"Total Sum Assured|Existing Cover Amount|Total Cover", text, default_conf=0.88)
    fields["total_existing_sum_assured"] = {"value": val, "confidence": conf}

    # Other Insurers
    val, conf = extract_key_value(r"Other Insurers?|Name of Companies|Insurer Names?", text, default_conf=0.85)
    fields["other_insurers"] = {"value": val, "confidence": conf}

    # Consent Confirmed
    val, conf = extract_regex_with_confidence(r"(?:Consent Confirmed|I Consent|Consent Given)[:\s]*(Yes|No)", text, default_conf=0.92)
    fields["consent_confirmed"] = {"value": val, "confidence": conf}

    # Declaration Date
    val, conf = extract_key_value(r"Declaration Date|Date", text, default_conf=0.85)
    fields["declaration_date"] = {"value": val, "confidence": conf}

    return fields


def extract_suitability_profiler_fields(text: str) -> Dict[str, Dict[str, Any]]:
    """Extracts Suitability Profiler fields."""
    fields = {}

    # Risk Appetite
    val, conf = extract_regex_with_confidence(r"\b(Conservative|Moderate|Aggressive|High Risk|Low Risk)\b", text, default_conf=0.92)
    fields["risk_appetite"] = {"value": val, "confidence": conf}

    # Investment Horizon
    val, conf = extract_key_value(r"Investment Horizon|Time Horizon|Duration", text, default_conf=0.85)
    fields["investment_horizon"] = {"value": val, "confidence": conf}

    # Annual Income Bracket
    val, conf = extract_key_value(r"Income Bracket|Annual Income Range|Income", text, default_conf=0.85)
    fields["income_bracket"] = {"value": val, "confidence": conf}

    # Recommended Product Category
    val, conf = extract_key_value(r"Recommended Product|Product Category|Recommended Plan", text, default_conf=0.85)
    fields["recommended_product"] = {"value": val, "confidence": conf}

    # Client Risk Score
    val, conf = extract_key_value(r"Risk Score|Suitability Score|Score", text, default_conf=0.88)
    fields["client_risk_score"] = {"value": val, "confidence": conf}

    return fields


def process_single_document(
    filename: str,
    raw_text: str,
    confidence_threshold: float = 0.70,
    mask_pii: bool = False
) -> Dict[str, Any]:
    """Processes a single document: classifies it, extracts fields, assigns confidence,

    flags low-confidence items, and structures output JSON.
    """
    doc_type, class_conf = classify_document(raw_text)

    # Dispatch to specific extractor
    extractors = {
        "Aadhaar": extract_aadhaar_fields,
        "PAN": extract_pan_fields,
        "Driving Licence": extract_dl_fields,
        "Passport": extract_passport_fields,
        "NACH/ECS": extract_nach_fields,
        "FATCA": extract_fatca_fields,
        "Benefit Illustration Declaration": extract_benefit_illustration_fields,
        "Moral Hazard Questionnaire": extract_moral_hazard_fields,
        "Multiple Policies Consent": extract_multiple_policies_fields,
        "Suitability Profiler": extract_suitability_profiler_fields,
    }

    if doc_type in extractors:
        raw_fields = extractors[doc_type](raw_text)
    else:
        # Fallback generic key-value extractor for unclassified documents
        raw_fields = {
            "document_summary": {"value": raw_text[:120].strip() if raw_text else None, "confidence": 0.50 if raw_text else 0.0}
        }

    # Annotate fields with review flags and human verification indicators
    processed_fields = {}
    review_needed_count = 0

    for fname, fdata in raw_fields.items():
        val = fdata.get("value")
        conf = fdata.get("confidence", 0.0)

        # Enforce strict null rule: if no value found, val is None and conf is 0.0
        if not val or str(val).lower() in ("null", "none", ""):
            val = None
            conf = 0.0

        is_low_conf = (conf < confidence_threshold)
        status = "Verified" if (conf >= confidence_threshold and val is not None) else ("Needs Review" if val is not None else "Not Found")

        if is_low_conf:
            review_needed_count += 1

        processed_fields[fname] = {
            "value": val,
            "confidence": round(conf, 2),
            "status": status,
            "is_low_confidence": is_low_conf
        }

    result = {
        "filename": filename,
        "document_type": doc_type,
        "classification_confidence": class_conf,
        "confidence_threshold": confidence_threshold,
        "handwriting_disclaimer": (
            "NOTICE: OCR handwriting extraction may be unreliable and subject to character distortion. "
            "All handwritten entries require mandatory secondary human verification."
        ),
        "total_fields": len(processed_fields),
        "flagged_for_human_review": review_needed_count,
        "review_required": (review_needed_count > 0 or doc_type == "Unknown / Unclassified"),
        "fields": processed_fields,
        "pii_masked": mask_pii
    }

    if mask_pii:
        result = redact_document_data(result, mask_active=True)

    return result


def render_document_processor_tab():
    """Streamlit UI renderer for Module 3."""
    st.markdown("## 🛡️ Identity & Insurance Document Processor")
    st.markdown(
        "Upload identity proofs and insurance forms for automatic classification across **10 document types**, "
        "structured field extraction, field confidence scoring, human review flagging, and sensitive PII protection."
    )

    # Handwriting Disclaimer Banner
    st.warning(
        "⚠️ **Disclaimer Regarding Scanned & Handwritten Documents:** OCR and handwriting recognition "
        "can be unreliable due to handwriting variance, scanning artifacts, and resolution constraints. "
        "Any fields flagged with confidence below the threshold must be verified by a human reviewer. "
        "Missing fields are strictly mapped to `null` without hallucination."
    )

    # Sidebar / Controls
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    with col_ctrl1:
        st.info("Supported formats: Images (PNG, JPG, JPEG), PDF, and Text files (TXT).")
    with col_ctrl2:
        conf_threshold = st.slider("Review Threshold", min_value=0.50, max_value=0.95, value=0.70, step=0.05,
                                   help="Fields with confidence below this threshold are flagged for human review.")
    with col_ctrl3:
        mask_pii = st.toggle("Mask Sensitive PII", value=True,
                             help="Safeguard sensitive numbers (Aadhaar, PAN, Bank Accounts, Passports).")

    # Document upload
    uploaded_files = st.file_uploader(
        "Upload one or more documents to process:",
        type=["png", "jpg", "jpeg", "pdf", "txt"],
        accept_multiple_files=True,
        key="doc_processor_uploader"
    )

    # Demo synthetic sample loader button
    st.markdown("---")
    col_demo, _ = st.columns([1, 2])
    with col_demo:
        load_synthetic_demo = st.button("📁 Load Synthetic Demo Package (All 10 Document Types)", use_container_width=True)

    # Process files
    results_list = []

    if uploaded_files:
        for uf in uploaded_files:
            fname = uf.name
            fname_lower = fname.lower()
            text_extracted = ""

            # Check if image
            if fname_lower.endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(uf)
                text_extracted, ocr_conf, ocr_msg = perform_ocr_on_image(img)
                if not text_extracted:
                    st.info(f"Image '{fname}': {ocr_msg}")
            else:
                uf_bytes = uf.read()
                sections, err = extract_text_from_file(uf_bytes, fname)
                if sections:
                    text_extracted = "\n".join(s["text"] for s in sections)
                elif err:
                    st.error(f"Error reading '{fname}': {err}")

            if text_extracted:
                res = process_single_document(fname, text_extracted, conf_threshold, mask_pii)
                results_list.append((fname, res, text_extracted))

    elif load_synthetic_demo:
        # Load synthetic sample files from demo_data
        import os
        synthetic_dir = os.path.join(os.path.dirname(__file__), "..", "demo_data", "synthetic_id_docs")
        if os.path.exists(synthetic_dir):
            for sfile in sorted(os.listdir(synthetic_dir)):
                if sfile.endswith(".txt"):
                    fpath = os.path.join(synthetic_dir, sfile)
                    with open(fpath, "r", encoding="utf-8") as f:
                        txt = f.read()
                    res = process_single_document(sfile, txt, conf_threshold, mask_pii)
                    results_list.append((sfile, res, txt))

    if not results_list:
        st.info("👆 Upload files above or click **'Load Synthetic Demo Package'** to test classification and extraction.")
        return

    st.success(f"Successfully processed {len(results_list)} document(s)!")

    # Summary metric cards across all documents
    total_docs = len(results_list)
    flagged_docs = sum(1 for _, r, _ in results_list if r["review_required"])
    verified_docs = total_docs - flagged_docs

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Processed Documents", total_docs)
    m2.metric("Verified Clean", verified_docs)
    m3.metric("Flagged for Review", flagged_docs)
    m4.metric("PII Masking Status", "Active 🔒" if mask_pii else "Unmasked ⚠️")

    # Display results per document
    st.markdown("### 📄 Processed Document Outputs")

    all_json_export = []

    for idx, (fname, res, raw_text) in enumerate(results_list):
        doc_type = res["document_type"]
        review_req = res["review_required"]
        flag_count = res["flagged_for_human_review"]

        status_header = f"🚨 {fname} - **{doc_type}** ({flag_count} fields need review)" if review_req else f"✅ {fname} - **{doc_type}** (Verified)"

        with st.expander(status_header, expanded=(idx == 0)):
            col_d1, col_d2 = st.columns([1, 1])

            with col_d1:
                st.markdown(f"**Document Type:** `{doc_type}`")
                st.markdown(f"**Classification Confidence:** `{int(res['classification_confidence'] * 100)}%`")
                if review_req:
                    st.error(f"⚠️ **Human Review Required:** {flag_count} field(s) have low confidence or require verification.")
                else:
                    st.success("✅ **Clean Extraction:** All mandatory fields verified above threshold.")

                # Table of Extracted Fields
                fields_table = []
                for f_name, f_info in res["fields"].items():
                    val = f_info["value"]
                    display_val = "null" if val is None else str(val)
                    fields_table.append({
                        "Field": f_name.replace("_", " ").title(),
                        "Extracted Value": display_val,
                        "Confidence": f"{int(f_info['confidence'] * 100)}%",
                        "Status": f_info["status"]
                    })

                fields_df = pd.DataFrame(fields_table)
                st.dataframe(fields_df, use_container_width=True, hide_index=True)

            with col_d2:
                st.markdown("**Structured JSON Output:**")
                st.json(res, expanded=False)

                # Raw extracted text preview
                with st.expander("Show Extracted Raw Text"):
                    st.text(raw_text[:1200] + ("..." if len(raw_text) > 1200 else ""))

        all_json_export.append(res)

    # Batch JSON Download button
    st.markdown("---")
    json_bytes = json.dumps(all_json_export, indent=2).encode("utf-8")
    st.download_button(
        label="📥 Download Structured JSON Output (All Documents)",
        data=json_bytes,
        file_name="processed_insurance_documents.json",
        mime="application/json",
        use_container_width=True
    )
