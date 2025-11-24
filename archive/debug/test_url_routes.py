#!/usr/bin/env python3
"""Quick test to find the right URL for precatório details"""

from playwright.sync_api import sync_playwright
import time

def test_routes():
    """Test different routes to find precatório details"""

    routes = [
        "#!/ordem-cronologica",
        # "#!/precatorios-pagos",
        # "#!/ConsultaPagamentos",
        # "#!/ordem-prioridade",
    ]

    entity_id = 86  # INSS

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for route in routes:
            url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio{route}?idEntidadeDevedora={entity_id}"
            print(f"\n{'='*60}")
            print(f"Testing: {route}")
            print(f"URL: {url}")
            print('='*60)

            page.goto(url, wait_until='networkidle')
            page.wait_for_timeout(5000)  # Wait for AngularJS

            # Try to find table
            try:
                rows = page.query_selector_all('tbody tr')
                print(f"✅ Found {len(rows)} rows")

                if rows and len(rows) > 0:
                    # Get first row cells
                    first_row = rows[0]
                    cells = first_row.query_selector_all('td')
                    cell_texts = [c.inner_text().strip() for c in cells]  # ALL cells
                    print(f"📋 First row cells ({len(cells)} total):")
                    for i, text in enumerate(cell_texts):
                        preview = text[:80] + '...' if len(text) > 80 else text
                        print(f"   Cell {i:2d}: '{preview}'")

                    # Also check for specific keywords in row text
                    row_text = first_row.inner_text()
                    has_precatorio_num = any(char.isdigit() and '/' in row_text for char in row_text)
                    has_currency = 'R$' in row_text
                    print(f"\n   Keywords: precatorio_num={has_precatorio_num}, currency={has_currency}")
            except Exception as e:
                print(f"❌ Error: {e}")

        browser.close()

if __name__ == '__main__':
    test_routes()
