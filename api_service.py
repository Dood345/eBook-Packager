import requests
from typing import Optional, Dict, List
from config import API_KEY, API_HOST, SEARCH_URL, DOWNLOAD_URL

class Book:
    """Represents a book result from the API"""
    def __init__(self, title: str, author: str, md5: str, year: str):
        self.title = title
        self.author = author
        self.md5 = md5
        self.year = year

def get_api_headers() -> Dict[str, str]:
    """Returns the required headers for RapidAPI requests"""
    return {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST,
    }

def search_for_book(title: str, author: str, year: str = "") -> List[str]:
    """
    Search for a book and return a list of up to 5 MD5 hashes.
    
    Args:
        title: Book title
        author: Book author
        year: Publication year (optional, often inconsistent in databases)
    
    Returns:
        A list of up to 5 MD5 hashes, or an empty list if no matches are found.
    """
    # Combine title and author for more reliable search
    # Year is often too specific and inconsistent in database entries
    query = f"{title} {year}".strip()
    
    # Build search parameters
    params = {
        'q': query,
        'author': author,
        'ext': 'epub',  # Search for EPUB format
        'sort': 'mostRelevant',
        'lang': 'en',
    }
    
    try:
        response = requests.get(
            SEARCH_URL,
            headers=get_api_headers(),
            params=params,
        )
        
        if not response.ok:
            print(f"Search API failed: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        
        # Check if response contains books
        if not data or 'books' not in data or not isinstance(data['books'], list) or len(data['books']) == 0:
            return []
        
        books = data['books']
        
        # Find all books with a matching title and collect their MD5 hashes
        title_lower = title.lower()
        md5_hashes = []
        for book in books:
            if book.get('title') and title_lower in book['title'].lower() and book.get('md5'):
                md5_hashes.append(book['md5'])
                if len(md5_hashes) == 5:
                    break
        
        return md5_hashes
        
    except requests.exceptions.RequestException as e:
        print(f"Error searching for book '{title}': {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error during search: {str(e)}")
        return []

def download_book(md5_hashes: List[str]) -> Optional[bytes]:
    """
    Download a book using a list of MD5 hashes, trying each one until successful.
    
    The API returns an array of download URLs from different mirrors.
    We use the first available link.
    
    Args:
        md5_hashes: A list of MD5 hashes for the book.
    
    Returns:
        Book file content as bytes if successful, None otherwise
    """
    if not md5_hashes:
        return None
    
    for md5_hash in md5_hashes:
        try:
            querystring = {"md5": md5_hash}
            
            # Step 1: Call the authenticated API endpoint to get array of final download links
            link_response = requests.get(
                DOWNLOAD_URL,
                headers=get_api_headers(),
                params=querystring
            )
            
            if not link_response.ok:
                print(f"API failed to provide download links for MD5 {md5_hash}. Status: {link_response.status_code}")
                print(f"Response: {link_response.text}")
                continue  # Try the next MD5 hash
            
            # The API returns an array of download URLs from different mirrors
            response_data = link_response.json()
            
            if not isinstance(response_data, list) or len(response_data) == 0:
                print(f'API response for MD5 {md5_hash} did not contain a valid array of download URLs.')
                continue
            
            # Use the first available link
            final_download_url = response_data[0]
            
            if not final_download_url or not isinstance(final_download_url, str):
                print(f'The first download link provided by the API for MD5 {md5_hash} is invalid.')
                continue
            
            print(f"Attempting to download from: {final_download_url}")
            
            # Step 2: Fetch the actual file from the final URL
            file_response = requests.get(
                final_download_url,
                timeout=120,  # Longer timeout for large files
                stream=True
            )
            
            if file_response.ok:
                print(f"Successfully downloaded book with MD5 {md5_hash}")
                return file_response.content  # Success! Return the content.
            else:
                print(f"Failed to download file from {final_download_url}. Status: {file_response.status_code}")
                # Continue to the next MD5 hash
        
        except requests.exceptions.RequestException as e:
            print(f"Error downloading book with MD5 {md5_hash}: {str(e)}")
            continue  # Try the next MD5 hash
        except Exception as e:
            print(f"Unexpected error during download for MD5 {md5_hash}: {str(e)}")
            continue  # Try the next MD5 hash
            
    print("All download attempts failed.")
    return None

def get_filename_from_response(response: requests.Response, book_id: str) -> str:
    """
    Extract filename from response headers or generate one.
    
    Args:
        response: The requests Response object
        book_id: Fallback identifier for the file
    
    Returns:
        Filename string
    """
    # Try to get filename from Content-Disposition header
    if 'Content-Disposition' in response.headers:
        content_disp = response.headers['Content-Disposition']
        if 'filename=' in content_disp:
            filename = content_disp.split('filename=')[1].strip('"\'')
            return filename
    
    # Fallback to using book_id with .epub extension
    return f"{book_id}.epub"
