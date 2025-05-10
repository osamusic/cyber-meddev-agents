from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ClassificationRequest(BaseModel):
    """Request to classify document sections"""
    section_ids: List[str] = []
    document_ids: List[str] = []
    all_documents: bool = False


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

    class Config:
        from_attributes = True
