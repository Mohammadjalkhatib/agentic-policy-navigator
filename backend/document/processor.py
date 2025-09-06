import os
import re
import hashlib
import PyPDF2
import docx
import pdfplumber
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List, Any, Optional
import time


class DocumentProcessor:
    """Processes documents and extracts content and metadata for indexing using alternative libraries."""

    def __init__(self):
        """Initialize the document processor with supported formats."""
        self.supported_extensions = {
            "text": [".txt", ".md", ".html", ".htm"],
            "office": [".docx"],
            "pdf": [".pdf"],
        }

        # Create temporary files directory if it doesn't exist
        self.temp_dir = "temp_uploads"
        os.makedirs(self.temp_dir, exist_ok=True)

    def is_supported_file(self, file_path: str) -> bool:
        """Check if the file type is supported by our system."""
        extension = Path(file_path).suffix.lower()
        return any(extension in exts for exts in self.supported_extensions.values())

    def process_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process a document and return its content and metadata.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing 'text' and 'metadata', or None if processing fails
        """
        try:
            if not self.is_supported_file(file_path):
                raise ValueError(f"Unsupported file type: {file_path}")

            # Check if file size is within allowed limit
            file_size = os.path.getsize(file_path)
            max_size = 20 * 1024 * 1024  # 20 MB
            if file_size > max_size:
                raise ValueError(f"File size exceeds maximum limit of 20 MB")

            extension = Path(file_path).suffix.lower()

            # Process file based on type
            if extension in self.supported_extensions["pdf"]:
                text_content = self._process_pdf(file_path)
            elif extension in self.supported_extensions["office"]:
                text_content = self._process_docx(file_path)
            elif extension in self.supported_extensions["text"]:
                text_content = self._process_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {extension}")

            if not text_content:
                return None

            # Get metadata
            file_stat = Path(file_path).stat()
            metadata = {
                "file_path": os.path.abspath(file_path),
                "file_name": Path(file_path).name,
                "file_type": extension,
                "file_size": file_stat.st_size,
                "last_modified": file_stat.st_mtime,
                "checksum": self._compute_file_checksum(file_path),
                "processing_date": int(time.time()),
                "source": "telegram_upload",
            }

            return {"text": text_content, "metadata": metadata}

        except Exception as e:
            print(f"Error processing document {file_path}: {str(e)}")
            return None

    def _process_pdf(self, file_path: str) -> str:
        """Process PDF file using pdfplumber for better text extraction."""
        text = ""
        try:
            # Try using pdfplumber first (for better text)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            # If pdfplumber fails, use PyPDF2 as fallback
            if not text.strip():
                with open(file_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error processing PDF {file_path}: {str(e)}")
            # Try using PyPDF2 as fallback
            try:
                with open(file_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                print(f"Secondary error processing PDF {file_path}: {str(e2)}")

        return text.strip()

    def _process_docx(self, file_path: str) -> str:
        """Process DOCX file using python-docx."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {str(e)}")
            return ""

    def _process_text(self, file_path: str) -> str:
        """Process text-based files (txt, html, etc.)."""
        extension = Path(file_path).suffix.lower()
        try:
            # Process regular text files
            if extension in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read().strip()

            # Process HTML files using BeautifulSoup
            elif extension in [".html", ".htm"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f, "html.parser")
                    # Remove script tags and invisible text
                    for script in soup(["script", "style"]):
                        script.decompose()
                    return soup.get_text(separator="\n", strip=True)

            return ""
        except Exception as e:
            print(f"Error processing text file {file_path}: {str(e)}")
            return ""

    def _compute_file_checksum(self, file_path: str) -> str:
        """Compute MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def batch_process(self, file_paths: list[str]) -> list[Dict[str, Any]]:
        """Process multiple documents in batch."""
        results = []
        for file_path in file_paths:
            result = self.process_file(file_path)
            if result:
                results.append(result)
        return results

    def save_temp_file(self, file_content: bytes, file_name: str) -> str:
        """Save temporary file and return its path."""
        temp_path = os.path.join(self.temp_dir, file_name)
        with open(temp_path, "wb") as f:
            f.write(file_content)
        return temp_path

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for file_name in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file_name)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting temp file {file_path}: {str(e)}")
