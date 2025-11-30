#!/usr/bin/env python3
"""
Test extraction of a single record with detailed expanded fields logging
"""

import sys
sys.path.insert(0, '/Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles')

from playwright.sync_api import sync_playwright
import time

def test_one_record():
    """Extract one record and check expanded fields"""

    output = []
    output.append("="*80)
    output.append("SINGLE RECORD EXPANDED FIELDS TEST")
    output.append("="*80)
    output.append("")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            # Navigate to Estado do RJ - Especial
            url = "https://www3.tjrj.jus.br/precatorio/#/debtor-entity/1/regime/especial/pending"
            output.append(f"🌐 Navigating to: {url}")
            page.goto(url, wait_until='networkidle', timeout=60000)

            # Wait for table
            output.append("⏳ Waiting for table...")
            page.wait_for_selector("tbody tr[ng-repeat-start]", timeout=15000)
            page.wait_for_timeout(5000)
            output.append("✅ Table loaded")
            output.append("")

            # Get first row
            rows = page.query_selector_all('tbody tr[ng-repeat-start]')
            output.append(f"Found {len(rows)} rows")

            if len(rows) == 0:
                output.append("❌ No rows found!")
                print("\n".join(output))
                browser.close()
                return

            # Get first row data
            row = rows[0]
            cells = row.query_selector_all('td')
            output.append(f"First row has {len(cells)} cells")
            output.append(f"Number: {cells[7].inner_text().strip() if len(cells) > 7 else 'N/A'}")
            output.append("")

            # Find toggle button
            toggle_btn = row.query_selector('td.toggle-preca')
            if not toggle_btn:
                output.append("❌ Toggle button not found!")
            else:
                output.append("✅ Toggle button found")

                # Click to expand
                output.append("🖱️  Clicking toggle button...")
                toggle_btn.click()
                page.wait_for_timeout(1000)

                # Check for expanded content
                detail_containers = page.query_selector_all('td[colspan] .row-detail-container')
                output.append(f"Found {len(detail_containers)} detail containers")

                if len(detail_containers) > 0:
                    detail_div = detail_containers[0]
                    detail_table = detail_div.query_selector('table.table-condensed')

                    if detail_table:
                        output.append("✅ Detail table found!")
                        detail_rows = detail_table.query_selector_all('tbody tr')
                        output.append(f"Detail table has {len(detail_rows)} rows")
                        output.append("")
                        output.append("Expanded fields:")

                        for detail_row in detail_rows:
                            cells_detail = detail_row.query_selector_all('td')
                            if len(cells_detail) >= 2:
                                label = cells_detail[0].inner_text().strip()
                                value = cells_detail[1].inner_text().strip()
                                output.append(f"  {label}: {value or '(empty)'}")

                        output.append("")
                        output.append("✅ SUCCESS: Expanded fields extracted!")
                    else:
                        output.append("❌ Detail table not found")
                else:
                    output.append("❌ No detail containers found")

            # Write results
            result_text = "\n".join(output)
            print(result_text)

            with open('test_one_record_output.txt', 'w') as f:
                f.write(result_text)

            output.append("")
            output.append(f"📄 Results written to: test_one_record_output.txt")

            time.sleep(3)

        except Exception as e:
            output.append(f"❌ Error: {e}")
            import traceback
            output.append(traceback.format_exc())

        finally:
            browser.close()

    final_output = "\n".join(output)
    print(final_output)

    with open('test_one_record_output.txt', 'w') as f:
        f.write(final_output)

if __name__ == '__main__':
    test_one_record()
