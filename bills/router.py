from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from .storage import upload_bill, fetch_metadata, fetch_bill_file

router = APIRouter(prefix="/api/v1/bills")

MAX_SIZE = 5 * 1024 * 1024
ALLOWED_CT = {"application/pdf", "image/png", "image/jpeg"}

@router.post("/upload")
async def upload_bill_endpoint(recharge_id: str = Form(...), file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(status_code=400, detail="Unsupported content type")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    try:
        meta = upload_bill(recharge_id, file.filename, file.content_type, data)
        return meta
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Upload failed")

@router.get("/{bill_id}")
async def get_bill_metadata(bill_id: str):
    meta = fetch_metadata(bill_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Bill not found")
    return meta

@router.get("/{bill_id}/download")
async def download_bill(bill_id: str):
    f = fetch_bill_file(bill_id)
    if not f:
        raise HTTPException(status_code=404, detail="Bill not found")
    filename, ct, data = f
    return StreamingResponse(iter([data]), media_type=ct, headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})
