import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

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

    def download_pdf(self, url, filename, subdir=None):
        """Download PDF from URL"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            if subdir:
                # Create subdirectory if it doesn't exist
                subdir_path = os.path.join(self.download_dir, subdir)
                if not os.path.exists(subdir_path):
                    os.makedirs(subdir_path)
                filepath = os.path.join(self.download_dir, subdir, filename)
            else:
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

    def links_finder(self, start_url, substring, output_file="found_links.json", max_depth=1):
        """
        Find all links in the webpage and all subpages that contain a specific substring
        and export them to a JSON file
        
        Args:
            start_url (str): The starting URL to search
            substring (str): The substring to search for in URLs
            output_file (str): The output JSON file name
            max_depth (int): Maximum depth for crawling subpages (default 1)
        """
        found_links = []
        visited_urls = set()
        
        def crawl(url, depth=0):
            if depth > max_depth or url in visited_urls:
                return
            
            visited_urls.add(url)
            print(f"Crawling: {url} (depth: {depth})")
            
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Parse the current page
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                links = soup.find_all('a', href=True)
                
                # Get base domain to filter external links
                base_domain = urlparse(start_url).netloc
                
                for link in links:
                    href = link['href']
                    full_url = urljoin(url, href)
                    link_text = link.get_text(strip=True)
                    
                    # Check if link contains the substring
                    if substring.lower() in full_url.lower():
                        link_data = {
                            "url": full_url,
                            "text": link_text,
                            "found_on": url
                        }
                        if link_data not in found_links:
                            found_links.append(link_data)
                            print(f"Found matching link: {full_url}")
                    
                    # Crawl subpages only if they're on the same domain
                    if depth < max_depth and urlparse(full_url).netloc == base_domain:
                        # Skip anchors, javascript links, etc.
                        if (full_url.startswith('http') and 
                            full_url not in visited_urls and 
                            not full_url.endswith(('.pdf', '.jpg', '.png', '.gif'))):
                            crawl(full_url, depth + 1)
            
            except Exception as e:
                print(f"Error crawling {url}: {str(e)}")
        
        # Start crawling from the initial URL
        crawl(start_url)
        
        # Export results to JSON
        with open(os.path.join(self.download_dir, output_file), 'w', encoding='utf-8') as f:
            json.dump({"found_links": found_links, "search_term": substring}, f, indent=4)
        
        print(f"Found {len(found_links)} links containing '{substring}'")
        print(f"Results saved to {os.path.join(self.download_dir, output_file)}")
        
        return found_links
    
    def download_pdfs_from_found_links_json(self, json_file_path):
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            for link in data['found_links']:
                filename, year = self.process_pdf_naming_hmmt(link['url'])
                self.download_pdf(link['url'], filename, year)

    def process_pdf_naming_hmmt(self, url_link):
        """Process PDF naming for HMMT"""
        naming_base = url_link.split("https://hmmt-archive.s3.amazonaws.com/tournaments/")[1]
        file_format = naming_base.split(".")[-1]
        naming_base = naming_base.split(".")[0]
        year = naming_base.split("/")[0]
        naming_base = naming_base.replace("/", "_")
        naming_base = naming_base.replace("-", "_")
        naming_base = naming_base.replace(" ", "_")
        naming_base = naming_base.replace("__", "_")
        return naming_base + "." + file_format, year

def main():
    # Example list of URLs containing PDF links
    urls = [
        # Add your URLs here
        # Example: "https://example.com/page-with-pdfs"
        # "https://www.isinj.com/mt-usamo/"
    ]

    downloader = PDFDownloader()
    try:
        # Option 1: Download PDFs from specified URLs
        downloader.process_urls(urls)
        
        # Option 2: Find links containing a specific substring
        # Uncomment the line below to use the links_finder feature
        # downloader.links_finder("https://www.hmmt.org/www/archive/problems", "https://hmmt-archive.s3.amazonaws.com/tournaments/", max_depth=3)

        # Option 3: Download PDFs from found links
        downloader.download_pdfs_from_found_links_json("downloads/found_links.json")
    finally:
        downloader.close()

if __name__ == "__main__":
    main() 