#!/usr/bin/env python3
"""
Simple HTML validation check
"""
import os
import glob
from pathlib import Path

def check_html_files():
    html_dir = Path('/Users/thc4/Github/m-k-annotation-data/html')
    html_files = list(html_dir.glob('*.html'))
    
    print(f"HTML Well-Formedness Check")
    print(f"Found {len(html_files)} HTML files")
    print("=" * 50)
    
    issues_found = 0
    
    for html_file in sorted(html_files):
        print(f"Checking: {html_file.name}")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic checks
            issues = []
            
            # Check for basic structure
            if '<html' not in content.lower():
                issues.append("Missing <html> tag")
            if '<head' not in content.lower():
                issues.append("Missing <head> tag")
            if '<body' not in content.lower():
                issues.append("Missing <body> tag")
            
            # Check for unclosed tags (basic)
            open_tags = content.count('<p>')
            close_tags = content.count('</p>')
            if open_tags != close_tags:
                issues.append(f"Mismatched <p> tags: {open_tags} open, {close_tags} close")
            
            open_div = content.count('<div')
            close_div = content.count('</div>')
            if open_div != close_div:
                issues.append(f"Mismatched <div> tags: {open_div} open, {close_div} close")
            
            # Check for proper encoding
            if '&lt;' in content and '<' in content:
                # This might indicate mixed encoding
                pass
            
            if issues:
                issues_found += len(issues)
                print(f"  ✗ {len(issues)} issue(s) found:")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print(f"  ✓ OK")
                
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
            issues_found += 1
    
    print("\n" + "=" * 50)
    print(f"Summary: {issues_found} total issues found across all files")
    
    return issues_found

if __name__ == "__main__":
    issues = check_html_files()
    if issues == 0:
        print("All HTML files appear well-formed!")
    else:
        print(f"{issues} issues detected that may need attention.")
