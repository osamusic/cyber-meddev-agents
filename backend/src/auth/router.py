from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session as SQLAlchemySession
from datetime import timedelta

from .auth import (
    authenticate_user, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    get_password_hash,
    regenerate_session_after_login
)
from .models import Token, UserCreate, User
from ..db.database import get_db
from ..db.models import User as UserModel

router = APIRouter(tags=["認証"])  # Authentication

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: SQLAlchemySession = Depends(get_db),
    request: Request = None,
    response: Response = None
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",  # Incorrect username or password
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if request and response:
        regenerate_session_after_login(request, response, user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(user: UserCreate, db: SQLAlchemySession = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に使用されています"  # Username already in use
        )
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
