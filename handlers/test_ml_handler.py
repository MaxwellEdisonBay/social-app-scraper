import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from handlers.ml_handler import get_relevant_posts, filter_similar_posts
from common.models.models import Post

def test_get_relevant_posts():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")

    # Test cases with different types of content
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
        ),
        # Medium relevance - Canadian education system
        Post(
            title="New funding for multicultural education programs",
            desc="Federal government announces increased funding for school programs that support immigrant children's integration, including language support and cultural activities.",
            url="https://example.com/education-funding"
        ),
        # Medium relevance - Canadian job market
        Post(
            title="Canadian tech sector expands hiring of international talent",
            desc="Major Canadian tech companies announce new initiatives to hire and support skilled immigrants, with special focus on refugees and temporary residents.",
            url="https://example.com/tech-hiring"
        ),
        # Medium relevance - Canadian housing market
        Post(
            title="New affordable housing initiative in major cities",
            desc="Municipal governments launch new programs to increase affordable housing stock, with priority given to immigrant and refugee families.",
            url="https://example.com/affordable-housing"
        ),
        # Medium relevance - Canadian social services
        Post(
            title="Expanded mental health support for newcomers",
            desc="Provincial government announces new mental health programs specifically designed for immigrant communities, including trauma counseling services.",
            url="https://example.com/mental-health"
        ),
        # Low relevance - Local weather
        Post(
            title="Winter storm warning for Toronto area",
            desc="Environment Canada issues winter storm warning for the Greater Toronto Area, with heavy snow expected.",
            url="https://example.com/weather"
        )
    ]

    print("\nTesting get_relevant_posts function")
    print("==================================")
    
    try:
        relevant_urls = get_relevant_posts(test_posts, api_key)
        print(f"\nFound {len(relevant_urls)} relevant posts")
        print("\nRelevant URLs:")
        for url in relevant_urls:
            print(f"- {url}")
            
        # Find the corresponding posts for better analysis
        print("\nRelevant Posts Details:")
        for post in test_posts:
            if post.url in relevant_urls:
                print(f"\nTitle: {post.title}")
                print(f"Description: {post.desc}")
                print(f"URL: {post.url}")
                
    except Exception as e:
        print(f"Error during testing: {e}")

def test_filter_similar_posts():
    print("\nTesting filter_similar_posts function")
    print("====================================")
    
    # Create some test posts
    existing_posts = [
        Post(
            title="Ukrainian community center opens in Toronto",
            desc="New community center for Ukrainian immigrants opens its doors in downtown Toronto.",
            url="https://example.com/community-center"
        ),
        Post(
            title="Canada housing market update",
            desc="Latest trends in Canadian real estate market show increasing prices.",
            url="https://example.com/housing-market"
        )
    ]
    
    new_posts = [
        # Similar to existing post (should be filtered)
        Post(
            title="New Ukrainian community center in Toronto",
            desc="Another community center for Ukrainian immigrants opens in Toronto area.",
            url="https://example.com/community-center-2"
        ),
        # Different post (should not be filtered)
        Post(
            title="Ukrainian art exhibition in Vancouver",
            desc="Contemporary Ukrainian artists showcase their work in Vancouver gallery.",
            url="https://example.com/art-exhibition"
        )
    ]
    
    try:
        filtered_posts = filter_similar_posts(new_posts, existing_posts)
        print(f"\nOriginal new posts: {len(new_posts)}")
        print(f"Filtered posts: {len(filtered_posts)}")
        
        print("\nFiltered Posts:")
        for post in filtered_posts:
            print(f"\nTitle: {post.title}")
            print(f"Description: {post.desc}")
            print(f"URL: {post.url}")
            
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_get_relevant_posts()
    test_filter_similar_posts() 