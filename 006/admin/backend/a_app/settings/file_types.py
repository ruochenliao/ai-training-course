"""
File type configurations and utilities.
This module defines supported file types and their processing methods.
"""
from enum import Enum
from typing import Dict, List, Set


class FileProcessingMethod(str, Enum):
    """Enum for file processing methods"""
    PDF_CONVERTER = "pdf_converter"  # Use PdfConverter for complex documents
    MARKDOWN = "markdown"  # Direct processing for markdown files
    TEXT = "text"  # Simple text processing


# Supported file extensions by processing method
SUPPORTED_FILE_TYPES: Dict[FileProcessingMethod, Set[str]] = {
    FileProcessingMethod.PDF_CONVERTER: {
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp",  # PDF and images
        ".pptx", ".docx", ".xlsx",  # Office documents
        ".html", ".epub"  # Web and ebook formats
    },
    FileProcessingMethod.MARKDOWN: {
        ".md", ".markdown"  # Markdown files
    },
    FileProcessingMethod.TEXT: {
        ".txt", ".csv", ".json", ".xml", ".yml", ".yaml",  # Plain text formats
        ".py", ".js", ".java", ".c", ".cpp", ".cs", ".go", ".rs",  # Code files
        ".html", ".css", ".sql", ".sh"  # Other text-based formats
    }
}

# All supported file extensions (flattened)
ALL_SUPPORTED_EXTENSIONS: Set[str] = set()
for extensions in SUPPORTED_FILE_TYPES.values():
    ALL_SUPPORTED_EXTENSIONS.update(extensions)


def get_processing_method(file_extension: str) -> FileProcessingMethod:
    """
    Determine the processing method for a given file extension.
    
    Args:
        file_extension: The file extension (including the dot)
        
    Returns:
        The appropriate processing method
        
    Raises:
        ValueError: If the file extension is not supported
    """
    file_extension = file_extension.lower()
    
    for method, extensions in SUPPORTED_FILE_TYPES.items():
        if file_extension in extensions:
            return method
            
    raise ValueError(f"Unsupported file extension: {file_extension}")


def is_supported_extension(file_extension: str) -> bool:
    """
    Check if a file extension is supported.
    
    Args:
        file_extension: The file extension (including the dot)
        
    Returns:
        True if supported, False otherwise
    """
    return file_extension.lower() in ALL_SUPPORTED_EXTENSIONS
