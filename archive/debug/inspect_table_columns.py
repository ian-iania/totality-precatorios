#!/usr/bin/env python3
"""
Inspect actual table columns on TJRJ website
"""

from playwright.sync_api import sync_playwright
import time

def inspect_table():
    """Check what columns are actually in the table"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Go to INSS entity page (has lots of data)
        url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=86"
        print(f"\n🔍 Inspecting table at: {url}\n")

        page.goto(url, wait_until='networkidle')
        time.sleep(3)

        # Find table headers
        print("=" * 80)
        print("TABLE HEADERS")
        print("=" * 80)

        headers = page.query_selector_all('thead th')
        print(f"\nFound {len(headers)} header cells:\n")

        for i, header in enumerate(headers):
            text = header.inner_text().strip()
            print(f"  Column {i:2d}: '{text}'")

        # Check first data row
        print("\n" + "=" * 80)
        print("FIRST DATA ROW")
        print("=" * 80)

        rows = page.query_selector_all('tbody tr')
        if rows and len(rows) > 0:
            first_row = rows[0]
            cells = first_row.query_selector_all('td')
            print(f"\nFound {len(cells)} data cells:\n")

            for i, cell in enumerate(cells):
                text = cell.inner_text().strip()
                preview = text[:50] + '...' if len(text) > 50 else text
                print(f"  Cell {i:2d}: '{preview}'")

        # Take screenshot
        page.screenshot(path='data/debug/table_structure.png', full_page=True)
        print(f"\n📸 Screenshot saved to: data/debug/table_structure.png")

        input("\n👀 Press Enter to close browser...")
        browser.close()

if __name__ == '__main__':
    inspect_table()
