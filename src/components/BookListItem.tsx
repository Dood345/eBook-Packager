import React from 'react';
import { Book, BookStatus } from '../types.ts';
import { Spinner } from './Spinner.tsx';
import { CheckCircleIcon, XCircleIcon, ClockIcon, DocumentQuestionIcon, TrashIcon } from './icons.tsx';

interface BookListItemProps {
  book: Book;
  onRemove: (id: string) => void;
}

const StatusIndicator: React.FC<{ status: BookStatus }> = ({ status }) => {
  switch (status) {
    case BookStatus.Pending:
      return <div className="flex items-center text-gray-400"><ClockIcon className="h-5 w-5 mr-2" /> Pending</div>;
    case BookStatus.Searching:
      return <div className="flex items-center text-blue-400"><Spinner /> Searching...</div>;
    case BookStatus.Found:
      return <div className="flex items-center text-green-400"><CheckCircleIcon className="h-5 w-5 mr-2" /> Found</div>;
    case BookStatus.NotFound:
      return <div className="flex items-center text-yellow-400"><DocumentQuestionIcon className="h-5 w-5 mr-2" /> Not Found</div>;
    case BookStatus.Error:
      return <div className="flex items-center text-red-400"><XCircleIcon className="h-5 w-5 mr-2" /> Error</div>;
    default:
      return null;
  }
};

export const BookListItem: React.FC<BookListItemProps> = ({ book, onRemove }) => {
  return (
    <div className="bg-gray-700/50 p-4 rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all duration-300">
      <div className="flex-grow">
        <p className="font-bold text-lg text-white">{book.title}</p>
        <p className="text-sm text-gray-400">{book.author} ({book.year || 'N/A'})</p>
         {book.status === BookStatus.Error && book.errorMessage && (
            <p className="text-xs text-red-300 mt-1">{book.errorMessage}</p>
         )}
      </div>
      <div className="flex items-center space-x-4 w-full sm:w-auto">
        <div className="w-40">
          <StatusIndicator status={book.status} />
        </div>
        <button
          onClick={() => onRemove(book.id)}
          className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-600 rounded-full transition-colors"
          aria-label="Remove book"
        >
          <TrashIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};