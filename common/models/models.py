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
    source: Optional[str] = None  # Source of the post (e.g., 'bbc', 'reuters')
    
    # ML-processed content
    en_title: Optional[str] = None
    en_text: Optional[str] = None
    uk_title: Optional[str] = None
    uk_text: Optional[str] = None
    
    # Full article content
    full_text: Optional[str] = None  # Full text of the article
    
    # Queue status
    status: str = 'queued'  # Default status for new posts

    def __str__(self):
        return f"""
        url: {self.url}
        title: {self.title}
        description: {self.desc}
        image_url: {self.image_url}
        created_at: {self.created_at}
        source: {self.source}
        en_title: {self.en_title}
        en_text: {self.en_text}
        uk_title: {self.uk_title}
        uk_text: {self.uk_text}
        full_text: {self.full_text[:100] + '...' if self.full_text and len(self.full_text) > 100 else self.full_text}
        status: {self.status}
        """