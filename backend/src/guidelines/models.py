from pydantic import BaseModel
from typing import List, Optional


class GuidelineBase(BaseModel):
    category: str
    standard: str
    control_text: str
    source_url: str
    region: str


class GuidelineCreate(GuidelineBase):
    guideline_id: str
    keywords: List[str]


class Guideline(GuidelineBase):
    id: int
    guideline_id: str
    keywords: List[str]

    class Config:
        from_attributes = True


class GuidelineSearch(BaseModel):
    query: str
    category: Optional[str] = None
    standard: Optional[str] = None
    region: Optional[str] = None
