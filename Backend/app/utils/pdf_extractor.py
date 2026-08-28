import io
import logging
from pypdf import PdfReader

logger = logging.getLogger("skillsetu.pdf_extractor")

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts readable text from PDF raw bytes using pypdf.
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        extracted_text = ""
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text += f"\n--- Page {page_num + 1} ---\n" + text
                
        cleaned = extracted_text.strip()
        if not cleaned:
            raise ValueError("No extractable text found in PDF document (may be scanned image/scanned PDF).")
            
        return cleaned
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        raise ValueError(f"Could not parse PDF content: {str(e)}")
