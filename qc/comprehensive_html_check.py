#!/usr/bin/env python3
"""
Comprehensive HTML Well-formedness Checker
Analyzes all HTML files in the directory for structural issues and encoding problems.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
import html
import chardet

def analyze_html_structure(content, filename):
    """Analyze HTML structure and return detailed findings."""
    findings = {
        'errors': [],
        'warnings': [],
        'info': []
    }
    
    # Check for DOCTYPE
    if not re.search(r'<!DOCTYPE\s+html', content, re.IGNORECASE):
        findings['errors'].append("Missing DOCTYPE declaration")
    
    # Check for basic HTML structure
    if not re.search(r'<html\b', content, re.IGNORECASE):
        findings['errors'].append("Missing <html> tag")
    
    if not re.search(r'<head\b', content, re.IGNORECASE):
        findings['errors'].append("Missing <head> tag")
    
    if not re.search(r'<body\b', content, re.IGNORECASE):
        findings['errors'].append("Missing <body> tag")
    
    # Check for closing tags
    if not re.search(r'</html>', content, re.IGNORECASE):
        findings['errors'].append("Missing </html> closing tag")
    
    if not re.search(r'</head>', content, re.IGNORECASE):
        findings['errors'].append("Missing </head> closing tag")
    
    if not re.search(r'</body>', content, re.IGNORECASE):
        findings['errors'].append("Missing </body> closing tag")
    
    # Check for meta charset
    charset_pattern = r'<meta\s+[^>]*charset\s*=\s*["\']?([^"\'>\s]+)'
    charset_matches = re.findall(charset_pattern, content, re.IGNORECASE)
    
    if not charset_matches:
        findings['warnings'].append("No charset declaration found in meta tags")
    else:
        for charset in charset_matches:
            if charset.lower() not in ['utf-8', 'utf8']:
                findings['warnings'].append(f"Non-UTF-8 charset declared: {charset}")
    
    # Check for title tag
    if not re.search(r'<title\b', content, re.IGNORECASE):
        findings['warnings'].append("Missing <title> tag")
    
    # Check for common unclosed tags (simplified approach)
    void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                     'link', 'meta', 'param', 'source', 'track', 'wbr'}
    
    # Find all opening and closing tags
    tag_pattern = r'<(/?)(\w+)(?:\s[^>]*)?/?>'
    tags = re.findall(tag_pattern, content, re.IGNORECASE)
    
    tag_stack = []
    for is_closing, tag_name in tags:
        tag_name = tag_name.lower()
        
        if is_closing:  # Closing tag
            if tag_stack and tag_stack[-1] == tag_name:
                tag_stack.pop()
            elif tag_name not in void_elements:
                findings['warnings'].append(f"Unexpected closing tag: </{tag_name}>")
        else:  # Opening tag
            if tag_name not in void_elements:
                tag_stack.append(tag_name)
    
    # Report unclosed tags (limit to avoid spam)
    if len(tag_stack) > 0:
        unclosed = tag_stack[:3]  # Show first 3 unclosed tags
        for tag in unclosed:
            findings['warnings'].append(f"Potentially unclosed tag: <{tag}>")
        if len(tag_stack) > 3:
            findings['warnings'].append(f"... and {len(tag_stack) - 3} more unclosed tags")
    
    # Check for common HTML issues
    # Check for empty head
    head_content = re.search(r'<head\b[^>]*>(.*?)</head>', content, re.IGNORECASE | re.DOTALL)
    if head_content:
        head_inner = head_content.group(1).strip()
        if not head_inner:
            findings['warnings'].append("Empty <head> section")
    
    # Check for malformed attributes (basic check)
    malformed_attrs = re.findall(r'<\w+[^>]*=[^"\'\s][^>\s]*[^"\'>]', content)
    if malformed_attrs:
        findings['warnings'].append(f"Potentially malformed attributes found: {len(malformed_attrs)} instances")
    
    # Statistical info
    findings['info'].append(f"File size: {len(content)} characters")
    findings['info'].append(f"Number of tags: {len(tags)}")
    
    return findings

def check_file_encoding(file_path):
    """Check file encoding and detect issues."""
    issues = []
    
    try:
        # First, try to detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        detected = chardet.detect(raw_data)
        
        # Try to read as UTF-8
        try:
            content = raw_data.decode('utf-8')
            
            # Check for BOM
            if content.startswith('\ufeff'):
                issues.append("File contains UTF-8 BOM")
                
        except UnicodeDecodeError:
            issues.append(f"File is not valid UTF-8 (detected as {detected['encoding']})")
            # Try with detected encoding
            try:
                content = raw_data.decode(detected['encoding'])
            except:
                content = raw_data.decode('latin-1', errors='replace')
        
        return content, issues
        
    except Exception as e:
        issues.append(f"Could not read file: {e}")
        return None, issues

def main():
    html_dir = Path('/Users/thc4/Github/m-k-annotation-data/html')
    
    print("HTML Well-formedness Check")
    print("=" * 50)
    
    if not html_dir.exists():
        print(f"ERROR: Directory not found: {html_dir}")
        return
    
    # Get all HTML files
    html_files = list(html_dir.glob('*.html'))
    total_files = len(html_files)
    
    print(f"Found {total_files} HTML files in {html_dir}")
    print()
    
    # Statistics tracking
    stats = {
        'total_files': total_files,
        'readable_files': 0,
        'files_with_errors': 0,
        'files_with_warnings': 0,
        'encoding_issues': 0,
        'structure_issues': 0
    }
    
    issue_summary = defaultdict(int)
    problem_files = []
    
    # Process all files
    for i, file_path in enumerate(html_files):
        print(f"Processing {i+1}/{total_files}: {file_path.name}")
        
        # Check encoding
        content, encoding_issues = check_file_encoding(file_path)
        
        if content is None:
            stats['encoding_issues'] += 1
            problem_files.append((file_path.name, "Could not read file"))
            continue
        
        stats['readable_files'] += 1
        
        # Analyze structure
        findings = analyze_html_structure(content, file_path.name)
        
        # Update statistics
        if encoding_issues:
            stats['encoding_issues'] += 1
        
        if findings['errors']:
            stats['files_with_errors'] += 1
            stats['structure_issues'] += 1
        
        if findings['warnings']:
            stats['files_with_warnings'] += 1
        
        # Track issues
        for issue in encoding_issues + findings['errors'] + findings['warnings']:
            issue_summary[issue] += 1
        
        # Track problematic files
        if findings['errors'] or encoding_issues:
            problem_desc = []
            if encoding_issues:
                problem_desc.append(f"Encoding: {len(encoding_issues)} issues")
            if findings['errors']:
                problem_desc.append(f"Structure: {len(findings['errors'])} errors")
            problem_files.append((file_path.name, "; ".join(problem_desc)))
    
    # Summary Report
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    
    print(f"Total files analyzed: {stats['total_files']}")
    print(f"Readable files: {stats['readable_files']}")
    print(f"Files with encoding issues: {stats['encoding_issues']}")
    print(f"Files with structural errors: {stats['files_with_errors']}")
    print(f"Files with warnings: {stats['files_with_warnings']}")
    print(f"Files with structural issues: {stats['structure_issues']}")
    
    # Calculate percentages
    if stats['total_files'] > 0:
        error_rate = (stats['files_with_errors'] / stats['total_files']) * 100
        warning_rate = (stats['files_with_warnings'] / stats['total_files']) * 100
        print(f"\nError rate: {error_rate:.1f}%")
        print(f"Warning rate: {warning_rate:.1f}%")
    
    # Most common issues
    if issue_summary:
        print(f"\nMost common issues:")
        sorted_issues = sorted(issue_summary.items(), key=lambda x: x[1], reverse=True)
        for issue, count in sorted_issues[:10]:  # Top 10 issues
            print(f"  • {issue}: {count} files")
    
    # Problem files
    if problem_files:
        print(f"\nFiles with significant issues:")
        for filename, issues in problem_files[:10]:  # Show first 10
            print(f"  • {filename}: {issues}")
        if len(problem_files) > 10:
            print(f"  ... and {len(problem_files) - 10} more files with issues")
    
    # Overall assessment
    print(f"\nOVERALL ASSESSMENT:")
    if stats['files_with_errors'] == 0 and stats['encoding_issues'] == 0:
        print("✓ All files appear to be well-formed HTML with no major issues")
    elif stats['files_with_errors'] < stats['total_files'] * 0.1:
        print("⚠ Most files are well-formed, but some have minor issues")
    else:
        print("✗ Significant issues found that may affect HTML processing")
    
    print(f"\nRecommendations:")
    if stats['encoding_issues'] > 0:
        print("- Address encoding issues in affected files")
    if stats['files_with_errors'] > 0:
        print("- Fix structural HTML errors to ensure proper rendering")
    if stats['files_with_warnings'] > 0:
        print("- Review warning messages for best practices")

if __name__ == "__main__":
    main()