from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ClassificationRequest(BaseModel):
    """Request to classify document sections"""
    section_ids: List[int] = []
    document_ids: List[int] = []
    all_documents: bool = False
    reclassify: bool = False  # 既に分類済みのドキュメントを再分類するかどうか


class KeywordExtractionConfig(BaseModel):
    """Configuration for keyword extraction"""
    min_keyword_length: int = 3
    max_keywords: int = 10


class ClassificationConfig(BaseModel):
    """Configuration for classification"""
    frameworks: List[str] = ["NIST_CSF", "IEC_62443"]
    keyword_config: KeywordExtractionConfig = KeywordExtractionConfig()


class ClassificationResult(BaseModel):
    """Result of classification operation"""
    processed_count: int
    categories_count: Dict[str, Any]
    frameworks: List[str]
    skipped_documents: List[str] = []
    message: Optional[str] = None
    total_count: int = 0
    current_count: int = 0
    status: str = "initializing"  # initializing, in_progress, completed, error

    class Config:
        from_attributes = True
