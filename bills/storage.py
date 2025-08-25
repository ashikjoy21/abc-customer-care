import os
import hashlib
import json
from datetime import datetime
from typing import Optional
from .schemas import BillMetadata

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("BILLS_BUCKET_NAME", "bills")
_client = None

def _get_client():
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase credentials missing")
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def _md5(b: bytes) -> str:
    h = hashlib.md5()
    h.update(b)
    return h.hexdigest()

def _public_url(path: str) -> Optional[str]:
    c = _get_client()
    try:
        r = c.storage.from_(BUCKET).get_public_url(path)
        if isinstance(r, dict):
            return r.get("data", {}).get("publicUrl")
    except Exception:
        return None
    return None

ALLOWED_EXT = {"pdf": "pdf", "jpg": "jpg", "jpeg": "jpg", "png": "png"}

def upload_bill(recharge_id: str, filename: str, content_type: str, data: bytes) -> BillMetadata:
    c = _get_client()
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXT:
        raise ValueError("Unsupported file type")
    norm_ext = ALLOWED_EXT[ext]
    stored_name = f"bill.{norm_ext}"
    bill_path = f"{recharge_id}/{stored_name}"
    meta_path = f"{recharge_id}/metadata.json"
    checksum = _md5(data)
    c.storage.from_(BUCKET).upload(path=bill_path, file=data, file_options={"content-type": content_type, "upsert": "true"})
    uploaded_at = datetime.utcnow()
    meta = BillMetadata(recharge_id=recharge_id, filename=stored_name, content_type=content_type, size_bytes=len(data), storage_bucket=BUCKET, storage_path=bill_path, file_url=_public_url(bill_path), uploaded_at=uploaded_at, checksum_md5=checksum)
    c.storage.from_(BUCKET).upload(path=meta_path, file=json.dumps(meta.model_dump()).encode("utf-8"), file_options={"content-type": "application/json", "upsert": "true"})
    return meta

def fetch_metadata(recharge_id: str) -> Optional[BillMetadata]:
    c = _get_client()
    meta_path = f"{recharge_id}/metadata.json"
    try:
        raw = c.storage.from_(BUCKET).download(meta_path)
        if not raw:
            return None
        data = json.loads(raw.decode("utf-8"))
        data["file_url"] = _public_url(data.get("storage_path", ""))
        return BillMetadata(**data)
    except Exception:
        return None

def fetch_bill_file(recharge_id: str) -> Optional[tuple[str, str, bytes]]:
    meta = fetch_metadata(recharge_id)
    if not meta:
        return None
    c = _get_client()
    try:
        b = c.storage.from_(meta.storage_bucket).download(meta.storage_path)
        return meta.filename, meta.content_type, b
    except Exception:
        return None
