import json
import os
from pathlib import Path
from typing import Dict, List


class TrackingManager:
    """Manages the tracking file for uploaded videos."""
    
    def __init__(self, tracking_file: str = "tracking.json"):
        self.tracking_file = tracking_file
        self.data = self._load_tracking_data()
    
    def _load_tracking_data(self) -> Dict:
        """Load tracking data from JSON file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"uploaded": {}}
        return {"uploaded": {}}
    
    def _save_tracking_data(self):
        """Save tracking data to JSON file."""
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def is_uploaded(self, file_path: str) -> bool:
        """Check if a file has been uploaded."""
        return file_path in self.data["uploaded"]
    
    def mark_uploaded(self, file_path: str, file_link: str):
        """Mark a file as uploaded and save the link."""
        self.data["uploaded"][file_path] = {
            "link": file_link,
            "uploaded_at": self._get_timestamp()
        }
        self._save_tracking_data()
    
    def get_file_link(self, file_path: str) -> str | None:
        """Get the link for an uploaded file."""
        if self.is_uploaded(file_path):
            return self.data["uploaded"][file_path]["link"]
        return None
    
    def get_unuploaded_files(self, video_dir: str) -> List[str]:
        """Get list of video files that haven't been uploaded."""
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v'}
        unuploaded = []
        
        video_path = Path(video_dir)
        if not video_path.exists():
            raise FileNotFoundError(f"Video directory not found: {video_dir}")
        
        for file_path in video_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                file_str = str(file_path)
                if not self.is_uploaded(file_str):
                    unuploaded.append(file_str)
        
        return sorted(unuploaded)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_stats(self) -> Dict:
        """Get upload statistics."""
        return {
            "total_uploaded": len(self.data["uploaded"]),
            "files": list(self.data["uploaded"].keys())
        }
