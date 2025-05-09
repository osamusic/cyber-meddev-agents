from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Optional

from ..db.database import get_db
from ..db.models import Guideline as GuidelineModel, GuidelineKeyword
from ..auth.auth import get_current_active_user
from .models import Guideline, GuidelineSearch

router = APIRouter(
    prefix="/guidelines",
    tags=["ガイドライン"],
    dependencies=[Depends(get_current_active_user)]
)

@router.get("/", response_model=List[Guideline])
async def get_guidelines(
    category: Optional[str] = None,
    standard: Optional[str] = None,
    region: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: SQLAlchemySession = Depends(get_db)
):
    """Get guidelines with optional filtering"""
    query = db.query(GuidelineModel)
    
    if category:
        query = query.filter(GuidelineModel.category == category)
    if standard:
        query = query.filter(GuidelineModel.standard == standard)
    if region:
        query = query.filter(GuidelineModel.region == region)
    
    guidelines = query.offset(skip).limit(limit).all()
    
    result = []
    for guideline in guidelines:
        keywords = [kw.keyword for kw in guideline.keywords]
        guideline_dict = {
            "id": guideline.id,
            "guideline_id": guideline.guideline_id,
            "category": guideline.category,
            "standard": guideline.standard,
            "control_text": guideline.control_text,
            "source_url": guideline.source_url,
            "region": guideline.region,
            "keywords": keywords
        }
        result.append(guideline_dict)
    
    return result

@router.get("/categories")
async def get_categories(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique categories"""
    categories = db.query(GuidelineModel.category).distinct().all()
    return [category[0] for category in categories]

@router.get("/standards")
async def get_standards(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique standards"""
    standards = db.query(GuidelineModel.standard).distinct().all()
    return [standard[0] for standard in standards]

@router.get("/regions")
async def get_regions(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique regions"""
    regions = db.query(GuidelineModel.region).distinct().all()
    return [region[0] for region in regions]

@router.post("/search", response_model=List[Guideline])
async def search_guidelines(
    search: GuidelineSearch,
    db: SQLAlchemySession = Depends(get_db)
):
    """Search guidelines by text and optional filters"""
    query = db.query(GuidelineModel).filter(
        GuidelineModel.control_text.contains(search.query)
    )
    
    if search.category:
        query = query.filter(GuidelineModel.category == search.category)
    if search.standard:
        query = query.filter(GuidelineModel.standard == search.standard)
    if search.region:
        query = query.filter(GuidelineModel.region == search.region)
    
    guidelines = query.all()
    
    result = []
    for guideline in guidelines:
        keywords = [kw.keyword for kw in guideline.keywords]
        guideline_dict = {
            "id": guideline.id,
            "guideline_id": guideline.guideline_id,
            "category": guideline.category,
            "standard": guideline.standard,
            "control_text": guideline.control_text,
            "source_url": guideline.source_url,
            "region": guideline.region,
            "keywords": keywords
        }
        result.append(guideline_dict)
    
    return result
