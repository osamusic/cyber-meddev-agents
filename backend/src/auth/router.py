from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session as SQLAlchemySession
from datetime import timedelta
import os
import logging
from typing import Optional

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

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])  # Authentication endpoints


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: SQLAlchemySession = Depends(get_db),
    request: Request = None,
    response: Response = None
):
    logger.info(f"Login attempt: username '{form_data.username}'")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.error(f"Authentication failed: username '{form_data.username}' not found or password mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User '{form_data.username}' logged in successfully")

    if request and response:
        regenerate_session_after_login(request, response, user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User)
async def register_user(
    user: UserCreate,
    admin_code: Optional[str] = None,
    db: SQLAlchemySession = Depends(get_db)
):
    existing_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already in use"
        )

    admin_secret = os.getenv("ADMIN_REGISTRATION_SECRET", "admin123")
    is_admin = admin_code is not None and admin_code == admin_secret

    user_count = db.query(UserModel).count()
    is_first_user = (user_count == 0)

    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        username=user.username,
        hashed_password=hashed_password,
        is_admin=(is_admin or is_first_user)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
