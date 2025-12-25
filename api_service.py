import requests
from typing import Optional, Dict, List, Any
import time
from config import API_KEY, API_HOST, SEARCH_URL, DOWNLOAD_URL

class Book:
    """Represents a book result from the API"""
    def __init__(self, title: str, author: str, md5: str, year: str, extension: str = ""):
        self.title = title
        self.author = author
        self.md5 = md5
        self.year = year
        self.extension = extension
    
    def __repr__(self):
        return f"<Book: {self.title} ({self.year}) .{{self.extension}}>"

def get_api_headers() -> Dict[str, str]:
    """Returns the required headers for RapidAPI requests"""
    return {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }

def search_for_book(query: str, author: str = "", limit: int = 20, file_type: str = "ebook") -> List[Dict[str, Any]]:
    """
    Search for a book using Anna's Archive API.
    
    Args:
        query: Book title or keywords
        author: Author name (optional)
        limit: Max number of MD5s to return
        file_type: 'ebook' or 'audiobook'
        
    Returns:
        List of book dictionaries with metadata
    """
    full_query = f"{query} {author}".strip()
    
    # Define extensions based on type
    if file_type == 'audiobook':
        # Common audiobook formats
        extensions = "mp3, m4b, m4a, flac"
        # We might want to remove 'comic' etc for audiobooks, but the API might not support excluding cats easily
        # keeping the user's provided categories for now but focusing on extensions
        categories = "fiction, nonfiction, unknown" 
    else:
        # User provided ebook extensions
        extensions = "pdf, epub, mobi, azw3"
        categories = "fiction, nonfiction, comic, magazine, musicalscore, other, unknown"

    querystring = {
        "q": full_query,
        "cat": categories,
        "page": "1",
        "ext": extensions,
        "sort": "mostRelevant",
        "source": "libgenLi, libgenRs" 
    }
    
    print(f"Searching for '{full_query}' ({file_type})...")
    
    try:
        response = requests.get(SEARCH_URL, headers=get_api_headers(), params=querystring)
        response.raise_for_status() # Raise error for bad status codes
        
        data = response.json()
        
        if not data or 'books' not in data:
            print("No books found or invalid response format.")
            return []
            
        books_data = data['books']
        results = []
        
        for book in books_data:
            # Basic validation
            if not book.get('md5') or not book.get('title'):
                continue
                
            results.append(book)
            if len(results) >= limit:
                break
                
        return results

    except Exception as e:
        print(f"Error searching for book '{full_query}': {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Response: {e.response.text}")
        return []

