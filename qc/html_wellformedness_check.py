#!/usr/bin/env python3
"""
HTML Well-formedness Checker
Checks HTML files for basic structural issues and encoding problems.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
import html

def check_html_structure(content, filename):
    """Check basic HTML structure and return issues found."""
    issues = []
    
    # Check for DOCTYPE
    if not re.search(r'<!DOCTYPE\s+html', content, re.IGNORECASE):
        issues.append("Missing DOCTYPE declaration")
    
    # Check for basic HTML structure
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
    
    # Check for common unclosed tags
    unclosed_tags = []
    
    # Simple regex to find opening and closing tags
    # This is a basic check - more sophisticated parsing would be needed for complex cases
    tag_pattern = r'<(/?)(\w+)(?:\s[^>]*)?>'
    tags = re.findall(tag_pattern, content, re.IGNORECASE)
    
    # Track self-closing and void elements
    void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                     'link', 'meta', 'param', 'source', 'track', 'wbr'}
    
    tag_stack = []
    for is_closing, tag_name in tags:
        tag_name = tag_name.lower()
        
        if is_closing:  # Closing tag
            if tag_stack and tag_stack[-1] == tag_name:
                tag_stack.pop()
            elif tag_name not in void_elements:
                unclosed_tags.append(f"Unexpected closing tag: </{tag_name}>")
        else:  # Opening tag
            if tag_name not in void_elements:
                tag_stack.append(tag_name)
    
    # Any remaining tags in stack are unclosed
    for unclosed in tag_stack:
        unclosed_tags.append(f"Unclosed tag: <{unclosed}>")
    
    if unclosed_tags:
        issues.extend(unclosed_tags[:5])  # Limit to first 5 to avoid spam
    
    return issues

def check_encoding(file_path):
    """Check file encoding and return issues."""
    issues = []
    
    try:
        # Try to read as UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for BOM
        if content.startswith('\ufeff'):
            issues.append("File contains UTF-8 BOM")
        
        # Check for common encoding declarations
        encoding_pattern = r'<meta\s+[^>]*charset\s*=\s*["\']?([^"\'>\s]+)'
        encoding_matches = re.findall(encoding_pattern, content, re.IGNORECASE)
        
        if not encoding_matches:
            issues.append("No charset declaration found")
        else:
            for charset in encoding_matches:
                if charset.lower() not in ['utf-8', 'utf8']:
                    issues.append(f"Non-UTF-8 charset declared: {charset}")
        
        return content, issues
        
    except UnicodeDecodeError:
        issues.append("File is not valid UTF-8")
        # Try to read with latin-1 as fallback
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return content, issues
        except Exception as e:
            issues.append(f"Could not read file: {e}")
            return None, issues

def main():
    html_dir = Path('/Users/thc4/Github/m-k-annotation-data/html')
    
    if not html_dir.exists():
        print(f"Directory not found: {html_dir}")
        return
    
    html_files = list(html_dir.glob('*.html'))
    print(f"Found {len(html_files)} HTML files")
    
    # Track statistics
    total_files = len(html_files)
    files_with_issues = 0
    issue_counts = defaultdict(int)
    
    # Sample files for detailed analysis (first 10, last 10, and some random ones)
    sample_files = []
    if total_files <= 20:
        sample_files = html_files
    else:
        sample_files = html_files[:10] + html_files[-10:]
    
    print(f"\nAnalyzing {len(sample_files)} sample files for detailed structure check...")
    
    for file_path in sample_files:
        print(f"\nChecking: {file_path.name}")
        
        # Check encoding
        content, encoding_issues = check_encoding(file_path)
        
        if content is None:
            files_with_issues += 1
            continue
        
        # Check HTML structure
        structure_issues = check_html_structure(content, file_path.name)
        
        all_issues = encoding_issues + structure_issues
        
        if all_issues:
            files_with_issues += 1
            print(f"  Issues found:")
            for issue in all_issues:
                print(f"    - {issue}")
                issue_counts[issue] += 1
        else:
            print(f"  No issues found")
    
    # Quick check for all files - just basic existence and readability
    print(f"\nQuick readability check for all {total_files} files...")
    unreadable_files = []
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(100)  # Just read first 100 chars
        except Exception as e:
            unreadable_files.append((file_path.name, str(e)))
    
    # Summary report
    print(f"\n{'='*60}")
    print("HTML WELL-FORMEDNESS CHECK SUMMARY")
    print(f"{'='*60}")
    print(f"Total HTML files found: {total_files}")
    print(f"Sample files analyzed: {len(sample_files)}")
    print(f"Files with issues in sample: {files_with_issues}")
    print(f"Unreadable files: {len(unreadable_files)}")
    
    if unreadable_files:
        print(f"\nUnreadable files:")
        for filename, error in unreadable_files:
            print(f"  - {filename}: {error}")
    
    if issue_counts:
        print(f"\nMost common issues found:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {issue}: {count} files")
    else:
        print(f"\nNo structural issues found in sample files!")
    
    print(f"\nNote: This analysis checked {len(sample_files)} sample files out of {total_files} total files.")
    print(f"For a complete analysis, all files would need to be checked individually.")

if __name__ == "__main__":
    main()