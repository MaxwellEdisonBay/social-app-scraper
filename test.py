import requests
from bs4 import BeautifulSoup

def get_bbc_us_canada_news():
    """
    Crawls the BBC News US & Canada page and extracts the latest news articles.

    Returns:
        A list of dictionaries, where each dictionary represents an article
        and contains the title, link, and summary (if available).
        Returns None if an error occurs.
    """
    url = "https://www.bbc.com/news/us-canada"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, "html.parser")

        articles = []
        article_elements = soup.find_all("div", {"data-testid": "dundee-card"}, recursive=True) #find all the promo divs that contain articles.

        for element in article_elements:
            image_el = element.find("img")
            link_el = element.find("a")
            title_el = element.find("h2")
            desc_el = element.find("p")
            # print(image_el, link_el, title_el, desc_el)
            articles.append({
                "url": link_el["href"],
                "title": title_el.text,
                "desc": desc_el.text,
                "imageUrl": image_el["src"]
            })


        return articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    news_articles = get_bbc_us_canada_news()

    if news_articles:
        for article in news_articles:
            print(article)
    else:
        print("Failed to retrieve news articles.")