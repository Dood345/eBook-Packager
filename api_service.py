import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Optional, Dict, List
import time
import tempfile
import os
from pathlib import Path
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
    """
    query = f"{title} {year}".strip()
    
    params = {
        'q': query,
        'author': author,
        'ext': 'epub',
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
        
        if not data or 'books' not in data or not isinstance(data['books'], list) or len(data['books']) == 0:
            return []
        
        books = data['books']
        
        title_lower = title.lower()
        md5_hashes = []
        for book in books:
            if book.get('title') and title_lower in book['title'].lower() and book.get('md5'):
                md5_hashes.append(book['md5'])
                if len(md5_hashes) == 5:
                    break
        
        return md5_hashes
        
    except Exception as e:
        print(f"Error searching for book '{title}': {str(e)}")
        return []

def download_via_annas_archive_website(md5_hash: str, timeout: int = 180, show_browser: bool = False) -> Optional[bytes]:
    """
    Navigate Anna's Archive website to download a book.
    
    Process:
    1. Go to annas-archive.org
    2. Search for the MD5 hash
    3. Click first result
    4. Look for libgen.is download link (no captcha)
    5. Click and wait for download
    
    Args:
        md5_hash: The MD5 hash of the book
        timeout: Maximum time to wait for download (seconds)
        show_browser: If True, the browser window will be shown.
    
    Returns:
        Downloaded file content as bytes if successful, None otherwise
    """
    driver = None
    download_dir = None
    
    try:
        print(f"\n{'='*60}")
        print(f"🌐 Starting browser automation for MD5: {md5_hash}")
        print(f"{ '='*60}\n")
        
        # Create temporary download directory
        download_dir = tempfile.mkdtemp()
        
        # Configure Chrome options
        chrome_options = Options()

        if not show_browser:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize browser
        print("Starting Chrome...")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(60)

        # Enable downloads in selenium
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        command_result = driver.execute("send_command", params)
        
        # Navigate to Anna's Archive MD5 page
        print(f"📖 Opening annas-archive.org/md5/{md5_hash}...")
        driver.get(f"https://annas-archive.org/md5/{md5_hash}")
        time.sleep(5)  # Give page time to load
        
        # Look for download links
        print("\n🔍 Scanning for download links...")
        
        # Scroll to load all content
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        
        # Look for slow download links
        print("Looking for slow download links...")
        slow_download_link = None
        
        try:
            # Find all links on the page
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            
            for link in all_links:
                link_text = link.text.lower()
                if 'slow' in link_text or 'external' in link_text:
                    slow_download_link = link
                    print(f"✓ Found slow download link: {link.get_attribute('href')}")
                    break
        except Exception as e:
            print(f"Error finding slow download link: {e}")

        if not slow_download_link:
            print("\n❌ No slow download links found on page")
            # Save screenshot for debugging
            try:
                screenshot_path = Path(download_dir) / "no_links_found.png"
                driver.save_screenshot(str(screenshot_path))
                print(f"📸 Screenshot saved: {screenshot_path}")
            except:
                pass
            return None

        # Click the slow download link
        print(f"\n🔽 Clicking slow download link...")
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", slow_download_link)
            time.sleep(1)
            slow_download_link.click()
            print("✓ Slow download link clicked")
            # Wait for the "Download now" button to be present, with a 30 second timeout for cloudflare
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download now') and @target='_blank']"))
            )
        except TimeoutException:
            print("✗ 'Download now' button not found within 30 seconds. Likely a Cloudflare page. Please try again with 'show_browser=True'.")
            return None
        except Exception as e:
            if "session deleted" in str(e):
                print("✗ Browser crashed, likely due to Cloudflare. Please try again with 'show_browser=True'.")
                return None
            print(f"✗ Failed to click slow download link: {e}")
            return None

        # Handle timer on the download page
        try:
            # First, check if "Download Now" is already present
            download_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download now') and @target='_blank']"))
            )
            print("✓ 'Download Now' button found immediately.")
            download_url = download_button.get_attribute('href')
            print(f"✓ Found download URL: {download_url}")
            driver.get(download_url)
            print("✓ Navigating to download URL")
        except TimeoutException:
            # If not present, then look for a timer
            try:
                timer_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'wait') or contains(text(), 'seconds')]" ))
                )
                
                timer_span_selector = (By.CLASS_NAME, "js-partner-countdown")
                # Loop to track and print timer
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        timer_element = driver.find_element(*timer_span_selector)
                        current_time_str = timer_element.text
                        print(f"⏳ Timer: {current_time_str} seconds remaining")
                        time.sleep(5)
                    except:
                        break # Timer disappeared

                # Wait for the timer to disappear or the download button to be clickable
                WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download now') and @target='_blank']"))
                )
                
                # Click the final download button
                download_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Download now') and @target='_blank']")
                download_url = download_button.get_attribute('href')
                print(f"✓ Found download URL: {download_url}")
                driver.get(download_url)
                print("✓ Navigating to download URL")

            except TimeoutException:
                print("✓ No timer detected, or download started automatically.")
            except Exception as e:
                print(f"Error handling timer or final download button: {e}")
        except Exception as e:
            print(f"Error handling timer or final download button: {e}")

        # Wait for download to start
        print("\n⏳ Waiting for download to start...")
        try:
            WebDriverWait(driver, 30).until(
                lambda d: any(f.endswith('.epub') or f.endswith('.pdf') for f in os.listdir(download_dir))
            )
            print("✓ Download started.")
        except TimeoutException:
            print("✗ Download did not start within 30 seconds.")
            return None

        # Wait for download to complete
        print(f"\n⏳ Waiting for download to complete... (timeout: {timeout}s)")
        start_time = time.time()
        downloaded_file = None
        
        while time.time() - start_time < timeout:
            files = list(Path(download_dir).glob("*"))
            complete_files = [
                f for f in files 
                if not str(f).endswith(('.crdownload', '.tmp', '.png'))
                and f.stat().st_size > 0
            ]
            if complete_files:
                latest_file = max(complete_files, key=lambda f: f.stat().st_mtime)
                initial_size = latest_file.stat().st_size
                time.sleep(2)
                final_size = latest_file.stat().st_size
                if initial_size == final_size and initial_size > 10000:
                    downloaded_file = latest_file
                    size_mb = final_size / (1024 * 1024)
                    print(f"\n✅ Download complete!")
                    print(f"   File: {downloaded_file.name}")
                    print(f"   Size: {size_mb:.2f} MB")
                    break
            time.sleep(1)
        
        if not downloaded_file:
            print(f"\n❌ Download timeout after {timeout} seconds")
            files_found = list(Path(download_dir).glob("*"))
            if files_found:
                print(f"Files in directory: {[f.name for f in files_found]}")
            return None
        
        # Read the file
        print("📖 Reading file...")
        with open(downloaded_file, 'rb') as f:
            content = f.read()
        
        print(f"✅ Successfully downloaded {len(content)} bytes via website")
        return content
        
    except Exception as e:
        print(f"\n❌ Website automation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup
        if driver:
            try:
                print("\nClosing browser...")
                driver.quit()
            except:
                pass
        
        # Clean up download directory
        if download_dir and os.path.exists(download_dir):
            try:
                for file in Path(download_dir).glob("*"):
                    try:
                        file.unlink()
                    except:
                        pass
                os.rmdir(download_dir)
            except:
                pass

def download_book(md5_hashes: List[str]) -> Optional[bytes]:
    """
    Download a book using a list of MD5 hashes.
    First tries direct API downloads, then falls back to website automation.
    """
    if not md5_hashes:
        return None
    
    print(f"\n{'='*60}")
    print(f"📦 Attempting to download book")
    print(f"   MD5 hashes to try: {len(md5_hashes)}")
    print(f"{ '='*60}\n")
    
    # Phase 1: Try API downloads
    print("📡 PHASE 1: Direct API downloads")
    print("-" * 40)
    
    for i, md5_hash in enumerate(md5_hashes):
        print(f"\n[{i+1}/{len(md5_hashes)}] Trying MD5: {md5_hash}")
        
        try:
            querystring = {"md5": md5_hash}
            
            link_response = requests.get(
                DOWNLOAD_URL,
                headers=get_api_headers(),
                params=querystring
            )
            
            if not link_response.ok:
                print(f"  ✗ API returned status {link_response.status_code}")
                continue
            
            response_data = link_response.json()
            
            if not isinstance(response_data, list) or len(response_data) == 0:
                print(f'  ✗ No download URLs available')
                continue
            
            final_download_url = response_data[0]
            print(f"  → Downloading from: {final_download_url[:60]}...")
            
            file_response = requests.get(
                final_download_url,
                timeout=120,
                stream=True
            )
            
            if file_response.ok:
                content = file_response.content
                size_mb = len(content) / (1024 * 1024)
                print(f"  ✅ Success! Downloaded {size_mb:.2f} MB")
                return content
            else:
                print(f"  ✗ Download failed (status {file_response.status_code})")
        
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            continue
    
    # Phase 2: Website automation fallback
    print(f"\n{'='*60}")
    print("⚠️  PHASE 2: All API downloads failed")
    print("🌐 Attempting website automation fallback...")
    print(f"{ '='*60}")
    
    if md5_hashes:
        first_md5 = md5_hashes[0]
        print(f"\nUsing first MD5: {first_md5}")
        content = download_via_annas_archive_website(first_md5, timeout=180, show_browser=False)
        
        if content:
            return content
    
    print(f"\n{'='*60}")
    print("❌ All download methods failed")
    print(f"{ '='*60}\n")
    return None

def get_filename_from_response(response: requests.Response, book_id: str) -> str:
    """Extract filename from response headers or generate one."""
    if 'Content-Disposition' in response.headers:
        content_disp = response.headers['Content-Disposition']
        if 'filename=' in content_disp:
            filename = content_disp.split('filename=')[1].strip('"')
            return filename
    
    return f"{book_id}.epub"