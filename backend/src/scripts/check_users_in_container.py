"""
Docker コンテナ内でユーザー情報を確認するスクリプト
"""
import os
import subprocess

def check_users_in_container():
    """Docker コンテナ内でユーザー情報を確認する"""
    print("===== Docker コンテナ内でユーザー情報を確認 =====")
    
    python_code = """
from src.db.database import get_db
from src.db.models import User
from src.auth.auth import verify_password

def check_users():
    db = next(get_db())
    users = db.query(User).all()
    
    print(f"登録ユーザー数: {len(users)}")
    
    for user in users:
        print(f"ユーザー名: {user.username}")
        print(f"管理者権限: {user.is_admin}")
        print(f"パスワードハッシュ: {user.hashed_password[:20]}...")
        
        is_valid = verify_password('password', user.hashed_password)
        print(f"パスワード 'password' は有効: {is_valid}")
        print("-" * 30)

if __name__ == "__main__":
    check_users()
"""
    
    temp_file = "/tmp/check_users.py"
    with open(temp_file, "w") as f:
        f.write(python_code)
    
    copy_cmd = ["docker", "cp", temp_file, "cyber-meddev-agents-backend-1:/app/check_users.py"]
    subprocess.run(copy_cmd, check=True)
    
    exec_cmd = ["docker", "exec", "cyber-meddev-agents-backend-1", "python", "/app/check_users.py"]
    subprocess.run(exec_cmd, check=True)
    
    os.remove(temp_file)
    
    print("===== ユーザー情報の確認が完了しました =====")

if __name__ == "__main__":
    check_users_in_container()
