from api_service import download_book_by_title
import os

def test_download():
    print("Testing download by title...")
    title = "Frankenstein"
    result = download_book_by_title(title)
    
    if result:
        print(f"Successfully downloaded {len(result)} bytes!")
        with open("frankenstein_test.epub", "wb") as f:
            f.write(result)
        print("Saved to frankenstein_test.epub")
        # cleanup
        os.remove("frankenstein_test.epub")
    else:
        print("Failed to download book.")

if __name__ == "__main__":
    test_download()
