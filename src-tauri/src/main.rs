// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use dotenvy::dotenv;
use futures::future::join_all;
use reqwest::header::{HeaderMap, HeaderValue};
use serde::{Deserialize, Serialize};
use std::env;
use std::fs::File;
use std::io::Write;
use tauri::AppHandle;
use tauri_plugin_dialog::DialogExt;
use zip::write::{FileOptions, ZipWriter};

#[derive(Deserialize, Debug)]
struct BookInput {
    title: String,
    author: String,
    year: String,
}

#[derive(Serialize, Debug)]
struct BookResult {
    title: String,
    author: String,
    year: String,
    status: String,
    download_url: Option<String>,
}

#[derive(Deserialize, Debug)]
struct ApiBook {
    title: String,
    author: String,
    md5: String,
    year: String,
}

#[derive(Deserialize, Debug)]
struct ApiResponse {
    books: Vec<ApiBook>,
}

async fn search_for_book(api_key: &str, api_host: &str, book: BookInput) -> BookResult {
    let query = format!("{} {} {}", book.title, book.author, book.year);
    let client = reqwest::Client::new();
    let mut headers = HeaderMap::new();
    
    // Better error handling for header creation
    let api_key_header = match HeaderValue::from_str(api_key) {
        Ok(header) => header,
        Err(_) => return BookResult { 
            title: book.title, 
            author: book.author, 
            year: book.year, 
            status: "Invalid API Key".to_string(), 
            download_url: None 
        },
    };
    
    let api_host_header = match HeaderValue::from_str(api_host) {
        Ok(header) => header,
        Err(_) => return BookResult { 
            title: book.title, 
            author: book.author, 
            year: book.year, 
            status: "Invalid API Host".to_string(), 
            download_url: None 
        },
    };

    headers.insert("x-rapidapi-key", api_key_header);
    headers.insert("x-rapidapi-host", api_host_header);

    let response = match client
        .get(format!("https://{}/search", api_host))
        .headers(headers)
        .query(&[
            ("q", query.as_str()), 
            ("ext", "epub"), 
            ("sort", "mostRelevant"), 
            ("lang", "en"), 
            ("limit", "10")
        ])
        .send()
        .await 
    {
        Ok(res) => res,
        Err(e) => {
            eprintln!("Search request failed: {}", e);
            return BookResult { 
                title: book.title, 
                author: book.author, 
                year: book.year, 
                status: "Search Error".to_string(), 
                download_url: None 
            };
        }
    };

    if !response.status().is_success() {
        eprintln!("Search failed with status: {}", response.status());
        return BookResult { 
            title: book.title, 
            author: book.author, 
            year: book.year, 
            status: format!("Search Failed: {}", response.status()), 
            download_url: None 
        };
    }

    let data = match response.json::<ApiResponse>().await {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Failed to parse JSON response: {}", e);
            return BookResult { 
                title: book.title, 
                author: book.author, 
                year: book.year, 
                status: "Parse Error".to_string(), 
                download_url: None 
            };
        }
    };

    // Look for exact matches first (title, author, and year), then partial matches
    let found_book = data.books.iter()
        .find(|b| {
            b.author.to_lowercase().contains(&book.author.to_lowercase()) &&
            b.title.to_lowercase().contains(&book.title.to_lowercase()) &&
            b.year == book.year
        })
        .or_else(|| {
            // If no exact year match, try without year but with title and author
            data.books.iter().find(|b| {
                b.author.to_lowercase().contains(&book.author.to_lowercase()) &&
                b.title.to_lowercase().contains(&book.title.to_lowercase())
            })
        })
        .or_else(|| {
            // Finally, try just author match
            data.books.iter().find(|b| 
                b.author.to_lowercase().contains(&book.author.to_lowercase())
            )
        });

    if let Some(found_book) = found_book {
        BookResult { 
            title: book.title, 
            author: book.author, 
            year: book.year, 
            status: "Found".to_string(), 
            download_url: Some(format!("https://{}/download?md5={}", api_host, found_book.md5)) 
        }
    } else {
        BookResult { 
            title: book.title, 
            author: book.author, 
            year: book.year, 
            status: "Not Found".to_string(), 
            download_url: None 
        }
    }
}

async fn download_book_data(api_key: &str, api_host: &str, url: &str) -> Result<Vec<u8>, String> {
    let client = reqwest::Client::new();
    let mut headers = HeaderMap::new();
    
    let api_key_header = HeaderValue::from_str(api_key)
        .map_err(|e| format!("Invalid API key header: {}", e))?;
    let api_host_header = HeaderValue::from_str(api_host)
        .map_err(|e| format!("Invalid API host header: {}", e))?;
    
    headers.insert("x-rapidapi-key", api_key_header);
    headers.insert("x-rapidapi-host", api_host_header);
    
    let link_response = client
        .get(url)
        .headers(headers)
        .send()
        .await
        .map_err(|e| format!("Failed to get download link: {}", e))?;
    
    if !link_response.status().is_success() {
        return Err(format!("Download link request failed: {}", link_response.status()));
    }
    
    let final_urls: Vec<String> = link_response
        .json()
        .await
        .map_err(|e| format!("Failed to parse download links: {}", e))?;
    
    if final_urls.is_empty() { 
        return Err("API did not return any final download URLs.".to_string()); 
    }
    
    let file_response = client
        .get(&final_urls[0])
        .send()
        .await
        .map_err(|e| format!("Failed to download file: {}", e))?;
    
    if !file_response.status().is_success() { 
        return Err(format!("Failed to download file from final URL: {}", file_response.status())); 
    }
    
    let file_bytes = file_response
        .bytes()
        .await
        .map_err(|e| format!("Failed to read file bytes: {}", e))?
        .to_vec();
    
    Ok(file_bytes)
}

