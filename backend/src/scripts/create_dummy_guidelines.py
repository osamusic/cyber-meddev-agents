#!/usr/bin/env python3
import bcrypt
from datetime import datetime
import json
from src.db.models import User, DocumentModel, Guideline, GuidelineKeyword, ClassificationResult
from src.db.database import engine, get_db
from sqlalchemy.orm import Session
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


def get_password_hash(password: str) -> str:
    """Generate a password hash using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def create_dummy_data():
    db = next(get_db())

    # Check if guidelines already exist
    existing_guidelines = db.query(Guideline).count()
    if existing_guidelines > 0:
        print("Guidelines already exist. Skipping dummy data creation.")
        return

    # Create dummy admin user
    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("password"),
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    print("Created dummy admin user")

    # Create dummy document
    document = DocumentModel(
        doc_id="dummy-doc-1",
        url="https://example.com/dummy-doc",
        title="Dummy Document for Classification",
        content="This is a dummy document for testing purposes.",
        source_type="PDF",
        downloaded_at=datetime.utcnow(),
        lang="ja",
        owner_id=admin_user.id
    )
    db.add(document)
    db.commit()
    print("Created dummy document")

    # Create dummy guidelines
    guidelines = [
        {
            "guideline_id": "NIST-CSF-ID.AM-1",
            "category": "NIST CSF",
            "standard": "ID.AM-1",
            "control_text": "物理デバイスとシステムのインベントリ",
            "source_url": "https://www.nist.gov/cyberframework",
            "region": "US",
            "keywords": ["インベントリ", "資産管理", "デバイス"]
        },
        {
            "guideline_id": "NIST-CSF-PR.AC-1",
            "category": "NIST CSF",
            "standard": "PR.AC-1",
            "control_text": "ID管理、認証、アクセス制御",
            "source_url": "https://www.nist.gov/cyberframework",
            "region": "US",
            "keywords": ["認証", "アクセス制御", "ID管理"]
        },
        {
            "guideline_id": "IEC-62443-SR-1.1",
            "category": "IEC 62443",
            "standard": "SR 1.1",
            "control_text": "人的リソースのセキュリティ",
            "source_url": "https://www.iec.ch/",
            "region": "International",
            "keywords": ["人的セキュリティ", "トレーニング", "意識向上"]
        },
        {
            "guideline_id": "IEC-62443-SR-2.1",
            "category": "IEC 62443",
            "standard": "SR 2.1",
            "control_text": "ネットワークセグメンテーション",
            "source_url": "https://www.iec.ch/",
            "region": "International",
            "keywords": ["ネットワーク", "セグメンテーション", "分離"]
        },
        {
            "guideline_id": "FDA-Guidance-1",
            "category": "FDA",
            "standard": "Guidance 1",
            "control_text": "医療機器のサイバーセキュリティ",
            "source_url": "https://www.fda.gov/",
            "region": "US",
            "keywords": ["医療機器", "サイバーセキュリティ", "FDA"]
        }
    ]

    created_guidelines = []

    for guideline_data in guidelines:
        keywords = guideline_data.pop("keywords")

        guideline = Guideline(**guideline_data)
        db.add(guideline)
        db.flush()  # Flush to get the ID

        for keyword in keywords:
            keyword_obj = GuidelineKeyword(
                guideline_id=guideline.id,
                keyword=keyword
            )
            db.add(keyword_obj)

        created_guidelines.append(guideline)

    db.commit()

    # Create classification results for each guideline
    for guideline in created_guidelines:
        # Create a dummy classification result that matches the guideline
        nist_result = {}
        iec_result = {}

        if "NIST" in guideline.category:
            nist_result = {
                "categories": {
                    "ID": {"score": 8, "reason": "資産管理に関連する内容が含まれています。"},
                    "PR": {"score": 5, "reason": "保護に関する内容が一部含まれています。"},
                    "DE": {"score": 3, "reason": "検知に関する内容はあまり含まれていません。"},
                    "RS": {"score": 2, "reason": "対応に関する内容はほとんど含まれていません。"},
                    "RC": {"score": 1, "reason": "復旧に関する内容はほとんど含まれていません。"}
                },
                "primary_category": "ID",
                "explanation": "このドキュメントは主に資産管理に関する内容が含まれています。"
            }
        elif "IEC" in guideline.category:
            iec_result = {
                "requirements": {
                    "FR1": {"score": 7, "reason": "識別と認証管理に関する内容が含まれています。"},
                    "FR2": {"score": 8, "reason": "使用制御に関する内容が多く含まれています。"},
                    "FR3": {"score": 5, "reason": "システム整合性に関する内容が一部含まれています。"},
                    "FR4": {"score": 4, "reason": "データ機密性に関する内容が一部含まれています。"},
                    "FR5": {"score": 3, "reason": "制限されたデータフローに関する内容はあまり含まれていません。"},
                    "FR6": {"score": 2, "reason": "適時応答に関する内容はほとんど含まれていません。"},
                    "FR7": {"score": 1, "reason": "リソース可用性に関する内容はほとんど含まれていません。"}
                },
                "primary_requirement": "FR2",
                "explanation": "このドキュメントは主に使用制御に関する内容が含まれています。"
            }
        else:
            # For FDA or other categories
            nist_result = {
                "categories": {
                    "ID": {"score": 6, "reason": "資産管理に関する内容が含まれています。"},
                    "PR": {"score": 7, "reason": "保護に関する内容が多く含まれています。"},
                    "DE": {"score": 4, "reason": "検知に関する内容が一部含まれています。"},
                    "RS": {"score": 3, "reason": "対応に関する内容はあまり含まれていません。"},
                    "RC": {"score": 2, "reason": "復旧に関する内容はほとんど含まれていません。"}
                },
                "primary_category": "PR",
                "explanation": "このドキュメントは主に保護に関する内容が含まれています。"
            }

            iec_result = {
                "requirements": {
                    "FR1": {"score": 5, "reason": "識別と認証管理に関する内容が一部含まれています。"},
                    "FR2": {"score": 6, "reason": "使用制御に関する内容が含まれています。"},
                    "FR3": {"score": 7, "reason": "システム整合性に関する内容が多く含まれています。"},
                    "FR4": {"score": 5, "reason": "データ機密性に関する内容が一部含まれています。"},
                    "FR5": {"score": 4, "reason": "制限されたデータフローに関する内容が一部含まれています。"},
                    "FR6": {"score": 3, "reason": "適時応答に関する内容はあまり含まれていません。"},
                    "FR7": {"score": 2, "reason": "リソース可用性に関する内容はほとんど含まれていません。"}
                },
                "primary_requirement": "FR3",
                "explanation": "このドキュメントは主にシステム整合性に関する内容が含まれています。"
            }

        # Create the classification result
        classification_result = ClassificationResult(
            document_id=document.id,  # Use document.id as document_id
            user_id=admin_user.id,
            result_json=json.dumps({
                "document_id": guideline.id,  # Use guideline.id in the result JSON
                "timestamp": datetime.now().isoformat(),
                "frameworks": {
                    "NIST_CSF": nist_result,
                    "IEC_62443": iec_result
                },
                "keywords": [keyword for keyword in keywords],
                "requirements": f"これは{guideline.standard}に関するガイドラインです。{guideline.control_text}について説明しています。",
            }, ensure_ascii=False)
        )
        db.add(classification_result)

    db.commit()
    print("Created dummy guidelines and classification results")
    print("Dummy data creation completed")


if __name__ == "__main__":
    create_dummy_data()
