from api_service import search_for_book, download_book

# Test search
md5_hashes = search_for_book("Automatic Noodle", "Annalee Newitz", "2025")
if md5_hashes:
    print(f"Found MD5 hashes: {md5_hashes}")
    
    # Test download
    data = download_book(md5_hashes)
    if data:
        print(f"Successfully downloaded {len(data)} bytes")
        # Save test file
        with open("test_book.epub", "wb") as f:
            f.write(data)
        print("Saved as test_book.epub")
    else:
        print("Download failed")
else:
    print("Book not found")