import os
from sentence_transformers import SentenceTransformer, util
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from common.models.models import Post
from google import genai
from typing import List
import json

def filter_similar_posts(new_posts: list[Post], existing_posts: list[Post], threshold: float = 0.8) -> list[Post]:
    if len(existing_posts) == 0:
        return new_posts

    model = SentenceTransformer('all-MiniLM-L6-v2')

    existing_titles = [post.title for post in existing_posts]
    existing_descriptions = [post.desc for post in existing_posts]

    existing_embeddings = model.encode(existing_titles + existing_descriptions, convert_to_tensor=True)

    filtered_posts = [] 
    for post in new_posts:
        title_embedding = model.encode(post.title, convert_to_tensor=True)
        description_embedding = model.encode(post.desc, convert_to_tensor=True)

        title_similarities = util.pytorch_cos_sim(title_embedding, existing_embeddings[:len(existing_titles)])
        description_similarities = util.pytorch_cos_sim(description_embedding, existing_embeddings[len(existing_titles):])

        if title_similarities.max() < threshold and description_similarities.max() < threshold:
            filtered_posts.append(post)

    return filtered_posts




def get_relevant_posts(posts: List[Post], api_key: str) -> List[str]:
    """
    Uses Google Cloud Vertex AI's Gemini model to send a list of posts with title and desc
    and returns a structured JSON based on the given prompt.

    Args:
        posts (List[Post]): List of Post objects containing title and desc.
        api_key (str): Gemini API key.

    Returns:
        List[str]: List of post URLs that are the most relevant for news display.
    """
    client = genai.Client(api_key=api_key)

    prompt = (
        "You are a news analyst for a Ukrainian community website in Canada. "
        "Analyze the following news post and determine if it's relevant for our community. "
        "If it's relevant, return a JSON array containing the post's URL. "
        "If it's not relevant, return an empty JSON array []. "
        "Consider these criteria:\n"
        "1. High priority: News about Ukraine or policies for Ukrainians in Canada\n"
        "2. Medium priority: Important Canadian or US news that affects the community\n"
        "3. Low priority: General news that might be less relevant\n\n"
        "IMPORTANT: Return ONLY a JSON array, with no additional text, no markdown formatting, and no explanations. "
        "For example, for a relevant post, return: [\"https://example.com/url\"]\n"
        "For an irrelevant post, return: []\n\n"
        "Title: {title}\n"
        "Description: {desc}\n"
        "URL: {url}"
    )

    relevant_urls = []
    for post in posts:
        try:
            formatted_prompt = prompt.format(
                title=post.title,
                desc=post.desc,
                url=post.url
            )
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=formatted_prompt
            )
            
            print(f"\nAnalyzing post: {post.title}")
            print(f"Raw response: {response.text}")
            
            # Try to extract URLs from the response
            try:
                # Clean the response text by removing markdown code block markers if present
                clean_text = response.text.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]  # Remove ```json
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]  # Remove ```
                clean_text = clean_text.strip()
                
                urls = json.loads(clean_text)
                if isinstance(urls, list):
                    relevant_urls.extend(urls)
                    print(f"Found URLs: {urls}")
                else:
                    print(f"Unexpected response format: {response.text}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                # If the response contains the URL directly, try to extract it
                if post.url in response.text:
                    relevant_urls.append(post.url)
                    print(f"Found URL in text: {post.url}")
                else:
                    print("No valid URLs found in response")
                    
        except Exception as e:
            print(f"Error processing post '{post.title}': {e}")
            continue

    return list(set(relevant_urls))  # Remove duplicates


def get_article_translation(api_key: str, title: str, text: str) -> tuple[str, str, str]:
    """
    Translates and improves article title and text to Ukrainian using Gemini API.
    Also improves the English text to be more readable while maintaining appropriate style.
    
    Args:
        api_key (str): Google API key for accessing Gemini
        title (str): Original article title in English
        text (str): Original article text in English
        
    Returns:
        tuple[str, str, str]: (Ukrainian title, Improved English text, Ukrainian text)
    """
    prompt = """Please help translate and improve this article content. The output should:
1. Translate the title to Ukrainian
2. Improve the English text to be more readable while maintaining journalistic style
3. Translate the improved text to Ukrainian

Please format the response as JSON with these keys:
- uk_title: Ukrainian translation of the title
- en_text: Improved English text
- uk_text: Ukrainian translation of the improved text

Original title: {title}

Original text:
{text}
"""

    try:
       
        client= genai.Client(api_key=api_key)
        
        formatted_prompt = prompt.format(
            title=title,
            text=text
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=formatted_prompt
        )
        
        # Clean the response text
        clean_text = response.text.strip()
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:]
        if clean_text.endswith('```'):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        result = json.loads(clean_text)
        return (
            result['uk_title'],
            result['en_text'], 
            result['uk_text']
        )
        
    except Exception as e:
        print(f"Error translating article: {e}")
        return None, None, None


