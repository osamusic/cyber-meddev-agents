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
from dotenv import load_dotenv

load_dotenv()


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="医療機器サイバーセキュリティ専門家システム",
    dependencies=[Depends(get_current_active_user)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

public_router = APIRouter()

@public_router.get("/")
def read_root():
    return {"message": "Cyber-Med-Agent Backend is running"}

public_router.include_router(auth_router)

app.include_router(public_router)
app.include_router(guidelines_router)
app.include_router(admin_router)
app.include_router(indexer_router)
app.include_router(crawler_router)
app.include_router(classifier_router)



@app.get("/me")
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user
