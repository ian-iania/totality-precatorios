"""
HTML Structure Capture Tool

Run this to capture the rendered HTML of TJRJ pages.
This will help Claude write the correct selectors.

Usage:
    python capture_html.py
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

def capture_page_structure(url: str, output_file: str, wait_selector: str = None):
    """Capture rendered HTML after JavaScript execution"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"📱 Navigating to: {url}")
        page.goto(url, wait_until='networkidle')
        page.wait_for_timeout(3000)

        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=10000)
                print(f"✅ Found selector: {wait_selector}")
            except:
                print(f"⚠️  Selector not found: {wait_selector}")

        # Get full rendered HTML
        html = page.content()

        # Save to file
        Path(output_file).write_text(html, encoding='utf-8')
        print(f"💾 Saved to: {output_file}")
        print(f"📊 Size: {len(html):,} characters")

        # Keep browser open for manual inspection
        input("\n👀 Inspect the page in browser, then press Enter to continue...")

        browser.close()

def main():
    print("=" * 60)
    print("🔍 TJRJ HTML Structure Capture Tool")
    print("=" * 60)

    # Capture main page
    print("\n1️⃣  Capturing main page...")
    capture_page_structure(
        "https://www.tjrj.jus.br/web/precatorios",
        "data/raw/main_page.html"
    )

    # Capture regime geral page
    print("\n2️⃣  Capturing regime geral page...")
    capture_page_structure(
        "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral",
        "data/raw/regime_geral.html",
        wait_selector="body"  # Update this after seeing the page
    )

    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print("\n📁 HTML files saved to data/raw/")
    print("\n🎯 Next steps:")
    print("   1. Open the HTML files")
    print("   2. Search for entity card patterns")
    print("   3. Share the relevant sections with Claude")
    print("   4. Claude will write the selectors!")

if __name__ == "__main__":
    main()
