"""
Docker コンテナ内で管理者ユーザーのパスワードを更新するスクリプト
"""
import os
import subprocess

def update_admin_password():
    """Docker コンテナ内で管理者ユーザーのパスワードを更新する"""
    print("===== Docker コンテナ内で管理者ユーザーのパスワードを更新 =====")
    
    python_code = """
from src.db.database import get_db
from src.db.models import User
from src.auth.auth import get_password_hash

def update_password():
    db = next(get_db())
    admin_user = db.query(User).filter(User.username == 'admin').first()
    
    if not admin_user:
        print('管理者ユーザー "admin" が見つかりません')
        return
    
    admin_user.hashed_password = get_password_hash('password')
    
    try:
        db.commit()
        print('管理者ユーザー "admin" のパスワードを更新しました')
    except Exception as e:
        db.rollback()
        print(f'パスワード更新エラー: {str(e)}')

if __name__ == "__main__":
    update_password()
"""
    
    temp_file = "/tmp/update_admin_password.py"
    with open(temp_file, "w") as f:
        f.write(python_code)
    
    copy_cmd = ["docker", "cp", temp_file, "cyber-meddev-agents-backend-1:/app/update_admin_password.py"]
    subprocess.run(copy_cmd, check=True)
    
    exec_cmd = ["docker", "exec", "cyber-meddev-agents-backend-1", "python", "/app/update_admin_password.py"]
    subprocess.run(exec_cmd, check=True)
    
    os.remove(temp_file)
    
    print("===== 管理者ユーザーのパスワード更新が完了しました =====")

if __name__ == "__main__":
    update_admin_password()
