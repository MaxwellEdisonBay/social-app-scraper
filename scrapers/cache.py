import pickle
from collections import OrderedDict
from os.path import exists
from scrapers.models import Post

CACHE_MAX_SIZE = 100


class ScraperCache:

    def __init__(self, tag: str = ""):
        print("tag: ", tag)
        self.tag = tag
        self._load_cache()

    def _load_cache(self):
        filename = f"/data/output_{self.tag}.sav"
        if not exists(filename):
            self.cache = OrderedDict()
            print("Cache file not found, creating new cache")
        else:
            try:
                with open(filename, "rb") as f:
                    self.cache = pickle.load(f)
                print(f"Cache loaded from {filename}")
            except Exception as e:
                print(f"Error loading cache from {filename}: {e}")

    def _save_cache(self):
        filename = f"/data/output_{self.tag}.sav"
        try:
            with open(filename, "ab") as f:
                pickle.dump(self.cache, f)
            print(f"Data written to {filename}")
        except Exception as e:
            print(f"Error writing to file: {e}")

    def add_posts(self, posts: list[Post]) -> list[Post]:
        new_posts: list[Post] = []
        for post in posts:
            if post.url not in self.cache:
                if len(self.cache) == CACHE_MAX_SIZE:
                    self.cache.popitem(last=False)
                self.cache[post.url] = post
                new_posts.append(post)
        self._save_cache()
        return new_posts

    def debug_print_posts(self):
        print(self.cache)


if __name__ == "__main__":
    test = ScraperCache()
    test.add_posts([
        Post("url1", "title", "desc", "image_url"),
        Post("url2", "title", "desc", "image_url"),
        Post("url3", "title", "desc", "image_url"),
        Post("url4", "title", "desc", "image_url"),
        Post("url1", "title", "desc", "image_url"),
    ])
    test.debug_print_posts()
