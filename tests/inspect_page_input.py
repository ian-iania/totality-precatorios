"""
Simple script to inspect the Estado RJ page and find the page input field

This script:
1. Opens the page
2. Waits longer for content
3. Captures screenshot
4. Dumps all input fields found
"""

from playwright.sync_api import sync_playwright
import time
import sys
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def inspect_page():
    """Inspect page and find all input fields"""

    logger.info("="*80)
    logger.info("🔍 Inspecting Estado RJ Page for Input Fields")
    logger.info("="*80)

    with sync_playwright() as p:
        logger.info("\n🚀 Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            # Navigate
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1"
            logger.info(f"\n📄 Navigating to: {url}")
            page.goto(url, wait_until='networkidle', timeout=60000)

            # Wait generously for AngularJS
            logger.info("⏳ Waiting for AngularJS to render (30 seconds)...")
            page.wait_for_timeout(30000)

            # Take screenshot
            screenshot_path = Path("output/estado_rj_page.png")
            screenshot_path.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")

            # Find all input fields
            logger.info("\n🔎 Finding all <input> elements on page...")
            inputs = page.query_selector_all('input')
            logger.info(f"Found {len(inputs)} input fields")

            # Inspect each input
            logger.info("\n" + "="*80)
            logger.info("INPUT FIELDS FOUND:")
            logger.info("="*80)

            for i, input_elem in enumerate(inputs, 1):
                try:
                    input_type = input_elem.get_attribute('type') or 'N/A'
                    input_name = input_elem.get_attribute('name') or 'N/A'
                    input_id = input_elem.get_attribute('id') or 'N/A'
                    input_class = input_elem.get_attribute('class') or 'N/A'
                    input_placeholder = input_elem.get_attribute('placeholder') or 'N/A'
                    input_value = input_elem.input_value() if input_elem.is_visible() else 'N/A'
                    is_visible = input_elem.is_visible()
                    is_enabled = input_elem.is_enabled()
                    ng_model = input_elem.get_attribute('ng-model') or 'N/A'

                    logger.info(f"\n[{i}] Input Field:")
                    logger.info(f"    type: {input_type}")
                    logger.info(f"    name: {input_name}")
                    logger.info(f"    id: {input_id}")
                    logger.info(f"    class: {input_class}")
                    logger.info(f"    placeholder: {input_placeholder}")
                    logger.info(f"    ng-model: {ng_model}")
                    logger.info(f"    value: {input_value}")
                    logger.info(f"    visible: {is_visible}")
                    logger.info(f"    enabled: {is_enabled}")

                    # If this looks like pagination input, highlight it
                    if ('page' in str(input_name).lower() or
                        'page' in str(input_id).lower() or
                        'página' in str(input_placeholder).lower() or
                        'page' in str(ng_model).lower()):
                        logger.info(f"    ⭐ POSSIBLE PAGE INPUT! ⭐")

                except Exception as e:
                    logger.warning(f"    Error inspecting input {i}: {e}")

            # Also check for pagination-related text
            logger.info("\n" + "="*80)
            logger.info("LOOKING FOR PAGINATION TEXT...")
            logger.info("="*80)

            body_text = page.inner_text('body')
            if 'Ir para' in body_text or 'página' in body_text:
                logger.info("✅ Found pagination-related text on page")
                # Find context around "Ir para"
                lines = body_text.split('\n')
                for i, line in enumerate(lines):
                    if 'Ir para' in line or ('página' in line.lower() and len(line) < 50):
                        logger.info(f"   Line {i}: {line.strip()}")
            else:
                logger.warning("⚠️  No 'Ir para página' text found")

            # Try to find pagination container
            logger.info("\n" + "="*80)
            logger.info("LOOKING FOR PAGINATION CONTAINERS...")
            logger.info("="*80)

            pagination_selectors = [
                '.pagination',
                'ul.pagination',
                'div.pagination',
                '[class*="pagination"]',
                '[class*="pager"]'
            ]

            for selector in pagination_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    logger.info(f"\n✅ Found {len(elements)} element(s) with selector: {selector}")
                    for idx, elem in enumerate(elements[:3], 1):  # Show first 3
                        try:
                            elem_html = elem.inner_html()
                            logger.info(f"   Element {idx} HTML (first 500 chars):")
                            logger.info(f"   {elem_html[:500]}...")
                        except:
                            pass

            logger.info("\n" + "="*80)
            logger.info("INSPECTION COMPLETE")
            logger.info("="*80)
            logger.info("Review the output above to find the page input field")
            logger.info(f"Screenshot saved to: {screenshot_path}")
            logger.info("\n⏳ Browser will stay open for 60 seconds for manual inspection...")
            time.sleep(60)

        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            logger.exception("Full traceback:")
            logger.info("\n⏳ Browser will stay open for 30 seconds...")
            time.sleep(30)

        finally:
            logger.info("\n🔚 Closing browser...")
            browser.close()


if __name__ == "__main__":
    inspect_page()
