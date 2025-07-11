#!/usr/bin/env python3
"""
Test script for simple footnotes PDF conversion
"""

import os
import sys
from convert_to_pdf_epub_simple_footnotes import prepare_html_for_conversion, convert_to_pdf

def test_simple_footnotes(filename):
    """Test simple footnotes PDF conversion"""
    
    # Paths
    html_dir = '../html'
    html_file = os.path.join(html_dir, filename)
    css_file = 'academic-print-simple-footnotes.css'
    output_file = f'./test_simple_footnotes_{os.path.splitext(filename)[0]}.pdf'
    
    # Check if files exist
    if not os.path.exists(html_file):
        print(f"Error: HTML file not found: {html_file}")
        return False
    
    if not os.path.exists(css_file):
        print(f"Error: CSS file not found: {css_file}")
        return False
    
    try:
        print(f"Converting {filename} to PDF with enhanced footnote formatting...")
        
        # Prepare HTML content
        print("  1. Preparing HTML content with enhanced footnote formatting...")
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
    
    print(f"Testing simple footnotes PDF conversion for: {filename}")
    success = test_simple_footnotes(filename)
    
    if success:
        print("\n✅ Simple footnotes test completed successfully!")
        print("📝 The PDF should have improved footnote formatting with proper superscripts.")
    else:
        print("\n❌ Simple footnotes test failed!")
        sys.exit(1)