import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('ANNAS_ARCHIVE_API_KEY', '')

# Validate that API key exists
if not API_KEY:
    raise ValueError("API_KEY not found! Please create a .env file with ANNAS_ARCHIVE_API_KEY")

# API Constants
API_HOST = 'annas-archive-api.p.rapidapi.com'
SEARCH_URL = 'https://annas-archive-api.p.rapidapi.com/search'
DOWNLOAD_URL = 'https://annas-archive-api.p.rapidapi.com/download'
