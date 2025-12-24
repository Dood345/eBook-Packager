# Anna's Archive Downloader

A smart, resilient tool to search and download ebooks (and audiobooks!) directly from Anna's Archive.

## Features
- **Spreadsheet Interface**: Clean table view allows granular control over your download list.
- **Smart Selection**: Automatically detects and selects the highest quality (largest) files.
- **Resilience**: Stores the top 3 best mirrors for every book and automatically falls back if one fails.
- **Audiobook Support**: Toggle "Get Audiobook" per row to search for and download an audiobook version alongside your ebook.
- **Structured Output**: Downloads are organized into folders: `Author/Title/File`.

## Setup
1.  **Get an API Key**:
    You need a RapidAPI key for the [Anna's Archive API](https://rapidapi.com/alexander-koba/api/annas-archive-api).
    
2.  **Environment Variables**:
    Create a `.env` file in the project root:
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

1.  **Search & Add**: 
    - Enter **Title** and optional **Author**.
    - Press `Enter` or click **Search & Add**.
    - If multiple authors are found (e.g. "King"), a dialog will ask you to select the correct one.
2.  **Manage List**:
    - The book is added to your table.
    - **Audiobook?**: Click the checkbox cell in the "Get Audiobook?" column to opt-in for an audiobook version.
3.  **Download**:
    - Click **Download All as ZIP**.
    - Select a save location.
    - Resulting ZIP will contain organized folders.

### Command Line / Scripting
You can use the `api_service` logic helpers in your own scripts:

```python
from api_service import search_for_book, download_book, get_largest_files

# Search for matches
books = search_for_book("The Hobbit", "J.R.R. Tolkien")

# Get top 3 best files (largest)
best_matches = get_largest_files(books, n=3)
md5s = [b['md5'] for b in best_matches]

# Download (tries all MD5s sequentially)
data = download_book(md5s)
```

## Under the Hood
This application uses a sophisticated logic flow to ensure you get the best file:

1.  **Search & Disambiguate**: 
    - Real-time API search ensures valid metadata.
    - User intervention prevents "wrong author" downloads.
2.  **Smart Selection**:
    - Instead of guessing, we parse file sizes (KB, MB, GB) from the API.
    - We queue the **Top 3** largest (highest quality) files for each book.
3.  **Resilient Download**:
    - The downloader attempts the largest file first.
    - If the link is dead or 404s, it seamlessly tries the next best option.
4.  **Structure**:
    - Files are sanitized and saved as:
      `<Author>/<Book Title>/<Filename>.<ext>`

### Libraries
- **`requests`**: API communication.
- **`tkinter`**: GUI (Treeview/Spreadsheet).
- **`python-dotenv`**: Config management.
