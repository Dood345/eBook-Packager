# Anna's Archive Downloader

A minimal, powerful tool to search and download ebooks (and audiobooks!) directly from Anna's Archive.

## Features
- **Search & Download**: Enter a title and author to automatically find and download books.
- **Bulk Download**: Add multiple books to a list and download them all as a verified ZIP package.
- **Smart Fallback**: Automatically tries multiple download mirrors provided by Anna's Archive.
- **Audiobook Support**: If an ebook isn't found, it can check for audiobook versions (or you can request them).

## Setup
1.  **Get an API Key**:
    You need a RapidAPI key for the [Anna's Archive API](https://rapidapi.com/alexander-koba/api/annas-archive-api).
    
2.  **Environment Variables**:
    Create a `.env` file in the project root (see `.env.example`):
    ```env
    ANNAS_ARCHIVE_API_KEY=your_rapidapi_key_here
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
### Graphical Interface
Run the main application:
```bash
python main.py
```
1.  Enter the **Title** and **Author**.
2.  (Optional) Enter the **Year**.
3.  Click **Add to List**.
4.  Repeat for as many books as you want.
5.  Click **Download All as ZIP**.

### Command Line / Scripting
You can use the `api_service` directly in your own scripts:

```python
from api_service import download_book_by_title

# Download a book and get the raw bytes
data = download_book_by_title("The Hobbit", "J.R.R. Tolkien")

if data:
    with open("The Hobbit.epub", "wb") as f:
        f.write(data)
```

## Under the Hood
This application is powered by the **Anna's Archive API** via RapidAPI.

### Logic Flow
1.  **Search**: 
    The app sends a search query (Title + Author) to the API.
    - *Default filters*: searches for `epub`, `pdf`, `mobi`, `azw3`.
    - *Categories*: `fiction`, `nonfiction`, etc.
    
2.  **Filter**:
    It retrieves the top 5 most relevant results, containing metadata and MD5 hashes.

3.  **Download**:
    Use the `download` endpoint with the specific MD5 hash to get direct download links (e.g., from Libgen mirrors).
    - Checks links sequentially until one works.
    - No browser automation or CAPTCHAs required (pure API).

### Libraries
- **`requests`**: Handles all HTTP communication with the API and file downloads.
- **`tkinter`**: Provides the lightweight graphical user interface (stdlib).
- **`python-dotenv`**: Securely manages the API key.

## Requirements
- Python 3.8+
- An active RapidAPI key for Anna's Archive API.
