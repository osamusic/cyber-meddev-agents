import requests
import hashlib
import os
import urllib.parse
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
import fitz  # PyMuPDF

from .models import CrawlTarget, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Crawler:
    """Crawler for cybersecurity-related medical documents from the web."""

    DEFAULT_HEADERS = {
        'User-Agent': 'Cyber-Med-Agent Crawler/1.0'
    }

    def __init__(self, db=None, target=None):
        self.session = self._init_session()
        self.visited_urls = set()
        self.db = db
        self.max_document_size = int(os.getenv("MAX_DOCUMENT_SIZE", "4000"))
        if target and target.max_document_size:
            self.max_document_size = target.max_document_size

    def _init_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(self.DEFAULT_HEADERS)
        return session

    def crawl(self, target: CrawlTarget) -> List[Document]:
        """Crawl a target URL and return extracted documents."""
        logger.info(f"Starting crawl for {target.url}")
        documents = []
        try:
            self._crawl_url(target.url, target, documents, depth=0)
        except Exception as e:
            logger.error(f"Error crawling {target.url}: {str(e)}")
        logger.info(f"Crawl completed. Found {len(documents)} documents")
        return documents

    def _crawl_url(self, url: str, target: CrawlTarget, documents: List[Document], depth: int) -> None:
        """Recursively crawl a URL up to the specified depth."""
        if depth > target.depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        logger.info(f"Crawling {url} (depth {depth})")

        if not self._should_crawl_url(url, target):
            return

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '').split(';')[0]

            if content_type in target.mime_filters:
                processed_docs = self._process_document(url, response, content_type, target)
                if processed_docs:
                    documents.extend(processed_docs)

            if content_type == 'text/html' and depth < target.depth:
                self._follow_links(response, url, target, documents, depth)

        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")

    def _should_crawl_url(self, url: str, target: CrawlTarget) -> bool:
        """Determine whether to crawl or skip based on the DB and update flags."""
        doc_id = hashlib.sha256(url.encode()).hexdigest()

        if self.db:
            from ..db.models import DocumentModel
            existing_doc = self.db.query(DocumentModel).filter_by(doc_id=doc_id).first()
            if existing_doc and not target.update_existing:
                logger.info(f"Skipping existing document: {url}")
                return False
        return True

    def _follow_links(self, response, base_url: str, target: CrawlTarget, documents: List[Document], depth: int) -> None:
        """Parse and recursively follow links on an HTML page."""
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = self._normalize_link(base_url, link['href'])
            self._crawl_url(href, target, documents, depth + 1)

    def _normalize_link(self, base_url: str, href: str) -> str:
        """Return an absolute URL based on the base URL and href."""
        if href.startswith('/'):
            parsed_base = urllib.parse.urlparse(base_url)
            return f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
        elif not href.startswith(('http://', 'https://')):
            return urllib.parse.urljoin(base_url + '/', href)
        return href

    def _clean_title(self, title: str, max_length: int = 100) -> str:
        """Clean and truncate document titles for standardization."""
        title = urllib.parse.unquote(title)
        match = re.match(r"(.+?)(\.[^.]+)?$", title)
        base, ext = match.groups() if match else (title, "")
        base = re.sub(r"[^\w\s\-ぁ-んァ-ン一-龯]", "", base)
        base = re.sub(r"[_\s]+", " ", base).strip()
        return base[:max_length].rstrip()

    def _process_document(self, url: str, response, content_type: str, target: CrawlTarget) -> List[Document]:
        """Convert a downloaded file into Document(s) depending on type."""
        try:
            title = url.split('/')[-1]
            toc_info, content, original_title = None, "", None

            if content_type == 'text/html':
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string if soup.title else url
                content = soup.get_text(separator='\n', strip=True)
                source_type = "HTML"

            elif content_type == 'application/pdf':
                source_type = "PDF"
                pdf_data = response.content
                try:
                    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
                    toc_info = self._extract_pdf_toc(pdf_document)
                    content, original_title = self._extract_pdf_text(pdf_document, url)
                    pdf_document.close()
                except Exception as e:
                    logger.error(f"Error extracting content from PDF {url}: {str(e)}")
                    content = f"Failed to extract content from PDF at {url}: {str(e)}"
                    original_title = title

            else:
                source_type = content_type.split('/')[-1].upper()
                content = f"Content from {url} - format {content_type}"
                original_title = title

            return self._split_document(
                content=content,
                source_type=source_type,
                url=url,
                title=self._clean_title(title),
                target=target,
                toc_info=toc_info,
                original_title=self._clean_title(original_title)
            )

        except Exception as e:
            logger.error(f"Error processing document {url}: {str(e)}")
            return []

    def _extract_pdf_toc(self, pdf_document) -> Optional[List[Dict]]:
        """Extract the Table of Contents from a PDF, if available."""
        toc = pdf_document.get_toc()
        if not toc:
            return None
        logger.info(f"PDF has TOC with {len(toc)} entries")
        return [
            {
                "level": level,
                "title": title,
                "page_num": page_num,
                "text": pdf_document[page_num].get_text() if 0 <= page_num < len(pdf_document) else ""
            }
            for level, title, page_num in toc
        ]

    def _extract_pdf_text(self, pdf_document, url: str) -> (str, Optional[str]):
        """Extracts all pages from a PDF as labeled text, returns text and original title."""
        content = ""
        for page_num in range(len(pdf_document)):
            text = pdf_document[page_num].get_text()
            content += f"[PAGE_{page_num}]\n{text}\n[/PAGE_{page_num}]\n"

        meta_title = pdf_document.metadata.get('title', '').strip()
        if not content.strip():
            logger.warning(f"No extractable text in PDF: {url}")
            content = f"PDF from {url} appears to contain no extractable text"
        return content, meta_title or url.split('/')[-1]

    def _split_document(
        self,
        content: str,
        source_type: str,
        url: str,
        title: str = "",
        target: Optional[CrawlTarget] = None,
        toc_info: Optional[List[Dict]] = None,
        original_title: Optional[str] = None
    ) -> List[Document]:
        """Split a document into multiple smaller parts if it exceeds the max size."""
        max_size = target.max_document_size if target and target.max_document_size else self.max_document_size
        logger.info(f"Splitting document from {url} (max {max_size} chars), content length: {len(content)}")

        original_title = original_title or title
        if len(content) <= max_size:
            doc_id = hashlib.sha256(url.encode()).hexdigest()
            return [Document(
                doc_id=doc_id,
                url=url,
                title=title,
                original_title=original_title,
                content=content,
                source_type=source_type,
                downloaded_at=datetime.now(),
                lang="en"
            )]

        docs = []
        chunks = self._split_content_by_type(content, source_type, max_size, title, toc_info)

        for i, chunk in enumerate(chunks):
            chunk_title = f"{chunk['title']} (Part {i + 1}/{len(chunks)})" if chunk['title'] == title else chunk['title']
            chunk_id = hashlib.sha256(f"{url}_{i}".encode()).hexdigest()

            docs.append(Document(
                doc_id=chunk_id,
                url=url,
                title=chunk_title,
                original_title=original_title,
                content=chunk['content'],
                source_type=source_type,
                downloaded_at=datetime.now(),
                lang="en"
            ))

        logger.info(f"Split document into {len(docs)} parts, avg size: {sum(len(d.content) for d in docs) // len(docs)} chars")
        return docs

    def _split_content_by_type(
        self,
        content: str,
        source_type: str,
        max_size: int,
        title: str,
        toc_info: Optional[List[Dict]]
    ) -> List[Dict[str, str]]:
        """Split content according to document type and optional TOC."""
        chunks = []

        if source_type == "PDF" and toc_info:
            logger.info(f"Using TOC-based split: {len(toc_info)} entries")
            chapters = []
            current = None

            for entry in toc_info:
                if entry["level"] == 1:
                    if current:
                        chapters.append(current)
                    current = {
                        "title": entry["title"],
                        "content": f"[CHAPTER: {entry['title']}]\n{entry['text']}",
                        "page_nums": {entry["page_num"]}
                    }
                elif current:
                    current["content"] += f"\n[SECTION: {entry['title']}]\n{entry['text']}"
                    current["page_nums"].add(entry["page_num"])

            if current:
                chapters.append(current)

            for chapter in chapters:
                if len(chapter["content"]) <= max_size:
                    chunks.append({"title": chapter["title"], "content": chapter["content"]})
                else:
                    paras = chapter["content"].split("\n\n")
                    chunk, count = "", 1
                    for para in paras:
                        if len(chunk) + len(para) > max_size and chunk:
                            chunks.append({
                                "title": f"{chapter['title']} (Part {count})",
                                "content": chunk
                            })
                            chunk, count = para, count + 1
                        else:
                            chunk = f"{chunk}\n\n{para}".strip()
                    if chunk:
                        chunks.append({
                            "title": f"{chapter['title']} (Part {count})",
                            "content": chunk
                        })

        elif source_type == "PDF":
            pages = re.split(r'\[/PAGE_\d+\]\n', content)
            current = ""
            for page in filter(str.strip, pages):
                if len(current) + len(page) > max_size and current:
                    chunks.append({"title": title, "content": current})
                    current = page
                else:
                    current += page
            if current:
                chunks.append({"title": title, "content": current})

        elif source_type == "HTML":
            paras = content.split("\n\n")
            current = ""
            for para in paras:
                if len(current) + len(para) > max_size and current:
                    chunks.append({"title": title, "content": current})
                    current = para
                else:
                    current = f"{current}\n\n{para}".strip()
            if current:
                chunks.append({"title": title, "content": current})

        else:
            chunks = [
                {"title": title, "content": content[i:i + max_size]}
                for i in range(0, len(content), max_size)
            ]

        return chunks
