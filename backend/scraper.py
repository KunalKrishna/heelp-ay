import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urlparse
import ipaddress
import socket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum number of redirects to follow (SSRF protection)
MAX_REDIRECTS = 3

# Blocked private/internal IP ranges for SSRF protection
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]


def is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private/internal IP address"""
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip_obj in blocked_range:
                return True
        return False
    except (socket.gaierror, ValueError):
        # If we can't resolve or parse, block it to be safe
        return True


def is_valid_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks"""
    try:
        parsed = urlparse(url)
        # Only allow http and https schemes
        if parsed.scheme not in ('http', 'https'):
            return False
        # Ensure hostname is present
        if not parsed.hostname:
            return False
        # Block private/internal IPs
        if is_private_ip(parsed.hostname):
            logger.warning(f"Blocked private/internal IP: {parsed.hostname}")
            return False
        return True
    except Exception:
        return False


def read_urls_from_file(file_path: str) -> List[str]:
    """Read URLs from a text file, one URL per line"""
    urls = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):  # Skip empty lines and comments
                    urls.append(url)
        logger.info(f"Read {len(urls)} URLs from {file_path}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
    return urls


def scrape_url(url: str) -> Optional[Dict[str, str]]:
    """Scrape text content from a single URL"""
    # Validate URL for security
    if not is_valid_url(url):
        logger.error(f"Invalid URL: {url}")
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Use Session to control redirects for SSRF protection
        session = requests.Session()
        session.max_redirects = MAX_REDIRECTS
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get title
        title = soup.title.string if soup.title else ""
        
        # Get main content
        # Try to find main content area first
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            # Get text and clean it up
            text = main_content.get_text(separator=' ', strip=True)
            # Remove excessive whitespace
            text = ' '.join(text.split())
        else:
            text = ""
        
        if text:
            logger.info(f"Successfully scraped: {url} ({len(text)} characters)")
            return {
                "url": url,
                "title": title.strip() if title else "",
                "content": text
            }
        else:
            logger.warning(f"No content found at: {url}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        return None


def scrape_urls(urls: List[str]) -> List[Dict[str, str]]:
    """Scrape multiple URLs and return their content"""
    results = []
    for url in urls:
        result = scrape_url(url)
        if result:
            results.append(result)
    logger.info(f"Successfully scraped {len(results)} out of {len(urls)} URLs")
    return results
