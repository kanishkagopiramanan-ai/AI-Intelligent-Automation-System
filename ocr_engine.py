"""OCR (Optical Character Recognition) Engine.

Supports scanned image and document text extraction using Tesseract OCR,
with graceful status detection and Windows path discovery.
"""

import io
import os
import shutil
from typing import Optional, Tuple, Union
from PIL import Image

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


# Common Tesseract installation paths on Windows
COMMON_WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]


def find_tesseract_executable() -> Optional[str]:
    """Finds the tesseract executable on Windows or system PATH."""
    if not HAS_PYTESSERACT:
        return None

    # Check if already in PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # Check known Windows install paths
    for path in COMMON_WINDOWS_TESSERACT_PATHS:
        if os.path.exists(path):
            return path

    return None


def is_tesseract_available() -> Tuple[bool, str]:
    """Checks whether Tesseract OCR is available and configured.

    Returns (is_available, status_message).
    """
    if not HAS_PYTESSERACT:
        return False, "pytesseract Python library is not installed (`pip install pytesseract`)."

    tess_path = find_tesseract_executable()
    if tess_path:
        try:
            pytesseract.pytesseract.tesseract_cmd = tess_path
            version = pytesseract.get_tesseract_version()
            return True, f"Tesseract OCR is active (version {version}) at `{tess_path}`."
        except Exception as e:
            return False, f"Tesseract found at `{tess_path}` but failed to execute: {str(e)}"

    return False, (
        "Tesseract OCR engine binary is not installed in Windows PATH. "
        "For scanned physical image OCR, install Tesseract via: "
        "`winget install UB-Mannheim.TesseractOCR` or download from GitHub. "
        "(Text-based PDFs and TXT documents do not require Tesseract)."
    )


def perform_ocr_on_image(
    image_bytes_or_file: Union[bytes, io.BytesIO, Image.Image]
) -> Tuple[str, float, str]:
    """Extracts text from an image using OCR with confidence estimation.

    Returns (extracted_text, average_confidence, notice_message).
    """
    available, msg = is_tesseract_available()
    if not available:
        return "", 0.0, msg

    try:
        if isinstance(image_bytes_or_file, Image.Image):
            pil_img = image_bytes_or_file
        elif isinstance(image_bytes_or_file, bytes):
            pil_img = Image.open(io.BytesIO(image_bytes_or_file))
        else:
            pil_img = Image.open(image_bytes_or_file)

        # Ensure image is in RGB or Grayscale mode for OCR
        if pil_img.mode not in ("L", "RGB"):
            pil_img = pil_img.convert("RGB")

        # Run pytesseract data extraction for word-level confidence
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
        extracted_words = []
        confidences = []

        for word, conf in zip(data["text"], data["conf"]):
            clean_word = str(word).strip()
            try:
                numeric_conf = float(conf)
            except (ValueError, TypeError):
                numeric_conf = -1.0

            if clean_word and numeric_conf >= 0:
                extracted_words.append(clean_word)
                confidences.append(numeric_conf)

        if not extracted_words:
            # Fallback to standard string extraction
            raw_text = pytesseract.image_to_string(pil_img).strip()
            return raw_text, 0.50 if raw_text else 0.0, "Extracted using basic OCR mode."

        combined_text = " ".join(extracted_words)
        avg_conf = (sum(confidences) / len(confidences)) / 100.0 if confidences else 0.50

        return combined_text, round(avg_conf, 2), "OCR extraction completed successfully."

    except Exception as e:
        return "", 0.0, f"OCR processing failed: {str(e)}"
