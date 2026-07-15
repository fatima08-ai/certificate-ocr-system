import pytesseract
from PIL import Image
from app.core.preprocessor import preprocess_image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(image_path: str) -> str:
    processed_path = preprocess_image(image_path)
    image = Image.open(processed_path)
    text = pytesseract.image_to_string(image, config='--psm 6')
    return text