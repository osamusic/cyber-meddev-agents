"""
Docker コンテナ内でダミーのガイドラインデータを作成するスクリプト
"""
import os
import subprocess

def create_dummy_in_container():
    """Docker コンテナ内でダミーのガイドラインデータを作成する"""
    print("===== Docker コンテナ内でダミーガイドラインデータを作成 =====")
    
    python_code = """
from src.db.database import get_db
from src.db.models import Guideline, GuidelineKeyword

def insert_guidelines():
    db = next(get_db())
    
    db.query(GuidelineKeyword).delete()
    db.query(Guideline).delete()
    db.commit()
    
    guidelines = [
        {
            "guideline_id": "IEC-62304-001",
            "category": "医療機器ソフトウェア",
            "standard": "IEC 62304",
            "control_text": "ソフトウェア開発プロセスの文書化",
            "source_url": "https://example.com/iec62304",
            "region": "国際",
            "keywords": ["ソフトウェア", "開発", "文書化"]
        },
        {
            "guideline_id": "ISO-14971-001",
            "category": "リスク管理",
            "standard": "ISO 14971",
            "control_text": "リスク分析と評価の実施",
            "source_url": "https://example.com/iso14971",
            "region": "国際",
            "keywords": ["リスク", "分析", "評価"]
        },
        {
            "guideline_id": "FDA-510K-001",
            "category": "規制対応",
            "standard": "FDA 510(k)",
            "control_text": "市販前届出の提出",
            "source_url": "https://example.com/fda510k",
            "region": "米国",
            "keywords": ["FDA", "510k", "届出"]
        },
        {
            "guideline_id": "PMDA-001",
            "category": "規制対応",
            "standard": "PMDA承認",
            "control_text": "医療機器製造販売承認申請",
            "source_url": "https://example.com/pmda",
            "region": "日本",
            "keywords": ["PMDA", "承認", "申請"]
        },
        {
            "guideline_id": "MDR-001",
            "category": "規制対応",
            "standard": "EU MDR",
            "control_text": "適合性評価と技術文書の作成",
            "source_url": "https://example.com/eumdr",
            "region": "欧州",
            "keywords": ["MDR", "適合性", "技術文書"]
        }
    ]
    
    for guideline_data in guidelines:
        guideline = Guideline(
            guideline_id=guideline_data["guideline_id"],
            category=guideline_data["category"],
            standard=guideline_data["standard"],
            control_text=guideline_data["control_text"],
            source_url=guideline_data["source_url"],
            region=guideline_data["region"]
        )
        db.add(guideline)
        db.flush()
        
        for keyword in guideline_data["keywords"]:
            keyword_obj = GuidelineKeyword(
                guideline_id=guideline.id,
                keyword=keyword
            )
            db.add(keyword_obj)
    
    db.commit()
    print("ダミーガイドラインデータを作成しました")

if __name__ == "__main__":
    insert_guidelines()
"""
    
    temp_file = "/tmp/insert_guidelines.py"
    with open(temp_file, "w") as f:
        f.write(python_code)
    
    copy_cmd = ["docker", "cp", temp_file, "cyber-meddev-agents-backend-1:/app/insert_guidelines.py"]
    subprocess.run(copy_cmd, check=True)
    
    exec_cmd = ["docker", "exec", "cyber-meddev-agents-backend-1", "python", "/app/insert_guidelines.py"]
    subprocess.run(exec_cmd, check=True)
    
    os.remove(temp_file)
    
    print("===== ダミーガイドラインデータの作成が完了しました =====")

if __name__ == "__main__":
    create_dummy_in_container()
