"""
Quick test: Validate direct page navigation using confirmed selector

This test:
1. Opens Estado RJ page
2. Jumps directly to page 100
3. Verifies we arrived at the correct page
"""

from playwright.sync_api import sync_playwright
import time
import re
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="INFO")


def quick_navigation_test():
    """Quick test of page navigation"""

    logger.info("="*80)
    logger.info("🚀 Quick Navigation Test - Page 1 → 100")
    logger.info("="*80)

    # Using confirmed selector
    PAGE_SELECTOR = 'input[ng-model="vm.PaginaText"]'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # Navigate
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1"
            logger.info(f"\n📄 Opening Estado RJ page...")
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)  # Wait for AngularJS

            # Verify page loaded
            logger.info("✅ Page loaded")

            # Find page input
            logger.info(f"\n🔍 Looking for input with selector: {PAGE_SELECTOR}")
            page_input = page.query_selector(PAGE_SELECTOR)

            if not page_input:
                logger.error("❌ Page input not found!")
                return False

            current_value = page_input.input_value()
            logger.info(f"✅ Found! Current page: {current_value}")

            # Navigate to page 100
            target_page = 100
            logger.info(f"\n🎯 Navigating to page {target_page}...")

            # Clear and fill
            page_input.click()
            page_input.fill('')
            page_input.fill(str(target_page))
            page_input.press('Enter')

            # Wait for navigation
            logger.info("⏳ Waiting for navigation...")
            page.wait_for_timeout(3000)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(2000)

            # Verify navigation
            logger.info("\n🔍 Verifying navigation...")

            # Check input value
            page_input_after = page.query_selector(PAGE_SELECTOR)
            new_value = page_input_after.input_value()
            logger.info(f"   Input field shows: {new_value}")

            if new_value == str(target_page):
                logger.info("   ✅ Input field updated correctly")
            else:
                logger.warning(f"   ⚠️  Input shows '{new_value}', expected '{target_page}'")

            # Check table content
            logger.info("\n📊 Checking table content...")
            rows = page.query_selector_all('tbody tr[ng-repeat-start]')
            logger.info(f"   Found {len(rows)} rows")

            if rows:
                first_row = rows[0]
                cells = first_row.query_selector_all('td')

                if len(cells) > 2:
                    ordem_text = cells[2].inner_text().strip()
                    logger.info(f"   First row ordem: {ordem_text}")

                    # Extract number
                    ordem_match = re.search(r'(\d+)', ordem_text)
                    if ordem_match:
                        ordem_num = int(ordem_match.group(1))

                        # Page 100 should show records 991-1000 (ordem ~993-1002)
                        expected_min = (target_page - 1) * 10 + 1
                        expected_max = target_page * 10

                        logger.info(f"   Expected ordem range: {expected_min}-{expected_max}")

                        if expected_min <= ordem_num <= expected_max + 10:
                            logger.info(f"   ✅ CONFIRMED! Ordem {ordem_num} is in expected range")
                            logger.info(f"\n🎉 SUCCESS! Navigation to page {target_page} works!")
                            logger.info("\n⏳ Browser will stay open for 15 seconds...")
                            time.sleep(15)
                            return True
                        else:
                            logger.warning(f"   ⚠️  Ordem {ordem_num} outside expected range")

            logger.warning("\n⚠️  Could not fully verify navigation")
            logger.info("\n⏳ Browser will stay open for 30 seconds for manual inspection...")
            time.sleep(30)
            return False

        except Exception as e:
            logger.error(f"\n❌ Test failed: {e}")
            logger.exception("Full traceback:")
            logger.info("\n⏳ Browser will stay open for 30 seconds...")
            time.sleep(30)
            return False

        finally:
            browser.close()


if __name__ == "__main__":
    logger.info("Starting quick navigation test...\n")
    result = quick_navigation_test()

    if result:
        logger.info("\n✅ TEST PASSED!")
        sys.exit(0)
    else:
        logger.error("\n❌ TEST FAILED!")
        sys.exit(1)
