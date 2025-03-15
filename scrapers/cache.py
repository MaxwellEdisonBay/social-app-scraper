from collections import OrderedDict

from scrapers.models import Post

CACHE_MAX_SIZE = 100


class ScraperCache:

    def __init__(self):
        self.dict = OrderedDict()

    def add_posts(self, posts: list[Post]) -> list[Post]:
        new_posts: list[Post] = []
        for post in posts:
            if post.url not in self.dict:
                if len(self.dict) == CACHE_MAX_SIZE:
                    self.dict.popitem(last=False)
                self.dict[post.url] = post
                new_posts.append(post)
        return new_posts

    def debug_print_posts(self):
        print(self.dict)


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
