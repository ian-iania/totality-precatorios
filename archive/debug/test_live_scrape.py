"""
Live Integration Test - Headless Mode

Tests the scraper against the actual TJRJ website.
"""

from src.scraper import TJRJPrecatoriosScraper
from src.models import ScraperConfig

def main():
    print("="*60)
    print("🧪 LIVE INTEGRATION TEST (Headless Mode)")
    print("="*60)

    # Create config with headless browser
    config = ScraperConfig(
        regime='geral',
        headless=True,  # Run in background
        max_retries=2,
        log_level='INFO'
    )

    print("\n✅ Configuration:")
    print(f"   Regime: {config.regime}")
    print(f"   Headless: {config.headless}")
    print(f"   Base URL: {config.base_url}")

    # Create scraper
    scraper = TJRJPrecatoriosScraper(config=config)

    print("\n📋 Testing entity extraction...")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.headless)
        page = browser.new_page()

        try:
            # Extract entities
            print("   Navigating to regime geral page...")
            entidades = scraper.get_entidades(page, 'geral')

            print(f"\n✅ ENTITY EXTRACTION: Found {len(entidades)} entities")

            if len(entidades) > 0:
                print(f"\n📊 Sample entities (first 5):")
                for i, ent in enumerate(entidades[:5], 1):
                    print(f"\n   {i}. {ent.nome_entidade}")
                    print(f"      ID: {ent.id_entidade}")
                    print(f"      Pagos: {ent.precatorios_pagos:,}")
                    print(f"      Pendentes: {ent.precatorios_pendentes:,}")
                    print(f"      Prioridade: R$ {float(ent.valor_prioridade):,.2f}")
                    print(f"      RPV: R$ {float(ent.valor_rpv):,.2f}")

                # Test precatório extraction for first entity (limit to avoid long test)
                test_entity = entidades[0]
                print(f"\n🔄 Testing precatório extraction for: {test_entity.nome_entidade}")
                print(f"   (Limiting to first 5 pages for testing)")

                precatorios = []
                page_limit = 5
                current_page = 1

                # Navigate to precatório list
                url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={test_entity.id_entidade}"
                page.goto(url, wait_until='networkidle')
                page.wait_for_timeout(2000)

                while current_page <= page_limit:
                    page_precatorios = scraper._extract_precatorios_from_page(page, test_entity)
                    precatorios.extend(page_precatorios)
                    print(f"   Page {current_page}: {len(page_precatorios)} precatórios")

                    # Try to go to next page
                    try:
                        next_button = page.query_selector("text=Próxima")
                        if not next_button:
                            break

                        is_disabled = next_button.get_attribute('disabled')
                        if is_disabled:
                            break

                        next_button.click()
                        page.wait_for_timeout(1500)
                        current_page += 1
                    except:
                        break

                print(f"\n✅ PRECATÓRIO EXTRACTION: Found {len(precatorios)} precatórios (limited test)")

                if len(precatorios) > 0:
                    print(f"\n📊 Sample precatórios (first 5):")
                    for i, prec in enumerate(precatorios[:5], 1):
                        print(f"\n   {i}. {prec.numero_precatorio}")
                        print(f"      Beneficiário: {prec.beneficiario}")
                        print(f"      Valor Orig: R$ {float(prec.valor_original):,.2f}")
                        print(f"      Valor Atual: R$ {float(prec.valor_atualizado):,.2f}")
                        print(f"      Tipo: {prec.tipo}")
                        print(f"      Status: {prec.status}")
                else:
                    print("\n⚠️  No precatórios extracted")
                    print("   This might indicate selector issues")

            else:
                print("\n⚠️  No entities extracted!")
                print("   The page structure may have changed")
                print("   Check logs/scraper.log for details")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    print("\nSummary:")
    print(f"  • Entities found: {len(entidades) if 'entidades' in locals() else 0}")
    print(f"  • Precatórios found: {len(precatorios) if 'precatorios' in locals() else 0}")
    print(f"  • Check logs/scraper.log for detailed logs")

if __name__ == "__main__":
    main()
