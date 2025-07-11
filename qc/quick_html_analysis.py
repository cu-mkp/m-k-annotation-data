#!/usr/bin/env python3
"""
Quick HTML Analysis Script
Performs basic well-formedness checks on HTML files
"""

import os
import re
from pathlib import Path

def check_basic_structure(content, filename):
    """Check basic HTML structure"""
    issues = []
    
    # Check for DOCTYPE
    if not re.search(r'<!DOCTYPE\s+html', content, re.IGNORECASE):
        issues.append("Missing DOCTYPE declaration")
    
    # Check for basic tags
    if not re.search(r'<html\b', content, re.IGNORECASE):
        issues.append("Missing <html> tag")
    
    if not re.search(r'<head\b', content, re.IGNORECASE):
        issues.append("Missing <head> tag")
    
    if not re.search(r'<body\b', content, re.IGNORECASE):
        issues.append("Missing <body> tag")
    
    # Check for closing tags
    if not re.search(r'</html>', content, re.IGNORECASE):
        issues.append("Missing </html> closing tag")
    
    if not re.search(r'</head>', content, re.IGNORECASE):
        issues.append("Missing </head> closing tag")
    
    if not re.search(r'</body>', content, re.IGNORECASE):
        issues.append("Missing </body> closing tag")
    
    # Check for charset
    if not re.search(r'<meta\s+[^>]*charset', content, re.IGNORECASE):
        issues.append("No charset declaration found")
    
    # Check for title
    if not re.search(r'<title\b', content, re.IGNORECASE):
        issues.append("Missing <title> tag")
    
    return issues

def main():
    html_dir = Path('/Users/thc4/Github/m-k-annotation-data/html')
    
    # Get all HTML files
    html_files = list(html_dir.glob('*.html'))
    total_files = len(html_files)
    
    print(f"HTML Well-formedness Check")
    print(f"Directory: {html_dir}")
    print(f"Total HTML files found: {total_files}")
    print("-" * 50)
    
    # Sample files for analysis
    sample_files = html_files[:10] + html_files[-10:]  # First 10 and last 10
    if len(html_files) > 20:
        # Add some from the middle
        mid_start = len(html_files) // 2 - 5
        mid_end = len(html_files) // 2 + 5
        sample_files.extend(html_files[mid_start:mid_end])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sample = []
    for f in sample_files:
        if f not in seen:
            seen.add(f)
            unique_sample.append(f)
    
    sample_files = unique_sample
    
    print(f"Analyzing {len(sample_files)} sample files...")
    print()
    
    all_issues = []
    files_with_issues = 0
    
    for i, file_path in enumerate(sample_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = check_basic_structure(content, file_path.name)
            
            if issues:
                files_with_issues += 1
                print(f"Issues in {file_path.name}:")
                for issue in issues:
                    print(f"  - {issue}")
                    all_issues.append(issue)
                print()
            
        except Exception as e:
            files_with_issues += 1
            print(f"Error reading {file_path.name}: {e}")
            print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files in directory: {total_files}")
    print(f"Sample files analyzed: {len(sample_files)}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Files without issues: {len(sample_files) - files_with_issues}")
    
    if all_issues:
        print(f"\nMost common issues:")
        issue_count = {}
        for issue in all_issues:
            issue_count[issue] = issue_count.get(issue, 0) + 1
        
        for issue, count in sorted(issue_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue}: {count} files")
    
    print(f"\nFile naming pattern analysis:")
    prefixes = {}
    for file_path in html_files:
        if file_path.name.startswith('ann_'):
            parts = file_path.name.split('_')
            if len(parts) >= 3:
                prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    print(f"Common filename patterns:")
    for pattern, count in sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {pattern}: {count} files")

if __name__ == "__main__":
    main()