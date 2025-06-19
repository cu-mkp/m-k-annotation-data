#!/usr/bin/env python3
"""
Script to add alt attributes to img tags in HTML files based on Excel data.

This script:
1. Reads Excel file to get mapping between image filenames (column B) and alt text (column U)
2. Processes all HTML files in ../html/ directory
3. Finds img tags and matches their src URLs with filenames from Excel
4. Adds alt attributes with corresponding text from Excel
"""

import os
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime

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

def load_alt_text_mapping(excel_file):
    """Load mapping from Excel file: uuid -> alt text"""
    df = pd.read_excel(excel_file, sheet_name='Sheet4')
    
    # Skip header row (row 0), get data from row 1 onwards
    mapping = {}
    for i in range(1, len(df)):
        uuid = df.iloc[i, 5]  # Column F (index 5) - UUID
        alt_text = df.iloc[i, 4]  # Column E (index 4) - Alt text
        
        # Skip if uuid or alt_text is NaN/empty
        if pd.isna(uuid) or not uuid or pd.isna(alt_text) or not alt_text:
            continue
        
        # Store mapping
        mapping[str(uuid).strip()] = str(alt_text).strip()
    
    return mapping

def extract_uuid_from_img_url(img_src):
    """Extract UUID from img src URL (part after last '/' and before file extension)"""
    if not img_src:
        return None
    
    # Get the part after the last '/'
    filename = img_src.split('/')[-1]
    
    # Remove common image file extensions
    if filename.endswith('.jpg'):
        filename = filename[:-4]
    elif filename.endswith('.png'):
        filename = filename[:-4]
    elif filename.endswith('.jpeg'):
        filename = filename[:-5]
    elif filename.endswith('.gif'):
        filename = filename[:-4]
    elif filename.endswith('.webp'):
        filename = filename[:-5]
    
    return filename

def find_matching_alt_text(img_src, alt_mapping):
    """Find alt text for an img src by matching UUID with spreadsheet UUIDs"""
    # Extract UUID from the img src URL
    img_uuid = extract_uuid_from_img_url(img_src)
    
    if not img_uuid:
        return None, None, 'NO_UUID'
    
    print(f"  Extracted UUID from URL: {img_uuid}")
    
    # Check if this UUID matches any in the spreadsheet
    if img_uuid in alt_mapping:
        alt_text = alt_mapping[img_uuid]
        print(f"  ✓ matched UUID in spreadsheet")
        return img_uuid, alt_text, 'MATCHED'
    
    # UUID not found in spreadsheet
    print(f"  UUID not found in spreadsheet")
    return img_uuid, None, 'UUID_NOT_FOUND'

