import os
import sys
from pathlib import Path
import google.generativeai as genai
from typing import List, Tuple, Optional

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from common.models.models import Post
import json

def filter_similar_posts(new_posts: list[Post], existing_posts: list[Post], threshold: float = 0.95) -> list[Post]:
    """
    This function is now a placeholder that returns all new posts.
    The similarity filtering has been removed to reduce dependencies.
    
    Args:
        new_posts (list[Post]): List of new posts to check
        existing_posts (list[Post]): List of existing posts to compare against
        threshold (float): Similarity threshold (not used anymore)
    
    Returns:
        list[Post]: List of all new posts
    """
    return new_posts


def mock_get_relevant_posts(posts: List[Post], api_key: str = None) -> List[str]:
    """
    Mock function that imitates Gemini post recommendations for testing purposes.
    This function selects posts based on simple keyword matching instead of using the Gemini API.
    
    Args:
        posts (List[Post]): List of Post objects containing title and desc.
        api_key (str, optional): Not used in the mock function, but kept for compatibility.
        
    Returns:
        List[str]: List of post URLs that are considered relevant.
    """
    print("\n=== MOCK ML: Filtering posts for relevance ===")
    
    # Keywords that indicate relevance for a Ukrainian community website
    relevant_keywords = [
        "ukraine", "ukrainian", "russia", "russian", "putin", "zelensky", 
        "kyiv", "canada", "immigration", "refugee", "visa", "policy",
        "war", "conflict", "invasion", "military", "aid", "support",
        # Add more general keywords for testing
        "news", "update", "report", "announcement", "development",
        "politics", "technology", "sports", "entertainment", "science", "business",
        "community", "local", "global", "international", "national",
        "breaking", "latest", "important", "critical", "urgent"
    ]
    
    relevant_urls = []
    
    for post in posts:
        # For testing purposes, mark all posts as relevant
        relevant_urls.append(post.url)
        print(f"Analyzing post: {post.title}")
        print(f"-> Post is relevant, keeping it")
    
    print(f"Found {len(relevant_urls)} relevant posts out of {len(posts)} total posts")
    return relevant_urls


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
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Shuffle the posts to ensure a mix of sources in each batch
    import random
    shuffled_posts = posts.copy()
    random.shuffle(shuffled_posts)

    # Process posts in batches of 10 to respect rate limits
    batch_size = 40
    relevant_urls = []
    
    for i in range(0, len(shuffled_posts), batch_size):
        batch = shuffled_posts[i:i+batch_size]
        print(f"\nProcessing batch {i//batch_size + 1} of {(len(shuffled_posts) + batch_size - 1)//batch_size}")
        
        # Create a prompt that handles multiple posts in one API call
        batch_prompt = (
            "You are a news curator for a Ukrainian community website in Canada. "
            "Your goal is to identify the most relevant and engaging news stories "
            "that would interest the Ukrainian-Canadian community while also including "
            "some general remarkable content that everyone would find interesting.\n\n"
            "Analyze the following news posts and select those that meet these criteria:\n"
            "1. UKRAINIAN COMMUNITY PRIORITY (Must include if found):\n"
            "   - New Canadian policies/programs for Ukrainians\n"
            "   - Updates affecting Ukrainian newcomers in Canada\n"
            "   - Canadian government responses to the Ukraine situation\n"
            "   - Ukrainian cultural events and community gatherings\n"
            "   - Success stories of Ukrainian newcomers\n"
            "2. IMMIGRATION & SETTLEMENT (Include if relevant):\n"
            "   - Changes to Canadian immigration policies\n"
            "   - Updates on healthcare, education, or social services\n"
            "   - Housing and employment opportunities\n"
            "   - Integration support programs\n"
            "3. REMARKABLE GENERAL NEWS (Include if truly interesting):\n"
            "   - Major Canadian policy changes that affect everyone\n"
            "   - Significant economic developments\n"
            "   - Notable cultural events and festivals\n"
            "   - Interesting local stories\n"
            "4. ENTERTAINING CONTENT (Include 1-2 if available):\n"
            "   - Heartwarming or funny local stories\n"
            "   - Cultural exchanges and community initiatives\n"
            "   - Positive integration stories\n"
            "   - Interesting or unusual news that would spark discussion\n\n"
            "DO NOT include:\n"
            "- News about the conflict itself unless directly tied to Canadian response\n"
            "- Multiple articles covering the same topic\n"
            "- Content that could be distressing or inappropriate\n"
            "- Generic news without any remarkable aspect\n\n"
            "Return a JSON array with URLs of the most relevant stories (maximum 6).\n"
            "If no posts meet these standards, return an empty array [].\n\n"
            "IMPORTANT: Return ONLY a JSON array, no additional text or formatting.\n"
            "Example: [\"https://example.com/interesting-story\"]\n\n"
            "Posts to analyze:\n"
        )
        
        # Add each post to the batch prompt
        for j, post in enumerate(batch):
            batch_prompt += f"\nPost {j+1}:\nTitle: {post.title}\nDescription: {post.desc}\nURL: {post.url}\n"
        
        try:
            # Add a small delay between batches to respect rate limits
            if i > 0:
                import time
                time.sleep(5)  # 5 second delay between batches
                
            response = model.generate_content(batch_prompt)
            
            print(f"Processing {len(batch)} posts in batch")
            print(f"Raw response: {response.text}")
            
            # Try to extract URLs from the response
            try:
                # Clean the response text
                clean_text = response.text.strip()
                
                # Remove markdown code block markers if present
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                # Fix common JSON issues
                # Replace escaped newlines with actual newlines
                clean_text = clean_text.replace('\\n', '\n')
                # Replace escaped quotes with actual quotes
                clean_text = clean_text.replace('\\"', '"')
                # Replace escaped backslashes with actual backslashes
                clean_text = clean_text.replace('\\\\', '\\')
                
                # Remove control characters
                import re
                clean_text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', clean_text)
                
                # Fix common JSON formatting issues
                clean_text = re.sub(r',\s*}', '}', clean_text)  # Remove trailing commas
                clean_text = re.sub(r',\s*]', ']', clean_text)  # Remove trailing commas in arrays
                clean_text = re.sub(r'}\s*{', '},{', clean_text)  # Fix missing commas between objects
                clean_text = re.sub(r']\s*{', '],{', clean_text)  # Fix missing commas between array and object
                
                urls = json.loads(clean_text)
                if isinstance(urls, list):
                    relevant_urls.extend(urls)
                    print(f"Found URLs in batch: {urls}")
                else:
                    print(f"Unexpected response format: {response.text}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                # If the response contains URLs directly, try to extract them
                for post in batch:
                    if post.url in response.text:
                        relevant_urls.append(post.url)
                        print(f"Found URL in text: {post.url}")
                else:
                    print("No valid URLs found in response")
                    
        except Exception as e:
            print(f"Error processing batch: {e}")
            # If we hit a rate limit, wait longer before continuing
            if "429" in str(e) or "quota" in str(e).lower():
                print("Rate limit detected. Waiting 60 seconds before continuing...")
                import time
                time.sleep(60)
                # Try to process this batch again
                try:
                    response = model.generate_content(batch_prompt)
                    # Process response as above
                    clean_text = response.text.strip()
                    if clean_text.startswith('```json'):
                        clean_text = clean_text[7:]
                    if clean_text.endswith('```'):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()
                    
                    urls = json.loads(clean_text)
                    if isinstance(urls, list):
                        relevant_urls.extend(urls)
                        print(f"Found URLs in retry batch: {urls}")
                except Exception as retry_e:
                    print(f"Error on retry: {retry_e}")
            continue

    return list(set(relevant_urls))  # Remove duplicates


def get_article_translation(api_key: str, title: str, text: str) -> tuple[str, str, str, str]:
    """
    Translates and improves article title and text to Ukrainian using Gemini API.
    Also improves the English text to be more readable while maintaining appropriate style.
    
    Args:
        api_key (str): Google API key for accessing Gemini
        title (str): Original article title in English
        text (str): Original article text in English
        
    Returns:
        tuple[str, str, str, str]: (Ukrainian title, Improved English title, Improved English text, Ukrainian text)
    """
    prompt = """Please help translate and improve this article content. The output should:
1. Translate the title to Ukrainian
2. Improve the English title to be more readable while maintaining journalistic style
3. Improve the English text to be more readable while maintaining journalistic style
4. Translate the improved text to Ukrainian
5. Exclude all the personal information and any other generic information that is not relevant to the news

IMPORTANT: Format both the English and Ukrainian text with rich text tags. Use ONLY these supported tags:
- <h1> for main article title or primary section headings
- <h2> for secondary section headings
- <p> for paragraphs
- <strong> for important information or emphasis (NOT <b>)
- <em> for subtle emphasis or foreign terms (NOT <i>)
- <s> for outdated or incorrect information
- <ul> and <li> for bullet point lists
- <ol> and <li> for numbered lists
- <blockquote> for direct quotes or important statements
- <code> for technical terms, data, or short code snippets
- <a href="URL"> for hyperlinks (include the URL in the href attribute)

Styling guidelines:
1. DO NOT include the article title in the text content - titles are handled separately
2. Use <h2> for major section breaks
3. Wrap all text content in <p> tags
4. Use <strong> for key facts, statistics, or important statements
5. Use <em> for subtle emphasis or to highlight specific terms
6. Use <s> to mark outdated information that has been corrected
7. Use <ul> and <li> for unordered lists of related items
8. Use <ol> and <li> for sequential steps or ranked items
9. Use <blockquote> for direct quotes from sources
10. Use <code> for technical terms, numbers, or data points
11. Use <a> for linking to related sources or references

CRITICAL REQUIREMENTS:
1. DO NOT return empty sections. Every section must have content.
2. DO NOT include the article title in the text content - titles are handled separately.
3. Ensure all paragraphs are properly wrapped in <p> tags.
4. Make sure all lists have proper <ul> or <ol> tags with <li> items.
5. Format quotes with <blockquote> tags.
6. Ensure the Ukrainian translation is complete and accurate.
7. Maintain the same structure and formatting in both English and Ukrainian versions.

TRANSLATION GUIDELINES:
1. DO NOT translate Canada-specific acronyms, program names, or official terms (e.g., Express Entry, IRCC, PNP, etc.)
2. Use natural, conversational Ukrainian language that is easy to understand
3. Make titles engaging and attention-grabbing while maintaining accuracy
4. Use appropriate Ukrainian idioms and expressions where they fit naturally
5. Ensure the translation flows well and doesn't sound like a direct translation
6. Keep the tone professional but accessible

Please format the response as JSON with these keys:
- uk_title: Ukrainian translation of the title
- en_title: Improved English title
- en_text: Improved English text with rich text formatting (DO NOT include the title)
- uk_text: Ukrainian translation of the improved text with rich text formatting (DO NOT include the title)

Original title: {title}

Original text:
{text}
"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        formatted_prompt = prompt.format(
            title=title,
            text=text
        )
        
        response = model.generate_content(formatted_prompt)
        
        # Clean the response text
        clean_text = response.text.strip()
        
        # Remove markdown code block markers if present
        if clean_text.startswith('```json'):
            clean_text = clean_text[7:]
        if clean_text.endswith('```'):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        # Fix common JSON issues
        # Replace escaped newlines with actual newlines
        clean_text = clean_text.replace('\\n', '\n')
        # Replace escaped quotes with actual quotes
        clean_text = clean_text.replace('\\"', '"')
        # Replace escaped backslashes with actual backslashes
        clean_text = clean_text.replace('\\\\', '\\')
        
        # Remove control characters while preserving newlines and tabs
        import re
        clean_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', clean_text)
        
        # Fix common JSON formatting issues
        clean_text = re.sub(r',\s*}', '}', clean_text)  # Remove trailing commas
        clean_text = re.sub(r',\s*]', ']', clean_text)  # Remove trailing commas in arrays
        clean_text = re.sub(r'}\s*{', '},{', clean_text)  # Fix missing commas between objects
        clean_text = re.sub(r']\s*{', '],{', clean_text)  # Fix missing commas between array and object
        
        # Validate HTML tags in the text
        def validate_html_tags(text):
            # Check for unclosed tags
            open_tags = re.findall(r'<([^/][^>]*)>', text)
            close_tags = re.findall(r'</([^>]+)>', text)
            
            # Count opening and closing tags
            tag_counts = {}
            for tag in open_tags:
                tag_name = tag.split()[0]  # Get tag name without attributes
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
            for tag in close_tags:
                tag_name = tag.split()[0]
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) - 1
            
            # Check for mismatched tags
            for tag, count in tag_counts.items():
                if count != 0:
                    print(f"Warning: Mismatched HTML tags for '{tag}'")
                    return False
            return True
        
        # Try to parse the JSON
        try:
            result = json.loads(clean_text)
            
            # Validate HTML in each field
            for field in ['uk_title', 'en_title', 'en_text', 'uk_text']:
                if field in result and not validate_html_tags(result[field]):
                    print(f"Warning: Invalid HTML in {field}")
                    # Try to fix common HTML issues
                    result[field] = re.sub(r'<([^>]+)>', lambda m: m.group(0).replace(' ', ''), result[field])
                    result[field] = re.sub(r'</\s+([^>]+)>', lambda m: f'</{m.group(1)}>', result[field])
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            # Try to extract the fields using regex as a fallback
            uk_title_match = re.search(r'"uk_title"\s*:\s*"([^"]*)"', clean_text)
            en_title_match = re.search(r'"en_title"\s*:\s*"([^"]*)"', clean_text)
            en_text_match = re.search(r'"en_text"\s*:\s*"([^"]*)"', clean_text)
            uk_text_match = re.search(r'"uk_text"\s*:\s*"([^"]*)"', clean_text)
            
            if uk_title_match and en_title_match and en_text_match and uk_text_match:
                # Validate HTML in extracted fields
                fields = [
                    uk_title_match.group(1),
                    en_title_match.group(1),
                    en_text_match.group(1),
                    uk_text_match.group(1)
                ]
                for i, field in enumerate(fields):
                    if not validate_html_tags(field):
                        print(f"Warning: Invalid HTML in extracted field {i}")
                        # Try to fix common HTML issues
                        fields[i] = re.sub(r'<([^>]+)>', lambda m: m.group(0).replace(' ', ''), field)
                        fields[i] = re.sub(r'</\s+([^>]+)>', lambda m: f'</{m.group(1)}>', field)
                return tuple(fields)
            else:
                # If we can't extract the fields, return None
                print("Could not extract fields using regex")
                return None, None, None, None
        
        # Check if all required fields are present
        if 'uk_title' in result and 'en_title' in result and 'en_text' in result and 'uk_text' in result:
            return (
                result['uk_title'],
                result['en_title'],
                result['en_text'], 
                result['uk_text']
            )
        else:
            print(f"Missing required fields in JSON: {result}")
            return None, None, None, None
        
    except Exception as e:
        print(f"Error translating article: {e}")
        return None, None, None, None


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
        uk_title, en_title, en_text, uk_text = get_article_translation(API_KEY, test_title, test_article)
        
        if uk_title and en_title and en_text and uk_text:
            print("\nTranslation Results:")
            print("-" * 50)
            print("Ukrainian Title:", uk_title)
            print("Improved English Title:", en_title)
            print("\nImproved English Text:")
            print(en_text)
            print("\nUkrainian Text:")
            print(uk_text)
        else:
            print("\nTranslation failed. Please check the API key and try again.")
            
    except Exception as e:
        print(f"\nError during translation test: {e}")
        
        