def download_book(md5_hashes: List[str], log_callback=None, progress_callback=None, timeout=60) -> Optional[bytes]:
    """
    Download a book using a list of MD5 hashes via the API.
    log_callback: function(str) -> void
    progress_callback: function(current_bytes, total_bytes) -> void
    timeout: read timeout in seconds
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    if not md5_hashes:
        return None
    
    log(f"Attempting download ({len(md5_hashes)} candidates)...")
    
    for i, md5_hash in enumerate(md5_hashes):
        log(f"Trying source {i+1}/{len(md5_hashes)}: {md5_hash}")
        
        try:
            querystring = {"md5": md5_hash}
            
            # Step 1: Get download links
            link_response = requests.get(
                DOWNLOAD_URL,
                headers=get_api_headers(),
                params=querystring,
                timeout=30 # Short timeout for metadata
            )
            
            if not link_response.ok:
                log(f"  > API Status: {link_response.status_code}")
                continue
            
            response_data = link_response.json()
            
            if not isinstance(response_data, list) or len(response_data) == 0:
                log(f'  > No URLs for this source')
                continue
            
            # Step 2: Try Links
            for download_url in response_data:
                if not download_url.startswith("http"): 
                    continue
                    
                log(f"  > Requesting file from: {download_url[:40]}...")
                
                try:
                    # Stream the download
                    with requests.get(download_url, timeout=timeout, stream=True) as file_response:
                        if file_response.ok:
                            total_size = int(file_response.headers.get('content-length', 0))
                            data_chunks = []
                            downloaded_size = 0
                            
                            for chunk in file_response.iter_content(chunk_size=8192):
                                if chunk:
                                    data_chunks.append(chunk)
                                    downloaded_size += len(chunk)
                                    if progress_callback and total_size > 0:
                                        progress_callback(downloaded_size, total_size)
                                        
                            content = b"".join(data_chunks)
                            size_mb = len(content) / (1024 * 1024)
                            log(f"  > Success! ({size_mb:.2f} MB)")
                            return content
                        else:
                            log(f"  > Link failed ({file_response.status_code})")
                except Exception as e:
                    log(f"  > Link error: {str(e)[:100]}") # Truncate error
                    
        except Exception as e:
            log(f"  > MD5 Error: {str(e)}")
            continue
            
    log(f"All sources failed.")
    return None

def download_book_by_title(title: str, author: str = "", file_type: str = "ebook") -> Optional[bytes]:
    """
    High-level function to search for a book by title and download the best result.
    
    Args:
        title: Book title
        author: Author name
        file_type: 'ebook' or 'audiobook'
    """
    print(f"\nStarting download process for: {title}")
    
    # Search
    books = search_for_book(title, author=author, limit=5, file_type=file_type)
    
    if not books:
        if file_type == 'ebook':
            print("No ebooks found. Trying audiobooks...")
            return download_book_by_title(title, author, file_type='audiobook')
        print("- No matching books found.")
        return None
        
    print(f"+ Found {len(books)} potential matches.")
    
    # Extract MD5s
    md5s = [b['md5'] for b in books]
    
    # Download
    content = download_book(md5s)
    
    if content:
        return content
    elif file_type == 'ebook':
        # If ebook download failed, prompt/try audiobook? 
        # For now, let's just log it. The user said "give the user to try to find audiobook as well"
        print("⚠️ Ebook download failed. Trying to find audiobook version...")
        return download_book_by_title(title, author, file_type='audiobook')
        
    return None


def parse_size(size_str: str) -> int:
    """Parses a size string like '3.4MB' into bytes."""
    if not size_str:
        return 0
    
    size_str = size_str.upper().strip()
    multipliers = {
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'B': 1
    }
    
    import re
    match = re.search(r'([\d\.]+)\s*([KMGT]?B)', size_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        return int(value * multipliers.get(unit, 1))
    
    return 0

def get_unique_authors(books: List[Dict[str, Any]]) -> List[str]:
    """Returns a sorted list of unique authors from book results."""
    authors = set()
    for book in books:
        if book.get('author'):
            authors.add(book['author'].strip())
    return sorted(list(authors))

def filter_by_author(books: List[Dict[str, Any]], author: str) -> List[Dict[str, Any]]:
    """Filters books by a specific author (case insensitive substring match)."""
    if not author:
        return books
    
    author_lower = author.lower()
    return [b for b in books if b.get('author') and author_lower in b['author'].lower()]

def get_largest_files(books: List[Dict[str, Any]], n: int = 3, max_size: int = None) -> List[Dict[str, Any]]:
    """
    Returns the top n books with the largest file sizes.
    If max_size is provided (in bytes), filters out files larger than that limit.
    """
    if not books:
        return []
        
    # Enrich books with parsed size if not present
    valid_books = []
    
    for book in books:
        if '_parsed_size' not in book:
            book['_parsed_size'] = parse_size(book.get('size', '0'))
            
        # Filter by max_size if specified
        if max_size is not None:
             if book['_parsed_size'] > max_size:
                 continue
                 
        valid_books.append(book)
            
    # Sort by size descending
    sorted_books = sorted(valid_books, key=lambda x: x['_parsed_size'], reverse=True)
    return sorted_books[:n]

def get_filename_from_response(response: requests.Response, default_name: str) -> str:
    """Extract filename from response headers or generate one."""
    if 'Content-Disposition' in response.headers:
        content_disp = response.headers['Content-Disposition']
        if 'filename=' in content_disp:
            filename = content_disp.split('filename=')[1].strip('"')
            return filename
    
    return default_name
