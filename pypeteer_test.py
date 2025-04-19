from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_largest_image_src(srcset):
    """Extracts the URL of the largest image from a srcset string."""
    if not srcset:
        return None
    sources = srcset.strip().split(',')
    largest_url = None
    largest_width = -1
    for source in sources:
        parts = source.strip().split()
        if len(parts) == 2 and parts[1].endswith('w'):
            try:
                width = int(parts[1][:-1])
                if width > largest_width:
                    largest_width = width
                    largest_url = parts[0]
            except ValueError:
                pass
        elif len(parts) == 1:
            largest_url = parts[0]
    return largest_url.strip() if largest_url else None

def extract_article_data(url):
    """
    Takes a URL, navigates to the page, extracts the largest image URL
    from the first image block and all the article text.

    Args:
        url (str): The URL of the article.

    Returns:
        tuple: A tuple containing the largest image URL (str or None) and
               a list of article text paragraphs (list of str).
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    largest_image_url = None
    article_text = []

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # Find the first image block and extract the largest image URL
        try:
            first_image_block = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article div[data-component="image-block"]'))
            )
            img_element = first_image_block.find_element(By.TAG_NAME, 'img')
            srcset = img_element.get_attribute('srcset')
            if srcset:
                largest_image_url = get_largest_image_src(srcset)
            else:
                largest_image_url = img_element.get_attribute('src')
        except:
            print("Could not find the first image block or extract the image URL.")

        # Extract all article text paragraphs
        text_blocks = driver.find_elements(By.CSS_SELECTOR, 'article div[data-component="text-block"] p')
        for block in text_blocks:
            article_text.append(block.text)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

    return largest_image_url, article_text

if __name__ == "__main__":
    article_url = "https://www.bbc.com/news/articles/c20xq5nd8jeo"
    largest_image, text_content = extract_article_data(article_url)

    if largest_image:
        print(f"Largest Image URL: {largest_image}")
    else:
        print("Could not extract the largest image URL.")

    if text_content:
        print("\nArticle Text:")
        for paragraph in text_content:
            print(paragraph)
    else:
        print("\nCould not extract any article text.")