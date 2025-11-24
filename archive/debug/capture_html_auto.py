"""
Automatic HTML capture - no user interaction required
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

def capture_page(url: str, output_file: str, wait_text: str = None):
    """Capture rendered HTML"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"📱 Navigating to: {url}")
        page.goto(url, wait_until='networkidle')

        if wait_text:
            try:
                page.wait_for_selector(f"text={wait_text}", timeout=15000)
                print(f"✅ Found: '{wait_text}'")
            except:
                print(f"⚠️  Timeout waiting for: '{wait_text}'")

        page.wait_for_timeout(3000)

        # Save HTML
        html = page.content()
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_text(html, encoding='utf-8')
        print(f"💾 Saved: {output_file} ({len(html):,} chars)")

        # Save sample of page text
        text = page.inner_text('body')
        text_file = output_file.replace('.html', '_text.txt')
        Path(text_file).write_text(text[:5000], encoding='utf-8')
        print(f"💾 Saved sample text: {text_file}")

        browser.close()

def main():
    print("="*60)
    print("🔍 HTML CAPTURE TOOL")
    print("="*60)

    # Capture regime geral
    print("\n1️⃣  Capturing REGIME GERAL page...")
    capture_page(
        "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral",
        "data/raw/rendered/regime_geral.html",
        "Precatórios Pagos"
    )

    # Capture INSS precatório list
    print("\n2️⃣  Capturing INSS precatório list...")
    capture_page(
        "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=86",
        "data/raw/rendered/inss_list.html",
        "Número do Precatório"
    )

    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)
    print("\nFiles saved to: data/raw/rendered/")
    print("\nNext: Check the text files to see actual data format")

if __name__ == "__main__":
    main()
