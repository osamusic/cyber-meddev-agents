from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LogEntry(BaseModel):
    id: int
    action: str
    timestamp: datetime
    user_id: int
    details: Optional[str] = None
    ip_address: Optional[str] = None
    
    class Config:
        orm_mode = True

class DocumentInfo(BaseModel):
    id: int
    doc_id: str
    title: str
    source_type: str
    downloaded_at: datetime
    url: str
    
    class Config:
        orm_mode = True

class DeleteConfirmation(BaseModel):
    confirmed: bool
