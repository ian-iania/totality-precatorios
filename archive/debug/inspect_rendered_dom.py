"""
DOM Inspector Tool - Captures RENDERED HTML after AngularJS loads

This will save the actual DOM content, not just the shell.
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def save_rendered_dom(url: str, output_file: str, wait_text: str = None):
    """
    Capture the actual rendered DOM after JavaScript execution

    Args:
        url: URL to visit
        output_file: Where to save HTML
        wait_text: Text to wait for before capturing (ensures content loaded)
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"\n📱 Navigating to: {url}")
        page.goto(url, wait_until='networkidle')

        # Wait for specific text to ensure Angular has rendered
        if wait_text:
            print(f"⏳ Waiting for text: '{wait_text}'...")
            try:
                page.wait_for_selector(f"text={wait_text}", timeout=15000)
                print(f"✅ Found: '{wait_text}'")
            except:
                print(f"⚠️  Timeout waiting for: '{wait_text}'")

        # Extra wait for Angular to fully render
        page.wait_for_timeout(3000)

        # Get the RENDERED HTML
        html = page.content()

        # Also get just the content div
        try:
            content_div = page.query_selector("#content, ng-view, [ng-view]")
            if content_div:
                content_html = content_div.inner_html()
                print(f"📦 Content div size: {len(content_html):,} chars")
            else:
                content_html = "<!-- Content div not found -->"
        except:
            content_html = "<!-- Error extracting content -->"

        # Save full HTML
        Path(output_file).write_text(html, encoding='utf-8')
        print(f"💾 Saved full HTML to: {output_file}")

        # Save just the content
        content_file = output_file.replace('.html', '_content.html')
        Path(content_file).write_text(content_html, encoding='utf-8')
        print(f"💾 Saved content to: {content_file}")

        # Print some sample text from the page for verification
        print(f"\n📄 Sample page text:")
        page_text = page.inner_text('body')
        print(page_text[:500])

        # Keep browser open for manual inspection
        print("\n" + "="*60)
        print("👀 Browser is open. Inspect with DevTools (F12):")
        print("   1. Right-click on entity card → Inspect")
        print("   2. Look for CSS classes, data attributes")
        print("   3. Copy outerHTML of one entity card")
        print("="*60)
        input("\nPress Enter when done inspecting...")

        browser.close()

def main():
    print("="*60)
    print("🔍 TJRJ DOM INSPECTOR")
    print("="*60)

    # Create output directory
    Path("data/raw/rendered").mkdir(parents=True, exist_ok=True)

    # Capture regime geral entities page
    print("\n1️⃣  Capturing REGIME GERAL page...")
    save_rendered_dom(
        url="https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral",
        output_file="data/raw/rendered/regime_geral_rendered.html",
        wait_text="Precatórios Pagos"  # Wait for entity cards to load
    )

    # Capture a precatório list page (INSS - ID 86)
    print("\n2️⃣  Capturing PRECATÓRIO LIST page (INSS)...")
    save_rendered_dom(
        url="https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=86",
        output_file="data/raw/rendered/precatorio_list_inss.html",
        wait_text="Número do Precatório"  # Wait for table header
    )

    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)
    print("\n📁 Files saved to: data/raw/rendered/")
    print("\n🎯 Next: Open the *_content.html files and look for:")
    print("   - Entity card HTML structure")
    print("   - Table structure for precatórios")
    print("   - CSS classes and data attributes")
    print("\nThen share a snippet with Claude!")

if __name__ == "__main__":
    main()
