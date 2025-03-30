# PDF Link Clicker and Downloader

This Python program automatically visits a list of URLs, finds PDF links on those pages, and downloads the PDFs.

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- pip (Python package installer)

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Open `main.py` and add your list of URLs to the `urls` list in the `main()` function:
```python
urls = [
    "https://example.com/page-with-pdfs",
    "https://another-example.com/more-pdfs"
]
```

2. Run the program:
```bash
python main.py
```

The program will:
- Create a `downloads` directory if it doesn't exist
- Visit each URL in the list
- Find all PDF links on each page
- Download the PDFs to the `downloads` directory
- Print progress and any errors that occur

## Features

- Automatically handles relative and absolute URLs
- Downloads PDFs in chunks to handle large files
- Runs Chrome in headless mode (no visible browser window)
- Creates unique filenames for PDFs without names
- Handles errors gracefully
- Shows download progress

## Notes

- Make sure you have permission to download the PDFs
- Some websites may block automated downloads
- The program runs Chrome in headless mode for better performance 