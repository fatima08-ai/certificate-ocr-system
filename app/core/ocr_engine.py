import pytesseract
from pytesseract import Output
from PIL import Image
from pdf2image import convert_from_path
from app.core.preprocessor import preprocess_image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\poppler-26.02.0\Library\bin'

def _get_text_and_confidence(image) -> tuple[str, float]:
    """Run OCR on a single image, returning extracted text and average word confidence."""
    data = pytesseract.image_to_data(image, config='--psm 6', output_type=Output.DICT)
    text = pytesseract.image_to_string(image, config='--psm 6')

    confidences = [int(c) for c in data['conf'] if int(c) != -1]
    avg_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0

    return text, avg_confidence

def extract_text(file_path: str) -> dict:
    """Extract raw text and OCR confidence from an image or PDF."""
    if file_path.lower().endswith(".pdf"):
        pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        full_text = ""
        all_confidences = []
        for page in pages:
            text, conf = _get_text_and_confidence(page)
            full_text += text + "\n"
            all_confidences.append(conf)
        avg_confidence = round(sum(all_confidences) / len(all_confidences), 1) if all_confidences else 0.0
        return {"text": full_text, "confidence": avg_confidence}
    else:
        processed_path = preprocess_image(file_path)
        image = Image.open(processed_path)
        text, confidence = _get_text_and_confidence(image)
        return {"text": text, "confidence": confidence}