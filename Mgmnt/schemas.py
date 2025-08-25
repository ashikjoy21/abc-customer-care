from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

RequestType = Literal["Renew","Renew with Bill","Change Password","Check Status","Check MAC"]
RequestStatus = Literal["pending","assigned","in_progress","resolved","cancelled"]
Priority = Literal["low","medium","high","urgent"]

class RequestCreate(BaseModel):
    customer_id: int
    type: RequestType
    requested_by: str
    description: Optional[str] = None
    priority: Priority = "medium"

class RequestOut(BaseModel):
    id: int
    customer_id: int
    type: str
    requested_by: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str
    priority: Optional[str] = None
    description: Optional[str] = None
    result_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class StatusUpdate(BaseModel):
    status: RequestStatus
    assigned_to: Optional[str] = None
    result_notes: Optional[str] = None
    notes: Optional[str] = None

class HistoryEntry(BaseModel):
    id: int
    request_id: int
    event: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
