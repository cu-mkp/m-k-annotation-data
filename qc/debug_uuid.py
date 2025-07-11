#!/usr/bin/env python3
"""
Debug script to check if a specific UUID exists in the Excel file
"""

import pandas as pd

def check_uuid_in_excel(target_uuid):
    """Check if a specific UUID exists in the Excel file"""
    excel_file = 'media-full-list-alt-text-permissions.xlsx'
    df = pd.read_excel(excel_file, sheet_name='release2')
    
    print(f"Looking for UUID: {target_uuid}")
    print(f"Excel file has {len(df)} rows")
    
    found_matches = []
    
    # Check each row for the target UUID
    for i in range(len(df)):
        drive_url = df.iloc[i, 2]  # Column C (index 2)
        alt_text = df.iloc[i, 20]  # Column U (index 20)
        
        if pd.isna(drive_url):
            continue
            
        drive_url_str = str(drive_url)
        
        # Check if target UUID appears anywhere in the URL
        if target_uuid in drive_url_str:
            found_matches.append({
                'row': i + 1,  # 1-indexed for Excel
                'url': drive_url_str,
                'alt_text': alt_text if not pd.isna(alt_text) else 'N/A'
            })
    
    if found_matches:
        print(f"\nFound {len(found_matches)} matches:")
        for match in found_matches:
            print(f"  Row {match['row']}: {match['url']}")
            print(f"    Alt text: {match['alt_text']}")
    else:
        print(f"\nNo matches found for UUID: {target_uuid}")
    
    # Also show first few rows of column C for reference
    print(f"\nFirst 10 rows of column C (Google Drive URLs):")
    for i in range(min(10, len(df))):
        url = df.iloc[i, 2]
        if not pd.isna(url):
            print(f"  Row {i+1}: {url}")

if __name__ == "__main__":
    # Check the specific UUID you mentioned
    check_uuid_in_excel("1tpkpHvN9d2Am_e4Cmx4WnIPrseuytqHh")