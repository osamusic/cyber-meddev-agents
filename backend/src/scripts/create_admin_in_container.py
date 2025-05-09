"""
Docker コンテナ内で管理者ユーザーを作成するスクリプト
"""
import os
import subprocess

def create_admin_in_container():
    """Docker コンテナ内で管理者ユーザーを作成する"""
    print("===== Docker コンテナ内で管理者ユーザーを作成 =====")
    
    python_code = """
from src.db.database import get_db
from src.db.models import User
from src.auth.auth import get_password_hash

db = next(get_db())
existing_user = db.query(User).filter(User.username == 'admin').first()
if existing_user:
    print('管理者ユーザー "admin" は既に存在します')
    if not existing_user.is_admin:
        existing_user.is_admin = True
        db.commit()
        print('ユーザー "admin" に管理者権限を付与しました')
else:
    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("password"),
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    print('管理者ユーザー "admin" を作成しました')
"""
    
    temp_file = "/tmp/create_admin.py"
    with open(temp_file, "w") as f:
        f.write(python_code)
    
    copy_cmd = ["docker", "cp", temp_file, "cyber-meddev-agents-backend-1:/app/create_admin.py"]
    subprocess.run(copy_cmd, check=True)
    
    exec_cmd = ["docker", "exec", "cyber-meddev-agents-backend-1", "python", "/app/create_admin.py"]
    subprocess.run(exec_cmd, check=True)
    
    os.remove(temp_file)
    
    print("===== 管理者ユーザー作成処理が完了しました =====")

if __name__ == "__main__":
    create_admin_in_container()
