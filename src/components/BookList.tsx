
import React from 'react';
import { Book } from '../types.ts';
import { BookListItem } from './BookListItem.tsx';

interface BookListProps {
  books: Book[];
  onRemoveBook: (id: string) => void;
}

export const BookList: React.FC<BookListProps> = ({ books, onRemoveBook }) => {
  return (
    <div className="space-y-4">
      {books.map((book) => (
        <BookListItem key={book.id} book={book} onRemove={onRemoveBook} />
      ))}
    </div>
  );
};