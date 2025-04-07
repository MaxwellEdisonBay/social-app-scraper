import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def test_ircc_request():
    url = "https://www.canada.ca/en/immigration-refugees-citizenship/news/2025/03/the-government-of-canada-is-investing-more-than-93-million-to-support-francophone-minority-communities.html"
    
    # Create a session with retry logic
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # More complete headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    print(f"Testing request to IRCC article...")
    print(f"URL: {url}")
    print("\nUsing headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    try:
        # Make the request with a longer timeout and SSL verification options
        response = session.get(
            url,
            headers=headers,
            timeout=(10, 30),  # (connect timeout, read timeout)
            verify=True,  # Enable SSL verification
            allow_redirects=True
        )
        
        # Print response details
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
            
        print(f"\nContent Length: {len(response.text)} characters")
        
        # Print the first 500 characters of content to verify we got HTML
        print("\nFirst 500 characters of content:")
        print(response.text[:500])
        
    except requests.exceptions.Timeout:
        print("Request timed out")
        print("  - Connect timeout: 10 seconds")
        print("  - Read timeout: 30 seconds")
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_ircc_request() 