from api_service import download_via_annas_archive_website

if __name__ == '__main__':
    # Test with a known MD5
    md5 = "6bc28c7b0f7d2e7772de26fcb6194b1b"
    content = download_via_annas_archive_website(md5, timeout=300, show_browser=True)

    if content:
        with open("test_book.epub", "wb") as f:
            f.write(content)
        print("Success!")