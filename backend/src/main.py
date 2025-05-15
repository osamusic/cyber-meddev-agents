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

# Create database tables based on models
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app without global dependencies
app = FastAPI(
    title="Medical Device Cybersecurity Expert System"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router for endpoints requiring authentication
protected_router = APIRouter(
    dependencies=[Depends(get_current_active_user)]
)

# Include protected routers
protected_router.include_router(guidelines_router)
protected_router.include_router(admin_router)
protected_router.include_router(indexer_router)
protected_router.include_router(crawler_router)
protected_router.include_router(classifier_router)

# Public router for endpoints that don't require authentication (e.g., login)
public_router = APIRouter()
public_router.include_router(auth_router)


@public_router.get("/")
async def read_root():
    return {"message": "Cyber-Med-Agent Backend is running"}


@app.get("/me")
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user

# Register routers
app.include_router(public_router)
app.include_router(protected_router)
