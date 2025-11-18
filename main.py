import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import zipfile
from pathlib import Path
from api_service import search_for_book, download_book

class EbookPackager:
    def __init__(self, root):
        self.root = root
        self.root.title("Anna's Archive Bulk Downloader")
        self.root.geometry("900x700")
        
        # Store book info: [(title, author, year), ...]
        self.books_to_download = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Instructions
        instructions = ttk.Label(
            main_frame, 
            text="Enter book details to search and download EPUBs from Anna's Archive",
            wraplength=800,
            justify=tk.LEFT
        )
        instructions.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Input fields
        ttk.Label(main_frame, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.title_entry = ttk.Entry(main_frame, width=40)
        self.title_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Author:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.author_entry = ttk.Entry(main_frame, width=40)
        self.author_entry.grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Year (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.year_entry = ttk.Entry(main_frame, width=40)
        self.year_entry.grid(row=3, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Add book button
        ttk.Button(
            main_frame, 
            text="Add to List", 
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
        
        # Remove book button
        ttk.Button(
            main_frame, 
            text="Remove Selected", 
            command=self.remove_book
        ).grid(row=7, column=0, pady=5, sticky=tk.W)
        
        # Clear all button
        ttk.Button(
            main_frame, 
            text="Clear All", 
            command=self.clear_all
        ).grid(row=7, column=1, pady=5, sticky=tk.W)
        
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
        
        if not title or not author:
            messagebox.showwarning("Input Error", "Please enter both title and author")
            return
        
        # Check for duplicates
        book_info = (title, author, year)
        if book_info in self.books_to_download:
            messagebox.showinfo("Duplicate", "This book is already in the list")
            return
        
        self.books_to_download.append(book_info)
        
        # Display in listbox
        display_text = f"{title} by {author}"
        if year:
            display_text += f" ({year})"
        self.book_listbox.insert(tk.END, display_text)
        
        # Clear input fields
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
        
        # Ask user where to save the ZIP
        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            initialfile="annas_archive_books.zip"
        )
        
        if not zip_path:
            return
        
        # Disable button during processing
        self.download_btn.config(state='disabled')
        
        # Create temporary directory for downloads
        temp_dir = Path("temp_downloads")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            self.progress['maximum'] = len(self.books_to_download)
            self.progress['value'] = 0
            
            downloaded_files = []
            failed_books = []
            
            # Download each book
            for i, (title, author, year) in enumerate(self.books_to_download):
                self.status_label.config(text=f"Processing ({i+1}/{len(self.books_to_download)}): {title}")
                self.root.update()
                
                # Search for book
                md5_hashes = search_for_book(title, author, year)
                
                if not md5_hashes:
                    failed_books.append(f"{title} by {author} - Not found")
                    self.progress['value'] = i + 1
                    self.root.update()
                    continue
                
                # Download book
                book_data = download_book(md5_hashes)
                
                if book_data:
                    # Save to temp file
                    safe_filename = f"{title[:50]}_by_{author[:30]}".replace('/', '_').replace('\\', '_')
                    file_path = temp_dir / f"{safe_filename}.epub"
                    
                    with open(file_path, 'wb') as f:
                        f.write(book_data)
                    
                    downloaded_files.append(file_path)
                else:
                    failed_books.append(f"{title} by {author} - Download failed")
                
                self.progress['value'] = i + 1
                self.root.update()
            
            # Create ZIP file
            if downloaded_files:
                self.status_label.config(text="Creating ZIP file...")
                self.root.update()
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in downloaded_files:
                        zipf.write(file_path, file_path.name)
                
                # Cleanup temp files
                for file_path in downloaded_files:
                    file_path.unlink()
                temp_dir.rmdir()
                
                success_msg = f"Successfully downloaded {len(downloaded_files)} books to:\n{zip_path}"
                
                if failed_books:
                    success_msg += f"\n\nFailed to download {len(failed_books)} books:\n" + "\n".join(failed_books[:5])
                    if len(failed_books) > 5:
                        success_msg += f"\n... and {len(failed_books) - 5} more"
                
                self.status_label.config(text=f"Complete! Downloaded {len(downloaded_files)} books.")
                messagebox.showinfo("Download Complete", success_msg)
            else:
                self.status_label.config(text="No books were downloaded.")
                messagebox.showerror("Download Failed", "None of the books could be found or downloaded:\n\n" + "\n".join(failed_books[:10]))
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_label.config(text="Error occurred")
        finally:
            # Re-enable button
            self.download_btn.config(state='normal')
            # Clean up temp directory if it still exists
            if temp_dir.exists():
                for file in temp_dir.glob('*'):
                    file.unlink()
                temp_dir.rmdir()

def main():
    root = tk.Tk()
    app = EbookPackager(root)
    root.mainloop()

if __name__ == "__main__":
    main()