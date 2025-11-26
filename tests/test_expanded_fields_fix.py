#!/usr/bin/env python3
"""
Quick test to verify expanded fields extraction fix
Tests only 2 pages (20 records) to validate DOM handling
"""

import sys
sys.path.insert(0, '/Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles')

from src.scraper import TJRJPrecatoriosScraper
from src.models import ScraperConfig, EntidadeDevedora
from decimal import Decimal
from playwright.sync_api import sync_playwright
import logging

# Set to INFO to see detailed extraction logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_expanded_fields():
    """Test expanded fields extraction on first 2 pages (20 records)"""

    print("\n" + "="*80)
    print("TESTING EXPANDED FIELDS EXTRACTION FIX")
    print("Testing 2 pages (20 records) from Estado do Rio de Janeiro - Especial")
    print("="*80 + "\n")

    config = ScraperConfig(
        regime='especial',
        headless=False,  # Show browser
        log_level='INFO'
    )

    scraper = TJRJPrecatoriosScraper(config)

    # Manually create the Estado do Rio de Janeiro entity
    estado_rj = EntidadeDevedora(
        id_entidade=1,
        nome_entidade="Estado do Rio de Janeiro",
        regime="especial",
        precatorios_pagos=0,
        precatorios_pendentes=17663,
        valor_prioridade=Decimal('0.00'),
        valor_rpv=Decimal('0.00')
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            print(f"📋 Entity: {estado_rj.nome_entidade}")
            print(f"   Testing first 2 pages only\n")

            # Navigate to the precatorios page
            url = f"https://www3.tjrj.jus.br/precatorio/#/debtor-entity/{estado_rj.id_entidade}/regime/{estado_rj.regime}/pending"
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(3000)

            all_precatorios = []

            # Extract from first 2 pages only
            for page_num in range(1, 3):
                print(f"\n{'='*80}")
                print(f"📄 PAGE {page_num}")
                print(f"{'='*80}")

                # Extract from current page
                precatorios = scraper._extract_precatorios_from_page(page, estado_rj)

                print(f"   Extracted: {len(precatorios)} precatórios")

                # Check expanded fields
                fields_with_expanded = 0
                for p in precatorios:
                    if p.classe or p.localizacao or p.ultima_fase:
                        fields_with_expanded += 1

                print(f"   With expanded fields: {fields_with_expanded}/{len(precatorios)}")

                all_precatorios.extend(precatorios)

                if page_num < 2:
                    # Click next page
                    next_btn = page.query_selector('li.next a[ng-click*="next"]')
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(2000)

            print(f"\n{'='*80}")
            print(f"✅ TEST COMPLETE")
            print(f"{'='*80}")
            print(f"Total extracted: {len(all_precatorios)} precatórios")

            # Analyze expanded fields coverage
            total_with_expanded = sum(1 for p in all_precatorios if p.classe or p.localizacao or p.ultima_fase)
            coverage = (total_with_expanded / len(all_precatorios) * 100) if all_precatorios else 0

            print(f"Records with expanded fields: {total_with_expanded}/{len(all_precatorios)} ({coverage:.1f}%)")

            if coverage >= 90:
                print("✅ SUCCESS: Expanded fields extraction working correctly!")
            elif coverage >= 50:
                print("⚠️  WARNING: Partial success, some records missing expanded fields")
            else:
                print("❌ FAILED: Most records missing expanded fields")

            # Show samples
            if len(all_precatorios) >= 2:
                print(f"\n📄 Sample from page 1:")
                p1 = all_precatorios[0]
                print(f"   Número: {p1.numero_precatorio}")
                print(f"   Classe: {p1.classe or 'MISSING'}")
                print(f"   Localização: {p1.localizacao or 'MISSING'}")
                print(f"   Última fase: {p1.ultima_fase or 'MISSING'}")

                if len(all_precatorios) >= 11:
                    print(f"\n📄 Sample from page 2 (record 11):")
                    p2 = all_precatorios[10]
                    print(f"   Número: {p2.numero_precatorio}")
                    print(f"   Classe: {p2.classe or 'MISSING'}")
                    print(f"   Localização: {p2.localizacao or 'MISSING'}")
                    print(f"   Última fase: {p2.ultima_fase or 'MISSING'}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_expanded_fields()
