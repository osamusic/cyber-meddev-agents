from .classifier import DocumentClassifier
from .models import ClassificationRequest, ClassificationConfig, ClassificationResult
from ..auth.models import User
from ..auth.auth import get_current_active_user, get_current_admin_user
from ..db.models import DocumentModel as DBDocument, ClassificationResult as DBClassificationResult
from ..db.database import get_db, SessionLocal
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import partial

# Use a single thread by default (increase max_workers if needed)
executor = ThreadPoolExecutor(max_workers=1)

# Track classification progress
classification_progress = {
    "total_documents": 0,
    "processed_documents": 0,
    "status": "idle",  # idle, initializing, in_progress, completed, error
    "started_at": None,
    "completed_at": None
}

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
    classification_request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Classify documents (admin only)"""
    client_host = request.client.host if request.client else "unknown"
    log_entry = {
        "action": "classify_documents",
        "timestamp": datetime.utcnow(),
        "user_id": current_user.id,
        "details": f"Classification requested for {len(classification_request.document_ids)} documents",
        "ip_address": client_host
    }
    logger.info(f"AUDIT LOG: {log_entry}")

    documents = []
    already_classified = []

    # Determine which documents to classify
    if classification_request.all_documents:
        if classification_request.reclassify:
            documents = db.query(DBDocument).all()
        else:
            subq = db.query(DBClassificationResult.document_id).distinct().subquery()
            documents = db.query(DBDocument).filter(~DBDocument.id.in_(db.query(subq.c.document_id))).all()
    elif classification_request.document_ids:
        for doc_id in classification_request.document_ids:
            doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
            if not doc:
                continue
            existing = db.query(DBClassificationResult).filter(
                DBClassificationResult.document_id == doc_id
            ).first()
            if existing and not classification_request.reclassify:
                already_classified.append(doc.title or f"Document {doc_id}")
            else:
                documents.append(doc)
    elif classification_request.section_ids:
        documents = db.query(DBDocument).filter(DBDocument.id.in_(classification_request.section_ids)).all()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No documents found for classification"
        )

    # Launch background task
    task_fn = partial(
        classify_documents_background,
        [doc.id for doc in documents],
        ClassificationConfig(),
        current_user.id
    )
    asyncio.get_event_loop().run_in_executor(executor, task_fn)

    # Initialize progress tracking
    global classification_progress
    classification_progress = {
        "total_documents": len(documents),
        "processed_documents": 0,
        "status": "initializing",
        "started_at": datetime.utcnow(),
        "completed_at": None
    }

    message = None
    if already_classified:
        message = (
            "The following documents were skipped because they have already been classified: " + ", ".join(already_classified)
        )

    return ClassificationResult(
        processed_count=len(documents),
        categories_count={},
        frameworks=["NIST_CSF", "IEC_62443"],
        skipped_documents=already_classified,
        message=message,
        total_count=len(documents),
        current_count=0,
        status="initializing"
    )


@router.get("/results/{document_id}", response_model=Dict[str, Any])
async def get_classification_results(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve classification result for a single document"""
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
        logger.error(f"Error parsing classification result: {e}")
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
    """Retrieve classification statistics"""
    total_documents = db.query(DBDocument).count()
    classified_documents = db.query(DBDocument).join(
        DBClassificationResult, DBDocument.id == DBClassificationResult.document_id
    ).distinct().count()

    nist_stats = {"ID": 0, "PR": 0, "DE": 0, "RS": 0, "RC": 0}
    iec_stats = {"FR1": 0, "FR2": 0, "FR3": 0, "FR4": 0, "FR5": 0, "FR6": 0, "FR7": 0}

    latest = db.query(DBClassificationResult).order_by(
        DBClassificationResult.document_id, DBClassificationResult.created_at.desc()
    ).all()

    seen = set()
    for cls in latest:
        if cls.document_id in seen:
            continue
        seen.add(cls.document_id)
        try:
            res = json.loads(cls.result_json)
            nist = res.get("frameworks", {}).get("NIST_CSF", {})
            primary_nist = nist.get("primary_category")
            if primary_nist in nist_stats:
                nist_stats[primary_nist] += 1

            iec = res.get("frameworks", {}).get("IEC_62443", {})
            primary_iec = iec.get("primary_requirement")
            if primary_iec in iec_stats:
                iec_stats[primary_iec] += 1
        except Exception as e:
            logger.error(f"Error parsing classification result: {e}")

    return {
        "total_documents": total_documents,
        "classified_documents": classified_documents,
        "classification_percentage": round(classified_documents / total_documents * 100, 2) if total_documents > 0 else 0,
        "nist_categories": nist_stats,
        "iec_requirements": iec_stats
    }


