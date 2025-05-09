import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.db.database import get_db
from src.db.models import User
from src.auth.auth import get_password_hash

def create_admin_user():
    """管理者ユーザーを作成する"""
    print("===== 管理者ユーザー作成 =====")
    
    db = next(get_db())
    
    existing_user = db.query(User).filter(User.username == 'admin').first()
    
    if existing_user:
        print(f"管理者ユーザー 'admin' は既に存在します")
        return
    
    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("password"),
        is_admin=True
    )
    
    try:
        db.add(admin_user)
        db.commit()
        print(f"管理者ユーザー 'admin' を作成しました")
    except Exception as e:
        db.rollback()
        print(f"ユーザー作成エラー: {str(e)}")

if __name__ == "__main__":
    create_admin_user()
