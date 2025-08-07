# eBook-Packager
# 📚 Ebook Packager

  <!-- Optional: Create a cool GIF of your app and upload it to imgur or directly to GitHub -->

**Ebook Packager** is a sleek, efficient desktop application designed to simplify the process of finding and packaging your favorite books. Built with a powerful Rust backend and a modern React frontend using the Tauri framework, it provides a seamless and secure experience for creating your own ebook collections.

Simply provide a list of books with their titles, authors, and publication years, and the app will automatically search for available EPUB versions, download them, and bundle them into a single, convenient ZIP archive.

---

## ✨ Features

*   **Bulk Processing:** Add multiple books at once by simply pasting a list.
*   **Intelligent Search:** Automatically finds the most relevant EPUB version of your books from Anna's Archive.
*   **Secure API Handling:** All API requests are handled by the Rust backend, keeping your API keys safe and off the client side.
*   **Direct Download & Zipping:** Downloads are processed efficiently on the backend, bypassing browser limitations and CORS issues.
*   **Native "Save As" Dialog:** Save your final ZIP archive anywhere on your computer with a native file dialog.
*   **Lightweight & Performant:** Built with Tauri for a small bundle size and minimal resource usage.

---

## 🛠️ Built With

*   [**Tauri**](https://tauri.app/) - The framework for building lightweight, fast, and secure desktop applications with web technologies.
*   [**React**](https://react.dev/) - The web framework for building the user interface.
*   [**TypeScript**](https://www.typescriptlang.org/) - For robust and type-safe code.
*   [**Rust**](https://www.rust-lang.org/) - For the high-performance and secure backend logic.
*   [**Vite**](https://vitejs.dev/) - For a blazing fast frontend development experience.
*   [**Tailwind CSS**](https://tailwindcss.com/) - For styling the user interface. <!-- Update this if you used a different CSS framework -->

---

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

You will need to have Node.js and the Rust toolchain installed on your system. Follow the official Tauri setup guide for detailed instructions for your operating system.

*   [**Setup Tauri Prerequisites**](https://tauri.app/v1/guides/getting-started/prerequisites)

### Development

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/ebook-packager.git
    cd ebook-packager
    ```

2.  **Install NPM packages:**
    ```sh
    npm install
    ```

3.  **Create your own environment file for the API key:**
    *   Create a new file at `src-tauri/.env`
    *   Add your RapidAPI key for the Anna's Archive API:
        ```env
        API_KEY="your_actual_api_key_here"
        ```

4.  **Run the application in development mode:**
    ```sh
    npm run tauri dev
    ```
    This will open the application in a development window with hot-reloading enabled for both the frontend and backend.

### Building for Production

To build the final, distributable application (`.exe` or `.msi` on Windows), run the following command:

```sh
npm run tauri build
```

The installer will be located in the `src-tauri/target/release/bundle/` directory.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgements

*   A big thanks to the Tauri team and community for creating such an incredible framework.
*   Hat tip to the operators of Anna's Archive for providing a valuable resource for knowledge.
