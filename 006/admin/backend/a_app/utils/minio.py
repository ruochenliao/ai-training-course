from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import UploadFile

from a_app.log import logger
from a_app.settings.config import settings


class FileStorage:
    """File storage operations"""

    def __init__(self):
        self.storage_dir = Path(settings.UPLOAD_DIR)
        self._ensure_storage_dir_exists()

    def _ensure_storage_dir_exists(self) -> None:
        """Ensure the storage directory exists, create it if it doesn't"""
        try:
            if not self.storage_dir.exists():
                self.storage_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Storage directory '{self.storage_dir}' created successfully")
            else:
                logger.info(f"Storage directory '{self.storage_dir}' already exists")
        except Exception as err:
            logger.error(f"Error checking/creating storage directory: {err}")
            raise

    async def upload_file(
        self, file: UploadFile, object_name: str, content_type: Optional[str] = None,
        file_data: Optional[bytes] = None
    ) -> Tuple[bool, str]:
        """
        Upload a file to local storage

        Args:
            file: The file to upload
            object_name: The name of the object in storage
            content_type: The content type of the file (not used in local storage)
            file_data: Optional pre-read file data

        Returns:
            Tuple of (success, message)
        """
        try:
            # Create the full path for the file
            file_path = self.storage_dir / object_name

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the file
            with open(file_path, "wb") as buffer:
                if file_data is None:
                    # 如果没有提供文件数据，则从文件对象中读取
                    file_data = await file.read()
                buffer.write(file_data)

            logger.info(f"File '{object_name}' uploaded successfully")
            return True, f"File '{object_name}' uploaded successfully"
        except Exception as err:
            logger.error(f"Unexpected error uploading file: {err}")
            return False, f"Unexpected error uploading file: {err}"

    def get_file_url(self, object_name: str) -> str:
        """
        Get a URL for accessing a file

        Args:
            object_name: The name of the object in storage

        Returns:
            The file URL
        """
        try:
            # In a real application, you would generate a URL based on your API endpoint
            # For now, we'll just return a relative path that can be used with a static file endpoint
            return f"/api/v1/knowledge/download?path={object_name}"
        except Exception as err:
            logger.error(f"Error generating file URL: {err}")
            raise

    def delete_file(self, object_name: str) -> Tuple[bool, str]:
        """
        Delete a file from local storage

        Args:
            object_name: The name of the object in storage

        Returns:
            Tuple of (success, message)
        """
        try:
            file_path = self.storage_dir / object_name
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File '{object_name}' deleted successfully")
                return True, f"File '{object_name}' deleted successfully"
            else:
                logger.warning(f"File '{object_name}' not found")
                return False, f"File '{object_name}' not found"
        except Exception as err:
            logger.error(f"Unexpected error deleting file: {err}")
            return False, f"Unexpected error deleting file: {err}"

    def delete_files(self, object_names: list) -> Tuple[bool, str]:
        """
        Delete multiple files from local storage

        Args:
            object_names: List of object names to delete

        Returns:
            Tuple of (success, message)
        """
        try:
            error_count = 0
            for name in object_names:
                file_path = self.storage_dir / name
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"Error deleting file {name}: {e}")
                        error_count += 1
                else:
                    logger.warning(f"File '{name}' not found")
                    error_count += 1

            if error_count == 0:
                logger.info(f"All {len(object_names)} files deleted successfully")
                return True, f"All {len(object_names)} files deleted successfully"
            else:
                return False, f"Error deleting {error_count} out of {len(object_names)} files"
        except Exception as err:
            logger.error(f"Unexpected error deleting files: {err}")
            return False, f"Unexpected error deleting files: {err}"

    def list_files(self, prefix: str = "", recursive: bool = True) -> List[dict]:
        """
        List files in local storage

        Args:
            prefix: The prefix to filter objects
            recursive: Whether to list objects recursively

        Returns:
            List of objects with metadata
        """
        try:
            prefix_path = self.storage_dir / prefix if prefix else self.storage_dir
            pattern = '**/*' if recursive else '*'

            result = []
            for file_path in prefix_path.glob(pattern):
                if file_path.is_file():
                    # Get relative path from storage directory
                    rel_path = file_path.relative_to(self.storage_dir)
                    result.append({
                        'name': str(rel_path),
                        'size': file_path.stat().st_size,
                        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                    })
            return result
        except Exception as err:
            logger.error(f"Error listing files: {err}")
            raise

    def get_file_metadata(self, object_name: str) -> dict:
        """
        Get metadata for a file

        Args:
            object_name: The name of the object in storage

        Returns:
            The object metadata
        """
        try:
            file_path = self.storage_dir / object_name
            if not file_path.exists():
                raise FileNotFoundError(f"File '{object_name}' not found")

            stat = file_path.stat()
            return {
                'name': object_name,
                'size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'content_type': self._guess_content_type(file_path),
            }
        except Exception as err:
            logger.error(f"Error getting file metadata: {err}")
            raise

    def _guess_content_type(self, file_path: Path) -> str:
        """
        Guess the content type of a file based on its extension

        Args:
            file_path: The path to the file

        Returns:
            The guessed content type
        """
        extension = file_path.suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
            '.7z': 'application/x-7z-compressed',
        }
        return content_types.get(extension, 'application/octet-stream')

    def get_file(self, object_name: str) -> Optional[Path]:
        """
        Get a file from storage

        Args:
            object_name: The name of the object in storage

        Returns:
            The file path if found, None otherwise
        """
        try:
            file_path = self.storage_dir / object_name
            if file_path.exists():
                return file_path
            return None
        except Exception as err:
            logger.error(f"Error getting file: {err}")
            return None


# 创建全局变量
_file_storage_instance = None

# 获取单例的函数
def get_file_storage():
    global _file_storage_instance
    if _file_storage_instance is None:
        logger.info("Initializing FileStorage singleton instance")
        _file_storage_instance = FileStorage()
    return _file_storage_instance

# 创建单例
file_storage = get_file_storage()
