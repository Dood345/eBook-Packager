// src/services/apiService.ts

import { invoke } from "@tauri-apps/api/core";

export interface BookInput {
  title: string;
  author: string;
  year: string;
}

export interface BookResult {
  title: string;
  author: string;
  year: string;
  status: string;
  download_url?: string;
  error_message?: string;
}

export interface ProcessingResult {
  results: BookResult[];
  zip_path?: string;
  summary: string;
}

export const processBooks = async (books: BookInput[]): Promise<ProcessingResult> => {
  try {
    const result = await invoke<ProcessingResult>("process_books", {
      books,
    });
    return result;
  } catch (error) {
    console.error("Failed to process books:", error);
    throw new Error(error as string);
  }
};