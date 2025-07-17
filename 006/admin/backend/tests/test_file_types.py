"""
Simple test for file type configuration.
"""
import os
import sys
import tempfile

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only the file_types module
from a_app.settings.file_types import FileProcessingMethod, get_processing_method, is_supported_extension


def test_file_types():
    """Test file type detection"""
    print("\n--- Testing File Type Detection ---")
    for ext in [".pdf", ".md", ".txt", ".docx", ".jpg", ".html", ".csv"]:
        try:
            method = get_processing_method(ext)
            print(f"File extension {ext} -> Processing method: {method}")
        except ValueError as e:
            print(f"File extension {ext} -> Error: {e}")


if __name__ == "__main__":
    test_file_types()
