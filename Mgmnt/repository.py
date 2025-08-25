import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from .schemas import RequestCreate, StatusUpdate

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
_client = None

def _get_client():
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase credentials missing")
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def create_request(payload: RequestCreate) -> Dict[str, Any]:
    c = _get_client()
    data = payload.model_dump()
    res = c.table("requests").insert(data).execute()
    row = res.data[0]
    _insert_history(row["id"], "created", None, row.get("status","pending"), payload.description)
    return row

def list_requests(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    c = _get_client()
    start = offset
    end = offset + limit - 1
    res = c.table("requests").select("*").order("created_at", desc=True).range(start, end).execute()
    return res.data or []

def update_request_status(request_id: int, upd: StatusUpdate) -> Dict[str, Any]:
    c = _get_client()
    current = c.table("requests").select("id,status").eq("id", request_id).single().execute().data
    if not current:
        raise ValueError("not_found")
    update_data = {"status": upd.status, "updated_at": datetime.utcnow().isoformat()}
    if upd.assigned_to is not None:
        update_data["assigned_to"] = upd.assigned_to
    if upd.result_notes is not None:
        update_data["result_notes"] = upd.result_notes
    res = c.table("requests").update(update_data).eq("id", request_id).execute()
    row = res.data[0]
    _insert_history(request_id, "status_change", current.get("status"), upd.status, upd.notes or upd.result_notes)
    return row

def _insert_history(request_id: int, event: str, from_status: Optional[str], to_status: Optional[str], notes: Optional[str]):
    c = _get_client()
    try:
        c.table("request_history").insert({"request_id": request_id, "event": event, "from_status": from_status, "to_status": to_status, "notes": notes}).execute()
    except Exception:
        pass

def get_history(request_id: int):
    c = _get_client()
    try:
        res = c.table("request_history").select("*").eq("request_id", request_id).order("created_at", desc=False).execute()
        return res.data or []
    except Exception:
        return []
