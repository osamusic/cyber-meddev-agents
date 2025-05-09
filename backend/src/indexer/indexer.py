import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from llama_index import (
    VectorStoreIndex, 
    SimpleDirectoryReader,
    Document,
    ServiceContext,
    StorageContext,
    load_index_from_storage
)
from llama_index.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms import OpenAI
import openai
from dotenv import load_dotenv
import httpx
import sys

from .models import IndexConfig, IndexStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY environment variable not set")

original_client_init = httpx.Client.__init__

def patched_client_init(self, *args, **kwargs):
    if 'proxies' in kwargs:
        logger.info("Removing 'proxies' parameter from httpx.Client.__init__")
        del kwargs['proxies']
    original_client_init(self, *args, **kwargs)

httpx.Client.__init__ = patched_client_init

original_async_client_init = httpx.AsyncClient.__init__

def patched_async_client_init(self, *args, **kwargs):
    if 'proxies' in kwargs:
        logger.info("Removing 'proxies' parameter from httpx.AsyncClient.__init__")
        del kwargs['proxies']
    original_async_client_init(self, *args, **kwargs)

httpx.AsyncClient.__init__ = patched_async_client_init

class CustomOpenAIEmbedding:
    """Custom embedding class that wraps OpenAI API to avoid compatibility issues"""
    
    def __init__(self):
        """Initialize with default parameters"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "text-embedding-ada-002"
    
    def get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        response = openai.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        response = openai.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]

class DocumentIndexer:
    """Indexer for medical device cybersecurity documents"""
    
    def __init__(self, storage_dir: str = "./storage"):
        """Initialize the indexer with storage directory"""
        self.storage_dir = storage_dir
        self.index_dir = os.path.join(storage_dir, "index")
        self.documents_dir = os.path.join(storage_dir, "documents")
        
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        self.index = self._load_or_create_index()
    
    def _load_or_create_index(self) -> VectorStoreIndex:
        """Load existing index or create a new one"""
        try:
            if os.path.exists(os.path.join(self.index_dir, "docstore.json")):
                logger.info("Loading existing index...")
                storage_context = StorageContext.from_defaults(persist_dir=self.index_dir)
                return load_index_from_storage(storage_context)
            else:
                logger.info("Creating new index...")
                return self._create_empty_index()
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return self._create_empty_index()
    
    def _create_empty_index(self) -> VectorStoreIndex:
        """Create a new empty index"""
        embed_model = CustomOpenAIEmbedding()
        llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
        service_context = ServiceContext.from_defaults(
            llm=llm,
            embed_model=embed_model,
            node_parser=SimpleNodeParser.from_defaults(
                chunk_size=1024,
                chunk_overlap=20
            )
        )
        
        index = VectorStoreIndex([], service_context=service_context)
        
        index.storage_context.persist(persist_dir=self.index_dir)
        
        return index
    
    def index_documents(self, documents: List[Dict[str, Any]], config: Optional[IndexConfig] = None) -> int:
        """Index a list of documents"""
        if not documents:
            logger.warning("No documents to index")
            return 0
        
        if config is None:
            config = IndexConfig()
        
        embed_model = CustomOpenAIEmbedding()
        llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
        service_context = ServiceContext.from_defaults(
            llm=llm,
            embed_model=embed_model,
            node_parser=SimpleNodeParser.from_defaults(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap
            )
        )
        
        llama_docs = []
        for doc in documents:
            doc_id = doc.get("doc_id", "")
            content = doc.get("content", "")
            metadata = {
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "source_type": doc.get("source_type", ""),
                "downloaded_at": doc.get("downloaded_at", datetime.now().isoformat())
            }
            
            doc_path = os.path.join(self.documents_dir, f"{doc_id}.json")
            with open(doc_path, "w") as f:
                json.dump(doc, f)
            
            llama_docs.append(Document(text=content, metadata=metadata))
        
        logger.info(f"Indexing {len(llama_docs)} documents...")
        self.index = self.index.insert_nodes(llama_docs, service_context=service_context)
        
        self.index.storage_context.persist(persist_dir=self.index_dir)
        
        return len(llama_docs)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for documents matching the query"""
        if not self.index:
            logger.warning("No index available for search")
            return []
        
        query_engine = self.index.as_query_engine(similarity_top_k=top_k)
        
        response = query_engine.query(query)
        
        results = []
        for node in response.source_nodes:
            results.append({
                "text": node.text,
                "score": node.score,
                "metadata": node.metadata
            })
        
        return results
    
    def get_stats(self) -> IndexStats:
        """Get statistics about the index"""
        if not self.index:
            return IndexStats(
                total_documents=0,
                total_chunks=0,
                last_updated=datetime.now()
            )
        
        doc_count = len(os.listdir(self.documents_dir))
        
        node_count = len(self.index.docstore.docs)
        
        if os.path.exists(os.path.join(self.index_dir, "docstore.json")):
            last_updated = datetime.fromtimestamp(
                os.path.getmtime(os.path.join(self.index_dir, "docstore.json"))
            )
        else:
            last_updated = datetime.now()
        
        return IndexStats(
            total_documents=doc_count,
            total_chunks=node_count,
            last_updated=last_updated
        )
