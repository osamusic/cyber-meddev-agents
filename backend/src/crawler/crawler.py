import requests
import hashlib
import mimetypes
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
from .models import CrawlTarget, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Crawler:
    """Crawler for medical device cybersecurity documents"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cyber-Med-Agent Crawler/1.0'
        })
        self.visited_urls = set()
        
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
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            
            if content_type in target.mime_filters:
                doc = self._process_document(url, response, content_type)
                if doc:
                    documents.append(doc)
            
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
    
    def _process_document(self, url: str, response, content_type: str) -> Optional[Document]:
        """Process a document based on its content type"""
        try:
            doc_id = hashlib.sha256(url.encode()).hexdigest()
            
            if content_type == 'text/html':
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else url
                content = soup.get_text(separator='\n', strip=True)
                source_type = "HTML"
            
            elif content_type == 'application/pdf':
                title = url.split('/')[-1]
                content = f"PDF content from {url} - will be extracted with PyMuPDF"
                source_type = "PDF"
            
            else:
                title = url.split('/')[-1]
                content = f"Content from {url} - format {content_type}"
                source_type = content_type.split('/')[-1].upper()
            
            lang = "en"  # Default to English
            
            return Document(
                doc_id=doc_id,
                url=url,
                title=title,
                content=content,
                source_type=source_type,
                downloaded_at=datetime.now(),
                lang=lang
            )
            
        except Exception as e:
            logger.error(f"Error processing document {url}: {str(e)}")
            return None
