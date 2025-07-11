#!/usr/bin/env python3
"""
Broken Link Checker for HTML Files

This script checks all HTML files in the ../html directory for broken links and missing images.
It uses parallel processing with intelligent rate limiting and browser headers to avoid false
positives from bot-blocking websites.

Key Features:
- Parallel processing with configurable batch sizes and worker limits
- Domain-specific rate limiting to respect server resources
- Browser headers to bypass basic bot detection
- Retry logic for 405/406 errors (Method Not Allowed/Not Acceptable)
- Categorizes results: definitely broken vs. potentially browser-accessible
- Progress tracking with intermediate saves
- Comprehensive reporting with actionable results

Dependencies:
- requests: HTTP library for making web requests
- beautifulsoup4: HTML parsing library
- urllib3: Low-level HTTP client (dependency of requests)

Usage:
    python check_broken_links.py

Output:
    broken_links_report.txt - Detailed report with categorized results
"""

import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urlparse

def extract_links_from_html(file_path):
    """
    Extract all links and image sources from an HTML file.
    
    This function parses HTML content and extracts:
    - HTTP/HTTPS links from <a> tags
    - Image URLs from <img> tags  
    - Local image file references
    - Resource links from <link> tags (CSS, etc.)
    
    Args:
        file_path (str): Path to the HTML file to parse
        
    Returns:
        list: List of tuples (link_type, url) where link_type is one of:
              'link', 'image', 'local_image', 'resource'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        # Find all <a> tags with href attributes (regular hyperlinks)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('http'):
                links.append(('link', href))
        
        # Find all <img> tags with src attributes (both HTTP and relative paths)
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            if src.startswith('http'):
                # Remote image URL - check if accessible
                links.append(('image', src))
            elif not src.startswith('#') and not src.startswith('data:'):
                # Relative path - check if file exists locally
                # Skip fragments (#) and data URLs (data:image/...)
                links.append(('local_image', src))
        
        # Find all <link> tags with href attributes (CSS, favicons, etc.)
        for link_tag in soup.find_all('link', href=True):
            href = link_tag['href']
            if href.startswith('http'):
                links.append(('resource', href))
        
        return links
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

# Global rate limiting data structures
# Each domain gets its own lock to prevent race conditions in parallel processing
domain_locks = defaultdict(threading.Lock)
# Track the last request time for each domain to enforce delays
domain_last_request = defaultdict(float)

def get_domain_delay(domain):
    """
    Get appropriate delay for domain to avoid rate limiting.
    
    Different websites have different tolerance for automated requests.
    Academic sites and museums tend to be more restrictive.
    
    Args:
        domain (str): The domain name (e.g., 'jstor.org')
        
    Returns:
        float: Delay in seconds between requests to this domain
    """
    if 'doi.org' in domain or 'jstor.org' in domain:
        return 2.0  # More conservative for academic sites (often rate-limited)
    elif 'oed.com' in domain or 'britishmuseum.org' in domain:
        return 3.0  # Very conservative for restrictive sites
    else:
        return 0.5  # Default delay for most sites

def check_url_with_rate_limit(url, timeout=10):
    """
    Check if a URL is accessible with domain-specific rate limiting and browser headers.
    
    This function implements several strategies to accurately test URL accessibility:
    1. Uses realistic browser headers to avoid bot detection
    2. Implements per-domain rate limiting to be respectful
    3. Falls back from HEAD to GET requests if needed
    4. Provides detailed status information for debugging
    
    Args:
        url (str): The URL to check
        timeout (int): Request timeout in seconds (default: 10)
        
    Returns:
        tuple: (status_code, reason) where:
               - status_code: HTTP status code (int) or None if failed
               - reason: Human-readable description of the result
    """
    domain = urlparse(url).netloc
    delay = get_domain_delay(domain)
    
    # Browser headers to avoid bot detection
    # These headers mimic a real Chrome browser to bypass basic bot filtering
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }
    
    # Use domain-specific locking to prevent multiple simultaneous requests to same domain
    with domain_locks[domain]:
        # Enforce minimum delay between requests to same domain
        time_since_last = time.time() - domain_last_request[domain]
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        
        # Try HEAD request first (faster, less bandwidth)
        try:
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            domain_last_request[domain] = time.time()
            
            # Some servers reject HEAD requests but accept GET
            if response.status_code in [405, 406]:
                try:
                    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                    # Mark as potentially working if successful with GET
                    if response.status_code == 200:
                        return response.status_code, f"{response.reason} (works with browser headers)"
                    return response.status_code, response.reason
                except requests.exceptions.RequestException:
                    return response.status_code, f"{response.reason} (HEAD only, may work in browser)"
            
            return response.status_code, response.reason
            
        except requests.exceptions.RequestException as e:
            try:
                # If HEAD completely fails, try GET request as fallback
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                domain_last_request[domain] = time.time()
                return response.status_code, f"{response.reason} (GET only)"
            except requests.exceptions.RequestException as e2:
                domain_last_request[domain] = time.time()
                return None, str(e2)

def check_url_batch(urls_batch, batch_id):
    """
    Check a batch of URLs in sequence within a single worker thread.
    
    This function processes a batch of URLs assigned to one worker thread.
    It maintains the rate limiting per domain even within the batch.
    
    Args:
        urls_batch (list): List of URLs to check
        batch_id (int): Identifier for this batch (for logging)
        
    Returns:
        dict: Mapping of url -> (status_code, reason) for all URLs in batch
    """
    results = {}
    for url in urls_batch:
        print(f"Batch {batch_id}: Checking {url}")
        status_code, reason = check_url_with_rate_limit(url)
        results[url] = (status_code, reason)
        # Log broken URLs immediately for monitoring progress
        if status_code is None or status_code >= 400:
            print(f"  Batch {batch_id} BROKEN: {url} [{status_code}: {reason}]")
    return results

def check_local_file(file_path, html_dir):
    """
    Check if a local file exists relative to the HTML directory.
    
    This function checks for local image files referenced in HTML.
    It tries multiple potential locations:
    1. Relative to the HTML directory
    2. Relative to the project root directory
    
    Args:
        file_path (str): Relative path to the file
        html_dir (str): Path to the HTML directory
        
    Returns:
        tuple: (exists, reason) where:
               - exists: True if file found, False otherwise
               - reason: Description of result
    """
    try:
        # Try relative to HTML directory first
        full_path = os.path.join(html_dir, file_path)
        if os.path.exists(full_path):
            return True, "File exists"
        
        # Try relative to project root as fallback
        project_root = os.path.dirname(html_dir)
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            return True, "File exists"
        
        return False, "File not found"
    except Exception as e:
        return False, str(e)

def main():
    """
    Main function that orchestrates the broken link checking process.
    
    Process Overview:
    1. Scan HTML directory for files
    2. Extract all links and images from HTML files  
    3. Check local files for existence
    4. Check remote URLs in parallel batches with rate limiting
    5. Generate comprehensive report with categorized results
    """
    html_dir = '../html'
    
    # Validate that the HTML directory exists
    if not os.path.exists(html_dir):
        print(f"HTML directory {html_dir} not found!")
        return
    
    # Discover all HTML files to process
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    print(f"Found {len(html_files)} HTML files to check")
    
    # Data structures to store results
    all_links = defaultdict(list)      # Maps filename -> list of (type, url) tuples
    broken_links = defaultdict(list)   # Maps filename -> list of broken links
    total_links = 0
    
    # Phase 1: Extract all links from HTML files
    print("Phase 1: Extracting links from HTML files...")
    for html_file in html_files:
        file_path = os.path.join(html_dir, html_file)
        links = extract_links_from_html(file_path)
        all_links[html_file] = links
        total_links += len(links)
        print(f"Found {len(links)} links/images in {html_file}")
    
    print(f"\nTotal links/images found: {total_links}")
    print("Checking links and images...")
    
    # Phase 2: Deduplicate URLs to avoid redundant checks
    # Many HTML files link to the same URLs, so we check each unique URL only once
    unique_urls = set()         # Remote HTTP/HTTPS URLs to check
    unique_local_files = set()  # Local file paths to verify
    
    for links in all_links.values():
        for link_type, url in links:
            if link_type == 'local_image':
                unique_local_files.add(url)
            else:
                unique_urls.add(url)
    
    # Storage for check results
    url_status = {}         # Maps URL -> (status_code, reason)
    local_file_status = {}  # Maps file_path -> (exists, reason)
    
    # Phase 3: Check local files first (faster than remote URLs)
    print(f"\nPhase 3: Checking {len(unique_local_files)} local files...")
    for i, file_path in enumerate(unique_local_files, 1):
        print(f"Checking local file {i}/{len(unique_local_files)}: {file_path}")
        exists, reason = check_local_file(file_path, html_dir)
        local_file_status[file_path] = (exists, reason)
        
        if not exists:
            print(f"  MISSING: {reason}")
    
    # Phase 4: Check remote URLs in parallel batches with progress tracking
    print(f"\nPhase 4: Checking {len(unique_urls)} remote URLs...")
    report_file = 'broken_links_report.txt'
    with open(report_file, 'w') as f:
        f.write("BROKEN LINKS CHECK IN PROGRESS (PARALLEL)\n")
        f.write("=" * 50 + "\n\n")
    
    # Split URLs into batches for parallel processing
    # Smaller batches provide better progress granularity and rate limiting control
    batch_size = 20  # Balance between progress reporting and efficiency
    url_batches = []
    unique_urls_list = list(unique_urls)
    
    for i in range(0, len(unique_urls_list), batch_size):
        batch = unique_urls_list[i:i + batch_size]
        url_batches.append(batch)
    
    print(f"Processing {len(url_batches)} batches with max {batch_size} URLs per batch")
    
    # Configure parallel processing
    # Conservative worker count to avoid overwhelming target servers
    max_workers = 4  # 4 concurrent worker threads
    broken_url_count = 0
    
    # Execute parallel URL checking
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batches to the thread pool for parallel execution
        future_to_batch = {
            executor.submit(check_url_batch, batch, i): i 
            for i, batch in enumerate(url_batches)
        }
        
        completed_batches = 0
        # Process completed batches as they finish (not necessarily in order)
        for future in as_completed(future_to_batch):
            batch_id = future_to_batch[future]
            try:
                # Get results from completed batch
                batch_results = future.result()
                url_status.update(batch_results)
                
                # Count broken URLs in this batch for progress reporting
                batch_broken = sum(1 for status, _ in batch_results.values() 
                                 if status is None or status >= 400)
                broken_url_count += batch_broken
                
                completed_batches += 1
                print(f"Completed batch {batch_id + 1}/{len(url_batches)} - found {batch_broken} broken URLs")
                
                # Save progress to report file in real-time
                with open(report_file, 'a') as f:
                    # Log any broken URLs found in this batch
                    for url, (status_code, reason) in batch_results.items():
                        if status_code is None or status_code >= 400:
                            f.write(f"BROKEN URL: {url} [{status_code}: {reason}]\n")
                    
                    # Update progress summary
                    f.write(f"\nProgress: Completed {completed_batches}/{len(url_batches)} batches, found {broken_url_count} broken URLs\n")
                
            except Exception as e:
                print(f"Batch {batch_id} failed with error: {e}")
                with open(report_file, 'a') as f:
                    f.write(f"ERROR: Batch {batch_id} failed: {e}\n")
    
    # Phase 5: Generate comprehensive final report with categorized results
    print(f"\nPhase 5: Generating final report...")
    report = []
    report.append("="*80)
    report.append("BROKEN LINKS AND MISSING FILES REPORT (WITH BROWSER HEADER TESTING)")
    report.append("="*80)
    
    broken_count = 0
    browser_working_count = 0
    definitely_broken_count = 0
    
    for html_file, links in all_links.items():
        file_issues = []
        for link_type, url in links:
            if link_type == 'local_image':
                exists, reason = local_file_status[url]
                if not exists:
                    file_issues.append((link_type, url, "MISSING", reason, "broken"))
                    broken_count += 1
                    definitely_broken_count += 1
            else:
                status_code, reason = url_status[url]
                if status_code is None or status_code >= 400:
                    # Categorize the issue
                    if "works with browser headers" in str(reason):
                        category = "browser_ok"
                        browser_working_count += 1
                    elif "may work in browser" in str(reason):
                        category = "maybe_ok"
                        browser_working_count += 1
                    else:
                        category = "broken"
                        definitely_broken_count += 1
                    
                    file_issues.append((link_type, url, status_code, reason, category))
                    broken_count += 1
        
        if file_issues:
            broken_links[html_file] = file_issues
            report.append(f"\n{html_file}:")
            
            # Group by category
            definitely_broken = [item for item in file_issues if item[4] == "broken"]
            browser_ok = [item for item in file_issues if item[4] == "browser_ok"]
            maybe_ok = [item for item in file_issues if item[4] == "maybe_ok"]
            
            if definitely_broken:
                report.append("  🔴 DEFINITELY BROKEN:")
                for link_type, url, status, reason, _ in definitely_broken:
                    report.append(f"    - [{link_type.upper()}] {url} [{status}: {reason}]")
            
            if browser_ok:
                report.append("  🟡 WORKS IN BROWSER:")
                for link_type, url, status, reason, _ in browser_ok:
                    report.append(f"    - [{link_type.upper()}] {url} [{status}: {reason}]")
            
            if maybe_ok:
                report.append("  🟠 MAY WORK IN BROWSER:")
                for link_type, url, status, reason, _ in maybe_ok:
                    report.append(f"    - [{link_type.upper()}] {url} [{status}: {reason}]")
    
    report.append(f"\nSUMMARY:")
    report.append(f"- HTML files checked: {len(html_files)}")
    report.append(f"- Total links/images found: {total_links}")
    report.append(f"- Unique remote URLs checked: {len(unique_urls)}")
    report.append(f"- Unique local files checked: {len(unique_local_files)}")
    report.append(f"- Total issues found: {broken_count}")
    report.append(f"  • Definitely broken: {definitely_broken_count}")
    report.append(f"  • Works in browser: {browser_working_count}")
    report.append(f"- Files with issues: {len(broken_links)}")
    
    if not broken_links:
        report.append("\n✅ No broken links or missing files found!")
    else:
        report.append(f"\n📊 Found issues in {len(broken_links)} files")
        report.append(f"💡 {browser_working_count} links work in browsers but fail automated checks")
    
    # Save and print final report
    final_report = '\n'.join(report)
    with open(report_file, 'w') as f:
        f.write(final_report)
    
    print(final_report)
    print(f"\nFull report saved to: {report_file}")

if __name__ == "__main__":
    main()