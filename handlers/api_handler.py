import requests


class ApiHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_news(self, endpoint: str):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return None

    def post_news(self, endpoint: str, data: dict):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error posting news: {e}")
            return None