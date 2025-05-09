import sys
import os
import jwt
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.auth.auth import SECRET_KEY, ALGORITHM
from src.db.database import get_db
from src.db.models import User

def check_auth():
    """認証関連の情報を検証する"""
    print("===== 認証状態の検証 =====")
    
    db = next(get_db())
    users = db.query(User).all()
    print(f"登録ユーザー数: {len(users)}")
    
    if len(users) > 0:
        user = users[0]
        print(f"ユーザー名: {user.username}, 管理者: {user.is_admin}")
        print(f"パスワードハッシュ: {user.hashed_password[:20]}...")
    
    print(f"JWTシークレットキー: {SECRET_KEY[:5]}...")
    print(f"JWTシークレットキー長: {len(SECRET_KEY)}")
    print(f"JWT暗号化アルゴリズム: {ALGORITHM}")
    
    try:
        test_token = jwt.encode({"sub": "test", "exp": datetime.utcnow().timestamp() + 3600}, SECRET_KEY, algorithm=ALGORITHM)
        print(f"テストトークン生成: {test_token[:20]}...")
        
        decoded = jwt.decode(test_token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"トークン検証成功: {decoded}")
    except Exception as e:
        print(f"トークン検証エラー: {str(e)}")
    
    if len(users) > 0:
        user = users[0]
        try:
            user_token = jwt.encode({"sub": user.username, "exp": datetime.utcnow().timestamp() + 3600}, SECRET_KEY, algorithm=ALGORITHM)
            print(f"ユーザー '{user.username}' のトークン生成: {user_token[:20]}...")
            
            user_decoded = jwt.decode(user_token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"ユーザートークン検証成功: {user_decoded}")
        except Exception as e:
            print(f"ユーザートークン検証エラー: {str(e)}")
    
if __name__ == "__main__":
    check_auth()
