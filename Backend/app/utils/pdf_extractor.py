import io
import logging
from pypdf import PdfReader
from app.schemas.material import _validate_text_content

logger = logging.getLogger("skillsetu.pdf_extractor")

# Maximum allowed PDF file size: 10 MB
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def extract_text_from_pdf_bytes(pdf_bytes: bytes, filename: str = "upload.pdf") -> str:
    """
    Validates and extracts readable text from PDF raw bytes using pypdf.

    Validation steps:
    1. File size check  — rejects PDFs > 10 MB
    2. Extension guard  — enforced at router level (here as a safety net)
    3. Pypdf extraction — raises ValueError for scanned/image PDFs with no text
    4. Content rules    — delegates to _validate_text_content:
                          min 50 words, max 15000, must be real alphabetic text
    """
    # --- Guard 1: File size ---
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        size_mb = round(len(pdf_bytes) / (1024 * 1024), 2)
        raise ValueError(
            f"PDF file is too large ({size_mb} MB). "
            "Please upload a PDF under 10 MB."
        )

    # --- Guard 2: Must have at least some bytes ---
    if len(pdf_bytes) == 0:
        raise ValueError("Uploaded file is empty. Please upload a valid PDF document.")

    # --- Guard 3: Pypdf text extraction ---
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        if len(reader.pages) == 0:
            raise ValueError("The uploaded PDF has no pages.")

        extracted_text = ""
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text += f"\n--- Page {page_num + 1} ---\n" + text

    except ValueError:
        raise  # re-raise our own validation errors
    except Exception as e:
        logger.error(f"Failed to parse PDF '{filename}': {e}")
        raise ValueError(
            "Could not read the PDF file. It may be corrupted, password-protected, "
            "or in an unsupported format. Please try a different file."
        )

    # --- Guard 4: Content quality validation (same rules as text-paste) ---
    # _validate_text_content raises ValueError with a clear message if content is invalid
    validated_text = _validate_text_content(
        extracted_text,
        field_name=f"PDF content ('{filename}')"
    )

    return validated_text

