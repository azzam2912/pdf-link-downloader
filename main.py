import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class PDFDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        self.setup_download_directory()
        self.setup_driver()

    def setup_download_directory(self):
        """Create download directory if it doesn't exist"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
        )
        
        # Let Selenium handle ChromeDriver
        self.driver = webdriver.Chrome(options=chrome_options)

    def download_pdf(self, url, filename):
        """Download PDF from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Successfully downloaded: {filename}")
            return True
        except Exception as e:
            print(f"Error downloading {filename}: {str(e)}")
            return False

    def process_page(self, url):
        """Process a single page and download all PDFs"""
        try:
            self.driver.get(url)
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get all links on the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                # Convert relative URLs to absolute URLs
                full_url = urljoin(url, href)
                
                # Check if the link is a PDF
                if full_url.lower().endswith('.pdf'):
                    filename = os.path.basename(full_url)
                    if not filename:
                        filename = f"document_{int(time.time())}.pdf"
                    self.download_pdf(full_url, filename)

        except Exception as e:
            print(f"Error processing page {url}: {str(e)}")

    def process_urls(self, urls):
        """Process a list of URLs"""
        for url in urls:
            print(f"\nProcessing: {url}")
            self.process_page(url)

    def close(self):
        """Close the browser"""
        self.driver.quit()

def main():
    # Example list of URLs containing PDF links
    urls = [
        # Add your URLs here
        # Example: "https://example.com/page-with-pdfs"
        "https://www.isinj.com/mt-amc8/",
        "https://www.isinj.com/mt-amc10/",
        "https://www.isinj.com/mt-amc12/"
    ]

    downloader = PDFDownloader()
    try:
        downloader.process_urls(urls)
    finally:
        downloader.close()

if __name__ == "__main__":
    main() 