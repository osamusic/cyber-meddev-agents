from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CrawlTarget(BaseModel):
    """Target URL for crawling with configuration"""
    url: str
    mime_filters: List[str] = ["application/pdf", "text/html", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    depth: int = 2
    name: Optional[str] = None
    update_existing: bool = True  # 既存のドキュメントを更新するかスキップするか
    max_document_size: Optional[int] = None  # ドキュメント分割の最大サイズ（文字数）
    
class Document(BaseModel):
    """Document extracted from crawling"""
    doc_id: str
    url: str
    title: str
    content: str
    source_type: str  # "PDF", "HTML", "DOCX"
    downloaded_at: datetime
    lang: str
