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


executor = ThreadPoolExecutor(max_workers=1)  # 同時1スレッドで制御（必要なら増やす）


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
    """ドキュメントを分類（管理者のみ）"""
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
    already_classified_docs = []

    if classification_request.all_documents:
        classified_doc_ids = db.query(DBClassificationResult.document_id).distinct().subquery()
        documents = db.query(DBDocument).filter(
            ~DBDocument.id.in_(db.query(classified_doc_ids.c.document_id))
        ).all()
    elif classification_request.document_ids:
        for doc_id in classification_request.document_ids:
            doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
            if not doc:
                continue

            existing_classification = db.query(DBClassificationResult).filter(
                DBClassificationResult.document_id == doc_id
            ).first()

            if existing_classification:
                already_classified_docs.append(doc.title or f"Document {doc_id}")
            else:
                documents.append(doc)
    elif classification_request.section_ids:
        documents = db.query(DBDocument).filter(DBDocument.id.in_(classification_request.section_ids)).all()

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No documents found for classification"
        )

    task_fn = partial(
        classify_documents_background,
        [doc.id for doc in documents],
        ClassificationConfig(),
        current_user.id
    )
    asyncio.get_event_loop().run_in_executor(executor, task_fn)

    global classification_progress
    classification_progress = {
        "total_documents": len(documents),
        "processed_documents": 0,
        "status": "initializing",
        "started_at": datetime.utcnow(),
        "completed_at": None
    }

    message = None
    if already_classified_docs:
        message = f"次のドキュメントは既に分類されているためスキップされました: {', '.join(already_classified_docs)}"

    return ClassificationResult(
        processed_count=len(documents),
        categories_count={},
        frameworks=["NIST_CSF", "IEC_62443"],
        skipped_documents=already_classified_docs,
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


@router.get("/all", response_model=List[Dict[str, Any]])
async def get_all_classifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """すべての分類結果を取得"""
    logger.info("すべての分類結果を取得中")

    subquery = db.query(
        DBClassificationResult.document_id,
        DBClassificationResult.id.label("latest_id")
    ).distinct(
        DBClassificationResult.document_id
    ).order_by(
        DBClassificationResult.document_id,
        DBClassificationResult.created_at.desc()
    ).subquery()

    classifications = db.query(DBClassificationResult).join(
        subquery,
        DBClassificationResult.id == subquery.c.latest_id
    ).all()

    results = []
    for classification in classifications:
        try:
            document = db.query(DBDocument).filter(DBDocument.id == classification.document_id).first()
            if not document:
                continue

            result_json = json.loads(classification.result_json)

            classification_data = {
                "id": classification.id,
                "document_id": classification.document_id,
                "document_title": document.title if document else "不明なドキュメント",
                "source_url": document.source_url if document and hasattr(document, 'source_url') else "",
                "created_at": classification.created_at.isoformat(),
                "summary": result_json.get("summary", ""),
                "keywords": result_json.get("keywords", []),
            }

            if "frameworks" in result_json and "NIST_CSF" in result_json["frameworks"]:
                nist_data = result_json["frameworks"]["NIST_CSF"]
                classification_data["nist"] = {
                    "primary_category": nist_data.get("primary_category", ""),
                    "categories": nist_data.get("categories", {}),
                    "explanation": nist_data.get("explanation", "")
                }

            if "frameworks" in result_json and "IEC_62443" in result_json["frameworks"]:
                iec_data = result_json["frameworks"]["IEC_62443"]
                classification_data["iec"] = {
                    "primary_requirement": iec_data.get("primary_requirement", ""),
                    "requirements": iec_data.get("requirements", {}),
                    "explanation": iec_data.get("explanation", "")
                }

            results.append(classification_data)
        except Exception as e:
            logger.error(f"分類結果の解析エラー: {str(e)}")

    logger.info(f"取得した分類結果: {len(results)}件")
    return results


def classify_documents_background(
    documents: List[int],
    config: ClassificationConfig,
    user_id: int
):
    """バックグラウンドでドキュメントを分類"""
    logger.info(f"Starting background classification for {len(documents)} documents")

    db = SessionLocal()
    try:
        # Update status to in_progress
        global classification_progress
        classification_progress["status"] = "in_progress"

        for idx, doc_id in enumerate(documents):
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

                classification_progress["processed_documents"] = idx + 1

                logger.info(f"Classification completed for document {doc_id} ({idx + 1}/{len(documents)})")
            except Exception as e:
                logger.error(f"Error classifying document {doc_id}: {str(e)}")
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
    """ドキュメント分類の進捗状況を取得"""
    global classification_progress

    return ClassificationResult(
        processed_count=classification_progress["total_documents"],
        categories_count={},
        frameworks=["NIST_CSF", "IEC_62443"],
        total_count=classification_progress["total_documents"],
        current_count=classification_progress["processed_documents"],
        status=classification_progress["status"]
    )
