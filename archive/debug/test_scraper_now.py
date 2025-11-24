"""
Quick Test Script - Test the scraper implementation

This tests just the first entity to verify it works.
"""

from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config
from src.models import ScraperConfig

def main():
    print("="*60)
    print("🧪 TESTING TJRJ SCRAPER")
    print("="*60)

    # Create config with visible browser for testing
    config = ScraperConfig(
        regime='geral',
        headless=False,  # Show browser
        max_retries=2,
        log_level='DEBUG'
    )

    # Create scraper
    scraper = TJRJPrecatoriosScraper(config=config)

    print("\n✅ Scraper initialized")
    print(f"   Regime: {config.regime}")
    print(f"   Headless: {config.headless}")

    # Test entity extraction only
    print("\n📋 Testing entity extraction...")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.headless)
        page = browser.new_page()

        try:
            # Extract entities
            entidades = scraper.get_entidades(page, 'geral')

            print(f"\n✅ Found {len(entidades)} entities!")

            if len(entidades) > 0:
                print("\n📊 First 3 entities:")
                for i, ent in enumerate(entidades[:3], 1):
                    print(f"\n{i}. {ent.nome_entidade}")
                    print(f"   ID: {ent.id_entidade}")
                    print(f"   Precatórios Pagos: {ent.precatorios_pagos}")
                    print(f"   Precatórios Pendentes: {ent.precatorios_pendentes}")
                    print(f"   Valor Prioridade: R$ {ent.valor_prioridade:,.2f}")
                    print(f"   Valor RPV: R$ {ent.valor_rpv:,.2f}")

                # Test precatório extraction for first entity
                print(f"\n🔄 Testing precatório extraction for: {entidades[0].nome_entidade}")

                precatorios = scraper.get_precatorios_entidade(page, entidades[0])

                print(f"\n✅ Found {len(precatorios)} precatórios!")

                if len(precatorios) > 0:
                    print("\n📊 First 3 precatórios:")
                    for i, prec in enumerate(precatorios[:3], 1):
                        print(f"\n{i}. {prec.numero_precatorio}")
                        print(f"   Beneficiário: {prec.beneficiario}")
                        print(f"   Valor: R$ {prec.valor_atualizado:,.2f}")
                        print(f"   Tipo: {prec.tipo}")
                        print(f"   Status: {prec.status}")
                else:
                    print("⚠️  No precatórios extracted")
                    print("   Check logs/scraper.log for details")

            else:
                print("⚠️  No entities extracted")
                print("   The scraper may need selector refinement")
                print("   Check logs/scraper.log for details")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

    print("\n" + "="*60)
    print("Test complete! Check logs/scraper.log for details")
    print("="*60)

if __name__ == "__main__":
    main()
