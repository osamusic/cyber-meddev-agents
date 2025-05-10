from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Dict, Any

from ..db.database import get_db
from ..db.models import DocumentModel
from ..auth.auth import get_current_active_user
from .models import IndexConfig, IndexStats, SearchQuery
from .indexer import DocumentIndexer

router = APIRouter(
    prefix="/index",
    tags=["インデックス"],
    dependencies=[Depends(get_current_active_user)]
)

indexer = DocumentIndexer(storage_dir="./storage")


@router.post("/documents")
async def index_documents(
    config: IndexConfig = Body(None),
    db: SQLAlchemySession = Depends(get_db)
):
    """Index all documents in the database"""
    documents = db.query(DocumentModel).all()

    docs_to_index = []
    for doc in documents:
        docs_to_index.append({
            "doc_id": doc.doc_id,
            "title": doc.title,
            "content": doc.content,
            "url": doc.url,
            "source_type": doc.source_type,
            "downloaded_at": (
                doc.downloaded_at.isoformat() if doc.downloaded_at else None
            )
        })

    num_indexed = indexer.index_documents(docs_to_index, config)

    result = {
        "message": (
            f"{num_indexed['indexed']} ドキュメントがインデックス化されました"
            f"（{num_indexed['skipped']} ドキュメントはスキップされました）"
        ),
        "stats": num_indexed
    }

    return result


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_index(query: SearchQuery):
    """Search the index for documents matching the query"""
    results = indexer.search(query.query, query.top_k)
    return results


@router.get("/stats", response_model=IndexStats)
async def get_index_stats():
    """Get statistics about the index"""
    stats = indexer.get_stats()
    return stats
