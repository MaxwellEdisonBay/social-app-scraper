from datetime import datetime, timedelta
from common.models.models import Post

def create_test_posts():
    """Create a list of test posts"""
    return [
        Post(
            url="https://example.com/test1",
            title="Test Article 1",
            desc="This is a test article about Ukrainian immigration",
            image_url="https://example.com/image1.jpg",
            created_at=datetime.now()
        ),
        Post(
            url="https://example.com/test2",
            title="Test Article 2",
            desc="This is a test article about sports",
            image_url="https://example.com/image2.jpg",
            created_at=datetime.now()
        ),
        Post(
            url="https://example.com/test3",
            title="Test Article 3",
            desc="This is a test article about Ukrainian refugees",
            image_url="https://example.com/image3.jpg",
            created_at=datetime.now()
        )
    ]

def create_similar_posts():
    """Create a list of posts similar to test posts"""
    return [
        Post(
            url="https://example.com/similar1",
            title="Similar Article 1",
            desc="This is an article about immigration in Ukraine",
            image_url="https://example.com/similar1.jpg",
            created_at=datetime.now()
        ),
        Post(
            url="https://example.com/similar2",
            title="Similar Article 2",
            desc="This is an article about Ukrainian migrants",
            image_url="https://example.com/similar2.jpg",
            created_at=datetime.now()
        )
    ]

def create_dissimilar_posts():
    """Create a list of posts dissimilar to test posts"""
    return [
        Post(
            url="https://example.com/dissimilar1",
            title="Dissimilar Article 1",
            desc="This is an article about climate change",
            image_url="https://example.com/dissimilar1.jpg",
            created_at=datetime.now()
        ),
        Post(
            url="https://example.com/dissimilar2",
            title="Dissimilar Article 2",
            desc="This is an article about technology",
            image_url="https://example.com/dissimilar2.jpg",
            created_at=datetime.now()
        )
    ]

def create_old_and_recent_posts():
    """Create old and recent posts for time-based tests"""
    old_post = Post(
        url="https://example.com/old",
        title="Old Article",
        desc="This is an old article",
        image_url="https://example.com/old.jpg",
        created_at=datetime.now() - timedelta(days=2),
        status='processed'
    )
    
    recent_post = Post(
        url="https://example.com/recent",
        title="Recent Article",
        desc="This is a recent article",
        image_url="https://example.com/recent.jpg",
        created_at=datetime.now() - timedelta(hours=12),
        status='processed'
    )
    
    new_post = Post(
        url="https://example.com/new",
        title="New Article",
        desc="This is a new article similar to the old one",
        image_url="https://example.com/new.jpg",
        created_at=datetime.now()
    )
    
    return old_post, recent_post, new_post 