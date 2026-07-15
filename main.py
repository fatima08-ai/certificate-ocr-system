from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import shutil
import os
import io
import pytesseract
from openpyxl import Workbook
from app.core.ocr_engine import extract_text
from app.core.extractor import extract_fields
from app.models.database import init_db, get_db, CertificateRecord
from typing import List

app = FastAPI(title="Certificate OCR System")
templates = Jinja2Templates(directory="templates")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".pdf"}


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/extract")
async def extract_certificate(file: UploadFile = File(...), db: Session = Depends(get_db)):
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

    record = CertificateRecord(
        filename=file.filename,
        candidate_name=structured_data.get("candidate_name"),
        certificate_title=structured_data.get("certificate_title"),
        organization=structured_data.get("organization"),
        issue_date=structured_data.get("issue_date"),
        certificate_number=structured_data.get("certificate_number"),
        confidence=str(confidence),
        raw_text=raw_text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "filename": file.filename,
        "raw_text": raw_text,
        "confidence": confidence,
        "extracted_fields": structured_data
    }


@app.get("/results/{record_id}")
async def get_result(record_id: int, db: Session = Depends(get_db)):
    record = db.query(CertificateRecord).filter(CertificateRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"No record found with id {record_id}")

    return {
        "id": record.id,
        "filename": record.filename,
        "extracted_fields": {
            "candidate_name": record.candidate_name,
            "certificate_title": record.certificate_title,
            "organization": record.organization,
            "issue_date": record.issue_date,
            "certificate_number": record.certificate_number,
        },
        "confidence": record.confidence,
        "created_at": record.created_at.isoformat(),
    }


@app.delete("/documents/{record_id}")
async def delete_document(record_id: int, db: Session = Depends(get_db)):
    record = db.query(CertificateRecord).filter(CertificateRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"No record found with id {record_id}")

    db.delete(record)
    db.commit()
    return {"message": f"Record {record_id} deleted successfully"}


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
@app.post("/extract-batch")
async def extract_batch(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Process multiple certificates in a single request."""
    results = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": f"Unsupported file type '{ext}'"
            })
            continue

        save_path = f"uploads/{file.filename}"
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            ocr_result = extract_text(save_path)
            raw_text = ocr_result["text"]
            confidence = ocr_result["confidence"]
            structured_data = extract_fields(raw_text)

            record = CertificateRecord(
                filename=file.filename,
                candidate_name=structured_data.get("candidate_name"),
                certificate_title=structured_data.get("certificate_title"),
                organization=structured_data.get("organization"),
                issue_date=structured_data.get("issue_date"),
                certificate_number=structured_data.get("certificate_number"),
                confidence=str(confidence),
                raw_text=raw_text,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            results.append({
                "id": record.id,
                "filename": file.filename,
                "success": True,
                "confidence": confidence,
                "extracted_fields": structured_data
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })

    return {"results": results}