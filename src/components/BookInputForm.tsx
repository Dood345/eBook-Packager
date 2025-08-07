
import React, { useState } from 'react';
import { PlusIcon } from './icons.tsx';

interface BookInputFormProps {
  onAddBooks: (books: { title: string; author: string; year: string }[]) => void;
  disabled: boolean;
}

export const BookInputForm: React.FC<BookInputFormProps> = ({ onAddBooks, disabled }) => {
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const lines = inputText.split('\n').filter(line => line.trim() !== '');
    if (lines.length === 0) {
      setError('Please enter at least one book.');
      return;
    }

    const newBooks: { title: string; author: string; year: string }[] = [];
    const errors: string[] = [];

    lines.forEach((line, index) => {
      const parts = line.split(',').map(part => part.trim());
      if (parts.length < 2 || !parts[0] || !parts[1]) {
        errors.push(`Line ${index + 1} is malformed. Expected format: Title, Author, Year.`);
      } else {
        newBooks.push({
          title: parts[0],
          author: parts[1],
          year: parts[2] || '',
        });
      }
    });

    if (errors.length > 0) {
      setError(errors.join('\n'));
      return;
    }

    onAddBooks(newBooks);
    setInputText('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="book-list" className="block text-sm font-medium text-gray-300">
          Book List
        </label>
        <textarea
          id="book-list"
          rows={8}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={disabled}
          className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm disabled:opacity-50 font-mono"
          placeholder={`The Hobbit, Tolkien, 1937\nDune, Herbert, 1965\nFoundation, Asimov, 1951`}
        />
        <p className="mt-2 text-xs text-gray-400">
          Format: <span className="font-semibold">Book Title, Author Last Name, Publication Year</span>. Each entry on a new line.
        </p>
      </div>

      {error && <pre className="text-red-400 text-sm whitespace-pre-wrap p-3 bg-red-900/20 rounded-md">{error}</pre>}
      
      <div className="text-right">
        <button
          type="submit"
          disabled={disabled || !inputText.trim()}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 disabled:bg-gray-500 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-primary-500 transition-colors"
        >
          <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
          Add Books to List
        </button>
      </div>
    </form>
  );
};