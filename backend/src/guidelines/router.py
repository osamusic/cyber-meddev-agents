from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Optional, Dict, Any
import json
import logging

from ..db.database import get_db
from ..db.models import Guideline as GuidelineModel, GuidelineKeyword, ClassificationResult
from ..auth.auth import get_current_active_user
from .models import Guideline, GuidelineSearch

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/guidelines",
    tags=["ガイドライン"],
    dependencies=[Depends(get_current_active_user)]
)

def get_classification_data(guideline_id: int, db: SQLAlchemySession) -> Optional[Dict[str, Any]]:
    """Get classification data for a guideline"""
    try:
        classification = db.query(ClassificationResult).filter(
            ClassificationResult.document_id == guideline_id
        ).order_by(ClassificationResult.created_at.desc()).first()
        
        if not classification:
            return None
        
        result = json.loads(classification.result_json)
        
        classification_data = {
            "created_at": classification.created_at.isoformat(),
            "summary": result.get("summary", ""),
            "keywords": result.get("keywords", []),
        }
        
        if "frameworks" in result and "NIST_CSF" in result["frameworks"]:
            nist_data = result["frameworks"]["NIST_CSF"]
            classification_data["nist"] = nist_data.get("primary_category")
        
        if "frameworks" in result and "IEC_62443" in result["frameworks"]:
            iec_data = result["frameworks"]["IEC_62443"]
            classification_data["iec"] = iec_data.get("primary_requirement")
        
        return classification_data
    except Exception as e:
        logger.error(f"Error getting classification data for guideline {guideline_id}: {str(e)}")
        return None

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
        
        classification_data = get_classification_data(guideline.id, db)
        if classification_data:
            guideline_dict["classification"] = classification_data
            
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
        
        classification_data = get_classification_data(guideline.id, db)
        if classification_data:
            guideline_dict["classification"] = classification_data
            
        result.append(guideline_dict)
    
    return result
