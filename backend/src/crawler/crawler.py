import requests
import hashlib
import mimetypes
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
import fitz  # PyMuPDF
from .models import CrawlTarget, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Crawler:
    """Crawler for medical device cybersecurity documents"""
    
    def __init__(self, db=None, target=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cyber-Med-Agent Crawler/1.0'
        })
        self.visited_urls = set()
        self.db = db  # データベースセッション
        
        self.max_document_size = int(os.getenv("MAX_DOCUMENT_SIZE", "4000"))
        if target and target.max_document_size:
            self.max_document_size = target.max_document_size
        
    def crawl(self, target: CrawlTarget) -> List[Document]:
        """Crawl a target URL and return extracted documents"""
        logger.info(f"Starting crawl for {target.url}")
        documents = []
        
        try:
            self._crawl_url(target.url, target, documents, depth=0)
        except Exception as e:
            logger.error(f"Error crawling {target.url}: {str(e)}")
        
        logger.info(f"Crawl completed. Found {len(documents)} documents")
        return documents
    
    def _crawl_url(self, url: str, target: CrawlTarget, documents: List[Document], depth: int) -> None:
        """Recursively crawl URLs up to specified depth"""
        if depth > target.depth or url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling {url} (depth {depth})")
        
        doc_id = hashlib.sha256(url.encode()).hexdigest()
        
        if self.db is not None:
            from ..db.models import DocumentModel
            existing_doc = self.db.query(DocumentModel).filter(
                DocumentModel.doc_id == doc_id
            ).first()
            
            if existing_doc and not target.update_existing:
                logger.info(f"Skipping existing document: {url}")
                return
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            
            if content_type in target.mime_filters:
                result_docs = self._process_document(url, response, content_type, target)
                if result_docs:
                    documents.extend(result_docs)
            
            if content_type == 'text/html' and depth < target.depth:
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    if href.startswith('/'):
                        from urllib.parse import urlparse
                        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                        href = base_url + href
                    elif not href.startswith(('http://', 'https://')):
                        if url.endswith('/'):
                            href = url + href
                        else:
                            href = url + '/' + href
                    
                    self._crawl_url(href, target, documents, depth + 1)
                    
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
    
    def _split_document(self, content: str, source_type: str, url: str, title: str = "", target: CrawlTarget = None) -> List[Document]:
        """大きなドキュメントを適切なサイズに分割する"""
        max_size = target.max_document_size or self.max_document_size
        logger.info(f"Splitting document from {url} with max size {max_size}")
        
        if len(content) <= max_size:
            doc_id = hashlib.sha256(url.encode()).hexdigest()
            return [Document(
                doc_id=doc_id,
                url=url,
                title=title,
                content=content,
                source_type=source_type,
                downloaded_at=datetime.now(),
                lang="en"
            )]
        
        docs = []
        chunks = []
        
        if source_type == "PDF":
            page_breaks = content.split("\f")
            current_chunk = ""
            
            for page in page_breaks:
                if len(current_chunk) + len(page) > max_size and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = page
                else:
                    current_chunk += page
            
            if current_chunk:
                chunks.append(current_chunk)
                
        elif source_type == "HTML":
            paragraphs = content.split("\n\n")
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 > max_size and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n\n"
                    current_chunk += para
            
            if current_chunk:
                chunks.append(current_chunk)
                
        else:
            for i in range(0, len(content), max_size):
                chunks.append(content[i:i+max_size])
        
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{url}_{i}".encode()).hexdigest()
            chunk_title = f"{title} (Part {i+1}/{len(chunks)})"
            
            docs.append(Document(
                doc_id=chunk_id,
                url=url,
                title=chunk_title,
                content=chunk,
                source_type=source_type,
                downloaded_at=datetime.now(),
                lang="en"
            ))
        
        logger.info(f"Document from {url} split into {len(docs)} parts")
        return docs
        
    def _process_document(self, url: str, response, content_type: str, target: CrawlTarget) -> List[Document]:
        """Process a document based on its content type and split if necessary"""
        try:
            doc_id = hashlib.sha256(url.encode()).hexdigest()
            
            if content_type == 'text/html':
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else url
                content = soup.get_text(separator='\n', strip=True)
                source_type = "HTML"
            
            elif content_type == 'application/pdf':
                title = url.split('/')[-1]
                try:
                    pdf_data = response.content
                    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
                    
                    content = ""
                    for page_num in range(len(pdf_document)):
                        page = pdf_document[page_num]
                        content += page.get_text()
                    
                    metadata = pdf_document.metadata
                    if metadata.get('title') and metadata.get('title').strip():
                        title = metadata.get('title')
                    
                    pdf_document.close()
                    
                    if not content.strip():
                        content = f"PDF from {url} appears to contain no extractable text (may be scanned or image-based)"
                        logger.warning(f"Empty content extracted from PDF: {url}")
                
                except Exception as e:
                    logger.error(f"Error extracting content from PDF {url}: {str(e)}")
                    content = f"Failed to extract content from PDF at {url}: {str(e)}"
                
                source_type = "PDF"
            
            else:
                title = url.split('/')[-1]
                content = f"Content from {url} - format {content_type}"
                source_type = content_type.split('/')[-1].upper()
            
            return self._split_document(
                content=content,
                source_type=source_type,
                url=url,
                title=title,
                target=target
            )
            
        except Exception as e:
            logger.error(f"Error processing document {url}: {str(e)}")
            return []
