import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from backend.core.config import settings

# Configure Tesseract path from settings
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image using Tesseract OCR.
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"Error processing image: {str(e)}"

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file by first converting pages to images,
    then running OCR on each image.
    """
    try:
        # Note: poppler_path is required on Windows
        images = convert_from_path(pdf_path, poppler_path=settings.POPPLER_PATH)
        full_text = ""
        
        for i, image in enumerate(images):
            full_text += f"\n--- Page {i+1} ---\n"
            text = pytesseract.image_to_string(image)
            full_text += text
            
        return full_text
    except Exception as e:
        return f"Error processing PDF: {str(e)}\n\nMake sure Poppler is installed and configured correctly."

def process_document(file_path: str) -> str:
    """
    Determines file type and routes to appropriate extraction function.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."
        
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        return extract_text_from_image(file_path)
    else:
        return f"Error: Unsupported file format '{ext}'."
