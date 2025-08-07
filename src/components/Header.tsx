
import React from 'react';
import { BookIcon } from './icons.tsx';

export const Header: React.FC = () => {
  return (
    <header className="bg-gray-900/70 backdrop-blur-sm shadow-lg sticky top-0 z-10 py-5">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="flex items-center justify-center space-x-4">
            <BookIcon className="h-10 w-10 text-primary-400" />
            <h1 className="text-4xl font-bold text-white tracking-tight">
                Ebook Packager
            </h1>
        </div>
        <p className="text-center text-gray-400 mt-2">Find and zip your favorite e-books.</p>
      </div>
    </header>
  );
};