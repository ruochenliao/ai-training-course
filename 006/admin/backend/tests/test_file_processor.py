"""
Test script for file processor functionality.
"""
import os
import asyncio
import tempfile
from pathlib import Path

import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from a_app.settings.file_types import FileProcessingMethod, get_processing_method, is_supported_extension
from a_app.tasks.file_processor import process_file_in_process
from a_app.utils.text_chunker import TextChunker


async def test_file_processing():
    """Test file processing with different file types"""
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a markdown file
        md_path = os.path.join(temp_dir, "test.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Test Markdown\n\nThis is a test markdown file.\n\n## Section 2\n\nMore content here.")

        # Create a text file
        txt_path = os.path.join(temp_dir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("This is a plain text file.\nIt has multiple lines.\nEach line should be processed correctly.")

        # Test markdown file processing
        print("\n--- Testing Markdown File Processing ---")
        success, markdown_text, error = process_file_in_process(md_path, ".md")
        print(f"Success: {success}")
        if success:
            print(f"Markdown content (first 100 chars): {markdown_text[:100]}...")
            # Test chunking
            chunks = TextChunker.chunk_markdown(markdown_text)
            print(f"Chunked into {len(chunks)} parts")
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i+1} (first 50 chars): {chunk[:50]}...")
        else:
            print(f"Error: {error}")

        # Test text file processing
        print("\n--- Testing Text File Processing ---")
        success, text_content, error = process_file_in_process(txt_path, ".txt")
        print(f"Success: {success}")
        if success:
            print(f"Text content (first 100 chars): {text_content[:100]}...")
            # Test chunking
            chunks = TextChunker.chunk_text(text_content)
            print(f"Chunked into {len(chunks)} parts")
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i+1} (first 50 chars): {chunk[:50]}...")
        else:
            print(f"Error: {error}")

        # Test file type detection
        print("\n--- Testing File Type Detection ---")
        for ext in [".pdf", ".md", ".txt", ".docx", ".jpg", ".html", ".csv"]:
            try:
                method = get_processing_method(ext)
                print(f"File extension {ext} -> Processing method: {method}")
            except ValueError as e:
                print(f"File extension {ext} -> Error: {e}")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_file_processing())
