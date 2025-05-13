from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List
from datetime import datetime

from ..db.database import get_db
from ..db.models import DocumentModel, User as UserModel, ClassificationResult as DBClassificationResult
from ..auth.auth import get_admin_user
from .models import DocumentInfo, DeleteConfirmation

router = APIRouter(
    prefix="/admin",
    tags=["管理者"],
    dependencies=[Depends(get_admin_user)]  # Ensure only admins can access
)


@router.get("/documents", response_model=List[DocumentInfo])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    db: SQLAlchemySession = Depends(get_db)
):
    """Get all documents (admin only)"""
    classified_doc_ids = db.query(DBClassificationResult.document_id).distinct().subquery()
    documents = db.query(DocumentModel).offset(skip).limit(limit).all()
    result = []
    for doc in documents:
        doc_dict = vars(doc)
        doc_dict["is_classified"] = db.query(classified_doc_ids.c.document_id).filter(
            classified_doc_ids.c.document_id == doc.id
        ).first() is not None
        result.append(doc_dict)
    return result


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    confirmation: DeleteConfirmation,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Delete a document (admin only)"""
    if not confirmation.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="削除を確認してください"  # Please confirm deletion
        )

    document = db.query(DocumentModel).filter(DocumentModel.doc_id == doc_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ドキュメントが見つかりません"  # Document not found
        )

    client_host = request.client.host if request.client else "unknown"
    log_entry = {
        "action": "document_delete",
        "timestamp": datetime.utcnow(),
        "user_id": current_user.id,
        "details": f"Document {document.title} (ID: {doc_id}) deleted",
        "ip_address": client_host
    }
    print(f"AUDIT LOG: {log_entry}")  # In a real implementation, save to database

    db.delete(document)
    db.commit()

    return {"message": "ドキュメントが削除されました"}  # Document deleted


@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: SQLAlchemySession = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users


@router.put("/users/{user_id}/admin")
async def toggle_admin_status(
    user_id: int,
    request: Request,
    db: SQLAlchemySession = Depends(get_db),
    current_user=Depends(get_admin_user)
):
    """Toggle admin status for a user (admin only)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"  # User not found
        )

    user.is_admin = not user.is_admin

    client_host = request.client.host if request.client else "unknown"
    log_entry = {
        "action": "admin_status_change",
        "timestamp": datetime.utcnow(),
        "user_id": current_user.id,
        "details":
            f"User {user.username} (ID: {user_id}) admin status changed to {user.is_admin}",
        "ip_address": client_host
    }
    print(f"AUDIT LOG: {log_entry}")  # In a real implementation, save to database

    db.commit()

    return {"message": f"ユーザー {user.username} の管理者権限が {'付与' if user.is_admin else '解除'} されました"}
