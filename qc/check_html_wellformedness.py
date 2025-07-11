#!/usr/bin/env python3
"""
HTML Well-Formedness Checker for all HTML files

This script checks all HTML files in the html directory for:
- Basic HTML structure
- Proper tag nesting
- Unclosed tags
- Missing required elements
- Encoding issues
"""
import os
import sys
from html.parser import HTMLParser
from pathlib import Path
import re

class HTMLWellFormednessChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.errors = []
        self.warnings = []
        self.has_html = False
        self.has_head = False
        self.has_body = False
        self.has_title = False
        self.self_closing_tags = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }

    def handle_starttag(self, tag, attrs):
        if tag == 'html':
            self.has_html = True
        elif tag == 'head':
            self.has_head = True
        elif tag == 'body':
            self.has_body = True
        elif tag == 'title':
            self.has_title = True
        
        # Track tag nesting for non-self-closing tags
        if tag not in self.self_closing_tags:
            self.tag_stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.self_closing_tags:
            return
        
        if not self.tag_stack:
            self.errors.append(f"Closing tag </{tag}> without opening tag")
            return
        
        # Check if tags are properly nested
        if self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        else:
            # Look for the matching opening tag
            if tag in self.tag_stack:
                idx = len(self.tag_stack) - 1 - self.tag_stack[::-1].index(tag)
                unclosed = self.tag_stack[idx+1:]
                if unclosed:
                    self.errors.append(f"Unclosed tags before </{tag}>: {', '.join(unclosed)}")
                # Remove the tag and everything after it
                self.tag_stack = self.tag_stack[:idx]
            else:
                self.errors.append(f"Closing tag </{tag}> without matching opening tag")

    def handle_data(self, data):
        # Check for potential encoding issues
        try:
            data.encode('utf-8')
        except UnicodeEncodeError as e:
            self.errors.append(f"Encoding issue: {e}")

    def error(self, message):
        self.errors.append(f"Parser error: {message}")

    def check_structure(self):
        """Check basic HTML document structure"""
        if not self.has_html:
            self.warnings.append("Missing <html> element")
        if not self.has_head:
            self.warnings.append("Missing <head> element")
        if not self.has_body:
            self.warnings.append("Missing <body> element")
        if not self.has_title:
            self.warnings.append("Missing <title> element")
        
        # Check for unclosed tags
        if self.tag_stack:
            self.errors.append(f"Unclosed tags at end of document: {', '.join(self.tag_stack)}")

def check_file_encoding(file_path):
    """Check if file can be read as UTF-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, None
    except UnicodeDecodeError as e:
        return None, f"UTF-8 encoding error: {e}"
    except Exception as e:
        return None, f"File read error: {e}"

def check_html_file(file_path):
    """Check a single HTML file for well-formedness"""
    print(f"Checking: {os.path.basename(file_path)}")
    
    # Check file encoding
    content, encoding_error = check_file_encoding(file_path)
    if encoding_error:
        return {
            'file': file_path,
            'errors': [encoding_error],
            'warnings': [],
            'status': 'ENCODING_ERROR'
        }
    
    # Parse HTML
    checker = HTMLWellFormednessChecker()
    
    try:
        checker.feed(content)
        checker.check_structure()
    except Exception as e:
        checker.errors.append(f"Critical parsing error: {e}")
    
    # Determine status
    if checker.errors:
        status = 'ERRORS'
    elif checker.warnings:
        status = 'WARNINGS'
    else:
        status = 'OK'
    
    return {
        'file': file_path,
        'errors': checker.errors,
        'warnings': checker.warnings,
        'status': status
    }

def main():
    html_dir = '../html'
    
    if not os.path.exists(html_dir):
        print(f"Error: HTML directory not found: {html_dir}")
        sys.exit(1)
    
    # Find all HTML files
    html_files = []
    for file in os.listdir(html_dir):
        if file.endswith('.html'):
            html_files.append(os.path.join(html_dir, file))
    
    if not html_files:
        print("No HTML files found!")
        sys.exit(1)
    
    html_files.sort()
    
    print("HTML Well-Formedness Check")
    print("=" * 50)
    print(f"Checking {len(html_files)} HTML files...")
    print()
    
    results = []
    files_with_errors = 0
    files_with_warnings = 0
    files_ok = 0
    
    # Check each file
    for file_path in html_files:
        result = check_html_file(file_path)
        results.append(result)
        
        if result['status'] == 'ERRORS':
            files_with_errors += 1
            print(f"  ✗ ERRORS: {len(result['errors'])} error(s)")
        elif result['status'] == 'WARNINGS':
            files_with_warnings += 1
            print(f"  ⚠ WARNINGS: {len(result['warnings'])} warning(s)")
        elif result['status'] == 'OK':
            files_ok += 1
            print(f"  ✓ OK")
        else:
            files_with_errors += 1
            print(f"  ✗ {result['status']}")
    
    # Generate detailed report
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total files checked: {len(html_files)}")
    print(f"Files with errors: {files_with_errors}")
    print(f"Files with warnings: {files_with_warnings}")
    print(f"Files OK: {files_ok}")
    
    # Show detailed errors and warnings
    if files_with_errors > 0 or files_with_warnings > 0:
        print("\n" + "=" * 50)
        print("DETAILED ISSUES")
        print("=" * 50)
        
        for result in results:
            if result['errors'] or result['warnings']:
                print(f"\n{os.path.basename(result['file'])}:")
                
                for error in result['errors']:
                    print(f"  ✗ ERROR: {error}")
                
                for warning in result['warnings']:
                    print(f"  ⚠ WARNING: {warning}")
    
    # Save detailed report
    report_path = 'html_wellformedness_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("HTML Well-Formedness Check Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total files checked: {len(html_files)}\n")
        f.write(f"Files with errors: {files_with_errors}\n")
        f.write(f"Files with warnings: {files_with_warnings}\n")
        f.write(f"Files OK: {files_ok}\n\n")
        
        f.write("Detailed Results:\n")
        f.write("-" * 20 + "\n\n")
        
        for result in results:
            f.write(f"{os.path.basename(result['file'])}: {result['status']}\n")
            
            for error in result['errors']:
                f.write(f"  ERROR: {error}\n")
            
            for warning in result['warnings']:
                f.write(f"  WARNING: {warning}\n")
            
            f.write("\n")
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Return appropriate exit code
    if files_with_errors > 0:
        sys.exit(1)
    elif files_with_warnings > 0:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()