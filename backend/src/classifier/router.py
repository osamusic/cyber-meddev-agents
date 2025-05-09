from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import os

from ..db.database import get_db
from ..db.models import Document as DBDocument, ClassificationResult as DBClassificationResult
from ..auth.auth import get_current_active_user, get_current_admin_user
from ..auth.models import User
from .models import ClassificationRequest, ClassificationConfig, ClassificationResult
from .classifier import DocumentClassifier

router = APIRouter(
    prefix="/classifier",
    tags=["classifier"],
    responses={404: {"description": "Not found"}},
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

classifier = DocumentClassifier()

@router.post("/classify", response_model=ClassificationResult)
async def classify_documents(
    request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """ドキュメントを分類（管理者のみ）"""
    logger.info(f"AUDIT LOG: {{'action': 'classify_documents', 'timestamp': {datetime.now()}, 'user_id': {current_user.id}, 'details': 'Classification requested for {len(request.document_ids)} documents', 'ip_address': '{current_user.last_login_ip}'}}")
    
    documents = []
    
    if request.all_documents:
        documents = db.query(DBDocument).all()
    elif request.document_ids:
        documents = db.query(DBDocument).filter(DBDocument.id.in_(request.document_ids)).all()
    elif request.section_ids:
        documents = db.query(DBDocument).filter(DBDocument.section_id.in_(request.section_ids)).all()
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No documents found for classification"
        )
    
    background_tasks.add_task(
        classify_documents_background,
        documents=[doc.id for doc in documents],
        config=ClassificationConfig(),
        user_id=current_user.id,
        db=db
    )
    
    return ClassificationResult(
        processed_count=len(documents),
        categories_count={},
        frameworks=["NIST_CSF", "IEC_62443"]
    )

@router.get("/results/{document_id}", response_model=Dict[str, Any])
async def get_classification_results(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """ドキュメントの分類結果を取得"""
    document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    classification = db.query(DBClassificationResult).filter(
        DBClassificationResult.document_id == document_id
    ).order_by(DBClassificationResult.created_at.desc()).first()
    
    if not classification:
        return {
            "document_id": document_id,
            "title": document.title,
            "status": "not_classified",
            "message": "This document has not been classified yet"
        }
    
    try:
        result = json.loads(classification.result_json)
        return {
            "document_id": document_id,
            "title": document.title,
            "status": "classified",
            "created_at": classification.created_at,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error parsing classification result: {str(e)}")
        return {
            "document_id": document_id,
            "title": document.title,
            "status": "error",
            "message": "Error parsing classification result"
        }

@router.get("/stats", response_model=Dict[str, Any])
async def get_classification_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """分類統計情報を取得"""
    total_documents = db.query(DBDocument).count()
    classified_documents = db.query(DBDocument).join(
        DBClassificationResult, DBDocument.id == DBClassificationResult.document_id
    ).distinct().count()
    
    nist_stats = {
        "ID": 0, "PR": 0, "DE": 0, "RS": 0, "RC": 0
    }
    
    iec_stats = {
        "FR1": 0, "FR2": 0, "FR3": 0, "FR4": 0, "FR5": 0, "FR6": 0, "FR7": 0
    }
    
    latest_classifications = db.query(DBClassificationResult).order_by(
        DBClassificationResult.document_id, DBClassificationResult.created_at.desc()
    ).all()
    
    document_ids = set()
    for classification in latest_classifications:
        if classification.document_id in document_ids:
            continue
        
        document_ids.add(classification.document_id)
        
        try:
            result = json.loads(classification.result_json)
            
            if "frameworks" in result and "NIST_CSF" in result["frameworks"]:
                nist_result = result["frameworks"]["NIST_CSF"]
                if "primary_category" in nist_result and nist_result["primary_category"] in nist_stats:
                    nist_stats[nist_result["primary_category"]] += 1
            
            if "frameworks" in result and "IEC_62443" in result["frameworks"]:
                iec_result = result["frameworks"]["IEC_62443"]
                if "primary_requirement" in iec_result and iec_result["primary_requirement"] in iec_stats:
                    iec_stats[iec_result["primary_requirement"]] += 1
        except Exception as e:
            logger.error(f"Error parsing classification result: {str(e)}")
    
    return {
        "total_documents": total_documents,
        "classified_documents": classified_documents,
        "classification_percentage": round(classified_documents / total_documents * 100, 2) if total_documents > 0 else 0,
        "nist_categories": nist_stats,
        "iec_requirements": iec_stats
    }

async def classify_documents_background(
    documents: List[int],
    config: ClassificationConfig,
    user_id: int,
    db: Session
):
    """バックグラウンドでドキュメントを分類"""
    logger.info(f"Starting background classification for {len(documents)} documents")
    
    for doc_id in documents:
        try:
            document = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
            if not document:
                logger.warning(f"Document {doc_id} not found")
                continue
            
            classification_result = classifier.classify_document(document.content, config)
            
            db_classification = DBClassificationResult(
                document_id=doc_id,
                user_id=user_id,
                result_json=json.dumps(classification_result),
                created_at=datetime.now()
            )
            
            db.add(db_classification)
            db.commit()
            
            logger.info(f"Classification completed for document {doc_id}")
        except Exception as e:
            logger.error(f"Error classifying document {doc_id}: {str(e)}")
            db.rollback()
    
    logger.info(f"Background classification completed for all documents")
