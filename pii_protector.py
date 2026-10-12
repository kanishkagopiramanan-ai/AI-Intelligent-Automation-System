"""PII (Personally Identifiable Information) Protector.

Provides masking, redaction, and compliance-friendly safeguards for sensitive
identity cards (Aadhaar, PAN, Passport, Driving Licence) and financial data
(Bank Account, IFSC, NACH mandates, FATCA TINs).
"""

import re
from typing import Any, Dict, Union


def mask_aadhaar(aadhaar_str: Union[str, None]) -> Union[str, None]:
    """Mask first 8 digits of a 12-digit Aadhaar number as per UIDAI norms.

    Example: '1234 5678 9012' -> 'XXXX-XXXX-9012'
    """
    if not aadhaar_str:
        return None
    clean = re.sub(r"[^0-9]", "", str(aadhaar_str))
    if len(clean) == 12:
        return f"XXXX-XXXX-{clean[-4:]}"
    elif len(clean) > 4:
        return "X" * (len(clean) - 4) + clean[-4:]
    return aadhaar_str


def mask_pan(pan_str: Union[str, None]) -> Union[str, None]:
    """Mask first 5 characters of a 10-character PAN card number.

    Example: 'ABCDE1234F' -> 'XXXXX1234F'
    """
    if not pan_str:
        return None
    clean = str(pan_str).strip().upper()
    if len(clean) == 10:
        return f"XXXXX{clean[5:]}"
    elif len(clean) > 4:
        return "X" * (len(clean) - 4) + clean[-4:]
    return pan_str


def mask_bank_account(account_str: Union[str, None]) -> Union[str, None]:
    """Mask bank account number leaving only the last 4 digits visible.

    Example: '123456789012' -> 'XXXXXXXX9012'
    """
    if not account_str:
        return None
    clean = re.sub(r"[^0-9A-Za-z]", "", str(account_str))
    if len(clean) > 4:
        return ("X" * (len(clean) - 4)) + clean[-4:]
    return account_str


def mask_passport(passport_str: Union[str, None]) -> Union[str, None]:
    """Mask passport number leaving only first letter and last 3 digits.

    Example: 'A1234567' -> 'A****567'
    """
    if not passport_str:
        return None
    clean = str(passport_str).strip().upper()
    if len(clean) >= 6:
        return clean[0] + ("*" * (len(clean) - 4)) + clean[-3:]
    return passport_str


def mask_driving_licence(dl_str: Union[str, None]) -> Union[str, None]:
    """Mask driving licence number leaving only state code and last 4 digits.

    Example: 'DL1420110012345' -> 'DL-XXXX-XXXX-2345'
    """
    if not dl_str:
        return None
    clean = re.sub(r"[^0-9A-Za-z]", "", str(dl_str))
    if len(clean) >= 8:
        prefix = clean[:2]
        suffix = clean[-4:]
        return f"{prefix}-XXXX-XXXX-{suffix}"
    return dl_str


def mask_phone(phone_str: Union[str, None]) -> Union[str, None]:
    """Mask contact phone numbers leaving only last 4 digits visible."""
    if not phone_str:
        return None
    clean = re.sub(r"[^0-9]", "", str(phone_str))
    if len(clean) >= 10:
        return f"XXXXXX{clean[-4:]}"
    return phone_str


def mask_tin(tin_str: Union[str, None]) -> Union[str, None]:
    """Mask tax identification number leaving only last 4 digits."""
    if not tin_str:
        return None
    clean = str(tin_str).strip()
    if len(clean) > 4:
        return ("*" * (len(clean) - 4)) + clean[-4:]
    return tin_str


def mask_field_value(field_name: str, value: Any) -> Any:
    """Smart field masking based on the semantic field name."""
    if value is None or str(value).lower() in ("null", "none", ""):
        return None

    val_str = str(value)
    name_lower = field_name.lower()

    if "aadhaar" in name_lower:
        return mask_aadhaar(val_str)
    elif "pan" in name_lower or "permanent_account_number" in name_lower:
        return mask_pan(val_str)
    elif "account_number" in name_lower or "acc_no" in name_lower or "bank_account" in name_lower:
        return mask_bank_account(val_str)
    elif "passport" in name_lower:
        return mask_passport(val_str)
    elif "dl_number" in name_lower or "driving_licence" in name_lower or "licence_number" in name_lower:
        return mask_driving_licence(val_str)
    elif "tin" in name_lower or "tax_id" in name_lower:
        return mask_tin(val_str)
    elif "phone" in name_lower or "mobile" in name_lower:
        return mask_phone(val_str)

    return value


def redact_document_data(data: Dict[str, Any], mask_active: bool = True) -> Dict[str, Any]:
    """Applies PII redaction to a nested document dictionary or extraction structure."""
    if not mask_active:
        return data

    redacted = {}
    for key, val in data.items():
        if isinstance(val, dict):
            # Check if this is an extracted field with structure {"value": ..., "confidence": ...}
            if "value" in val:
                copy_val = dict(val)
                copy_val["value"] = mask_field_value(key, copy_val["value"])
                redacted[key] = copy_val
            else:
                redacted[key] = redact_document_data(val, mask_active=True)
        elif isinstance(val, list):
            redacted[key] = [
                redact_document_data(item, mask_active=True) if isinstance(item, dict) else item
                for item in val
            ]
        else:
            redacted[key] = mask_field_value(key, val)
    return redacted
