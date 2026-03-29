"""
TenderBot Global — PDF Parsing Service
Extracts text from uploaded PDF documents.
"""
import fitz  # PyMuPDF
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_pdf(content: bytes) -> Optional[str]:
    """
    Extracts plain text from a PDF file provided as bytes.
    """
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=content, filetype="pdf")
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
            
        doc.close()
        
        if not full_text.strip():
            logger.warning("Extracted PDF text is empty.")
            return None
            
        return full_text
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return None
