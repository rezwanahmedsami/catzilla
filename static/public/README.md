
    # Catzilla Static Files Demo

    This demo showcases Catzilla's static file serving capabilities.

    ## Features

    - **High Performance**: Zero-copy file serving when possible
    - **Compression**: Automatic gzip compression for text files
    - **Caching**: Smart caching headers for optimal performance
    - **Security**: Secure file serving with access controls
    - **Range Requests**: Support for partial content requests
    - **MIME Detection**: Automatic content type detection

    ## Directory Structure

    ```
    static/
    ├── assets/     - CSS, JS, and other assets
    ├── public/     - Public HTML files and content
    ├── media/      - Images, videos, audio files
    └── downloads/  - Downloadable files and archives
    ```

    ## API Endpoints

    - `GET /static/*` - Serve static files
    - `GET /files/info/{filename}` - Get file information
    - `GET /files/download/{filename}` - Force file download
    - `GET /browse/*` - Browse directory contents

    ## Security Features

    - Path traversal protection
    - File type validation
    - Access control headers
    - CORS support for cross-origin requests
