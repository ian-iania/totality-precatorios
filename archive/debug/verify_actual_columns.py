#!/usr/bin/env python3
"""
Verify ACTUAL visible columns on TJRJ table
"""

from playwright.sync_api import sync_playwright
import time

def verify_columns():
    """Check what's ACTUALLY visible on the page"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Use the EXACT URL the user provided (Estado do Rio de Janeiro)
        url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1"
        print(f"\n🔍 Checking: {url}\n")

        page.goto(url, wait_until='networkidle')
        time.sleep(5)  # Wait for AngularJS

        # Get VISIBLE headers
        print("=" * 80)
        print("VISIBLE TABLE HEADERS (from thead)")
        print("=" * 80)

        headers = page.query_selector_all('thead th')
        visible_headers = []
        for i, header in enumerate(headers):
            text = header.inner_text().strip()
            is_visible = page.evaluate('(element) => element.offsetParent !== null', header)
            if text or is_visible:
                visible_headers.append((i, text))
                print(f"  Header {i:2d}: '{text}' (visible={is_visible})")

        # Get first data row
        print("\n" + "=" * 80)
        print("FIRST DATA ROW (all cells)")
        print("=" * 80)

        time.sleep(2)
        rows = page.query_selector_all('tbody tr')

        if rows and len(rows) > 0:
            first_row = rows[0]
            cells = first_row.query_selector_all('td')
            print(f"\nTotal cells: {len(cells)}\n")

            for i, cell in enumerate(cells):
                text = cell.inner_text().strip()
                is_visible = page.evaluate('(element) => element.offsetParent !== null', cell)
                preview = text[:60] + '...' if len(text) > 60 else text
                print(f"  Cell {i:2d}: '{preview}' (visible={is_visible})")

        # Also check what the user sees in browser
        print("\n" + "=" * 80)
        print("EXTRACTING SAMPLE ROW DATA")
        print("=" * 80)

        if rows and len(rows) > 0:
            row_data = {}
            first_row = rows[0]
            cells = first_row.query_selector_all('td')

            print("\nBased on visible cells:")
            for i, cell in enumerate(cells):
                text = cell.inner_text().strip()
                if text:  # Only show non-empty cells
                    print(f"  Cell {i}: {text}")

        time.sleep(2)
        browser.close()

if __name__ == '__main__':
    verify_columns()
