from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import shutil
import os
from fastapi import UploadFile, File, HTTPException
from app.core.ocr_engine import extract_text

app = FastAPI(title="Certificate OCR System")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff"}

@app.post("/extract")
async def extract_certificate(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text = extract_text(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    return {"filename": file.filename, "raw_text": raw_text}