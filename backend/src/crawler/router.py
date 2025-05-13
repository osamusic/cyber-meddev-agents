from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List
from datetime import datetime
import logging

from ..db.database import get_db
from ..db.models import DocumentModel
from ..auth.auth import get_admin_user
from .models import CrawlTarget, Document
from .crawler import Crawler

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/crawler",
    tags=["クローラー"],
    dependencies=[Depends(get_admin_user)]  # 管理者のみがアクセス可能
)


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_crawler(
    target: CrawlTarget,
    background_tasks: BackgroundTasks,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """クローラーを実行する（管理者のみ）"""
    client_host = request.client.host if request.client else "unknown"

    log_entry = {
        "action": "crawler_run",
        "timestamp": datetime.utcnow(),
        "user_id": current_user.id,
        "details": f"Crawler started for URL {target.url} with depth {target.depth}",
        "ip_address": client_host
    }
    logger.info(f"AUDIT LOG: {log_entry}")

    background_tasks.add_task(
        run_crawler_task,
        target=target,
        db=db,
        user_id=current_user.id
    )

    return {
        "message": "クローラーが開始されました",
        "target": target.dict(),
        "status": "processing"
    }


@router.get("/status", response_model=List[Document])
async def get_crawler_status(
    limit: int = 10,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """最近クロールされたドキュメントのステータスを取得する（管理者のみ）"""
    recent_documents = db.query(DocumentModel).order_by(
        DocumentModel.downloaded_at.desc()
    ).limit(limit).all()

    return [
        Document(
            doc_id=doc.doc_id,
            url=doc.url,
            title=doc.title,
            original_title=doc.original_title if doc.original_title else doc.title,
            content=doc.content,
            source_type=doc.source_type,
            downloaded_at=doc.downloaded_at,
            lang=doc.lang
        ) for doc in recent_documents
    ]


def run_crawler_task(target: CrawlTarget, db: SQLAlchemySession, user_id: int):
    """バックグラウンドでクローラーを実行するタスク"""
    try:
        crawler = Crawler(db=db)  # データベースセッションをクローラーに渡す
        documents = crawler.crawl(target)

        for doc in documents:
            existing_doc = db.query(DocumentModel).filter(
                DocumentModel.doc_id == doc.doc_id
            ).first()

            if existing_doc:
                existing_doc.title = doc.title
                existing_doc.original_title = doc.original_title
                existing_doc.content = doc.content
                existing_doc.downloaded_at = doc.downloaded_at
            else:
                db_doc = DocumentModel(
                    doc_id=doc.doc_id,
                    url=doc.url,
                    title=doc.title,
                    original_title=doc.original_title,
                    content=doc.content,
                    source_type=doc.source_type,
                    downloaded_at=doc.downloaded_at,
                    lang=doc.lang,
                    owner_id=user_id
                )
                db.add(db_doc)

        db.commit()
        logger.info(
            f"Crawler completed for {target.url}, saved {len(documents)} documents"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error in crawler task: {str(e)}")
