#!/usr/bin/env python3
"""
PDF and EPUB Converter for HTML Files

This tool converts HTML files to attractive PDFs and EPUBs using professional 
academic styling with enhanced footnote formatting.

Key Features:
- Enhanced frontmatter with metadata from JSON files
- Professional typography optimized for academic content
- Improved superscript formatting for footnote references
- Enhanced endnotes styling
- Batch processing capabilities
- WeasyPrint for high-quality PDF generation

Usage:
    python convert_to_pdf_epub.py [--pdf-only] [--epub-only] [--output-dir OUTPUT]
"""
import os
import sys
import argparse
import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import weasyprint
from bs4 import BeautifulSoup
import shutil

def check_dependencies():
    """
    Check if required dependencies are installed.
    
    Returns:
        tuple: (missing_python_deps, missing_system_deps)
    """
    missing_python = []
    missing_system = []
    
    # Check Python dependencies
    try:
        import weasyprint
    except ImportError:
        missing_python.append("weasyprint")
    
    try:
        import bs4
    except ImportError:
        missing_python.append("beautifulsoup4")
    
    # Check system dependencies
    try:
        subprocess.run(['pandoc', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_system.append("pandoc")
    
    return missing_python, missing_system

def load_metadata(html_dir: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load annotations and authors metadata from JSON files.
    
    Args:
        html_dir (str): Directory containing the JSON files
        
    Returns:
        tuple: (annotations_data, authors_data)
    """
    annotations_file = os.path.join(html_dir, 'annotations.json')
    authors_file = os.path.join(html_dir, 'authors.json')
    
    annotations_data = {}
    authors_data = {}
    
    try:
        if os.path.exists(annotations_file):
            with open(annotations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert list to dict indexed by ID
                if 'content' in data:
                    annotations_data = {item['id']: item for item in data['content']}
    except Exception as e:
        print(f"Warning: Could not load annotations.json: {e}")
    
    try:
        if os.path.exists(authors_file):
            with open(authors_file, 'r', encoding='utf-8') as f:
                authors_data = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load authors.json: {e}")
    
    return annotations_data, authors_data

def create_frontmatter(annotation_id: str, annotations_data: Dict[str, Any], 
                      authors_data: Dict[str, Any]) -> str:
    """
    Create enhanced frontmatter HTML for the document.
    
    Args:
        annotation_id (str): The annotation ID (extracted from filename)
        annotations_data (dict): Loaded annotations metadata
        authors_data (dict): Loaded authors metadata
        
    Returns:
        str: HTML frontmatter content
    """
    if annotation_id not in annotations_data:
        return ""
    
    annotation = annotations_data[annotation_id]
    
    # Build author information
    author_info = []
    for author_id in annotation.get('authorIDs', []):
        if author_id in authors_data:
            author = authors_data[author_id]
            author_name = author.get('fullName', '')
            author_type = author.get('authorType', '')
            if author_name and author_type:
                author_info.append(f"{author_name}<br><em>{author_type}</em>")
            elif author_name:
                author_info.append(author_name)
    
    # Extract abstract text (remove HTML tags for cleaner display)
    abstract = annotation.get('abstract', '')
    if abstract:
        # Parse HTML and extract text, but keep basic formatting
        abstract_soup = BeautifulSoup(abstract, 'html.parser')
        # Remove <mark> tags but keep content
        for mark in abstract_soup.find_all('mark'):
            mark.unwrap()
        abstract = str(abstract_soup)
    
    # Build frontmatter HTML
    frontmatter_parts = []
    
    # Title page
    full_title = annotation.get('fullTitle', annotation.get('name', ''))
    year = annotation.get('year', '')
    if full_title:
        frontmatter_parts.append(f'<div class="title-page">')
        frontmatter_parts.append(f'<h1 class="document-title">{full_title}</h1>')
        
        # Authors side by side
        if author_info:
            frontmatter_parts.append('<div class="authors-container">')
            for author in author_info:
                frontmatter_parts.append(f'<div class="author">{author}</div>')
            frontmatter_parts.append('</div>')
        
        # Year on title page
        if year:
            frontmatter_parts.append(f'<div class="title-year">{year}</div>')
        
        frontmatter_parts.append('</div>')
    
    # Citation page (verso)
    cite_as = annotation.get('citeAs', '')
    doi = annotation.get('doi', '')
    if cite_as or doi:
        frontmatter_parts.append('<div class="citation-page">')
        
        if cite_as:
            frontmatter_parts.append('<div class="citation-section">')
            frontmatter_parts.append('<h3>How to Cite</h3>')
            frontmatter_parts.append(f'<p class="citation-text">{cite_as}</p>')
            frontmatter_parts.append('</div>')
        
        if doi:
            frontmatter_parts.append(f'<div class="doi-section"><strong>DOI:</strong> <a href="{doi}">{doi}</a></div>')
        
        frontmatter_parts.append('</div>')
    
    # Abstract on separate page
    if abstract:
        frontmatter_parts.append('<div class="abstract-page">')
        frontmatter_parts.append('<h3>Abstract</h3>')
        frontmatter_parts.append(f'<div class="abstract-text">{abstract}</div>')
        frontmatter_parts.append('</div>')
    
    # Add page break before main content
    frontmatter_parts.append('<div class="page-break"></div>')
    
    return '\n'.join(frontmatter_parts)

def convert_to_pdf(html_content: str, output_path: str) -> bool:
    """
    Convert HTML content to PDF using WeasyPrint.
    
    Args:
        html_content (str): HTML content to convert
        output_path (str): Path where PDF should be saved
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Create WeasyPrint HTML document
        html_doc = weasyprint.HTML(string=html_content, base_url=os.getcwd())
        
        # Generate PDF
        html_doc.write_pdf(output_path)
        return True
        
    except Exception as e:
        print(f"PDF conversion error: {e}")
        return False

def convert_to_epub(html_file_path: str, output_path: str, temp_dir: str) -> bool:
    """
    Convert HTML file to EPUB using Pandoc.
    
    Args:
        html_file_path (str): Path to the HTML file
        output_path (str): Path where EPUB should be saved
        temp_dir (str): Temporary directory for intermediate files
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Use pandoc to convert HTML to EPUB
        cmd = [
            'pandoc',
            html_file_path,
            '-o', output_path,
            '--epub-metadata=<dc:language>en</dc:language>',
            '--epub-cover-image=', # Empty to disable default cover
            '--self-contained'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            print(f"Pandoc error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"EPUB conversion error: {e}")
        return False

def link_figure_references(soup: BeautifulSoup) -> int:
    """
    Link figure references to their corresponding figures.
    
    This function:
    1. Finds all figure references in text (e.g., "Fig. 1", "Figure 2")
    2. Finds all figures with captions
    3. Creates proper links between references and figures
    4. Adds IDs to figures if missing
    
    Args:
        soup (BeautifulSoup): Parsed HTML document
        
    Returns:
        int: Number of figure references linked
    """
    import re
    
    # Find all figures and assign IDs
    figures = soup.find_all('figure')
    figure_map = {}  # Maps figure number to figure element
    
    for figure in figures:
        figcaption = figure.find('figcaption')
        if figcaption:
            caption_text = figcaption.get_text()
            # Look for figure number in caption (Fig. 1, Figure 2, etc.)
            fig_match = re.search(r'Fig\.?\s*(\d+)', caption_text, re.IGNORECASE)
            if fig_match:
                fig_num = fig_match.group(1)
                figure_id = f"figure-{fig_num}"
                figure['id'] = figure_id
                figure_map[fig_num] = figure
    
    # Find figure references in text and link them
    linked_count = 0
    
    # Look for figure references in various formats
    patterns = [
        r'<i><u>Fig\.?\s*(\d+)</u></i>',  # <i><u>Fig. 1</u></i>
        r'Fig\.?\s*(\d+)',               # Fig. 1 or Figure 1
        r'Figure\s+(\d+)',               # Figure 1
    ]
    
    # Get all text content and search for patterns
    body_content = str(soup.body) if soup.body else str(soup)
    
    for pattern in patterns:
        matches = re.finditer(pattern, body_content, re.IGNORECASE)
        for match in matches:
            fig_num = match.group(1)
            if fig_num in figure_map:
                # Find the actual element in the soup
                full_match = match.group(0)
                
                # Look for the text in the soup and replace with linked version
                for element in soup.find_all(text=re.compile(re.escape(full_match), re.IGNORECASE)):
                    parent = element.parent
                    if parent:
                        # Create new linked version
                        new_link = soup.new_tag('a', href=f"#figure-{fig_num}")
                        new_link['class'] = 'figure-ref'
                        
                        # Handle different formats
                        if '<i><u>' in full_match:
                            new_i = soup.new_tag('i')
                            new_u = soup.new_tag('u')
                            new_u.string = re.sub(r'<[^>]+>', '', full_match)
                            new_i.append(new_u)
                            new_link.append(new_i)
                        else:
                            new_link.string = full_match
                        
                        # Replace the text with linked version
                        element.replace_with(new_link)
                        linked_count += 1
    
    # Handle specific markup patterns more carefully
    for element in soup.find_all(['i', 'u', 'em', 'strong']):
        if element.get_text():
            text = element.get_text()
            fig_match = re.search(r'Fig\.?\s*(\d+)', text, re.IGNORECASE)
            if fig_match:
                fig_num = fig_match.group(1)
                if fig_num in figure_map and not element.find('a'):  # Don't double-link
                    # Wrap in link
                    link = soup.new_tag('a', href=f"#figure-{fig_num}")
                    link['class'] = 'figure-ref'
                    element.wrap(link)
                    linked_count += 1
    
    return linked_count

def add_figure_backlinks(soup: BeautifulSoup) -> int:
    """
    Add back-links from figures to their references in the text.
    
    This function:
    1. Finds all figures with IDs
    2. For each figure, finds text references that link to it
    3. Adds a back-link list in the figure caption
    
    Args:
        soup (BeautifulSoup): Parsed HTML document
        
    Returns:
        int: Number of back-links added
    """
    backlinks_added = 0
    
    # Find all figures with IDs
    figures = soup.find_all('figure', id=True)
    
    for figure in figures:
        figure_id = figure.get('id')
        if not figure_id:
            continue
        
        # Find all links that reference this figure
        refs = soup.find_all('a', href=f"#{figure_id}")
        
        if refs:
            # Create subtle back-link elements
            figcaption = figure.find('figcaption')
            if figcaption:
                # Add subtle back-links after the caption text
                backlink_container = soup.new_tag('span', class_='figure-backlinks')
                
                for i, ref in enumerate(refs):
                    if i > 0:
                        backlink_container.append(" ")
                    
                    # Create back-link to the reference location
                    # Try to find a nearby element we can reference
                    ref_parent = ref.parent
                    ref_id = None
                    
                    # Look for an ID in the reference or its ancestors
                    for ancestor in [ref] + list(ref.parents)[:3]:  # Check ref and up to 3 ancestors
                        if ancestor.get('id'):
                            ref_id = ancestor.get('id')
                            break
                    
                    # If no ID found, create one for the paragraph containing the reference
                    if not ref_id and ref_parent and ref_parent.name in ['p', 'div', 'section']:
                        ref_id = f"ref-to-{figure_id}-{i+1}"
                        ref_parent['id'] = ref_id
                    
                    # Create subtle back-link (just an arrow)
                    backlink = soup.new_tag('a', href=f"#{ref_id}" if ref_id else "#")
                    backlink['class'] = 'figure-backlink'
                    backlink['title'] = f'Go to reference {i+1}'
                    backlink.string = "↑"
                    backlink_container.append(backlink)
                
                # Add a space before the back-links
                figcaption.append(" ")
                figcaption.append(backlink_container)
                backlinks_added += 1
    
    return backlinks_added

def add_footnote_backlinks(soup: BeautifulSoup) -> int:
    """
    Add enhanced back-links from endnotes to their references in the text.
    
    This function enhances existing footnote back-links and adds multiple 
    back-links if a footnote is referenced multiple times.
    
    Args:
        soup (BeautifulSoup): Parsed HTML document
        
    Returns:
        int: Number of enhanced back-links added
    """
    enhanced_backlinks = 0
    
    # Find footnotes section
    footnotes_section = soup.find('div', class_='footnotes') or soup.find('section', id='footnotes')
    if not footnotes_section:
        return 0
    
    # Find all footnote items
    footnote_items = footnotes_section.find_all('li', id=True)
    
    for item in footnote_items:
        fn_id = item.get('id')
        if not fn_id or not fn_id.startswith('fn'):
            continue
        
        # Find all references to this footnote in the text
        fn_refs = soup.find_all('a', href=f"#{fn_id}")
        
        if len(fn_refs) > 1:
            # Multiple references - enhance the back-link
            existing_backlink = item.find('a', class_='footnote-back')
            if existing_backlink:
                # Replace single back-link with multiple back-links
                backlink_container = soup.new_tag('span', class_='multiple-backlinks')
                backlink_container.string = " ["
                
                for i, ref in enumerate(fn_refs):
                    if i > 0:
                        backlink_container.append(", ")
                    
                    # Create back-link to the footnote reference in text
                    # The standard pattern is fnrefX for footnote X
                    fn_number = fn_id[2:]  # Remove 'fn' prefix
                    ref_id = f"fnref{fn_number}"
                    if i > 0:
                        ref_id += f"-{i+1}"  # For multiple references
                    
                    # Create individual back-link
                    backlink = soup.new_tag('a', href=f"#{ref_id}")
                    backlink['class'] = 'footnote-backlink'
                    backlink.string = f"↩{i+1}" if i > 0 else "↩"
                    backlink_container.append(backlink)
                
                backlink_container.append("]")
                existing_backlink.replace_with(backlink_container)
                enhanced_backlinks += 1
        
        elif len(fn_refs) == 1:
            # Single reference - enhance existing back-link style and ensure correct href
            existing_backlink = item.find('a', class_='footnote-back')
            if existing_backlink:
                # Ensure the href points to the correct fnref ID
                fn_number = fn_id[2:]  # Remove 'fn' prefix
                existing_backlink['href'] = f"#fnref{fn_number}"
                existing_backlink['class'] = 'footnote-backlink enhanced'
                enhanced_backlinks += 1
    
    return enhanced_backlinks

def clean_external_links(soup: BeautifulSoup) -> int:
    """
    Clean up external links to remove URL display in text while maintaining hyperlinks.
    
    This function:
    1. Finds all external links (http/https)
    2. Removes URL display from link text if the text is just the URL
    3. Keeps meaningful link text intact
    4. Ensures links remain clickable
    
    Args:
        soup (BeautifulSoup): Parsed HTML document
        
    Returns:
        int: Number of external links cleaned
    """
    import re
    
    cleaned_count = 0
    
    # Find all external links
    external_links = soup.find_all('a', href=re.compile(r'^https?://'))
    
    for link in external_links:
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        # Skip if link has no text or already has meaningful text
        if not link_text:
            continue
        
        # Check if the link text is just the URL or a slightly modified URL
        if (link_text == href or 
            link_text.replace('http://', '').replace('https://', '') == href.replace('http://', '').replace('https://', '') or
            link_text.startswith('http')):
            
            # Try to create meaningful link text from the URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(href)
                domain = parsed.netloc
                
                # Remove www. prefix
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                # Create clean link text
                if 'doi.org' in domain:
                    link.string = 'DOI Link'
                elif 'jstor.org' in domain:
                    link.string = 'JSTOR'
                elif 'archive.org' in domain:
                    link.string = 'Internet Archive'
                elif 'wikipedia.org' in domain:
                    link.string = 'Wikipedia'
                elif 'makingandknowing.org' in domain:
                    link.string = 'Making and Knowing Project'
                elif 'edition640.makingandknowing.org' in domain:
                    link.string = 'Edition 640'
                elif 'creativecommons.org' in domain:
                    link.string = 'Creative Commons'
                else:
                    # Use domain name as link text
                    link.string = domain
                
                cleaned_count += 1
                
            except Exception:
                # If URL parsing fails, use generic text
                link.string = 'External Link'
                cleaned_count += 1
        
        # Handle links that are inside other elements and might show URLs
        elif len(link_text) > 50 and 'http' in link_text:
            # Very long link text that contains URLs - try to clean it
            clean_text = re.sub(r'https?://[^\s<>"]+', '', link_text).strip()
            if clean_text and len(clean_text) > 3:
                link.string = clean_text
                cleaned_count += 1
    
    return cleaned_count

def prepare_html_for_conversion(html_file_path: str, css_file_path: str, 
                               html_dir: str = None) -> str:
    """
    Prepare HTML file for conversion with improved footnote formatting.
    
    This version:
    1. Parses the HTML file
    2. Improves footnote reference formatting (ensures proper superscript)
    3. Enhances endnotes section styling
    4. Injects the academic CSS stylesheet
    5. Optimizes the document structure for PDF/EPUB
    
    Args:
        html_file_path (str): Path to the HTML file to process
        css_file_path (str): Path to the CSS stylesheet
        html_dir (str): Directory containing HTML files and metadata (optional)
        
    Returns:
        str: Modified HTML content ready for conversion
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Load metadata if html_dir is provided
    annotations_data = {}
    authors_data = {}
    if html_dir:
        annotations_data, authors_data = load_metadata(html_dir)
    
    # Extract annotation ID from filename
    filename = os.path.basename(html_file_path)
    annotation_id = os.path.splitext(filename)[0]
    
    # Ensure proper HTML structure
    if not soup.html:
        new_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
        if soup.head:
            new_soup.head.replace_with(soup.head)
        if soup.body:
            new_soup.body.replace_with(soup.body)
        else:
            for element in soup.contents:
                if hasattr(element, 'name'):
                    new_soup.body.append(element.extract())
        soup = new_soup
    
    # Ensure head section exists
    if not soup.head:
        head = soup.new_tag('head')
        soup.html.insert(0, head)
    
    # Add UTF-8 meta tag
    meta_charset = soup.find('meta', attrs={'charset': True})
    if not meta_charset:
        meta = soup.new_tag('meta', charset='utf-8')
        soup.head.insert(0, meta)
    
    # Add viewport meta for responsive design
    meta_viewport = soup.find('meta', attrs={'name': 'viewport'})
    if not meta_viewport:
        meta = soup.new_tag('meta', 
                           attrs={'name': 'viewport', 
                                 'content': 'width=device-width, initial-scale=1.0'})
        soup.head.append(meta)
    
    # Read and embed CSS
    with open(css_file_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Remove any existing links to external stylesheets
    for link in soup.find_all('link', rel='stylesheet'):
        link.decompose()
    
    # Add our CSS as an embedded stylesheet
    style_tag = soup.new_tag('style', type='text/css')
    style_tag.string = css_content
    soup.head.append(style_tag)
    
    # Improve footnote formatting (keep as endnotes but enhance styling)
    print("  Improving footnote formatting...")
    
    # Find and enhance footnote references
    footnote_refs = soup.find_all('a', class_='footnote-ref')
    if footnote_refs:
        print(f"    Found {len(footnote_refs)} footnote references")
        for ref in footnote_refs:
            # Ensure proper superscript formatting
            sup_elem = ref.find('sup')
            if sup_elem:
                # Add CSS class for consistent styling
                ref.attrs['class'] = ref.get('class', []) + ['enhanced-footnote-ref']
                sup_elem.attrs['class'] = sup_elem.get('class', []) + ['enhanced-footnote-sup']
    
    # Enhance footnotes section - look for both div and section elements
    footnotes_section = soup.find('div', class_='footnotes') or soup.find('section', id='footnotes')
    if footnotes_section:
        print(f"    Enhanced footnotes section")
        # Add enhanced class while preserving existing classes
        existing_classes = footnotes_section.get('class', [])
        if 'enhanced-footnotes' not in existing_classes:
            footnotes_section.attrs['class'] = existing_classes + ['enhanced-footnotes']
        
        # Add section title if missing
        h2_title = footnotes_section.find('h2')
        if not h2_title:
            title = soup.new_tag('h2')
            title.string = 'Notes'
            footnotes_section.insert(0, title)
    
    # Link figure references to figures
    print("  Linking figure references to figures...")
    figure_refs_count = link_figure_references(soup)
    if figure_refs_count > 0:
        print(f"    Linked {figure_refs_count} figure references")
    
    # Clean up external links (remove URL display in text)
    print("  Cleaning up external link display...")
    external_links_count = clean_external_links(soup)
    if external_links_count > 0:
        print(f"    Cleaned {external_links_count} external links")
    
    # Add bidirectional linking from figures to their references
    print("  Adding figure back-links...")
    figure_backlinks_count = add_figure_backlinks(soup)
    if figure_backlinks_count > 0:
        print(f"    Added back-links to {figure_backlinks_count} figures")
    
    # Add enhanced footnote back-links
    print("  Enhancing footnote back-links...")
    footnote_backlinks_count = add_footnote_backlinks(soup)
    if footnote_backlinks_count > 0:
        print(f"    Enhanced {footnote_backlinks_count} footnote back-links")
    
    # Create and insert enhanced frontmatter if metadata is available
    if annotations_data and annotation_id in annotations_data:
        frontmatter_html = create_frontmatter(annotation_id, annotations_data, authors_data)
        if frontmatter_html:
            frontmatter_soup = BeautifulSoup(frontmatter_html, 'html.parser')
            
            # Remove the existing simple title structure if present
            existing_h1 = soup.body.find('h1')
            existing_h4 = None
            if existing_h1:
                next_sibling = existing_h1.find_next_sibling()
                if next_sibling and next_sibling.name == 'h4':
                    existing_h4 = next_sibling
            
            # Insert frontmatter at the beginning of body
            for element in reversed(frontmatter_soup.contents):
                if hasattr(element, 'name'):
                    soup.body.insert(0, element)
            
            # Remove old title elements if they exist
            if existing_h1:
                existing_h1.decompose()
            if existing_h4:
                existing_h4.decompose()
    
    # Add a title if missing
    if not soup.title:
        title_tag = soup.new_tag('title')
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title_tag.string = h1.get_text(strip=True)
        else:
            filename = os.path.basename(html_file_path)
            title_tag.string = os.path.splitext(filename)[0].replace('_', ' ').title()
        soup.head.append(title_tag)
    
    # Convert relative image paths to absolute paths
    html_dir_path = os.path.dirname(html_file_path)
    for img in soup.find_all('img', src=True):
        src = img['src']
        if not src.startswith(('http://', 'https://', 'data:')):
            abs_path = os.path.abspath(os.path.join(html_dir_path, src))
            if os.path.exists(abs_path):
                img['src'] = f"file://{abs_path}"
            else:
                print(f"Warning: Image not found: {abs_path}")
    
    return str(soup)

def process_html_files(html_dir: str, output_dir: str, css_file: str, 
                      create_pdf: bool = True, create_epub: bool = True) -> Tuple[int, int, List[str]]:
    """
    Process all HTML files in the directory for conversion.
    
    Args:
        html_dir (str): Directory containing HTML files
        output_dir (str): Directory to save converted files
        css_file (str): Path to CSS stylesheet
        create_pdf (bool): Whether to create PDF files
        create_epub (bool): Whether to create EPUB files
        
    Returns:
        tuple: (successful_conversions, total_files, error_list)
    """
    # Find all HTML files
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    total_files = len(html_files)
    successful_conversions = 0
    errors = []
    
    print(f"Found {total_files} HTML files to convert")
    
    # Create output directories
    if create_pdf:
        pdf_dir = os.path.join(output_dir, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
    
    if create_epub:
        epub_dir = os.path.join(output_dir, 'epubs')
        os.makedirs(epub_dir, exist_ok=True)
    
    # Process each file
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, html_file in enumerate(html_files, 1):
            base_name = os.path.splitext(html_file)[0]
            html_path = os.path.join(html_dir, html_file)
            
            print(f"Processing {i}/{total_files}: {html_file}")
            
            try:
                # Prepare HTML content
                prepared_html = prepare_html_for_conversion(html_path, css_file, html_dir)
                
                # Create temporary HTML file for processing
                temp_html_path = os.path.join(temp_dir, f"{base_name}_prepared.html")
                with open(temp_html_path, 'w', encoding='utf-8') as f:
                    f.write(prepared_html)
                
                file_success = True
                
                # Convert to PDF
                if create_pdf:
                    pdf_path = os.path.join(pdf_dir, f"{base_name}.pdf")
                    if convert_to_pdf(prepared_html, pdf_path):
                        print(f"  ✓ PDF created: {pdf_path}")
                    else:
                        print(f"  ✗ PDF conversion failed")
                        errors.append(f"PDF conversion failed for {html_file}")
                        file_success = False
                
                # Convert to EPUB
                if create_epub:
                    epub_path = os.path.join(epub_dir, f"{base_name}.epub")
                    if convert_to_epub(temp_html_path, epub_path, temp_dir):
                        print(f"  ✓ EPUB created: {epub_path}")
                    else:
                        print(f"  ✗ EPUB conversion failed")
                        errors.append(f"EPUB conversion failed for {html_file}")
                        file_success = False
                
                if file_success:
                    successful_conversions += 1
                    
            except Exception as e:
                error_msg = f"Error processing {html_file}: {e}"
                print(f"  ✗ {error_msg}")
                errors.append(error_msg)
    
    return successful_conversions, total_files, errors

def main():
    """Main function that orchestrates the conversion process."""
    parser = argparse.ArgumentParser(description='Convert HTML files to PDF and EPUB formats with enhanced formatting')
    parser.add_argument('--pdf-only', action='store_true', 
                       help='Create only PDF files')
    parser.add_argument('--epub-only', action='store_true', 
                       help='Create only EPUB files')
    parser.add_argument('--output-dir', '-o', default='./converted_documents',
                       help='Output directory for converted files (default: ./converted_documents)')
    parser.add_argument('--html-dir', default='../html',
                       help='Directory containing HTML files (default: ../html)')
    
    args = parser.parse_args()
    
    # Determine what to create
    if args.pdf_only and args.epub_only:
        print("Error: Cannot specify both --pdf-only and --epub-only")
        sys.exit(1)
    
    create_pdf = not args.epub_only
    create_epub = not args.pdf_only
    
    # Check if directories exist
    html_dir = os.path.abspath(args.html_dir)
    if not os.path.exists(html_dir):
        print(f"Error: HTML directory not found: {html_dir}")
        sys.exit(1)
    
    css_file = os.path.join(os.path.dirname(__file__), 'academic-print.css')
    if not os.path.exists(css_file):
        print(f"Error: CSS file not found: {css_file}")
        sys.exit(1)
    
    # Check dependencies
    print("Checking dependencies...")
    missing_python, missing_system = check_dependencies()
    
    if missing_python:
        print(f"Missing Python packages: {', '.join(missing_python)}")
        print("Install with: pip install " + " ".join(missing_python))
        sys.exit(1)
    
    if missing_system:
        if create_epub and 'pandoc' in missing_system:
            print("Warning: pandoc not found. EPUB creation will be disabled.")
            create_epub = False
        if not create_pdf and not create_epub:
            print("No conversion tools available.")
            sys.exit(1)
    
    # Create output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting files from: {html_dir}")
    print(f"Output directory: {output_dir}")
    print(f"CSS stylesheet: {css_file}")
    print(f"Creating: {'PDF' if create_pdf else ''} {'EPUB' if create_epub else ''}")
    print("Special feature: Enhanced footnote formatting")
    print("=" * 60)
    
    # Process files
    successful, total, errors = process_html_files(
        html_dir, output_dir, css_file, create_pdf, create_epub
    )
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total HTML files: {total}")
    print(f"Successful conversions: {successful}")
    print(f"Failed conversions: {total - successful}")
    
    if errors:
        print(f"\nErrors encountered ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if successful > 0:
        print(f"\n✓ Converted files saved to: {output_dir}")
        if create_pdf:
            print(f"  PDFs: {os.path.join(output_dir, 'pdfs')}")
        if create_epub:
            print(f"  EPUBs: {os.path.join(output_dir, 'epubs')}")
    
    # Save detailed report
    report_path = os.path.join(output_dir, 'conversion_report.txt')
    with open(report_path, 'w') as f:
        f.write("PDF/EPUB Conversion Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"HTML directory: {html_dir}\n")
        f.write(f"Output directory: {output_dir}\n")
        f.write(f"CSS stylesheet: {css_file}\n")
        f.write(f"Formats created: {'PDF' if create_pdf else ''} {'EPUB' if create_epub else ''}\n")
        f.write("Special feature: Enhanced footnote formatting\n\n")
        f.write(f"Total files processed: {total}\n")
        f.write(f"Successful conversions: {successful}\n")
        f.write(f"Failed conversions: {total - successful}\n\n")
        
        if errors:
            f.write("Errors:\n")
            for error in errors:
                f.write(f"  - {error}\n")
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main()