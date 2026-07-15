from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, UploadFile, File, HTTPException
import shutil
import os
import io
import pytesseract
from openpyxl import Workbook
from app.core.ocr_engine import extract_text
from app.core.extractor import extract_fields

app = FastAPI(title="Certificate OCR System")
templates = Jinja2Templates(directory="templates")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".pdf"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/extract")
async def extract_certificate(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a JPG, PNG, TIFF, or PDF."
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


@app.post("/export")
async def export_to_excel(file: UploadFile = File(...)):
    """Extract certificate data and return it as a downloadable Excel file."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    save_path = f"uploads/{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        ocr_result = extract_text(save_path)
        structured_data = extract_fields(ocr_result["text"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    wb = Workbook()
    ws = wb.active
    ws.title = "Certificate Data"

    ws.append(["Field", "Value"])
    for key, value in structured_data.items():
        clean_key = key.replace("_", " ").title()
        ws.append([clean_key, value if value else "Not found"])

    for column_cells in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column_cells)
        col_letter = column_cells[0].column_letter
        ws.column_dimensions[col_letter].width = max_length + 4

    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=extracted_{file.filename}.xlsx"}
    )