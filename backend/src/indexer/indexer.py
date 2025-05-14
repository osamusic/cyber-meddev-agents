import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv
import httpx
from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.llms.openai import OpenAI
from llama_index.llms.openrouter import OpenRouter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .models import IndexConfig, IndexStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

if os.getenv("OPENROUTER_API_KEY"):
    openai.api_type = "openrouter"
    openai.api_key = os.getenv("OPENROUTER_API_KEY")
    MODEL = "deepseek/deepseek-r1:free"
    logger.info(f"Using OpenRouter model: {MODEL}")
    Settings.llm = OpenRouter(model=MODEL)
    Settings.embed_model = HuggingFaceEmbedding()
else:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_type = "openai"
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(f"Using OpenAI model: {MODEL}")
    Settings.llm = OpenAI(model=MODEL)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

if not openai.api_key:
    logger.warning("API_KEY environment variable not set")


# グローバルな既定値を設定

Settings.node_parser = SimpleNodeParser(chunk_size=256, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = os.getenv("MAX_DOCUMENT_SIZE", 4000)

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


class DocumentIndexer:
    """Indexer for medical device cybersecurity documents"""

    def __init__(self, storage_dir: str = "./storage"):
        """Initialize the indexer with storage directory"""
        self.storage_dir = storage_dir
        self.index_dir = os.path.join(storage_dir, "index")
        self.documents_dir = os.path.join(storage_dir, "documents")

        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)

        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> VectorStoreIndex:
        """Load existing index or create a new one"""
        try:
            if os.path.exists(os.path.join(self.index_dir, "docstore.json")):
                logger.info("Loading existing index...")
                storage_context = StorageContext.from_defaults(persist_dir=self.index_dir)
                return load_index_from_storage(storage_context=storage_context)
            else:
                logger.info("Creating new index...")
                return self._create_empty_index()
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return self._create_empty_index()

    def _create_empty_index(self) -> VectorStoreIndex:
        """Create a new empty index"""
        try:
            logger.info("Creating empty vector store index...")
            os.makedirs(self.index_dir, exist_ok=True)
            storage_context = StorageContext.from_defaults()
            index = VectorStoreIndex.from_documents([], storage_context=storage_context)
            index.storage_context.persist(persist_dir=self.index_dir)
            logger.info("Empty index created successfully")
            return index
        except Exception as e:
            logger.error(f"Error creating empty index: {str(e)}")

    def index_documents(self, documents: List[Dict[str, Any]], config: Optional[IndexConfig] = None) -> Dict[str, int]:
        """Index a list of documents"""
        if not documents:
            logger.warning("No documents to index")
            return {"indexed": 0, "skipped": 0, "total": 0}

        if config is None:
            config = IndexConfig()

        if self.index is None:
            logger.warning("Index is None, attempting to recreate...")
            self.index = self._load_or_create_index()

        if not hasattr(self.index, 'insert_nodes') or not callable(getattr(self.index, 'insert_nodes', None)):
            logger.error("Index does not have a valid insert_nodes method")
            raise RuntimeError("Invalid index structure, unable to insert documents")

        if not hasattr(self.index, 'storage_context'):
            logger.warning("Index does not have a storage_context attribute, some functionality may be limited")

        try:
            existing_docs = set()
            if not config.force_reindex and os.path.exists(self.documents_dir):
                for filename in os.listdir(self.documents_dir):
                    if filename.endswith('.json'):
                        doc_id = filename.replace('.json', '')
                        existing_docs.add(doc_id)
                logger.info(f"Found {len(existing_docs)} already indexed documents")

            new_docs = []
            skipped_docs = []

            llama_docs = []
            for doc in documents:
                doc_id = doc.get("doc_id", "")
                content = doc.get("content", "")

                if not doc_id:
                    logger.warning("Skipping document with empty doc_id")
                    continue

                if not config.force_reindex and doc_id in existing_docs:
                    logger.info(f"Skipping already indexed document: {doc_id}")
                    skipped_docs.append(doc_id)
                    continue

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
                new_docs.append(doc_id)

            if llama_docs:
                logger.info(f"Indexing {len(llama_docs)} new documents...")
                self.index.insert_nodes(llama_docs)

                logger.info(f"Persisting index to {self.index_dir}...")
                if hasattr(self.index, 'storage_context') and self.index.storage_context is not None:
                    self.index.storage_context.persist(persist_dir=self.index_dir)
                else:
                    logger.warning("Index does not have a storage_context, skipping persistence")
            else:
                logger.info("No new documents to index")

            return {"indexed": len(new_docs), "skipped": len(skipped_docs), "total": len(documents)}
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for documents matching the query"""
        if not self.index:
            logger.warning("No index available for search")
            return []

        query_engine = self.index.as_query_engine(similarity_top_k=top_k)

        response = query_engine.query(query)

        results = []
        for node in response.source_nodes:
            try:
                text = node.text
            except ValueError:
                logger.warning(f"Node is not a TextNode, using fallback text. Node type: {type(node)}")
                text = "No text content available for this node"
            
            results.append({
                "text": text,
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
