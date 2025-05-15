import os
import json
import logging
import re
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
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.llms.openrouter import OpenRouter as LlamaOpenRouter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from .models import IndexConfig, IndexStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure LLM and embedding models based on environment
if os.getenv("OPENROUTER_API_KEY"):
    openai.api_type = "openrouter"
    openai.api_key = os.getenv("OPENROUTER_API_KEY")
    MODEL = "deepseek/deepseek-r1:free"
    logger.info(f"Using OpenRouter model: {MODEL}")
    Settings.llm = LlamaOpenRouter(model=MODEL)
    Settings.embed_model = HuggingFaceEmbedding()
else:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_type = "openai"
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(f"Using OpenAI model: {MODEL}")
    Settings.llm = LlamaOpenAI(model=MODEL)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

if not openai.api_key:
    logger.warning("API_KEY environment variable not set")

# Global default settings
Settings.node_parser = SimpleNodeParser(chunk_size=256, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = int(os.getenv("MAX_DOCUMENT_SIZE", 4000))

# Patch httpx client to remove 'proxies' parameter
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
        """Initialize the indexer with a storage directory"""
        self.storage_dir = storage_dir
        self.index_dir = os.path.join(storage_dir, "index")
        self.documents_dir = os.path.join(storage_dir, "documents")

        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)

        self.index = self._load_or_create_index()

    def _load_or_create_index(self) -> VectorStoreIndex:
        """Load an existing index or create a new one"""
        try:
            index_file = os.path.join(self.index_dir, "docstore.json")
            if os.path.exists(index_file):
                logger.info("Loading existing index...")
                storage_context = StorageContext.from_defaults(persist_dir=self.index_dir)
                return load_index_from_storage(storage_context=storage_context)
            else:
                logger.info("Creating new index...")
                return self._create_empty_index()
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return self._create_empty_index()

    def _create_empty_index(self) -> VectorStoreIndex:
        """Create a new empty vector store index"""
        try:
            logger.info("Creating empty vector store index...")
            storage_context = StorageContext.from_defaults()
            index = VectorStoreIndex.from_documents([], storage_context=storage_context)
            index.storage_context.persist(persist_dir=self.index_dir)
            logger.info("Empty index created successfully")
            return index
        except Exception as e:
            logger.error(f"Error creating empty index: {e}")

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        config: Optional[IndexConfig] = None
    ) -> Dict[str, int]:
        """Index a list of documents and track how many were indexed or skipped"""
        if not documents:
            logger.warning("No documents to index")
            return {"indexed": 0, "skipped": 0, "total": 0}

        config = config or IndexConfig()
        if self.index is None:
            logger.warning("Index is None, recreating index...")
            self.index = self._load_or_create_index()

        # Validate index methods
        if not hasattr(self.index, 'insert_nodes'):
            logger.error("Index missing 'insert_nodes' method")
            raise RuntimeError("Invalid index structure, cannot insert documents")

        existing_docs = set()
        if not config.force_reindex and os.path.exists(self.documents_dir):
            for fname in os.listdir(self.documents_dir):
                if fname.endswith('.json'):
                    existing_docs.add(fname.replace('.json', ''))
            logger.info(f"Found {len(existing_docs)} already indexed documents")

        new_docs, skipped = [], []
        llama_docs = []
        for doc in documents:
            doc_id = doc.get("doc_id", "")
            content = doc.get("content", "")
            if not doc_id:
                logger.warning("Skipping document with empty doc_id")
                continue
            if not config.force_reindex and doc_id in existing_docs:
                logger.info(f"Skipping already indexed document: {doc_id}")
                skipped.append(doc_id)
                continue

            # Save raw document
            doc_path = os.path.join(self.documents_dir, f"{doc_id}.json")
            with open(doc_path, "w") as f:
                json.dump(doc, f)

            metadata = {
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "source_type": doc.get("source_type", ""),
                "downloaded_at": doc.get("downloaded_at", datetime.now().isoformat())
            }
            llama_docs.append(Document(text=content, metadata=metadata))
            new_docs.append(doc_id)

        # Insert new documents into the index
        if llama_docs:
            logger.info(f"Indexing {len(llama_docs)} new documents...")
            self.index.insert_nodes(llama_docs)
            logger.info(f"Persisting index to {self.index_dir}...")
            self.index.storage_context.persist(persist_dir=self.index_dir)
        else:
            logger.info("No new documents to index")

        return {"indexed": len(new_docs), "skipped": len(skipped), "total": len(documents)}

    def to_markdown(self, text: str) -> str:
        """Convert raw text lines into markdown format with headings and lists"""
        lines = text.splitlines()
        md = []
        for line in lines:
            line = line.strip()
            if not line:
                md.append("")
                continue
            # [SECTION: X] -> ### SECTION: X
            sec = re.match(r"\[SECTION:\s*(.*?)\]", line)
            if sec:
                md.append(f"### SECTION: {sec.group(1)}")
                continue
            # [PAGE_15] -> ### PAGE_15
            if re.match(r"^\[PAGE_[0-9]+\]", line):
                md.append(f"### {line.strip('[]')}")
                continue
            # Numeric headings e.g., 5.4 Title
            if re.match(r"^\d+(\.\d+)*\s+[A-Z].*", line):
                md.append(f"### {line}")
                continue
            # Subheadings e.g., 5.5.1 Labeling
            if re.match(r"^\d+\.\d+\.\d+\s+.*", line):
                md.append(f"#### {line}")
                continue
            # Bullet list starting with special character
            if line.startswith("") or line.startswith(" •"):
                md.append(f"- {line.lstrip(' •')} ")
                continue
            # Lines ending with colon -> bold
            if re.match(r"^[A-Za-z\s]+:$", line):
                md.append(f"**{line}**")
                continue
            # URLs -> block quote
            if "http" in line:
                md.append(f"> ({line})")
                continue
            md.append(line)
        return "\n".join(md)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for relevant documents"""
        if not self.index:
            logger.warning("No index available for search")
            return []
        query_engine = self.index.as_query_engine(similarity_top_k=top_k)
        response = query_engine.query(query)
        results = []
        for scored_node in response.source_nodes:
            node = scored_node.node
            try:
                content = node.get_content()
            except Exception:
                content = "No text content available"
            results.append({
                "text": self.to_markdown(content),
                "score": scored_node.score,
                "metadata": getattr(node, "metadata", {})
            })
        return results

    def get_stats(self) -> IndexStats:
        """Return statistics about the index and stored documents"""
        # Count stored documents
        total_docs = len(os.listdir(self.documents_dir))
        # Determine total chunks/nodes in the index structure
        total_chunks = 0
        struct = getattr(self.index, "index_struct", None)
        if struct:
            if hasattr(struct, "node_ids"):
                total_chunks = len(struct.node_ids)
            elif hasattr(struct, "nodes"):
                total_chunks = len(struct.nodes)
            elif hasattr(struct, "_node_ids"):
                total_chunks = len(struct._node_ids)
        if total_chunks == 0:
            logger.warning("Unable to determine total chunks, falling back to docstore size")
            total_chunks = len(self.index.docstore.docs)
        # Get last updated timestamp
        index_file = os.path.join(self.index_dir, "docstore.json")
        if os.path.exists(index_file):
            last_updated = datetime.fromtimestamp(os.path.getmtime(index_file))
        else:
            last_updated = datetime.now()
        return IndexStats(
            total_documents=total_docs,
            total_chunks=total_chunks,
            last_updated=last_updated
        )