// Helper function to sanitize filename
fn sanitize_filename(input: &str) -> String {
    input
        .chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' => '-',
            c if c.is_control() => '-',
            c => c,
        })
        .collect::<String>()
        .trim()
        .to_string()
}

#[tauri::command]
async fn process_books(app: AppHandle, books: Vec<BookInput>) -> Result<String, String> {
    dotenv().ok();
    
    let api_key = env::var("API_KEY")
        .map_err(|_| "API_KEY environment variable not found. Please set it in your .env file.".to_string())?;
    
    if api_key.is_empty() {
        return Err("API_KEY is empty. Please provide a valid API key.".to_string());
    }
    
    let api_host = "annas-archive-api.p.rapidapi.com";

    if books.is_empty() {
        return Err("No books provided for processing.".to_string());
    }

    println!("Processing {} books...", books.len());

    // Search for all books concurrently
    let search_futures = books.into_iter().map(|book| {
        let api_key_clone = api_key.clone();
        let api_host_clone = api_host.to_string();
        async move {
            search_for_book(&api_key_clone, &api_host_clone, book).await
        }
    });

    let search_results = join_all(search_futures).await;

    // Filter books that were found
    let books_to_download: Vec<_> = search_results
        .iter()
        .filter_map(|res| {
            if res.status == "Found" {
                res.download_url.as_ref().map(|url| (res, url.clone()))
            } else {
                None
            }
        })
        .collect();

    println!("Found {} books to download", books_to_download.len());

    if books_to_download.is_empty() {
        // Still show results for books that weren't found
        let mut status_summary = String::new();
        for result in search_results {
            status_summary.push_str(&format!(
                "• {} by {} ({}): {}\n", 
                result.title, result.author, result.year, result.status
            ));
        }
        return Ok(format!("No books found to download.\n\nSearch Results:\n{}", status_summary));
    }

    // Ask user where to save the zip file
    let file_path = app
        .dialog()
        .file()
        .add_filter("Zip Archive", &["zip"])
        .set_title("Save Ebook Package")
        .set_file_name("ebook-package.zip")
        .blocking_save_file();

    if let Some(file_path) = file_path {
        let path_buf = match file_path.as_path() {
            Some(path) => path.to_path_buf(),
            None => return Err("Invalid file path selected".to_string()),
        };
        let file = File::create(&path_buf)
            .map_err(|e| format!("Failed to create zip file: {}", e))?;
        
        let mut zip = ZipWriter::new(file);
        let options = FileOptions::<()>::default()
            .compression_method(zip::CompressionMethod::Deflated);

        // Download all books concurrently
        let download_futures = books_to_download.into_iter().map(|(book_meta, url)| {
            let api_key_clone = api_key.clone();
            let api_host_clone = api_host.to_string();
            async move {
                println!("Downloading: {} by {}", book_meta.title, book_meta.author);
                let data = download_book_data(&api_key_clone, &api_host_clone, &url).await;
                (book_meta, data)
            }
        });

        let download_results = join_all(download_futures).await;

        let mut successful_downloads = 0;
        let mut failed_downloads = 0;

        for (book_meta, data_result) in download_results {
            match data_result {
                Ok(data) => {
                    // Format: author_lastname - year - title.epub
                    let sanitized_author = sanitize_filename(&book_meta.author);
                    let sanitized_title = sanitize_filename(&book_meta.title);
                    let sanitized_year = sanitize_filename(&book_meta.year);
                    
                    let file_name = format!("{} - {} - {}.epub", 
                        sanitized_author, sanitized_year, sanitized_title);
                    
                    match zip.start_file(file_name, options) {
                        Ok(_) => {
                            match zip.write_all(&data) {
                                Ok(_) => {
                                    successful_downloads += 1;
                                    println!("✓ Added to zip: {}", book_meta.title);
                                }
                                Err(e) => {
                                    failed_downloads += 1;
                                    eprintln!("✗ Failed to write {} to zip: {}", book_meta.title, e);
                                }
                            }
                        }
                        Err(e) => {
                            failed_downloads += 1;
                            eprintln!("✗ Failed to create zip entry for {}: {}", book_meta.title, e);
                        }
                    }
                }
                Err(e) => {
                    failed_downloads += 1;
                    eprintln!("✗ Failed to download book \"{}\": {}", book_meta.title, e);
                }
            }
        }

        zip.finish().map_err(|e| format!("Failed to finalize zip file: {}", e))?;
        
        let summary = if failed_downloads > 0 {
            format!(
                "Package saved to {:?}\n\n✓ {} books downloaded successfully\n✗ {} books failed to download", 
                path_buf, successful_downloads, failed_downloads
            )
        } else {
            format!(
                "✓ Successfully saved {} books to {:?}", 
                successful_downloads, path_buf
            )
        };
        
        Ok(summary)
    } else {
        Ok("Save operation was cancelled.".to_string())
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![process_books])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}