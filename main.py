import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import zipfile
from pathlib import Path
from api_service import search_for_book, download_book, get_unique_authors, filter_by_author, get_largest_files

class AuthorSelectionDialog(tk.Toplevel):
    def __init__(self, parent, authors):
        super().__init__(parent)
        self.title("Select Author")
        self.geometry("400x300")
        self.selected_author = None
        
        ttk.Label(self, text="Multiple authors found. Please select one:", padding=10).pack()
        
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for author in authors:
            self.listbox.insert(tk.END, author)
            
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Select", command=self.on_select).pack(side=tk.RIGHT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=10)
        
        self.transient(parent)
        self.grab_set()
        self.wait_window()
        
    def on_select(self):
        selection = self.listbox.curselection()
        if selection:
            self.selected_author = self.listbox.get(selection[0])
            self.destroy()

class EbookPackager:
    def __init__(self, root):
        self.root = root
        self.root.title("Anna's Archive Bulk Downloader")
        self.root.geometry("900x700")
        
        # Store book info: [{title, author, md5, size, extension}, ...]
        self.books_to_download = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Instructions
        instructions = ttk.Label(
            main_frame, 
            text="Enter book details. The app will automatically find the best quality file.",
            wraplength=800,
            justify=tk.LEFT
        )
        instructions.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Input fields
        ttk.Label(main_frame, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.title_entry = ttk.Entry(main_frame, width=40)
        self.title_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Author (Optional):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.author_entry = ttk.Entry(main_frame, width=40)
        self.author_entry.grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Year (Optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.year_entry = ttk.Entry(main_frame, width=40)
        self.year_entry.grid(row=3, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Add book button
        ttk.Button(
            main_frame, 
            text="Search & Add", 
            command=self.add_book
        ).grid(row=1, column=2, rowspan=3, padx=5, pady=5, sticky=(tk.N, tk.S))
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        
        # Book list
        ttk.Label(main_frame, text="Books to Download:").grid(
            row=5, column=0, columnspan=3, sticky=tk.W, pady=5
        )
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.book_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set, 
            height=15,
            font=('TkDefaultFont', 9)
        )
        self.book_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.book_listbox.yview)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Download button
        self.download_btn = ttk.Button(
            main_frame, 
            text="Download All as ZIP", 
            command=self.download_all
        )
        self.download_btn.grid(row=8, column=0, columnspan=3, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=500, mode='determinate')
        self.progress.grid(row=9, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", wraplength=800)
        self.status_label.grid(row=10, column=0, columnspan=3, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
    
    def add_book(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        year = self.year_entry.get().strip()
        
        if not title:
            messagebox.showwarning("Input Error", "Please enter at least a title")
            return
            
        self.status_label.config(text="Searching...")
        self.root.update()
        
        # 1. Search
        query = title
        if year:
            query = f"{title} {year}"
            
        # Increased limit for better selection
        books = search_for_book(query=query, author=author, limit=20)
        
        if not books:
            messagebox.showinfo("Not Found", f"No books found for '{title}'")
            self.status_label.config(text="Ready")
            return
            
        # 2. Disambiguate Author
        selected_author = author
        if not author:
            # Check unique authors
            unique_authors = get_unique_authors(books)
            if len(unique_authors) > 1:
                dialog = AuthorSelectionDialog(self.root, unique_authors)
                if dialog.selected_author:
                    selected_author = dialog.selected_author
                else:
                    self.status_label.config(text="Selection cancelled")
                    return
        
        # 3. Filter and Select Best
        filtered_books = filter_by_author(books, selected_author)
        if not filtered_books:
            # Fallback (shouldn't happen if logic is correct)
            filtered_books = books 
            
        best_matches = get_largest_files(filtered_books, n=3)
        
        if not best_matches:
            messagebox.showerror("Error", "Could not find a valid file match.")
            return
            
        primary_match = best_matches[0]
            
        # 4. Add to List
        # Check duplicates (check if primary MD5 is already in list)
        for b in self.books_to_download:
            # Check if any of the new MD5s match existing primary MD5s
            if b['primary_md5'] == primary_match['md5']:
                messagebox.showinfo("Duplicate", "This specific file is already in the list.")
                self.status_label.config(text="Ready")
                return

        # Store metadata
        # We store the primary match details for display, but keep all MD5s for download
        entry = primary_match.copy()
        entry['primary_md5'] = primary_match['md5']
        entry['all_md5s'] = [b['md5'] for b in best_matches]
        
        self.books_to_download.append(entry)
        
        # Display
        size_str = primary_match.get('size', 'Unknown size')
        ext = primary_match.get('ext', 'unknown')
        match_count = len(best_matches)
        display_text = f"{primary_match['title']} by {primary_match['author']} [{ext.upper()}, {size_str}] ({match_count} sources)"
        self.book_listbox.insert(tk.END, display_text)
        
        # Reset input
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.status_label.config(text=f"Added: {display_text}")

    def remove_book(self):
        selection = self.book_listbox.curselection()
        if selection:
            index = selection[0]
            self.book_listbox.delete(index)
            del self.books_to_download[index]
            self.status_label.config(text="Book removed")
    
    def clear_all(self):
        if self.books_to_download:
            if messagebox.askyesno("Clear All", "Remove all books from the list?"):
                self.book_listbox.delete(0, tk.END)
                self.books_to_download.clear()
                self.status_label.config(text="List cleared")
    
    def download_all(self):
        if not self.books_to_download:
            messagebox.showwarning("No Books", "Please add books to download")
            return
        
        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            initialfile="annas_archive_books.zip"
        )
        
        if not zip_path:
            return
        
        self.download_btn.config(state='disabled')
        temp_dir = Path("temp_downloads")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            self.progress['maximum'] = len(self.books_to_download)
            self.progress['value'] = 0
            
            downloaded_files = []
            failed_books = []
            
            for i, book in enumerate(self.books_to_download):
                title = book.get('title', 'Unknown')
                author = book.get('author', 'Unknown')
                # Use the list of MD5s we stored
                md5_list = book.get('all_md5s', [book.get('md5')])
                ext = book.get('ext', 'epub')
                
                self.status_label.config(text=f"Downloading ({i+1}/{len(self.books_to_download)}): {title}")
                self.root.update()
                
                # Direct download trying all candidate MD5s
                content = download_book(md5_list)
                
                if content:
                    safe_filename = f"{title[:50]}_by_{author[:30]}".replace('/', '_').replace('\\', '_')
                    file_path = temp_dir / f"{safe_filename}.{ext}"
                    
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    downloaded_files.append(file_path)
                else:
                    failed_books.append(f"{title} - Download failed")
                
                self.progress['value'] = i + 1
                self.root.update()
            
            # Create ZIP
            if downloaded_files:
                self.status_label.config(text="Creating ZIP file...")
                self.root.update()
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in downloaded_files:
                        zipf.write(file_path, file_path.name)
                
                # Cleanup
                for file_path in downloaded_files:
                    file_path.unlink()
                temp_dir.rmdir()
                
                msg = f"Downloaded {len(downloaded_files)} books to:\n{zip_path}"
                if failed_books:
                    msg += f"\n\nFailed: {len(failed_books)} match(es)"
                    
                messagebox.showinfo("Complete", msg)
                self.status_label.config(text="Download Complete")
            else:
                self.status_label.config(text="Failed")
                messagebox.showerror("Failed", "No books downloaded.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            self.download_btn.config(state='normal')
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except: pass

def main():
    root = tk.Tk()
    app = EbookPackager(root)
    root.mainloop()

if __name__ == "__main__":
    main()