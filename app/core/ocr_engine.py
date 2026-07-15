import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from app.core.preprocessor import preprocess_image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\poppler-26.02.0\Library\bin'

def extract_text(file_path: str) -> str:
    """Extract raw text from an image or PDF using Tesseract OCR."""
    if file_path.lower().endswith(".pdf"):
        pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, config='--psm 6') + "\n"
        return text
    else:
        processed_path = preprocess_image(file_path)
        image = Image.open(processed_path)
        return pytesseract.image_to_string(image, config='--psm 6')