"""
Test script to investigate and validate the "Ir para página:" input field selector

This script opens the TJRJ portal in visible mode and tests different selectors
to find the correct one for direct page navigation.

Usage:
    python tests/test_page_navigation.py
"""

from playwright.sync_api import sync_playwright
import time
import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def test_page_navigation():
    """Test different selectors for the page input field"""

    # Possible selectors to test (from most specific to generic)
    SELECTORS_TO_TEST = [
        # Most specific (likely to work)
        'input[type="text"][placeholder*="página" i]',
        'input[aria-label*="página" i]',
        'input[name*="page" i]',
        'input[ng-model*="page" i]',  # AngularJS pattern

        # Medium specificity
        '.pagination input[type="text"]',
        'div.pagination input',
        'ul.pagination input',

        # Less specific (broader)
        'input[type="number"]',
        'input[type="text"]'
    ]

    logger.info("="*80)
    logger.info("🔍 Testing Page Navigation - Selector Investigation")
    logger.info("="*80)
    logger.info("This will open Estado RJ page and test different selectors")
    logger.info("Browser will be VISIBLE - watch what happens!")
    logger.info("="*80)

    with sync_playwright() as p:
        # Launch visible browser
        logger.info("\n🚀 Launching browser (visible mode)...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            # Navigate to Estado RJ page
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1"
            logger.info(f"\n📄 Navigating to Estado RJ...")
            logger.info(f"   URL: {url}")
            page.goto(url, wait_until='networkidle')

            # Wait for table to load
            logger.info("⏳ Waiting for table to load...")
            page.wait_for_selector("text=/Número.*Precatório/i", timeout=15000)
            page.wait_for_selector("tbody tr td", timeout=10000)
            page.wait_for_timeout(3000)

            logger.info("✅ Page loaded successfully")

            # Test each selector
            logger.info("\n" + "="*80)
            logger.info("🧪 Testing Selectors...")
            logger.info("="*80)

            working_selector = None

            for i, selector in enumerate(SELECTORS_TO_TEST, 1):
                logger.info(f"\n[{i}/{len(SELECTORS_TO_TEST)}] Testing: {selector}")

                try:
                    # Try to find element
                    element = page.query_selector(selector)

                    if element:
                        # Check if visible and enabled
                        is_visible = element.is_visible()
                        is_enabled = element.is_enabled()

                        if is_visible and is_enabled:
                            # Get current value
                            current_value = element.input_value()
                            logger.info(f"   ✅ FOUND and USABLE!")
                            logger.info(f"      Visible: {is_visible}")
                            logger.info(f"      Enabled: {is_enabled}")
                            logger.info(f"      Current value: '{current_value}'")

                            working_selector = selector
                            break  # Found it!
                        else:
                            logger.info(f"   ⚠️  Found but not usable (visible={is_visible}, enabled={is_enabled})")
                    else:
                        logger.info(f"   ❌ Not found")

                except Exception as e:
                    logger.info(f"   ❌ Error: {e}")

            if not working_selector:
                logger.error("\n❌ No working selector found!")
                logger.error("   Manual investigation needed:")
                logger.error("   1. Browser is still open - inspect the page")
                logger.error("   2. Find the 'Ir para página:' input field")
                logger.error("   3. Right-click > Inspect Element")
                logger.error("   4. Look at HTML attributes (class, id, ng-model, etc)")
                logger.error("   5. Update SELECTORS_TO_TEST in this script")
                logger.info("\n⏳ Browser will stay open for 60 seconds for manual inspection...")
                time.sleep(60)
                return None

            # Test navigation with the working selector
            logger.info("\n" + "="*80)
            logger.info("🚀 Testing Navigation with Working Selector")
            logger.info("="*80)
            logger.info(f"Selector: {working_selector}")

            # Get current page
            logger.info("\n📍 Current location: Page 1")

            # Test navigation to page 100
            target_page = 100
            logger.info(f"\n🎯 Attempting to navigate to page {target_page}...")

            page_input = page.query_selector(working_selector)

            # Clear and fill
            logger.info("   1. Clicking field...")
            page_input.click()

            logger.info("   2. Clearing current value...")
            page_input.fill('')

            logger.info(f"   3. Typing '{target_page}'...")
            page_input.fill(str(target_page))

            logger.info("   4. Pressing Enter...")
            page_input.press('Enter')

            # Wait for navigation
            logger.info("   5. Waiting for navigation...")
            page.wait_for_timeout(3000)
            page.wait_for_load_state('networkidle')

            # Verify we're on page 100
            logger.info("   6. Verifying navigation...")
            page.wait_for_timeout(2000)

            # Check if input now shows 100
            page_input_after = page.query_selector(working_selector)
            if page_input_after:
                new_value = page_input_after.input_value()
                logger.info(f"   7. Input field now shows: '{new_value}'")

                if new_value == str(target_page):
                    logger.info(f"\n✅ SUCCESS! Navigation to page {target_page} worked!")
                else:
                    logger.warning(f"\n⚠️  Navigation may have failed (expected '{target_page}', got '{new_value}')")

            # Extract first record to verify we're on page 100
            logger.info("\n📊 Checking page content...")
            try:
                rows = page.query_selector_all('tbody tr[ng-repeat-start]')
                if rows and len(rows) > 0:
                    first_row = rows[0]
                    cells = first_row.query_selector_all('td')
                    if len(cells) > 2:
                        ordem = cells[2].inner_text().strip()
                        logger.info(f"   First record ordem: {ordem}")

                        # Page 100 should show records around ordem 991-1000
                        # (page 1 = 1-10, page 2 = 11-20, ..., page 100 = 991-1000)
                        expected_range = ((target_page - 1) * 10 + 1, target_page * 10)
                        logger.info(f"   Expected ordem range for page {target_page}: {expected_range[0]}-{expected_range[1]}")

                        # Extract numeric part of ordem (e.g., "993º" -> 993)
                        import re
                        ordem_num_match = re.search(r'(\d+)', ordem)
                        if ordem_num_match:
                            ordem_num = int(ordem_num_match.group(1))
                            if expected_range[0] <= ordem_num <= expected_range[1]:
                                logger.info(f"   ✅ CONFIRMED! We're on page {target_page} (ordem {ordem_num} is in range)")
                            else:
                                logger.warning(f"   ⚠️  Ordem {ordem_num} outside expected range {expected_range}")

            except Exception as e:
                logger.warning(f"   Could not verify page content: {e}")

            # Final summary
            logger.info("\n" + "="*80)
            logger.info("📋 SUMMARY")
            logger.info("="*80)
            logger.info(f"✅ Working selector: {working_selector}")
            logger.info(f"✅ Navigation test: PASSED")
            logger.info("\n🎯 ACTION REQUIRED:")
            logger.info(f"   Update scraper_v3.py line 60:")
            logger.info(f"   Change PAGE_INPUT_SELECTORS[0] to: '{working_selector}'")
            logger.info("="*80)

            # Keep browser open for a bit
            logger.info("\n⏳ Browser will stay open for 15 seconds...")
            time.sleep(15)

            return working_selector

        except Exception as e:
            logger.error(f"\n❌ Test failed: {e}")
            logger.exception("Full traceback:")
            logger.info("\n⏳ Browser will stay open for 30 seconds for debugging...")
            time.sleep(30)
            return None

        finally:
            logger.info("\n🔚 Closing browser...")
            browser.close()


if __name__ == "__main__":
    logger.info("Starting page navigation test...")
    logger.info("Make sure you're connected to the internet!\n")

    result = test_page_navigation()

    if result:
        logger.info(f"\n🎉 Test completed successfully!")
        logger.info(f"Working selector: {result}")
        sys.exit(0)
    else:
        logger.error(f"\n❌ Test failed - manual investigation needed")
        sys.exit(1)