@router.get("/all", response_model=List[Dict[str, Any]])
async def get_all_classifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve all latest classification results"""
    logger.info("Retrieving all classification results")

    subq = db.query(
        DBClassificationResult.document_id,
        DBClassificationResult.id.label("latest_id")
    ).distinct(
        DBClassificationResult.document_id
    ).order_by(
        DBClassificationResult.document_id,
        DBClassificationResult.created_at.desc()
    ).subquery()

    classifications = db.query(DBClassificationResult).join(
        subq, DBClassificationResult.id == subq.c.latest_id
    ).all()

    results = []
    for cls in classifications:
        try:
            doc = db.query(DBDocument).filter(DBDocument.id == cls.document_id).first()
            if not doc:
                continue

            data = json.loads(cls.result_json)
            entry = {
                "id": cls.id,
                "document_id": cls.document_id,
                "document_title": doc.title or "Unknown Document",
                "source_url": getattr(doc, "source_url", ""),
                "created_at": cls.created_at.isoformat(),
                "requirements": data.get("requirements", []),
                "keywords": data.get("keywords", []),
            }

            if "frameworks" in data:
                nist = data["frameworks"].get("NIST_CSF", {})
                entry["nist"] = {
                    "primary_category": nist.get("primary_category", ""),
                    "categories": nist.get("categories", {}),
                    "explanation": nist.get("explanation", "")
                }
                iec = data["frameworks"].get("IEC_62443", {})
                entry["iec"] = {
                    "primary_requirement": iec.get("primary_requirement", ""),
                    "requirements": iec.get("requirements", {}),
                    "explanation": iec.get("explanation", "")
                }

            results.append(entry)
        except Exception as e:
            logger.error(f"Error processing classification result: {e}")

    logger.info(f"Number of classification results retrieved: {len(results)}")
    return results


def classify_documents_background(
    documents: List[int],
    config: ClassificationConfig,
    user_id: int
):
    """Classify documents in the background"""
    logger.info(f"Starting background classification for {len(documents)} documents")

    db = SessionLocal()
    try:
        classification_progress["status"] = "in_progress"

        for idx, doc_id in enumerate(documents):
            try:
                document = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
                if not document:
                    logger.warning(f"Document {doc_id} not found")
                    continue

                classification_result = classifier.classify_document(document.content, config)

                db_entry = DBClassificationResult(
                    document_id=doc_id,
                    user_id=user_id,
                    result_json=json.dumps(classification_result),
                    created_at=datetime.now()
                )
                db.add(db_entry)
                db.commit()

                classification_progress["processed_documents"] = idx + 1
                logger.info(f"Classification completed for document {doc_id} ({idx + 1}/{len(documents)})")
            except Exception as e:
                logger.error(f"Error classifying document {doc_id}: {e}")
                db.rollback()

        classification_progress["status"] = "completed"
        classification_progress["completed_at"] = datetime.utcnow()
    finally:
        db.close()
        logger.info("Background classification completed for all documents")


@router.get("/progress", response_model=ClassificationResult)
async def get_classification_progress(
    current_user: User = Depends(get_current_active_user),
):
    """Get current classification progress"""
    return ClassificationResult(
        processed_count=classification_progress["total_documents"],
        categories_count={},
        frameworks=["NIST_CSF", "IEC_62443"],
        total_count=classification_progress["total_documents"],
        current_count=classification_progress["processed_documents"],
        status=classification_progress["status"]
    )
