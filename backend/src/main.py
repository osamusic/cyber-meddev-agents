from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as SQLAlchemySession
import os
from dotenv import load_dotenv

load_dotenv()

from .db.database import engine, Base, get_db
from .auth.router import router as auth_router
from .auth.auth import get_current_active_user
from .guidelines.router import router as guidelines_router
from .admin.router import router as admin_router
from .indexer.router import router as indexer_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="医療機器サイバーセキュリティ専門家システム")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(guidelines_router)
app.include_router(admin_router)
app.include_router(indexer_router)

@app.get("/")
def read_root():
    return {"message": "Cyber-Med-Agent Backend is running"}

@app.get("/me")
async def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user
