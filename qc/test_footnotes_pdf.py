#!/usr/bin/env python3
"""
Quick test script for footnotes PDF conversion
"""

import os
import sys
from convert_to_pdf_epub_footnotes import prepare_html_for_conversion, convert_to_pdf

def test_footnotes_conversion(filename):
    """Test footnotes PDF conversion for a single HTML file"""
    
    # Paths
    html_dir = '../html'
    html_file = os.path.join(html_dir, filename)
    css_file = 'academic-print-footnotes.css'
    output_file = f'./test_footnotes_{os.path.splitext(filename)[0]}.pdf'
    
    # Check if files exist
    if not os.path.exists(html_file):
        print(f"Error: HTML file not found: {html_file}")
        return False
    
    if not os.path.exists(css_file):
        print(f"Error: CSS file not found: {css_file}")
        return False
    
    try:
        print(f"Converting {filename} to PDF with footnotes...")
        
        # Prepare HTML content
        print("  1. Preparing HTML content and converting endnotes to footnotes...")
        prepared_html = prepare_html_for_conversion(html_file, css_file, html_dir)
        
        # Convert to PDF
        print("  2. Converting to PDF...")
        success = convert_to_pdf(prepared_html, output_file)
        
        if success:
            print(f"  ✓ PDF created successfully: {output_file}")
            
            # Check file size
            size = os.path.getsize(output_file)
            print(f"  📄 File size: {size:,} bytes ({size/1024:.1f} KB)")
            return True
        else:
            print("  ✗ PDF conversion failed")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

if __name__ == "__main__":
    filename = "ann_310_ie_19.html"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if not filename.endswith('.html'):
            filename += '.html'
    
    print(f"Testing footnotes PDF conversion for: {filename}")
    success = test_footnotes_conversion(filename)
    
    if success:
        print("\n✅ Footnotes test completed successfully!")
        print("📝 The PDF should now have footnotes at the bottom of each page instead of endnotes.")
    else:
        print("\n❌ Footnotes test failed!")
        sys.exit(1)