if __name__ == "__main__":
    # Test data
    test_posts = [
        # High relevance - Ukrainian immigration
        Post(
            title="New immigration program for Ukrainian refugees in Canada",
            desc="The Canadian government announces a new pathway for Ukrainian refugees to settle in Canada permanently.",
            url="https://example.com/ukraine-immigration"
        ),
        # High relevance - Ukrainian culture in Canada
        Post(
            title="Local Toronto restaurant opens Ukrainian cuisine branch",
            desc="Popular Toronto restaurant expands to serve traditional Ukrainian dishes in the heart of the city.",
            url="https://example.com/ukrainian-restaurant"
        ),
        # High relevance - Ukrainian community event
        Post(
            title="Ukrainian cultural festival in Vancouver draws record crowds",
            desc="Annual Ukrainian cultural festival brings together thousands in Vancouver's downtown, featuring traditional music, dance, and food.",
            url="https://example.com/ukrainian-festival"
        ),
        # Medium relevance - Canadian policy affecting immigrants
        Post(
            title="Canada announces new housing support program for newcomers",
            desc="Federal government launches initiative to help immigrant families with housing costs across Canada, including special provisions for refugee families.",
            url="https://example.com/housing-policy"
        ),
        # Medium relevance - Canadian election results
        Post(
            title="Federal election results: Impact on immigration policies",
            desc="New government's stance on immigration and refugee policies could affect future Ukrainian refugee programs in Canada.",
            url="https://example.com/election-results"
        ),
        # Medium relevance - Canadian-Ukrainian relations
        Post(
            title="Canada announces new trade agreement with Ukraine",
            desc="Bilateral trade agreement between Canada and Ukraine expected to create new business opportunities and strengthen economic ties.",
            url="https://example.com/trade-agreement"
        ),
        # Low relevance - General sports
        Post(
            title="General sports news about basketball",
            desc="Regular season basketball game results from last night.",
            url="https://example.com/sports"
        ),
        # Low relevance - Entertainment
        Post(
            title="New Netflix series about cooking shows",
            desc="Popular streaming platform announces new cooking competition series featuring international cuisines.",
            url="https://example.com/netflix"
        ),
        # High relevance - Ukrainian language education
        Post(
            title="Free Ukrainian language classes for newcomers in Toronto",
            desc="Local community center launches free Ukrainian language program for recent immigrants and their children.",
            url="https://example.com/language-classes"
        ),
        # Medium relevance - Canadian healthcare
        Post(
            title="New healthcare coverage for temporary residents",
            desc="Provincial government expands healthcare coverage to include temporary residents, affecting many Ukrainian refugees.",
            url="https://example.com/healthcare"
        )
    ]

    # Replace with your actual API key
    API_KEY = os.getenv("GOOGLE_API_KEY")

    # try:
    #     relevant_urls = get_relevant_posts(test_posts, API_KEY)
    #     print("\nTest Results:")
    #     print("-------------")
    #     print(f"Found {len(relevant_urls)} relevant posts")
    #     print("\nRelevant URLs:")
    #     for url in relevant_urls:
    #         print(f"- {url}")
            
    #     # Find the corresponding posts for better analysis
    #     print("\nRelevant Posts Details:")
    #     for post in test_posts:
    #         if post.url in relevant_urls:
    #             print(f"\nTitle: {post.title}")
    #             print(f"Description: {post.desc}")
    #             print(f"URL: {post.url}")
    # except Exception as e:
    #     print(f"Error during testing: {e}")
        
    print("\nTesting Article Translation:")
    print("---------------------------")
    
    # Test article content
    test_article = """
    Important meeting held in Ottawa regarding support for Ukraine.
    During the meeting, new assistance programs were discussed.
    
    Participants emphasized the need for continued humanitarian aid.
    The discussion also covered cooperation with international partners.
    """
    
    # Test translation with a sample article
    test_title = "Canada announces new support package for Ukraine"
    print("\nOriginal Title:", test_title)
    print("\nOriginal Text:")
    print(test_article)
    
    try:
        uk_title, en_text, uk_text = get_article_translation(API_KEY, test_title, test_article)
        
        if uk_title and en_text and uk_text:
            print("\nTranslation Results:")
            print("-" * 50)
            print("Ukrainian Title:", uk_title)
            print("\nImproved English Text:")
            print(en_text)
            print("\nUkrainian Text:")
            print(uk_text)
        else:
            print("\nTranslation failed. Please check the API key and try again.")
            
    except Exception as e:
        print(f"\nError during translation test: {e}")
        
        
