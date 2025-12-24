from api_service import parse_size, get_unique_authors, get_largest_files

def test_helpers():
    print("Testing parse_size...")
    assert parse_size("100B") == 100
    assert parse_size("1 KB") == 1024
    assert parse_size("1.5 MB") == 1572864
    assert parse_size("1GB") == 1073741824
    print("PASSED")
    
    print("\nTesting get_unique_authors...")
    books = [
        {'author': 'Stephen King'},
        {'author': 'Stephen King'},
        {'author': 'J.K. Rowling'},
        {'author': 'Author Z'}
    ]
    authors = get_unique_authors(books)
    print(f"Authors found: {authors}")
    assert len(authors) == 3
    assert authors[0] == 'Author Z' # Alphabetical
    print("PASSED")
    
    print("\nTesting get_largest_files...")
    books_with_sizes = [
        {'title': 'Small', 'size': '500KB'},
        {'title': 'Medium', 'size': '3MB'},
        {'title': 'Large', 'size': '1.2GB'},
        {'title': 'Tiny', 'size': '100B'},
        {'title': 'Medium2', 'size': '5MB'}
    ]
    largests = get_largest_files(books_with_sizes, n=3)
    print(f"Top files found: {[b['title'] for b in largests]}")
    
    assert len(largests) == 3
    assert largests[0]['title'] == 'Large'    # 1.2GB
    assert largests[1]['title'] == 'Medium2'  # 5MB
    assert largests[2]['title'] == 'Medium'   # 3MB
    print("PASSED")

if __name__ == "__main__":
    test_helpers()
