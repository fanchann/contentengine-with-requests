import os
from typing import List


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory(path: str):
        """Create directory if it doesn't exist."""
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def safe_filename(filename: str, max_length: int = 255) -> str:
        """Create a safe filename with length limit."""
        # Remove or replace dangerous characters
        safe = filename.replace("/", "_").replace("\\", "_").replace(":", "_")
        safe = safe.replace("*", "_").replace("?", "_").replace('"', "_")
        safe = safe.replace("<", "_").replace(">", "_").replace("|", "_")
        
        # Truncate if too long
        if len(safe) > max_length:
            name, ext = os.path.splitext(safe)
            max_name_len = max_length - len(ext)
            safe = name[:max_name_len] + ext
        
        return safe
    
    @staticmethod
    def get_file_extension(filename: str, default: str = "") -> str:
        """Get file extension or return default."""
        _, ext = os.path.splitext(filename)
        return ext or default
    
    @staticmethod
    def uniq_list(seq: List[str]) -> List[str]:
        """Remove duplicates while preserving order."""
        seen = set()
        result = []
        for item in seq:
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result