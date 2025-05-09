from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    documents = relationship("DocumentModel", back_populates="owner")

class DocumentModel(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String, unique=True, index=True)
    url = Column(String)
    title = Column(String)
    content = Column(Text)
    source_type = Column(String)  # PDF, HTML, DOCX
    downloaded_at = Column(DateTime)
    lang = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="documents")
    sections = relationship("DocumentSection", back_populates="document")

class DocumentSection(Base):
    __tablename__ = "document_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True)
    text_chunk = Column(Text)
    document_id = Column(Integer, ForeignKey("documents.id"))
    section_number = Column(Integer)
    
    document = relationship("DocumentModel", back_populates="sections")
    guidelines = relationship("Guideline", back_populates="section")

class Guideline(Base):
    __tablename__ = "guidelines"
    
    id = Column(Integer, primary_key=True, index=True)
    guideline_id = Column(String, unique=True, index=True)
    category = Column(String, index=True)
    standard = Column(String, index=True)
    control_text = Column(Text)
    source_url = Column(String)
    region = Column(String)
    section_id = Column(Integer, ForeignKey("document_sections.id"))
    
    section = relationship("DocumentSection", back_populates="guidelines")
    keywords = relationship("GuidelineKeyword", back_populates="guideline")

class GuidelineKeyword(Base):
    __tablename__ = "guideline_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    guideline_id = Column(Integer, ForeignKey("guidelines.id"))
    
    guideline = relationship("Guideline", back_populates="keywords")
