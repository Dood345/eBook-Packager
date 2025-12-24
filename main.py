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
        self.listbox.bind('<Double-Button-1>', lambda e: self.on_select())
        
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
        self.root.geometry("1000x700")
        
        # Store book info: [{title, author, md5, size, extension, all_md5s, get_audiobook}, ...]
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
            wraplength=900,
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
        
        # Book list Header
        ttk.Label(main_frame, text="Books to Download (Click 'Audiobook?' to toggle):").grid(
            row=5, column=0, columnspan=3, sticky=tk.W, pady=5
        )
        
        # Treeview (Spreadsheet)
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        columns = ('title', 'author', 'info', 'audiobook')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('title', text='Title')
        self.tree.heading('author', text='Author')
        self.tree.heading('info', text='Ebook Info')
        self.tree.heading('audiobook', text='Get Audiobook?')
        
        self.tree.column('title', width=300)
        self.tree.column('author', width=200)
        self.tree.column('info', width=250)
        self.tree.column('audiobook', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click for checkbox toggle
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Bind keys
        self.title_entry.bind('<Return>', lambda e: self.add_book())
        self.author_entry.bind('<Return>', lambda e: self.add_book())
        self.year_entry.bind('<Return>', lambda e: self.add_book())
        
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
        
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == '#4': # The 'audiobook' column (1-based index in generic identification, but usually #1,#2...)
                # Let's double check column index. headings are not counted.
                # Columns are #1, #2, #3, #4 corresponding to title, author, info, audiobook
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    # Toggle value
                    current_idx = int(item_id)
                    book = self.books_to_download[current_idx]
                    book['get_audiobook'] = not book.get('get_audiobook', False)
                    
                    # Update display
                    symbol = "☑" if book['get_audiobook'] else "☐"
                    self.tree.set(item_id, 'audiobook', symbol)

    def add_book(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        year = self.year_entry.get().strip()
        
        if not title:
            messagebox.showwarning("Input Error", "Please enter at least a title")
            return
            
        self.status_label.config(text="Searching...")
        self.root.update()
        # Disable add button temporarily? No reference to it, skipping.
        
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

        # Prepare entry
        entry = primary_match.copy()
        entry['primary_md5'] = primary_match['md5']
        entry['all_md5s'] = [b['md5'] for b in best_matches]
        entry['get_audiobook'] = False # Default
        
        self.books_to_download.append(entry)
        index = len(self.books_to_download) - 1
        
        # Display
        size_str = primary_match.get('size', 'Unknown size')
        ext = primary_match.get('ext', 'unknown')
        match_count = len(best_matches)
        
        info_text = f"{ext.upper()}, {size_str} ({match_count} sources)"
        display_title = primary_match['title']
        display_author = primary_match['author']
        
        # Insert into tree using 'iid' as the index in our list for easy lookup
        self.tree.insert('', tk.END, iid=str(index), values=(display_title, display_author, info_text, "☐"))
        
        # Reset input
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.status_label.config(text=f"Added: {display_title}")

    def remove_book(self):
        selection = self.tree.selection()
        if selection:
            # We need to handle removal carefully to keep indices in sync or use IDs
            # Easiest way with the list mapping is to clear and rebuild, 
            # OR just remove from list and tree.
            # Since we used index as IID, removing one messes up the sync for subsequent items if we just use index.
            # Better approach: Get all items, filter out removed, rebuild list, reload tree.
            
            indexes_to_remove = sorted([int(x) for x in selection], reverse=True)
            
            for index in indexes_to_remove:
                del self.books_to_download[index]
            
            # Refresh Tree
            self.tree.delete(*self.tree.get_children())
            for i, book in enumerate(self.books_to_download):
                primary_match = book
                size_str = primary_match.get('size', 'Unknown size')
                ext = primary_match.get('ext', 'epub') # fallback
                match_count = len(book.get('all_md5s', []))
                info_text = f"{ext.upper()}, {size_str} ({match_count} sources)"
                audio_symbol = "☑" if book['get_audiobook'] else "☐"
                
                self.tree.insert('', tk.END, iid=str(i), values=(book['title'], book['author'], info_text, audio_symbol))
                
            self.status_label.config(text="Book(s) removed")
    
    def clear_all(self):
        if self.books_to_download:
            if messagebox.askyesno("Clear All", "Remove all books from the list?"):
                self.tree.delete(*self.tree.get_children())
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
            # Count logical operations (ebooks + audiobooks)
            total_ops = 0
            for b in self.books_to_download:
                total_ops += 1
                if b.get('get_audiobook'):
                    total_ops += 1
            
            self.progress['maximum'] = total_ops
            current_op = 0
            
            # Helper to create safe folder names
            def safe_name(text):
                return "".join([c for c in text if c.isalpha() or c.isdigit() or c==' ']).strip()

            downloaded_files = [] # List of tuples: (local_path, arcname)
            failed_books = []
            
            for i, book in enumerate(self.books_to_download):
                title = book.get('title', 'Unknown')
                author = book.get('author', 'Unknown')
                
                clean_title = safe_name(title)
                clean_author = safe_name(author)
                
                # --- EBOOK DOWNLOAD ---
                current_op += 1
                self.progress['value'] = current_op
                self.status_label.config(text=f"Downloading Ebook: {title}")
                self.root.update()
                
                md5_list = book.get('all_md5s', [book.get('md5')])
                ext = book.get('ext', 'epub')
                
                content = download_book(md5_list)
                
                if content:
                    safe_filename = f"{clean_title}".replace(' ', '_')
                    file_path = temp_dir / f"{safe_filename}.{ext}"
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    # Structure: Author/Title/File.ext
                    arcname = f"{clean_author}/{clean_title}/{safe_filename}.{ext}"
                    downloaded_files.append((file_path, arcname))
                else:
                    failed_books.append(f"{title} (Ebook) - Download failed")
                
                # --- AUDIOBOOK DOWNLOAD (If successfully toggled) ---
                if book.get('get_audiobook'):
                    current_op += 1
                    self.progress['value'] = current_op
                    self.status_label.config(text=f"Searching Audiobook: {title}")
                    self.root.update()
                    
                    # 1. Search for audiobook
                    ab_books = search_for_book(query=title, author=author, limit=10, file_type='audiobook')
                    if ab_books:
                        # 2. Get largest sorted files
                        filtered_ab = filter_by_author(ab_books, author)
                        if not filtered_ab: filtered_ab = ab_books
                        
                        best_ab_matches = get_largest_files(filtered_ab, n=3)
                        if best_ab_matches:
                             # 3. Download
                             ab_md5s = [b['md5'] for b in best_ab_matches]
                             self.status_label.config(text=f"Downloading Audiobook: {title}")
                             self.root.update()
                             
                             ab_content = download_book(ab_md5s)
                             if ab_content:
                                 ab_ext = best_ab_matches[0].get('ext', 'mp3')
                                 safe_filename_ab = f"{clean_title}_AUDIOBOOK".replace(' ', '_')
                                 file_path_ab = temp_dir / f"{safe_filename_ab}.{ab_ext}"
                                 with open(file_path_ab, 'wb') as f:
                                     f.write(ab_content)
                                 
                                 # Structure: Author/Title/File.ext
                                 arcname_ab = f"{clean_author}/{clean_title}/{safe_filename_ab}.{ab_ext}"
                                 downloaded_files.append((file_path_ab, arcname_ab))
                             else:
                                 failed_books.append(f"{title} (Audiobook) - Download failed")
                        else:
                            failed_books.append(f"{title} (Audiobook) - No good files found")
                    else:
                        failed_books.append(f"{title} (Audiobook) - Not found")

            # Create ZIP
            if downloaded_files:
                self.status_label.config(text="Creating ZIP file...")
                self.root.update()
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path, arcname in downloaded_files:
                        zipf.write(file_path, arcname)
                
                # Cleanup
                for file_path, _ in downloaded_files:
                    try: file_path.unlink()
                    except: pass
                try: temp_dir.rmdir()
                except: pass
                
                msg = f"Downloaded {len(downloaded_files)} files to:\n{zip_path}"
                if failed_books:
                    msg += f"\n\nFailed items:\n" + "\n".join(failed_books[:5])
                    
                messagebox.showinfo("Complete", msg)
                self.status_label.config(text="Download Complete")
            else:
                self.status_label.config(text="Failed")
                messagebox.showerror("Failed", "No files downloaded.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            self.download_btn.config(state='normal')
            if temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir) 
                except: pass

def main():
    root = tk.Tk()
    app = EbookPackager(root)
    root.mainloop()

if __name__ == "__main__":
    main()