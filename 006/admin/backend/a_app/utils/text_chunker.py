"""
Text chunking utilities for processing text documents.
Provides optimized chunking strategies for different document types.
"""
import logging
import re
from typing import List, Callable, Optional, Dict, Any, Tuple, Set

# Try to import langchain text splitters
try:
    # Try newer langchain_text_splitters package first
    from langchain_text_splitters import (
        RecursiveCharacterTextSplitter,
        MarkdownTextSplitter,
        MarkdownHeaderTextSplitter
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Fall back to older langchain package structure
        from langchain.text_splitter import (
            RecursiveCharacterTextSplitter,
            MarkdownTextSplitter,
            MarkdownHeaderTextSplitter
        )
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        print("Langchain text splitters not found. Chunking functionality will be limited.")

# Set up logging
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CHUNK_SIZE_BYTES = 1024  # Default chunk size in bytes
DEFAULT_OVERLAP_RATIO = 0.1     # Default overlap as a ratio of chunk size
MIN_CHUNK_SIZE_BYTES = 100      # Minimum allowed chunk size
MAX_CHUNK_SIZE_BYTES = 8192     # Maximum recommended chunk size

# Special content patterns
CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```')  # Matches Markdown code blocks
TABLE_PATTERN = re.compile(r'\|[^\|]+\|[^\|]+\|[\s\S]*?(?:\n\n|$)')  # Matches Markdown tables
MATH_BLOCK_PATTERN = re.compile(r'\$\$[\s\S]*?\$\$')  # Matches math blocks


class ChunkerConfig:
    """
    Configuration class for text chunking parameters.
    """
    def __init__(
        self,
        chunk_size_bytes: int = DEFAULT_CHUNK_SIZE_BYTES,
        overlap_ratio: float = DEFAULT_OVERLAP_RATIO,
        respect_special_blocks: bool = True,
        preserve_markdown_structure: bool = True,
        language: str = 'auto'
    ):
        """
        Initialize chunker configuration.

        Args:
            chunk_size_bytes: Target size of each chunk in bytes
            overlap_ratio: Ratio of overlap between chunks (0.0 to 0.5)
            respect_special_blocks: Whether to keep code blocks, tables, etc. intact
            preserve_markdown_structure: Whether to preserve Markdown structure
            language: Language of the text ('auto', 'en', 'zh', etc.)
        """
        # Validate and set chunk size
        if chunk_size_bytes < MIN_CHUNK_SIZE_BYTES:
            logger.warning(f"Chunk size {chunk_size_bytes} bytes is too small. Using minimum: {MIN_CHUNK_SIZE_BYTES}")
            self.chunk_size_bytes = MIN_CHUNK_SIZE_BYTES
        elif chunk_size_bytes > MAX_CHUNK_SIZE_BYTES:
            logger.warning(f"Chunk size {chunk_size_bytes} bytes is very large. This may affect performance.")
            self.chunk_size_bytes = chunk_size_bytes
        else:
            self.chunk_size_bytes = chunk_size_bytes

        # Validate and set overlap ratio
        if overlap_ratio < 0.0:
            logger.warning(f"Overlap ratio {overlap_ratio} is negative. Using 0.0.")
            self.overlap_ratio = 0.0
        elif overlap_ratio > 0.5:
            logger.warning(f"Overlap ratio {overlap_ratio} is too large. Using maximum: 0.5")
            self.overlap_ratio = 0.5
        else:
            self.overlap_ratio = overlap_ratio

        # Calculate overlap bytes
        self.overlap_bytes = int(self.chunk_size_bytes * self.overlap_ratio)

        # Other settings
        self.respect_special_blocks = respect_special_blocks
        self.preserve_markdown_structure = preserve_markdown_structure
        self.language = language


def get_byte_length(text: str) -> int:
    """
    Get the byte length of a string when encoded as UTF-8.

    Args:
        text: The text to measure

    Returns:
        The byte length
    """
    return len(text.encode('utf-8'))


def extract_special_blocks(text: str) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """
    Extract special blocks (code blocks, tables, math) from text and replace with placeholders.
    This helps preserve these blocks during chunking.

    Args:
        text: The text to process

    Returns:
        Tuple containing:
        - Processed text with placeholders
        - Dictionary mapping placeholders to original content
        - Dictionary with metadata about each block
    """
    if not text or not text.strip():
        return text, {}, {}

    # Initialize
    processed_text = text
    blocks = {}
    metadata = {}

    # Process code blocks
    code_blocks = CODE_BLOCK_PATTERN.findall(text)
    for i, block in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        blocks[placeholder] = block
        metadata[placeholder] = {"type": "code", "length": get_byte_length(block)}
        processed_text = processed_text.replace(block, placeholder, 1)

    # Process tables
    tables = TABLE_PATTERN.findall(processed_text)
    for i, block in enumerate(tables):
        placeholder = f"__TABLE_BLOCK_{i}__"
        blocks[placeholder] = block
        metadata[placeholder] = {"type": "table", "length": get_byte_length(block)}
        processed_text = processed_text.replace(block, placeholder, 1)

    # Process math blocks
    math_blocks = MATH_BLOCK_PATTERN.findall(processed_text)
    for i, block in enumerate(math_blocks):
        placeholder = f"__MATH_BLOCK_{i}__"
        blocks[placeholder] = block
        metadata[placeholder] = {"type": "math", "length": get_byte_length(block)}
        processed_text = processed_text.replace(block, placeholder, 1)

    return processed_text, blocks, metadata


def restore_special_blocks(text: str, blocks: Dict[str, str]) -> str:
    """
    Restore special blocks from placeholders.

    Args:
        text: Text with placeholders
        blocks: Dictionary mapping placeholders to original content

    Returns:
        Text with original content restored
    """
    if not blocks:
        return text

    result = text
    for placeholder, content in blocks.items():
        result = result.replace(placeholder, content)

    return result


class TextChunker:
    """
    Utility class for chunking text documents into smaller pieces.
    Supports different chunking strategies based on document type.
    """

    @staticmethod
    def chunk_markdown(markdown_text: str, config: Optional[ChunkerConfig] = None) -> List[str]:
        """
        Chunk markdown text, prioritizing semantic boundaries (headings, paragraphs, tables).

        Strategy:
        1. Extract and preserve special blocks (code, tables, math) if configured
        2. Split by headings (H1-H6)
        3. Combine adjacent heading chunks if they don't exceed max_chunk_size_bytes
        4. For heading chunks that *still* exceed max_chunk_size_bytes:
           a. Try using MarkdownTextSplitter (respects paragraphs, lists, etc.)
           b. If any resulting chunks are *still* too large, use RecursiveCharacterTextSplitter
              on those specific oversized chunks as a final fallback
        5. Restore special blocks if they were extracted
        6. Perform final size validation

        Args:
            markdown_text: The markdown text to chunk
            config: Chunking configuration (uses defaults if None)

        Returns:
            A list of markdown text chunks
        """
        # Use default config if none provided
        if config is None:
            config = ChunkerConfig()

        # Shorthand for readability
        max_chunk_size_bytes = config.chunk_size_bytes
        overlap_bytes = config.overlap_bytes
        # Handle empty or whitespace-only text
        if not markdown_text or not markdown_text.strip():
            logger.warning("Empty or whitespace-only markdown text provided.")
            return []

        # --- 1. Extract special blocks if configured ---
        blocks = {}
        blocks_metadata = {}
        processed_text = markdown_text

        if config.respect_special_blocks:
            processed_text, blocks, blocks_metadata = extract_special_blocks(markdown_text)
            logger.debug(f"Extracted {len(blocks)} special blocks from markdown text")

        # --- 2. Check if Langchain is available ---
        if not LANGCHAIN_AVAILABLE:
            logger.warning("Langchain text splitters not available. Falling back to simple size-based splitting.")
            # Basic fallback: split purely by size
            chunks = []
            text_bytes = processed_text.encode('utf-8')
            for i in range(0, len(text_bytes), max_chunk_size_bytes):
                chunk = text_bytes[i:i + max_chunk_size_bytes].decode('utf-8', errors='ignore')
                # Restore special blocks if they were extracted
                if config.respect_special_blocks:
                    chunk = restore_special_blocks(chunk, blocks)
                chunks.append(chunk)
            return chunks

        # --- 3. Check if entire document fits ---
        doc_size = get_byte_length(processed_text)
        if doc_size <= max_chunk_size_bytes:
            logger.info(f"Document size ({doc_size} bytes) is within max_chunk_size ({max_chunk_size_bytes}). Returning as single chunk.")
            # Restore special blocks if they were extracted
            if config.respect_special_blocks:
                processed_text = restore_special_blocks(processed_text, blocks)
            return [processed_text]

        # --- 4. Define headers to split on ---
        headers_to_split_on = [
            {"level": 1, "name": "Header 1", "tag": "#"},
            {"level": 2, "name": "Header 2", "tag": "##"},
            {"level": 3, "name": "Header 3", "tag": "###"},
            {"level": 4, "name": "Header 4", "tag": "####"},
            {"level": 5, "name": "Header 5", "tag": "#####"},
            {"level": 6, "name": "Header 6", "tag": "######"},
        ]

        # --- 5. Perform initial split by headers ---
        try:
            if not config.preserve_markdown_structure:
                # Skip header-based splitting if not preserving structure
                logger.info("Skipping header-based splitting as preserve_markdown_structure=False")
                raise ValueError("Skipping header-based splitting")

            header_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on,  # Split on these headers
                strip_headers=False,  # Keep headers in content for context
                return_each_line=False  # Process chunks, not lines
            )
            # Langchain splitters return 'Document' objects. We need page_content.
            header_splits_docs = header_splitter.split_text(processed_text)
            # Handle case where splitter might return objects without page_content or empty content
            header_splits = [doc.page_content for doc in header_splits_docs if hasattr(doc, 'page_content') and doc.page_content]

            if not header_splits:
                # If header splitting produced nothing (e.g., no headers), treat the whole document as one section
                logger.warning("MarkdownHeaderTextSplitter produced no sections. Treating document as a single section.")
                header_splits = [processed_text]
            else:
                logger.info(f"Initial header splitting created {len(header_splits)} sections.")

        except Exception as e:
            logger.warning(f"MarkdownHeaderTextSplitter failed: {e}. Falling back to recursive splitting of entire document.")
            # If header splitting fails, fall back to splitting the entire document
            chunks = TextChunker._recursive_markdown_aware_split(processed_text, max_chunk_size_bytes, overlap_bytes)

            # Restore special blocks if they were extracted
            if config.respect_special_blocks:
                chunks = [restore_special_blocks(chunk, blocks) for chunk in chunks]

            return chunks

        # --- 6. Process header-based splits: combine small ones, split large ones ---
        final_chunks = []          # Final list of chunks
        current_chunk_content = "" # Content of current chunk being built
        current_chunk_size = 0     # Size of current chunk (bytes)

        for i, section_content in enumerate(header_splits):
            if not section_content.strip():  # Skip empty sections
                continue

            section_size = get_byte_length(section_content)  # Size of current section

            # Case A: Current section is *itself* too large
            if section_size > max_chunk_size_bytes:
                logger.info(f"Section {i+1} ({section_size} bytes) exceeds max_chunk_size ({max_chunk_size_bytes}). Recursively splitting (markdown-aware).")
                # If there's accumulated content in current_chunk_content, finalize it first
                if current_chunk_content:
                    final_chunks.append(current_chunk_content)
                    current_chunk_content = ""  # Reset current chunk
                    current_chunk_size = 0

                # --- Optimized splitting of large chunk ---
                sub_chunks = TextChunker._recursive_markdown_aware_split(section_content, max_chunk_size_bytes, overlap_bytes)
                final_chunks.extend(sub_chunks)  # Add sub-chunks to final list
                # Reset current chunk content since this large chunk has been processed
                current_chunk_content = ""
                current_chunk_size = 0
                continue  # Process next header section

            # Case B: Adding this section would make current chunk too large
            elif current_chunk_size + section_size > max_chunk_size_bytes and current_chunk_content:
                # Finalize current chunk before it gets too large
                final_chunks.append(current_chunk_content)
                # Start new chunk with this section
                current_chunk_content = section_content
                current_chunk_size = section_size

            # Case C: Section can be added to current chunk
            else:
                # If there's already content, add a newline separator
                if current_chunk_content:
                    current_chunk_content += "\n\n"
                    current_chunk_size += 2  # Account for newlines
                # Add this section to current chunk
                current_chunk_content += section_content
                current_chunk_size += section_size

        # Don't forget to add the last chunk if it has content
        if current_chunk_content:
            final_chunks.append(current_chunk_content)

        # --- 7. Final validation: ensure no chunk exceeds the size limit ---
        verified_chunks = []
        for chunk in final_chunks:
            chunk_size = get_byte_length(chunk)
            if chunk_size <= max_chunk_size_bytes:
                verified_chunks.append(chunk)
            else:
                # This shouldn't happen with our algorithm, but just in case
                logger.warning(f"Found chunk of size {chunk_size} bytes after processing. Splitting further.")
                sub_chunks = TextChunker._recursive_markdown_aware_split(chunk, max_chunk_size_bytes, overlap_bytes)
                verified_chunks.extend(sub_chunks)

        # --- 8. Restore special blocks if they were extracted ---
        if config.respect_special_blocks and blocks:
            verified_chunks = [restore_special_blocks(chunk, blocks) for chunk in verified_chunks]

        logger.info(f"Markdown processed into {len(verified_chunks)} final chunks.")
        # Log min/max/avg chunk sizes for tuning
        if verified_chunks:
            chunk_sizes = [get_byte_length(c) for c in verified_chunks]
            logger.info(f"Chunk size stats (bytes): min={min(chunk_sizes)}, max={max(chunk_sizes)}, avg={sum(chunk_sizes)/len(chunk_sizes):.2f}")
        return verified_chunks

    @staticmethod
    def _recursive_markdown_aware_split(text: str, max_chunk_size_bytes: int, overlap_bytes: int,
                                        language: str = 'auto') -> List[str]:
        """
        Recursively split text, prioritizing Markdown structure, then falling back.

        Args:
            text: The text to split
            max_chunk_size_bytes: Maximum chunk size (bytes)
            overlap_bytes: Overlap size (bytes)
            language: Language of the text for better splitting

        Returns:
            List of text chunks
        """
        # Handle empty or whitespace-only text
        if not text or not text.strip():
            return []

        # Handle text that already fits in a chunk
        if get_byte_length(text) <= max_chunk_size_bytes:
            return [text]

        if not LANGCHAIN_AVAILABLE:  # Safety check
            logger.warning("Langchain splitters unavailable in _recursive_markdown_aware_split. Using basic splitting.")
            # Basic fallback: split purely by size
            chunks = []
            text_bytes = text.encode('utf-8')
            for i in range(0, len(text_bytes), max_chunk_size_bytes):
                chunk = text_bytes[i:i + max_chunk_size_bytes].decode('utf-8', errors='ignore')
                if chunk.strip():
                    chunks.append(chunk)
            return chunks

        # Determine language-specific separators
        if language == 'zh' or language == 'ja' or language == 'ko':
            # For Chinese, Japanese, Korean: character-level splitting is more appropriate
            # as these languages don't use spaces between words
            separators = ["\n\n", "\n", "。", "，", "、", ""]
        else:
            # Default separators for most languages
            separators = ["\n\n", "\n", ". ", ", ", " ", ""]

        initial_chunks = []
        try:
            # --- Attempt 1: MarkdownTextSplitter ---
            # This splitter understands Markdown structures like paragraphs, lists, code blocks.
            markdown_splitter = MarkdownTextSplitter(
                chunk_size=max_chunk_size_bytes,  # Target size (bytes)
                chunk_overlap=overlap_bytes,      # Overlap size (bytes)
                length_function=get_byte_length   # Key: use byte length
            )
            initial_chunks = markdown_splitter.split_text(text)
            logger.debug(f"Attempted splitting with MarkdownTextSplitter, got {len(initial_chunks)} chunks.")

        except Exception as e:
            logger.warning(f"MarkdownTextSplitter failed during recursive splitting: {e}. Continuing with RecursiveCharacterTextSplitter.")
            initial_chunks = [text]  # Treat as one chunk, to be split by next stage

        # --- Attempt 2: RecursiveCharacterTextSplitter (fallback) ---
        # If MarkdownTextSplitter fails or produces chunks that are still too large,
        # use RecursiveCharacterTextSplitter as a fallback.
        final_sub_chunks = []
        needs_recursive_fallback = False  # Flag if fallback is needed

        if not initial_chunks:  # If MarkdownTextSplitter produced nothing
            needs_recursive_fallback = True
            initial_chunks = [text]  # Prepare original text for fallback splitter

        # Check if any chunks from MarkdownTextSplitter are still too large
        oversized_chunks = []
        valid_chunks = []
        for chunk in initial_chunks:
            if get_byte_length(chunk) > max_chunk_size_bytes:
                needs_recursive_fallback = True
                oversized_chunks.append(chunk)
            elif chunk.strip():  # Keep valid non-empty chunks
                valid_chunks.append(chunk)

        if needs_recursive_fallback:
            logger.debug(f"Falling back to RecursiveCharacterTextSplitter for {len(oversized_chunks)} oversized chunks.")
            recursive_splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_chunk_size_bytes,
                chunk_overlap=overlap_bytes,
                length_function=get_byte_length,  # Use byte length
                separators=separators,  # Language-aware separators
                keep_separator=True  # Keep separator to better maintain structure
            )

            # Process only the oversized chunks
            processed_chunks = []
            for chunk in oversized_chunks:
                split_result = recursive_splitter.split_text(chunk)
                processed_chunks.extend(split_result)

            # Combine valid chunks with processed oversized chunks
            final_sub_chunks = valid_chunks + processed_chunks
        else:
            # If MarkdownTextSplitter worked well and all chunks are within size limit
            final_sub_chunks = valid_chunks

        # Sort chunks to maintain original document order if possible
        # This assumes chunks contain some position information from the original text
        # final_sub_chunks.sort(key=lambda x: text.find(x[:min(50, len(x))]) if x[:min(50, len(x))] in text else float('inf'))

        # Finally filter out empty strings and ensure no chunk exceeds the limit
        result = []
        for chunk in final_sub_chunks:
            if not chunk.strip():
                continue

            chunk_size = get_byte_length(chunk)
            if chunk_size <= max_chunk_size_bytes:
                result.append(chunk)
            else:
                # This is a safety check that shouldn't be needed, but just in case
                logger.warning(f"Found chunk of size {chunk_size} bytes after recursive splitting. Performing emergency split.")
                # Emergency split by bytes
                chunk_bytes = chunk.encode('utf-8')
                for i in range(0, len(chunk_bytes), max_chunk_size_bytes):
                    sub_chunk = chunk_bytes[i:i + max_chunk_size_bytes].decode('utf-8', errors='ignore')
                    if sub_chunk.strip():
                        result.append(sub_chunk)

        return result

    @staticmethod
    def chunk_text(text: str, config: Optional[ChunkerConfig] = None) -> List[str]:
        """
        Chunk plain text, trying to respect paragraph and sentence boundaries.

        Args:
            text: The text to chunk
            config: Chunking configuration (uses defaults if None)

        Returns:
            List of text chunks
        """
        # Use default config if none provided
        if config is None:
            config = ChunkerConfig()

        # Shorthand for readability
        max_chunk_size_bytes = config.chunk_size_bytes
        overlap_bytes = config.overlap_bytes
        language = config.language

        # Handle empty or whitespace-only text
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text provided.")
            return []

        # Check if entire text fits in one chunk
        if get_byte_length(text) <= max_chunk_size_bytes:
            return [text]

        # Determine language-specific separators
        if language == 'zh' or language == 'ja' or language == 'ko':
            # For Chinese, Japanese, Korean: character-level splitting is more appropriate
            separators = ["\n\n", "\n", "。", "，", "、", ""]
        else:
            # Default separators for most languages
            separators = ["\n\n", "\n", ". ", ", ", " ", ""]

        if not LANGCHAIN_AVAILABLE:
            # Basic fallback: split purely by size
            chunks = []
            text_bytes = text.encode('utf-8')
            for i in range(0, len(text_bytes), max_chunk_size_bytes):
                chunk = text_bytes[i:i + max_chunk_size_bytes].decode('utf-8', errors='ignore')
                if chunk.strip():
                    chunks.append(chunk)
            return chunks

        # Use RecursiveCharacterTextSplitter with paragraph awareness
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size_bytes,
            chunk_overlap=overlap_bytes,
            length_function=get_byte_length,
            separators=separators,  # Language-aware separators
            keep_separator=True
        )

        try:
            chunks = splitter.split_text(text)
            logger.debug(f"Split text into {len(chunks)} chunks using RecursiveCharacterTextSplitter")

            # Validate chunks
            valid_chunks = []
            for chunk in chunks:
                if not chunk.strip():
                    continue

                chunk_size = get_byte_length(chunk)
                if chunk_size <= max_chunk_size_bytes:
                    valid_chunks.append(chunk)
                else:
                    # This shouldn't happen with RecursiveCharacterTextSplitter, but just in case
                    logger.warning(f"Found oversized chunk ({chunk_size} bytes) after splitting. Performing emergency split.")
                    # Emergency split by bytes
                    chunk_bytes = chunk.encode('utf-8')
                    for i in range(0, len(chunk_bytes), max_chunk_size_bytes):
                        sub_chunk = chunk_bytes[i:i + max_chunk_size_bytes].decode('utf-8', errors='ignore')
                        if sub_chunk.strip():
                            valid_chunks.append(sub_chunk)

            return valid_chunks

        except Exception as e:
            logger.error(f"Error splitting text: {e}. Falling back to basic splitting.")
            # Basic fallback: split purely by size
            chunks = []
            text_bytes = text.encode('utf-8')
            for i in range(0, len(text_bytes), max_chunk_size_bytes):
                chunk = text_bytes[i:i + max_chunk_size_bytes].decode('utf-8', errors='ignore')
                if chunk.strip():
                    chunks.append(chunk)
            return chunks
