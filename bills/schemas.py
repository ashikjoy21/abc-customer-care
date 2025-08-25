from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class BillMetadata(BaseModel):
    recharge_id: str = Field(...)
    filename: str
    content_type: str
    size_bytes: int
    storage_bucket: str
    storage_path: str
    file_url: Optional[HttpUrl] = None
    uploaded_at: datetime
    checksum_md5: Optional[str] = None
