from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Optional, Dict, Any
import json
import logging

from ..db.database import get_db
from ..db.models import Guideline as GuidelineModel, GuidelineKeyword, ClassificationResult
from ..auth.auth import get_current_active_user, get_admin_user
from .models import Guideline, GuidelineSearch, GuidelineCreate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/guidelines",
    tags=["guidelines"],
    dependencies=[Depends(get_current_active_user)]  # All authenticated users can access
)


def _get_classification_data(guideline_id: int, db: SQLAlchemySession) -> Optional[Dict[str, Any]]:
    """Retrieve classification data for a guideline"""
    try:
        classification = (
            db.query(ClassificationResult)
              .filter(ClassificationResult.document_id == guideline_id)
              .order_by(ClassificationResult.created_at.desc())
              .first()
        )
        if not classification:
            return None

        result = json.loads(classification.result_json)
        data: Dict[str, Any] = {
            "created_at": classification.created_at.isoformat(),
            "requirements": result.get("requirements", []),
            "keywords": result.get("keywords", []),
        }
        # Include NIST primary category if available
        nist = result.get("frameworks", {}).get("NIST_CSF", {})
        if nist:
            data["nist"] = nist.get("primary_category")
        # Include IEC primary requirement if available
        iec = result.get("frameworks", {}).get("IEC_62443", {})
        if iec:
            data["iec"] = iec.get("primary_requirement")
        return data
    except Exception as e:
        logger.error(f"Error fetching classification data for guideline {guideline_id}: {e}")
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
    """Retrieve guidelines with optional filters"""
    query = db.query(GuidelineModel)
    if category:
        query = query.filter(GuidelineModel.category == category)
    if standard:
        query = query.filter(GuidelineModel.standard == standard)
    if region:
        query = query.filter(GuidelineModel.region == region)

    guidelines = query.offset(skip).limit(limit).all()
    results: List[Dict[str, Any]] = []
    for g in guidelines:
        keywords = [kw.keyword for kw in g.keywords]
        item = {
            "id": g.id,
            "guideline_id": g.guideline_id,
            "category": g.category,
            "standard": g.standard,
            "control_text": g.control_text,
            "source_url": g.source_url,
            "region": g.region,
            "keywords": keywords
        }
        data = _get_classification_data(g.id, db)
        if data:
            item["classification"] = data
        results.append(item)
    return results


