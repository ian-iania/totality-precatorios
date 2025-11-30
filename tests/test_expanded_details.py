#!/usr/bin/env python3
"""
Test script to extract expanded precatório details
Tests the +/- button functionality and detail extraction
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_expanded_details():
    """Test extraction of expanded precatório details"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Access Estado do Rio de Janeiro entity (ID=1)
        url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/ordem-cronologica?idEntidadeDevedora=1"
        print(f"\n🔍 Accessing: {url}\n")

        page.goto(url, wait_until='networkidle')
        time.sleep(5)

        print("=" * 80)
        print("TESTING EXPANDED DETAILS EXTRACTION")
        print("=" * 80)

        # Find all table rows
        rows = page.query_selector_all('tbody tr[ng-repeat-start]')
        print(f"\n✅ Found {len(rows)} precatório rows\n")

        # Test first 3 rows
        for i in range(min(3, len(rows))):
            row = rows[i]

            print(f"\n{'='*80}")
            print(f"PRECATÓRIO #{i+1}")
            print(f"{'='*80}")

            # Get basic info from main row
            cells = row.query_selector_all('td')
            cell_texts = [cell.inner_text().strip() for cell in cells]

            # Find visible columns (skip first cell which is toggle button)
            print(f"\n📋 Basic Info:")
            if len(cell_texts) > 1:
                # Based on HTML: ordem, entidade, numero, situacao, natureza, orcamento, valor_historico, saldo_atualizado
                # The exact indices depend on which columns are visible (ng-show conditions)
                print(f"  Row data: {cell_texts[1:8]}")  # Print first few cells

            # Find and click the toggle button
            toggle_btn = row.query_selector('td.toggle-preca')
            if toggle_btn:
                print(f"\n🖱️  Clicking expand button...")
                toggle_btn.click()
                time.sleep(1)  # Wait for expansion

                # The expanded row is the next sibling tr with ng-repeat-end
                # We need to query it from the page, not from current row
                # Get all rows again and find the detail row
                all_rows = page.query_selector_all('tbody tr')

                # Find the detail row - it should be right after the current row
                # Look for tr[ng-repeat-end] that contains the details table
                detail_container = page.query_selector_all('td[colspan] .row-detail-container')

                if len(detail_container) > i:
                    detail_div = detail_container[i]

                    # Find the details table inside
                    detail_table = detail_div.query_selector('table.table-condensed')

                    if detail_table:
                        # Get all rows from the details table (skip header)
                        detail_rows = detail_table.query_selector_all('tbody tr')

                        print(f"\n📄 Expanded Details ({len(detail_rows)} fields):")

                        details = {}
                        for detail_row in detail_rows:
                            cells = detail_row.query_selector_all('td')
                            if len(cells) >= 2:
                                label = cells[0].inner_text().strip()
                                value = cells[1].inner_text().strip()
                                details[label] = value
                                print(f"  {label}: {value}")

                        # Print structured data
                        print(f"\n📊 Structured Details:")
                        print(json.dumps(details, indent=2, ensure_ascii=False))
                    else:
                        print("  ❌ Detail table not found")
                else:
                    print("  ❌ Detail container not found")
            else:
                print("  ❌ Toggle button not found")

            print()

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

        time.sleep(3)
        browser.close()

if __name__ == '__main__':
    test_expanded_details()
