"""Unit tests for Module 3: Identity & Insurance Document Processor."""

import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.document_processor import (
    classify_document,
    process_single_document,
)
from utils.pii_protector import (
    mask_aadhaar,
    mask_pan,
    mask_bank_account,
    mask_passport,
    mask_driving_licence,
    redact_document_data,
)


class TestDocumentProcessor(unittest.TestCase):
    def test_pii_masking_functions(self):
        # Aadhaar: first 8 digits masked
        self.assertEqual(mask_aadhaar("1234 5678 9012"), "XXXX-XXXX-9012")
        self.assertEqual(mask_aadhaar("123456789012"), "XXXX-XXXX-9012")

        # PAN: first 5 chars masked
        self.assertEqual(mask_pan("ABCPK4829D"), "XXXXX4829D")

        # Bank Account: only last 4 visible
        self.assertEqual(mask_bank_account("50100294829104"), "XXXXXXXXXX9104")

        # Passport: first letter and last 3 visible
        self.assertEqual(mask_passport("Z4829104"), "Z****104")

        # Driving Licence: state code and last 4 visible
        self.assertEqual(mask_driving_licence("HR2620150049281"), "HR-XXXX-XXXX-9281")

    def test_classification_all_10_types(self):
        samples = {
            "Aadhaar": "Government of India Unique Identification Authority of India UIDAI Mera Aadhaar 4892 7301 9542",
            "PAN": "Income Tax Department Govt. of India Permanent Account Number Card PAN ABCPK4829D",
            "Driving Licence": "Union of India Transport Department Driving Licence Authorisation to Drive LMV DL No: HR2620150049281",
            "Passport": "Passport Republic of India Type P Country Code IND Passport No: Z4829104 Given Name Rajesh",
            "NACH/ECS": "National Automated Clearing House NACH ECS Mandate UMRN IFSC Bank Name HDFC Maximum Amount",
            "FATCA": "Foreign Account Tax Compliance Act FATCA CRS Tax Residency TIN Country of Tax Residence",
            "Benefit Illustration Declaration": "Benefit Illustration Declaration Guaranteed Benefits Sum Assured Policy Term Modal Premium",
            "Moral Hazard Questionnaire": "Confidential Underwriting Report Moral Hazard Questionnaire MHQ Proposer's Income Justification for Insurance",
            "Multiple Policies Consent": "Declaration of Multiple Policies Concurrent Policies Total Sum Assured Across Insurers Consent Confirmed: Yes",
            "Suitability Profiler": "Suitability Profiler Risk Appetite Moderate Investment Horizon 10 Years Product Suitability Score"
        }

        for expected_type, text in samples.items():
            doc_type, conf = classify_document(text)
            self.assertEqual(doc_type, expected_type, f"Failed for {expected_type}, got {doc_type}")
            self.assertGreater(conf, 0.40)

    def test_process_document_with_missing_fields_strict_null(self):
        # Text with missing fields should strictly return None (null), not invented strings
        sparse_text = "Income Tax Department Permanent Account Number PAN Card PAN ABCPK4829D"
        res = process_single_document("test_pan.txt", sparse_text, confidence_threshold=0.70)

        self.assertEqual(res["document_type"], "PAN")
        fields = res["fields"]
        self.assertEqual(fields["pan_number"]["value"], "ABCPK4829D")
        self.assertEqual(fields["pan_number"]["status"], "Verified")

        # Father's name and DOB are missing in sparse_text -> must be strictly None (null)
        self.assertIsNone(fields["fathers_name"]["value"])
        self.assertEqual(fields["fathers_name"]["confidence"], 0.0)
        self.assertEqual(fields["fathers_name"]["status"], "Not Found")
        self.assertTrue(fields["fathers_name"]["is_low_confidence"])

    def test_human_review_flagging(self):
        sparse_text = "UIDAI Aadhaar Enrolment Date of Birth: 1988"
        res = process_single_document("test_aadhaar.txt", sparse_text, confidence_threshold=0.70)
        self.assertTrue(res["review_required"])
        self.assertGreater(res["flagged_for_human_review"], 0)

    def test_pii_redaction_mode(self):
        text = "Income Tax Department Permanent Account Number PAN: ABCPK4829D Name: Rajesh Sharma"
        res = process_single_document("test.txt", text, mask_pii=True)
        # PAN should be masked in fields output
        self.assertEqual(res["fields"]["pan_number"]["value"], "XXXXX4829D")


if __name__ == "__main__":
    unittest.main()
