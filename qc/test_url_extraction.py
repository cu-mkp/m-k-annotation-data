#!/usr/bin/env python3
"""
Test URL extraction function with various Google Drive URL formats
"""

import pandas as pd

def extract_google_drive_id_from_url(url):
    """Extract Google Drive file ID from a Google Drive URL using id= pattern"""
    if not url or pd.isna(url):
        return None
    
    url = str(url)
    # Look for id= pattern in the URL
    if 'id=' in url:
        start = url.find('id=') + 3
        end = url.find('&', start)
        if end == -1:
            end = url.find('/', start)
        if end == -1:
            end = len(url)
        return url[start:end]
    
    # Also handle /file/d/ pattern as fallback
    if '/file/d/' in url:
        start = url.find('/file/d/') + 8
        end = url.find('/', start)
        if end == -1:
            end = url.find('?', start)
        if end == -1:
            end = len(url)
        return url[start:end]
    
    return None

def test_urls():
    """Test various URL formats"""
    test_cases = [
        "https://drive.google.com/file/d/0BwJi-u8sfkVDQjNyU0F6aWhyLXc/view?usp=drivesdk",
        "https://drive.google.com/file/d/1tpkpHvN9d2Am_e4Cmx4WnIPrseuytqHh/view?usp=drivesdk", 
        "https://drive.google.com/open?id=1F9G9RQf2SAc69750ehjfDCxYA__c32xF",
        "https://drive.google.com/file/d/0BwJi-u8sfkVDdGdMMHREdThwZkU/view?usp=drivesdk",
        "https://drive.google.com/open?id=1hN08MRf8QrH7ZEcTA0wltPNFZs-TvT2J"
    ]
    
    print("Testing URL extraction:")
    print("-" * 80)
    for url in test_cases:
        extracted_id = extract_google_drive_id_from_url(url)
        print(f"URL: {url}")
        print(f"Extracted ID: {extracted_id}")
        print()

if __name__ == "__main__":
    test_urls()