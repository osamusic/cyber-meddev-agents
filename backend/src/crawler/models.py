from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CrawlTarget(BaseModel):
    """Target URL for crawling with configuration"""
    url: str
    mime_filters: List[str] = ["application/pdf", "text/html", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    depth: int = 2
    name: Optional[str] = None
    
class Document(BaseModel):
    """Document extracted from crawling"""
    doc_id: str
    url: str
    title: str
    content: str
    source_type: str  # "PDF", "HTML", "DOCX"
    downloaded_at: datetime
    lang: str
