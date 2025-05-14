from .classifier.router import router as classifier_router
from .crawler.router import router as crawler_router
from .indexer.router import router as indexer_router
from .admin.router import router as admin_router
from .guidelines.router import router as guidelines_router
from .auth.auth import get_current_active_user
from .auth.router import router as auth_router
from .db.models import Base
from .db.database import engine
from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware


Base.metadata.create_all(bind=engine)

# アプリ全体に依存関係を設定しない
app = FastAPI(
    title="医療機器サイバーセキュリティ専門家システム"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 認証が必要なルーターにだけ Depends をつける
protected_router = APIRouter(
    dependencies=[Depends(get_current_active_user)]
)

# 認証が必要なエンドポイントをこのルーターに追加
protected_router.include_router(guidelines_router)
protected_router.include_router(admin_router)
protected_router.include_router(indexer_router)
protected_router.include_router(crawler_router)
protected_router.include_router(classifier_router)

# 公開ルーター（ログインなど）
public_router = APIRouter()
public_router.include_router(auth_router)


@public_router.get("/")
def read_root():
    return {"message": "Cyber-Med-Agent Backend is running"}


@app.get("/me")
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user

# ルーター登録
app.include_router(public_router)
app.include_router(protected_router)
