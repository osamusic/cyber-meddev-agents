from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime

from ..db.database import get_db
from ..db.models import Guideline as GuidelineModel, GuidelineKeyword, ClassificationResult
from ..auth.auth import get_current_active_user, get_admin_user
from .models import Guideline, GuidelineSearch, GuidelineCreate

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
    logger.info("カテゴリー一覧を取得中")
    categories = db.query(GuidelineModel.category).distinct().all()
    result = [cat[0] for cat in categories if cat[0]]
    logger.info(f"取得したカテゴリー: {result}")
    return result

@router.get("/standards")
async def get_standards(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique standards"""
    logger.info("標準規格一覧を取得中")
    standards = db.query(GuidelineModel.standard).distinct().all()
    result = [std[0] for std in standards if std[0]]
    logger.info(f"取得した標準規格: {result}")
    return result

@router.get("/regions")
async def get_regions(db: SQLAlchemySession = Depends(get_db)):
    """Get all unique regions"""
    logger.info("地域一覧を取得中")
    regions = db.query(GuidelineModel.region).distinct().all()
    result = [reg[0] for reg in regions if reg[0]]
    logger.info(f"取得した地域: {result}")
    return result

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

@router.post("/", response_model=Guideline)
async def create_guideline(
    guideline: GuidelineCreate,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user = Depends(get_admin_user)  # 管理者のみがガイドラインを作成可能
):
    """ガイドラインを作成（管理者のみ）"""
    client_host = request.client.host if request.client else "unknown"
    
    existing = db.query(GuidelineModel).filter(GuidelineModel.guideline_id == guideline.guideline_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ガイドラインID '{guideline.guideline_id}' は既に存在します"
        )
    
    db_guideline = GuidelineModel(
        guideline_id=guideline.guideline_id,
        category=guideline.category,
        standard=guideline.standard,
        control_text=guideline.control_text,
        source_url=guideline.source_url,
        region=guideline.region
    )
    
    db.add(db_guideline)
    db.flush()  # IDを取得するためにフラッシュする
    
    for keyword in guideline.keywords:
        keyword_obj = GuidelineKeyword(
            guideline_id=db_guideline.id,
            keyword=keyword
        )
        db.add(keyword_obj)
    
    log_entry = {
        "action": "guideline_create",
        "timestamp": datetime.utcnow(),
        "user_id": current_user.id,
        "details": f"Guideline {guideline.guideline_id} created",
        "ip_address": client_host
    }
    logger.info(f"AUDIT LOG: {log_entry}")
    
    try:
        db.commit()
        logger.info(f"ガイドライン '{guideline.guideline_id}' を作成しました")
    except Exception as e:
        db.rollback()
        logger.error(f"ガイドライン作成エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ガイドライン作成中にエラーが発生しました: {str(e)}"
        )
    
    keywords = [kw.keyword for kw in db_guideline.keywords]
    
    return {
        "id": db_guideline.id,
        "guideline_id": db_guideline.guideline_id,
        "category": db_guideline.category,
        "standard": db_guideline.standard,
        "control_text": db_guideline.control_text,
        "source_url": db_guideline.source_url,
        "region": db_guideline.region,
        "keywords": keywords
    }
@router.put("/{guideline_id}", response_model=Guideline)
async def update_guideline(
    guideline_id: str,
    guideline: GuidelineCreate,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user = Depends(get_admin_user)  # 管理者のみがガイドラインを更新可能
):
    """ガイドラインを更新（管理者のみ）"""
    client_host = request.client.host if request.client else "unknown"
    
    db_guideline = db.query(GuidelineModel).filter(GuidelineModel.guideline_id == guideline_id).first()
    if not db_guideline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ガイドラインID '{guideline_id}' が見つかりません"
        )
    
    db_guideline.category = guideline.category
    db_guideline.standard = guideline.standard
    db_guideline.control_text = guideline.control_text
    db_guideline.source_url = guideline.source_url
    db_guideline.region = guideline.region
    
    db.query(GuidelineKeyword).filter(GuidelineKeyword.guideline_id == db_guideline.id).delete()
    
    for keyword in guideline.keywords:
        keyword_obj = GuidelineKeyword(
            guideline_id=db_guideline.id,
            keyword=keyword
        )
        db.add(keyword_obj)
    
    log_entry = {
        "action": "guideline_update",
        "timestamp": datetime.utcnow(),
        "user_id": current_user.id,
        "details": f"Guideline {guideline_id} updated",
        "ip_address": client_host
    }
    logger.info(f"AUDIT LOG: {log_entry}")
    
    try:
        db.commit()
        logger.info(f"ガイドライン '{guideline_id}' を更新しました")
    except Exception as e:
        db.rollback()
        logger.error(f"ガイドライン更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ガイドライン更新中にエラーが発生しました: {str(e)}"
        )
    
    keywords = [kw.keyword for kw in db_guideline.keywords]
    
    return {
        "id": db_guideline.id,
        "guideline_id": db_guideline.guideline_id,
        "category": db_guideline.category,
        "standard": db_guideline.standard,
        "control_text": db_guideline.control_text,
        "source_url": db_guideline.source_url,
        "region": db_guideline.region,
        "keywords": keywords
    }
