import os
from pathlib import Path
from typing import Optional
from .processor import DocumentProcessor
from .indexer import get_or_create_index, document_exists
import logging

logger = logging.getLogger(__name__)


class DefaultDataLoader:
    def __init__(self):
        self.default_dir = Path(__file__).parent.parent / "data" / "default"
        self.processor = DocumentProcessor()

    def get_default_pdf_path(self) -> Optional[str]:
        """Get path to default PDF file if it exists."""
        if not self.default_dir.exists():
            return None

        for file in self.default_dir.glob("*.pdf"):
            return str(file)
        return None

    def load_default_content(self) -> bool:
        """
        Load default PDF content into the index if not already present.
        Returns True if successful, False otherwise.
        """
        try:
            # Get default PDF path
            pdf_path = self.get_default_pdf_path()

            # Add more detailed error logging
            if not pdf_path:
                logger.error("Default PDF file not found in data/default directory")
                return False

            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not accessible: {pdf_path}")
                return False

            # Add file size check
            file_size = os.path.getsize(pdf_path)
            if file_size > (20 * 1024 * 1024):  # 20MB limit
                logger.error(f"PDF file too large: {file_size/1024/1024:.2f}MB")
                return False

            index = get_or_create_index()

            # Check if document already exists in index
            file_path = os.path.abspath(pdf_path)
            metadata = {"file_path": file_path}

            if document_exists(index, metadata):
                logger.info("Default content already indexed")
                return True

            # Process the PDF
            result = self.processor.process_file(pdf_path)
            if not result:
                logger.error("Failed to process default PDF")
                return False

            # Add metadata
            result["metadata"]["source"] = "default_content"

            # Index the content
            from .indexer import process_and_upsert_document

            index_result = process_and_upsert_document(index, result)

            success = index_result["status"] == "success"
            if success:
                logger.info("Successfully loaded default content")
            else:
                logger.error(
                    f"Failed to index default content: {index_result['message']}"
                )

            return success

        except Exception as e:
            logger.error(f"Error loading default content: {str(e)}", exc_info=True)
            return False
