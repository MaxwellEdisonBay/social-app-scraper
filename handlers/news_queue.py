from typing import List
import pickle
import os

from common.models.models import Post


class NewsQueue:
    def __init__(self, cache_file='news_queue_cache.pkl', backlog_file='news_backlog_cache.pkl', max_backlog_size=150):
        self.max_backlog_size = max_backlog_size
        self.queue: List[Post] = []
        self.backlog: List[Post] = []
        self.cache_file = cache_file
        self.backlog_file = backlog_file
        self._load_cache()
        self._load_backlog()

    def add_news(self, posts: List[Post]):
        """Adds news to the queue."""
        self.queue.extend(posts)
        self._save_cache()

    def evaluate_and_post(self):
        """
        Placeholder function to evaluate and post news.
        This should be implemented to handle the actual posting of news,
        and is intended to be called by a cron job.
        """
        if self.queue:
            print(f"Evaluating and posting {len(self.queue)} news items.")
            from handlers.ml_handler import filter_similar_posts
            filtered_posts = filter_similar_posts(self.queue, self.backlog)
            for post in filtered_posts:
                print(f"Title: {post.title}")
                print(f"URL: {post.url}")
                self.backlog.append(post)
            self.queue = []  # Clear the queue after processing
            self._save_cache()  # Clear the cache after processing
            self._enforce_backlog_size()  # Enforce the maximum backlog size
            self._save_backlog()  # Save the backlog after processing
        else:
            print("No news in the queue to evaluate and post.")

    def _save_cache(self):
        """Saves the current queue to a pickle file."""
        data = [post for post in self.queue]
        with open(self.cache_file, 'wb') as f:
            pickle.dump(data, f)

    def _save_backlog(self):
        """Saves the current backlog to a pickle file."""
        data = [post for post in self.backlog]
        with open(self.backlog_file, 'wb') as f:
            pickle.dump(data, f)

    def _load_backlog(self):
        """Loads the backlog from a pickle file if it exists."""
        if os.path.exists(self.backlog_file):
            with open(self.backlog_file, 'rb') as f:
                data = pickle.load(f)
            self.backlog = [Post(**item.__dict__) for item in data]

    def _load_cache(self):
        """Loads the queue from a pickle file if it exists."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
            self.queue = [Post(**item.__dict__) for item in data]

    def _enforce_backlog_size(self):
        """Ensures the backlog does not exceed the maximum size by removing the oldest posts."""
        if len(self.backlog) > self.max_backlog_size:
            excess_count = len(self.backlog) - self.max_backlog_size
            self.backlog = self.backlog[excess_count:]


if __name__ == '__main__':
    # Mock Post class
    from common.models.models import Post

    # Create some mock existing posts
    existing_posts = [
        Post(title="Breaking News: Market Crash", desc="The stock market has crashed today.",
             url="http://example.com/1", image_url="http://example.com/image1.jpg"),
        Post(title="Sports Update: Local Team Wins", desc="The local team has won the championship.",
             url="http://example.com/2", image_url="http://example.com/image2.jpg")
    ]

    # Create some new posts, some of which are similar to existing ones
    new_posts = [
        Post(title="Market Crash Today", desc="The stock market experienced a significant crash.",
             url="http://example.com/3", image_url="http://example.com/image3.jpg"),
        Post(title="Local Team Wins Championship", desc="The local team has secured the championship title.",
             url="http://example.com/4", image_url="http://example.com/image4.jpg"),
        Post(title="Weather Update: Sunny Day", desc="The weather is sunny and clear today.",
             url="http://example.com/5", image_url="http://example.com/image5.jpg")
    ]

    # Initialize the NewsQueue with existing posts in the backlog
    news_queue = NewsQueue()
    news_queue.backlog.extend(existing_posts)
    news_queue._save_backlog()

    # Add new posts to the queue
    news_queue.add_news(new_posts)

    # Evaluate and post the news
    news_queue.evaluate_and_post()

    # Print the final state of the backlog
    print("Final backlog:")
    for post in news_queue.backlog:
        print(f"Title: {post.title}, URL: {post.url}")