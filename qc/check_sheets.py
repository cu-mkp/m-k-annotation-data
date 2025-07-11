#!/usr/bin/env python3
"""
Check available sheets in the Excel file
"""

import pandas as pd

def check_sheets():
    """Check available sheets in the Excel file"""
    excel_file = 'media-full-list-alt-text-permissions.xlsx'
    
    # Get sheet names
    xl_file = pd.ExcelFile(excel_file)
    sheet_names = xl_file.sheet_names
    
    print(f"Available sheets in {excel_file}:")
    for i, sheet in enumerate(sheet_names):
        print(f"  {i}: '{sheet}'")
    
    return sheet_names

if __name__ == "__main__":
    check_sheets()