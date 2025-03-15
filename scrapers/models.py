class Post:
    def __init__(self, url: str, title: str, desc: str, image_url: str):
        self.url = url
        self.title = title
        self.desc = desc
        self.image_url = image_url

    def __str__(self):
        return f"""
        url: {self.url}
        title: {self.title}
        description: {self.desc}
        image_url: {self.image_url}
        """