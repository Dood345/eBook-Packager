// src/types.ts

// The new statuses that match our new workflow
export enum BookStatus {
  Pending = 'Pending',
  Searching = 'Searching',
  Found = 'Found',       // Replaces 'Downloading' and 'Completed'
  NotFound = 'Not Found',
  Error = 'Error',
}

export interface Book {
  id: string;
  title: string;
  author: string;
  year: string;
  status: BookStatus;
  downloadUrl?: string; // We now store the URL instead of the data
  errorMessage?: string;
}