@router.get("/categories")
async def get_categories(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique guideline categories"""
    logger.info("Fetching guideline categories")
    categories = db.query(GuidelineModel.category).distinct().all()
    result = [c[0] for c in categories if c[0]]
    logger.info(f"Categories fetched: {result}")
    return result


@router.get("/standards")
async def get_standards(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique guideline standards"""
    logger.info("Fetching guideline standards")
    standards = db.query(GuidelineModel.standard).distinct().all()
    result = [s[0] for s in standards if s[0]]
    logger.info(f"Standards fetched: {result}")
    return result


@router.get("/regions")
async def get_regions(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique guideline regions"""
    logger.info("Fetching guideline regions")
    regions = db.query(GuidelineModel.region).distinct().all()
    result = [r[0] for r in regions if r[0]]
    logger.info(f"Regions fetched: {result}")
    return result


@router.post("/search", response_model=List[Guideline])
async def search_guidelines(search: GuidelineSearch, db: SQLAlchemySession = Depends(get_db)):
    """Search guidelines by text and filters"""
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
    results: List[Dict[str, Any]] = []
    for g in guidelines:
        keywords = [kw.keyword for kw in g.keywords]
        item = {
            "id": g.id,
            "guideline_id": g.guideline_id,
            "category": g.category,
            "standard": g.standard,
            "control_text": g.control_text,
            "source_url": g.source_url,
            "region": g.region,
            "keywords": keywords
        }
        data = _get_classification_data(g.id, db)
        if data:
            item["classification"] = data
        results.append(item)
    return results


@router.post("/", response_model=Guideline)
async def create_guideline(
    guideline: GuidelineCreate,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)  # Admins only
):
    """Create a new guideline (admin only)"""
    client_ip = request.client.host if request.client else "unknown"
    existing = (
        db.query(GuidelineModel)
          .filter(GuidelineModel.guideline_id == guideline.guideline_id)
          .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guideline ID '{guideline.guideline_id}' already exists"
        )

    db_g = GuidelineModel(
        guideline_id=guideline.guideline_id,
        category=guideline.category,
        standard=guideline.standard,
        control_text=guideline.control_text,
        source_url=guideline.source_url,
        region=guideline.region
    )
    db.add(db_g)
    db.flush()  # Get generated ID
    for kw in guideline.keywords:
        db.add(GuidelineKeyword(guideline_id=db_g.id, keyword=kw))

    logger.info(f"AUDIT LOG: {{'action':'create_guideline','user_id':{current_user.id},'guideline_id':'{guideline.guideline_id}','ip_address':'{client_ip}'}}")
    try:
        db.commit()
        logger.info(f"Guideline '{guideline.guideline_id}' created successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating guideline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create guideline: {e}"
        )

    return {
        "id": db_g.id,
        "guideline_id": db_g.guideline_id,
        "category": db_g.category,
        "standard": db_g.standard,
        "control_text": db_g.control_text,
        "source_url": db_g.source_url,
        "region": db_g.region,
        "keywords": [kw.keyword for kw in db_g.keywords]
    }


@router.put("/{guideline_id}", response_model=Guideline)
async def update_guideline(
    guideline_id: str,
    guideline: GuidelineCreate,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)  # Admins only
):
    """Update an existing guideline (admin only)"""
    client_ip = request.client.host if request.client else "unknown"
    db_g = (
        db.query(GuidelineModel)
          .filter(GuidelineModel.guideline_id == guideline_id)
          .first()
    )
    if not db_g:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guideline ID '{guideline_id}' not found"
        )
    db_g.category = guideline.category
    db_g.standard = guideline.standard
    db_g.control_text = guideline.control_text
    db_g.source_url = guideline.source_url
    db_g.region = guideline.region
    db.query(GuidelineKeyword).filter(GuidelineKeyword.guideline_id == db_g.id).delete()
    for kw in guideline.keywords:
        db.add(GuidelineKeyword(guideline_id=db_g.id, keyword=kw))

    logger.info(f"AUDIT LOG: {{'action':'update_guideline','user_id':{current_user.id},'guideline_id':'{guideline_id}','ip_address':'{client_ip}'}}")
    try:
        db.commit()
        logger.info(f"Guideline '{guideline_id}' updated successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating guideline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update guideline: {e}"
        )

    return {
        "id": db_g.id,
        "guideline_id": db_g.guideline_id,
        "category": db_g.category,
        "standard": db_g.standard,
        "control_text": db_g.control_text,
        "source_url": db_g.source_url,
        "region": db_g.region,
        "keywords": [kw.keyword for kw in db_g.keywords]
    }


@router.delete("/{guideline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guideline(
    guideline_id: str,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)  # Admins only
):
    """Delete a guideline (admin only)"""
    client_ip = request.client.host if request.client else "unknown"
    db_g = (
        db.query(GuidelineModel)
          .filter(GuidelineModel.guideline_id == guideline_id)
          .first()
    )
    if not db_g:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guideline ID '{guideline_id}' not found"
        )
    db.query(GuidelineKeyword).filter(GuidelineKeyword.guideline_id == db_g.id).delete()
    db.delete(db_g)
    logger.info(f"AUDIT LOG: {{'action':'delete_guideline','user_id':{current_user.id},'guideline_id':'{guideline_id}','ip_address':'{client_ip}'}}")
    try:
        db.commit()
        logger.info(f"Guideline '{guideline_id}' deleted successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting guideline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete guideline: {e}"
        )
    return None
