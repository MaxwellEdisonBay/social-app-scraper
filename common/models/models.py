from dataclasses import dataclass
from typing import Optional

@dataclass
class Post:
    title: str
    desc: str
    url: str
    image_url: Optional[str] = None

    def __str__(self):
        return f"""
        url: {self.url}
        title: {self.title}
        description: {self.desc}
        image_url: {self.image_url}
        """