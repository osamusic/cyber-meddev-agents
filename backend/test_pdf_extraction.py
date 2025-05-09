import fitz  # PyMuPDF
import requests
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_sample_pdf(url, save_path):
    """サンプルPDFをダウンロードする"""
    response = requests.get(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)
    logger.info(f"Downloaded PDF to {save_path}")
    return save_path

def extract_pdf_text(pdf_path):
    """PDFからテキストを抽出する"""
    pdf_document = fitz.open(pdf_path)
    
    content = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        page_text = page.get_text()
        content += page_text
        
        if '\f' in repr(page_text):
            logger.info(f"Page {page_num}: Form feed character found")
        else:
            logger.info(f"Page {page_num}: No form feed character")
    
    content_with_markers = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        page_text = page.get_text()
        content_with_markers += f"[PAGE_{page_num}]\n{page_text}\n[/PAGE_{page_num}]\n"
    
    pdf_document.close()
    
    return content, content_with_markers

def test_pdf_splitting(content, max_size=4000):
    """PDFの分割テスト"""
    pages_by_formfeed = content.split('\f')
    logger.info(f"Number of pages after splitting by form feed: {len(pages_by_formfeed)}")
    
    chunks = []
    for i in range(0, len(content), max_size):
        chunks.append(content[i:i+max_size])
    logger.info(f"Number of chunks after splitting by fixed size: {len(chunks)}")
    
    paragraphs = content.split('\n\n')
    current_chunk = ""
    para_chunks = []
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > max_size and current_chunk:
            para_chunks.append(current_chunk)
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para
    
    if current_chunk:
        para_chunks.append(current_chunk)
    
    logger.info(f"Number of chunks after splitting by paragraphs: {len(para_chunks)}")
    
    return pages_by_formfeed, chunks, para_chunks

def test_marker_based_splitting(content_with_markers, max_size=4000):
    """マーカーベースの分割テスト"""
    import re
    
    pages = re.split(r'\[/PAGE_\d+\]\n', content_with_markers)
    pages = [p for p in pages if p.strip()]  # 空のページを削除
    
    logger.info(f"Number of pages after splitting by markers: {len(pages)}")
    
    chunks = []
    current_chunk = ""
    
    for page in pages:
        if len(current_chunk) + len(page) > max_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = page
        else:
            current_chunk += page
    
    if current_chunk:
        chunks.append(current_chunk)
    
    logger.info(f"Number of chunks after marker-based splitting: {len(chunks)}")
    
    return chunks

if __name__ == "__main__":
    url = 'https://www.imdrf.org/sites/default/files/docs/imdrf/final/technical/imdrf-tech-200318-pp-mdc-n60.pdf'
    pdf_path = download_sample_pdf(url, '/tmp/sample.pdf')
    
    content, content_with_markers = extract_pdf_text(pdf_path)
    
    logger.info(f"Total content length: {len(content)} characters")
    logger.info(f"First 100 characters: {repr(content[:100])}")
    
    max_size = 4000
    logger.info(f"Testing splitting with max_size={max_size}")
    pages_by_formfeed, chunks, para_chunks = test_pdf_splitting(content, max_size)
    
    marker_chunks = test_marker_based_splitting(content_with_markers, max_size)
    
    logger.info("=== Splitting Results ===")
    logger.info(f"Form feed splitting: {len(pages_by_formfeed)} parts")
    logger.info(f"Fixed size splitting: {len(chunks)} parts")
    logger.info(f"Paragraph splitting: {len(para_chunks)} parts")
    logger.info(f"Marker-based splitting: {len(marker_chunks)} parts")
