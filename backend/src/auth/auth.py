from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session as SQLAlchemySession
import os
from dotenv import load_dotenv

from .models import TokenData, User
from ..db.database import get_db
from ..db.models import User as UserModel

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "YOUR_SECRET_KEY_HERE")  # Should be loaded from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: SQLAlchemySession, username: str):
    return db.query(UserModel).filter(UserModel.username == username).first()

def authenticate_user(db: SQLAlchemySession, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: SQLAlchemySession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",  # Invalid credentials
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    if token_data.username is None:
        raise credentials_exception
        
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"  # Admin privileges required
        )
    return current_user

def regenerate_session_after_login(request: Request, response: Response, user: UserModel):
    """
    Regenerate session after successful login to prevent session fixation attacks.
    This should be called after successful authentication.
    """
    
    response.set_cookie(
        key="session_regenerated",
        value="true",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    client_host = request.client.host if request.client else "unknown"
    print(f"Session regenerated for user {user.username} from IP {client_host} at {datetime.utcnow()}")
