from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Post:
    # Basic post data
    title: str
    desc: str
    url: str
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # ML-processed content
    english_title: Optional[str] = None
    english_summary: Optional[str] = None
    ukrainian_title: Optional[str] = None
    ukrainian_summary: Optional[str] = None

    def __str__(self):
        return f"""
        url: {self.url}
        title: {self.title}
        description: {self.desc}
        image_url: {self.image_url}
        created_at: {self.created_at}
        english_title: {self.english_title}
        english_summary: {self.english_summary}
        ukrainian_title: {self.ukrainian_title}
        ukrainian_summary: {self.ukrainian_summary}
        """