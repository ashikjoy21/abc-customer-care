from fastapi import APIRouter, HTTPException, Query
from .schemas import RequestCreate, RequestOut, StatusUpdate, HistoryEntry
from .repository import create_request, list_requests, update_request_status, get_history

router = APIRouter(prefix="/api/v1/requests")

@router.post("", response_model=RequestOut)
def create_request_endpoint(payload: RequestCreate):
    try:
        row = create_request(payload)
        return row
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=list[RequestOut])
def list_requests_endpoint(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    try:
        return list_requests(limit=limit, offset=offset)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{request_id}/status", response_model=RequestOut)
def update_status_endpoint(request_id: int, payload: StatusUpdate):
    try:
        row = update_request_status(request_id, payload)
        return row
    except ValueError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="Request not found")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{request_id}/history", response_model=list[HistoryEntry])
def history_endpoint(request_id: int):
    return get_history(request_id)
