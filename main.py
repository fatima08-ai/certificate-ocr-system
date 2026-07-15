from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import shutil
import os
from fastapi import UploadFile, File, HTTPException
from app.core.ocr_engine import extract_text
from app.core.extractor import extract_fields

app = FastAPI(title="Certificate OCR System")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".pdf"}

import pytesseract

@app.post("/extract")
async def extract_certificate(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a JPG, PNG, or TIFF image."
        )
    if file.size == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty. Please select a valid file.")

    save_path = f"uploads/{file.filename}"
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save the uploaded file. Please try again.")

    try:
        ocr_result = extract_text(save_path)
        raw_text = ocr_result["text"]
        confidence = ocr_result["confidence"]
    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="OCR engine not found on the server. Please contact the administrator."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    try:
        structured_data = extract_fields(raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Field extraction failed: {str(e)}")

    return {
        "filename": file.filename,
        "raw_text": raw_text,
        "confidence": confidence,
        "extracted_fields": structured_data
    }