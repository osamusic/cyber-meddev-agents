import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
db_path = BASE_DIR / "data" / "cyber_med_agent.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
sqlite_url = f"sqlite:///{db_path.as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", sqlite_url)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
