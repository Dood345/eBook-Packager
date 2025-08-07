// src/App.tsx

import React, { useState } from 'react';
import { Book, BookStatus } from './types.ts';
import { Header } from './components/Header.tsx';
import { BookInputForm } from './components/BookInputForm.tsx';
import { BookList } from './components/BookList.tsx';
import { processBooks, type BookInput } from './services/apiService.ts';
import { Spinner } from './components/Spinner.tsx';

const App: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('Download All as ZIP');
  const [globalError, setGlobalError] = useState<string | null>(null);

  const addBooks = (newBookEntries: Omit<Book, 'id' | 'status'>[]) => {
    const newBooks = newBookEntries.map(entry => ({
      ...entry,
      id: crypto.randomUUID(),
      status: BookStatus.Pending,
    }));
    const uniqueNewBooks = newBooks.filter(newBook => 
      !books.some(existingBook => 
        existingBook.title.trim().toLowerCase() === newBook.title.trim().toLowerCase() &&
        existingBook.author.trim().toLowerCase() === newBook.author.trim().toLowerCase() &&
        existingBook.year.trim() === newBook.year.trim()
      )
    );
    setBooks(prevBooks => [...prevBooks, ...uniqueNewBooks]);
  };

  const removeBook = (id: string) => {
    setBooks(prevBooks => prevBooks.filter(book => book.id !== id));
  };

  const handleProcessBooks = async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    setGlobalError(null);
    setProcessingMessage('Processing...');

    const booksToProcess: BookInput[] = books.map(b => ({ 
      title: b.title, 
      author: b.author, 
      year: b.year 
    }));

    try {
      const result = await processBooks(booksToProcess);
      
      // Update book statuses in the UI
      setBooks(prevBooks => 
        prevBooks.map(book => {
          const matchingResult = result.results.find(r => 
            r.title === book.title && 
            r.author === book.author && 
            r.year === book.year
          );
          
          if (matchingResult) {
            return {
              ...book,
              status: matchingResult.status as BookStatus,
              // You might want to store error message in your Book type too
            };
          }
          return book;
        })
      );

      // Show summary message
      alert(result.summary);
      
    } catch (error: any) {
      console.error('An error occurred:', error);
      setGlobalError(error.message || 'An unknown error occurred.');
    } finally {
      setIsProcessing(false);
      setProcessingMessage('Download All as ZIP');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-gray-800 shadow-2xl rounded-lg p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4 text-primary-400">Add Books to Your Package</h2>
            <p className="mb-6 text-gray-400">
                Enter your book list below. The application will search for EPUB versions and prepare them for packaging.
            </p>
            <BookInputForm onAddBooks={addBooks} disabled={isProcessing} />
        </div>

        <div className="bg-gray-800 shadow-2xl rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4 text-primary-400">Your Book List</h2>
            {books.length > 0 ? (
                <>
                    <BookList books={books} onRemoveBook={removeBook} />
                    <div className="mt-8 text-center">
                        <button
                            onClick={handleProcessBooks}
                            disabled={isProcessing || books.length === 0}
                            className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-primary-500 transition-colors duration-200"
                        >
                            {isProcessing ? (
                                <>
                                    <Spinner />
                                    {processingMessage}
                                </>
                            ) : (
                                'Download All as ZIP'
                            )}
                        </button>
                        {globalError && <p className="mt-4 text-red-400">{globalError}</p>}
                    </div>
                </>
            ) : (
                <p className="text-gray-400 text-center py-8">Your list is empty. Add some books above to get started.</p>
            )}
        </div>
      </main>
    </div>
  );
};

export default App;