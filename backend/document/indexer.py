import os
import re
import hashlib
from typing import Any, Dict, List, Optional

from config.secrets import AIxPLAIN_API_KEY, DEFAULT_INDEX_ID
from config.settings import INDEXING

if AIxPLAIN_API_KEY and not os.environ.get("AIxPLAIN_API_KEY"):
    os.environ["AIxPLAIN_API_KEY"] = AIxPLAIN_API_KEY
    os.environ["TEAM_API_KEY"] = AIxPLAIN_API_KEY

from aixplain.factories import IndexFactory
from aixplain.modules.model.record import Record
from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator


def get_or_create_index(index_name: str = INDEXING.get("INDEX_NAME")) -> Any:
    """
    Get an existing index by DEFAULT_INDEX_ID, then by name, or create a new one.
    """
    try:
        # 1) Try to get index using DEFAULT_INDEX_ID (if specified)
        if DEFAULT_INDEX_ID:
            try:
                idx = IndexFactory.get(DEFAULT_INDEX_ID)
                return idx
            except Exception:
                # Failed to get default index - continue trying
                pass

        # 2) Search for index by name
        try:
            indexes = IndexFactory.list().get("results", [])
            for idx in indexes:
                if getattr(idx, "name", None) == index_name:
                    return idx
        except Exception:
            # Ignore index list errors and continue to creation attempt
            pass

        # 3) Create new index (use correct EMBEDDING_MODEL key)
        embedding_model = INDEXING.get("EMBEDDING_MODEL")
        new_index = IndexFactory.create(
            name=index_name,
            description="Knowledge base for document storage and retrieval",
            embedding_model=embedding_model,
        )
        return new_index

    except Exception as e:
        raise RuntimeError(f"Error managing index: {str(e)}")


def compute_document_checksum(text: str) -> str:
    """
    Compute document checksum for change detection.

    Args:
        text: Document text to hash

    Returns:
        MD5 checksum of the text
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def document_exists(index: Any, metadata: Dict[str, Any]) -> bool:
    """
    Check if a document already exists in the index using metadata.

    Args:
        index: Index object to search
        meta Document metadata containing file_path

    Returns:
        True if document exists, False otherwise
    """
    if "file_path" not in metadata:
        return False

    # Create filter to search for the document
    filters = [
        IndexFilter(
            field="file_path",
            value=metadata["file_path"],
            operator=IndexFilterOperator.EQUALS,
        )
    ]

    # Search the index
    try:
        response = index.search(query="", top_k=1, filters=filters)

        # If we found a result, the document exists
        return len(response.details) > 0
    except Exception:
        return False


def chunk_text(text: str, max_chunk_size: int = 200, overlap: int = 20) -> List[str]:
    """
    Split text into chunks while preserving context.

    Args:
        text: Input text to chunk
        max_chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    # Split text into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        # If sentence is longer than allowed size, split it
        if len(sentence) > max_chunk_size:
            words = sentence.split()
            temp_chunk = []
            temp_size = 0

            for word in words:
                if temp_size + len(word) + 1 > max_chunk_size:
                    if temp_chunk:
                        chunks.append(" ".join(temp_chunk))
                    temp_chunk = [word]
                    temp_size = len(word)
                else:
                    temp_chunk.append(word)
                    temp_size += len(word) + 1

            if temp_chunk:
                chunks.append(" ".join(temp_chunk))
        else:
            # Add sentence to current chunk if size is appropriate
            if current_size + len(sentence) + 1 <= max_chunk_size or not current_chunk:
                current_chunk.append(sentence)
                current_size += len(sentence) + 1
            else:
                # Save current chunk and start a new one
                chunks.append(" ".join(current_chunk))
                # Add slight overlap with next chunk to preserve context
                overlap_sentences = (
                    current_chunk[-(overlap // 50) :]
                    if len(current_chunk) > overlap // 50
                    else current_chunk
                )
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) + 1 for s in current_chunk)

    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def process_and_upsert_document(
    index: Any, document_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process and upsert a document into the index after checking if it exists.

    Args:
        index: Target index object
        document_ Dictionary containing 'text' and 'metadata'

    Returns:
        Dictionary with operation status and details
    """
    text = document_data.get("text", "")
    metadata = document_data.get("metadata", {})

    # Ensure required fields are present
    if not text:
        return {"status": "error", "message": "Text content is required in JSON input"}

    # Ensure file_path and file_size are in metadata
    if "file_size" not in metadata:
        metadata["file_size"] = len(text)
    if "file_path" not in metadata:
        metadata["file_path"] = "unknown_path"

    # Check if document already exists in the index
    if document_exists(index, metadata):
        return {
            "status": "skipped",
            "message": "Document already exists in the index. Skipping insertion.",
            "file_path": metadata["file_path"],
        }

    # Split text into chunks
    chunks = chunk_text(text)

    # Create records for insertion
    records = []
    for i, chunk in enumerate(chunks):
        # Create unique ID for the record
        chunk_id = (
            f"{metadata.get('id', 'doc')}_{i}"
            if "id" in metadata
            else f"{hashlib.md5(metadata['file_path'].encode()).hexdigest()}_{i}"
        )

        # Create record with metadata
        record = Record(
            id=chunk_id,
            value=chunk,
            attributes={
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "document_checksum": compute_document_checksum(text),
            },
        )
        records.append(record)

    # Insert records into the index
    try:
        index.upsert(records)
        return {
            "status": "success",
            "message": f"Successfully added {len(chunks)} chunks to the index",
            "index_id": index.id,
            "total_chunks": len(chunks),
            "file_path": metadata["file_path"],
            "file_size": metadata["file_size"],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error inserting document: {str(e)}",
            "file_path": metadata["file_path"],
        }