def process_html_file(file_path, alt_mapping):
    """Process a single HTML file to add alt attributes to img tags"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        modified = False
        
        # Find all img tags
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            if img.get('src'):
                src = img['src']
                
                # Check if alt attribute already exists (we'll replace it)
                existing_alt = img.get('alt', '')
                if existing_alt:
                    print(f"  Found existing alt: '{existing_alt}'")
                
                # Find matching alt text
                matched_filename, alt_text = find_matching_alt_text(src, alt_mapping)
                
                if alt_text:
                    img['alt'] = alt_text
                    modified = True
                    if existing_alt:
                        print(f"  ✓ Replaced alt attribute: '{alt_text}'")
                    else:
                        print(f"  ✓ Added alt attribute: '{alt_text}'")
        
        # Write back to file if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_html_file_with_report(file_path, alt_mapping):
    """Process a single HTML file and return report data"""
    filename = os.path.basename(file_path)
    report_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        modified = False
        
        # Find all img tags
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            if img.get('src'):
                src = img['src']
                
                # Check if alt attribute already exists (we'll replace it)
                existing_alt = img.get('alt', '')
                if existing_alt:
                    print(f"  Found existing alt: '{existing_alt}'")
                
                # Extract UUID and find matching alt text
                img_uuid = extract_uuid_from_img_url(src)
                
                matched_filename, alt_text, match_status = find_matching_alt_text(src, alt_mapping)
                
                if match_status == 'MATCHED' and alt_text:
                    img['alt'] = alt_text
                    modified = True
                    if existing_alt:
                        print(f"  ✓ Replaced alt attribute: '{alt_text}'")
                    else:
                        print(f"  ✓ Added alt attribute: '{alt_text}'")
                    
                    # Add to report
                    report_data.append({
                        'filename': filename,
                        'uuid': img_uuid,
                        'status': 'MATCHED',
                        'alt_text': alt_text
                    })
                elif match_status == 'UUID_NOT_FOUND':
                    # UUID not found in spreadsheet - keep existing alt if present
                    if existing_alt:
                        print(f"  UUID not found in spreadsheet, keeping existing alt: '{existing_alt}'")
                        status_text = 'UUID NOT IN SPREADSHEET (kept existing)'
                        alt_display = existing_alt
                    else:
                        print(f"  UUID not found in spreadsheet, no alt attribute added")
                        status_text = 'UUID NOT IN SPREADSHEET (no alt)'
                        alt_display = 'N/A'
                    
                    # Add to report
                    report_data.append({
                        'filename': filename,
                        'uuid': img_uuid,
                        'status': status_text,
                        'alt_text': alt_display
                    })
                else:
                    # Other cases (e.g., UUID extraction failed)
                    if existing_alt:
                        print(f"  No match found, keeping existing alt: '{existing_alt}'")
                        status_text = 'NO MATCH (kept existing)'
                        alt_display = existing_alt
                    else:
                        print(f"  No match found, no alt attribute added")
                        status_text = 'NO MATCH (no alt)'
                        alt_display = 'N/A'
                    
                    # Add to report
                    report_data.append({
                        'filename': filename,
                        'uuid': img_uuid or 'UNKNOWN',
                        'status': status_text,
                        'alt_text': alt_display
                    })
        
        # Write back to file if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
        
        return report_data
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return [{
            'filename': filename,
            'uuid': 'ERROR',
            'status': 'ERROR',
            'alt_text': str(e)
        }]

def generate_report(report_data):
    """Generate a text report of all processed images"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('alt_text_report.txt', 'w', encoding='utf-8') as f:
        f.write("ALT TEXT PROCESSING REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {timestamp}\n\n")
        
        # Summary stats
        total_images = len(report_data)
        matched_images = len([item for item in report_data if item['status'] == 'MATCHED'])
        uuid_not_in_spreadsheet_kept = len([item for item in report_data if item['status'] == 'UUID NOT IN SPREADSHEET (kept existing)'])
        uuid_not_in_spreadsheet_no_alt = len([item for item in report_data if item['status'] == 'UUID NOT IN SPREADSHEET (no alt)'])
        no_match_kept = len([item for item in report_data if item['status'] == 'NO MATCH (kept existing)'])
        no_match_no_alt = len([item for item in report_data if item['status'] == 'NO MATCH (no alt)'])
        errors = len([item for item in report_data if item['status'] == 'ERROR'])
        
        f.write(f"SUMMARY:\n")
        f.write(f"Total images processed: {total_images}\n")
        f.write(f"Successfully matched: {matched_images}\n")
        f.write(f"UUID not in spreadsheet - kept existing alt: {uuid_not_in_spreadsheet_kept}\n")
        f.write(f"UUID not in spreadsheet - no alt attribute: {uuid_not_in_spreadsheet_no_alt}\n")
        f.write(f"Other no match - kept existing alt: {no_match_kept}\n")
        f.write(f"Other no match - no alt attribute: {no_match_no_alt}\n")
        f.write(f"Errors: {errors}\n\n")
        
        # Detailed results
        f.write("DETAILED RESULTS:\n")
        f.write("-" * 50 + "\n")
        f.write(f"{'Filename':<25} {'UUID':<35} {'Status':<10} {'Alt Text'}\n")
        f.write("-" * 120 + "\n")
        
        for item in report_data:
            alt_text_preview = item['alt_text'][:50] + "..." if len(item['alt_text']) > 50 else item['alt_text']
            f.write(f"{item['filename']:<25} {item['uuid']:<35} {item['status']:<10} {alt_text_preview}\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write(f"Report generated by add_alt_text.py on {timestamp}\n")

def generate_file_summary_report(report_data):
    """Generate a summary report by HTML file showing match statistics"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Group data by filename
    file_stats = {}
    for item in report_data:
        filename = item['filename']
        if filename not in file_stats:
            file_stats[filename] = {
                'matched': 0,
                'not_matched': 0,
                'total': 0
            }
        
        file_stats[filename]['total'] += 1
        if item['status'] == 'MATCHED':
            file_stats[filename]['matched'] += 1
        else:
            file_stats[filename]['not_matched'] += 1
    
    # Write file summary report
    with open('file_summary_report.txt', 'w', encoding='utf-8') as f:
        f.write("HTML FILE SUMMARY REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {timestamp}\n\n")
        
        f.write("Images Match Statistics by HTML File:\n")
        f.write("-" * 72 + "\n")
        f.write(f"{'Filename':<25} {'Total':<8} {'Matched':<8} {'Not Matched':<12} {'Match %':<8} {'Not Match %':<12}\n")
        f.write("-" * 72 + "\n")
        
        total_files = 0
        total_images = 0
        total_matched = 0
        files_with_matches = 0
        
        for filename in sorted(file_stats.keys()):
            stats = file_stats[filename]
            match_percentage = (stats['matched'] / stats['total'] * 100) if stats['total'] > 0 else 0
            not_match_percentage = (stats['not_matched'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            f.write(f"{filename:<25} {stats['total']:<8} {stats['matched']:<8} {stats['not_matched']:<12} {match_percentage:<7.1f}% {not_match_percentage:<11.1f}%\n")
            
            total_files += 1
            total_images += stats['total']
            total_matched += stats['matched']
            if stats['matched'] > 0:
                files_with_matches += 1
        
        f.write("-" * 72 + "\n")
        f.write(f"{'TOTALS:':<25} {total_images:<8} {total_matched:<8} {total_images - total_matched:<12} {(total_matched/total_images*100):<7.1f}% {((total_images - total_matched)/total_images*100):<11.1f}%\n")
        
        f.write(f"\nSUMMARY:\n")
        f.write(f"Total HTML files processed: {total_files}\n")
        f.write(f"Files with at least one match: {files_with_matches}\n")
        f.write(f"Files with no matches: {total_files - files_with_matches}\n")
        f.write(f"Overall match rate: {(total_matched/total_images*100):.1f}%\n")
        
        f.write("\n" + "=" * 72 + "\n")
        f.write(f"Report generated by add_alt_text.py on {timestamp}\n")

def main():
    # Load alt text mapping from Excel
    excel_file = 'alt-text-metadata-uuid.xlsx'
    print(f"Loading alt text mapping from {excel_file}...")
    
    alt_mapping = load_alt_text_mapping(excel_file)
    print(f"Loaded {len(alt_mapping)} UUID -> alt text mappings")
    
    # Process HTML files
    html_dir = '../html'
    if not os.path.exists(html_dir):
        print(f"Error: HTML directory {html_dir} not found")
        return
    
    print(f"\nProcessing HTML files in {html_dir}...")
    
    files_processed = 0
    files_modified = 0
    report_data = []
    
    for filename in sorted(os.listdir(html_dir)):
        if filename.endswith('.html'):
            file_path = os.path.join(html_dir, filename)
            print(f"Processing {filename}...")
            
            # Process file and collect report data
            file_report = process_html_file_with_report(file_path, alt_mapping)
            report_data.extend(file_report)
            
            # Check if file was modified
            if any(item['status'] == 'MATCHED' for item in file_report):
                files_modified += 1
            files_processed += 1
    
    # Generate detailed report
    generate_report(report_data)
    
    # Generate file summary report
    generate_file_summary_report(report_data)
    
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Files modified: {files_modified}")
    print(f"Detailed report saved to: alt_text_report.txt")
    print(f"File summary report saved to: file_summary_report.txt")

if __name__ == "__main__":
    main()