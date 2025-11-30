#!/usr/bin/env python3
"""
Minimal debug test for expanded fields - single page only
"""

import sys
sys.path.insert(0, '/Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles')

from src.scraper import TJRJPrecatoriosScraper
from src.models import ScraperConfig, EntidadeDevedora
from decimal import Decimal
from playwright.sync_api import sync_playwright

def test_single_page():
    """Test expanded fields on just the first page"""

    print("\n" + "="*80)
    print("MINIMAL DEBUG TEST - FIRST PAGE ONLY")
    print("="*80 + "\n")

    config = ScraperConfig(
        regime='especial',
        headless=False,
        log_level='DEBUG'  # Maximum verbosity
    )

    scraper = TJRJPrecatoriosScraper(config)

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
            print(f"📋 Entity: {estado_rj.nome_entidade}\n")

            # Navigate
            url = f"https://www3.tjrj.jus.br/precatorio/#/debtor-entity/{estado_rj.id_entidade}/regime/{estado_rj.regime}/pending"
            print(f"🌐 Navigating to: {url}")
            page.goto(url, wait_until='networkidle', timeout=60000)

            # Wait for table
            print("⏳ Waiting for table to load...")
            page.wait_for_selector("tbody tr td", timeout=10000)
            page.wait_for_timeout(5000)  # Extra time for AngularJS

            print("✅ Table loaded\n")

            # Extract first page
            print("📄 Extracting first page...")
            precatorios = scraper._extract_precatorios_from_page(page, estado_rj)

            print(f"\n{'='*80}")
            print(f"RESULTS")
            print(f"{'='*80}")
            print(f"Total extracted: {len(precatorios)}")

            # Check expanded fields
            with_expanded = 0
            for p in precatorios:
                if p.classe or p.localizacao or p.ultima_fase:
                    with_expanded += 1

            print(f"With expanded fields: {with_expanded}/{len(precatorios)}")

            if len(precatorios) > 0:
                print(f"\n📄 First record:")
                p0 = precatorios[0]
                print(f"   Número: {p0.numero_precatorio}")
                print(f"   Situação: {p0.situacao}")
                print(f"   Valor: R$ {p0.saldo_atualizado:,.2f}")
                print(f"   Classe: {p0.classe or '❌ MISSING'}")
                print(f"   Localização: {p0.localizacao or '❌ MISSING'}")
                print(f"   Última fase: {p0.ultima_fase or '❌ MISSING'}")
                print(f"   Possui Herdeiros: {p0.possui_herdeiros or '❌ MISSING'}")

            if len(precatorios) >= 5:
                print(f"\n📄 Fifth record:")
                p4 = precatorios[4]
                print(f"   Número: {p4.numero_precatorio}")
                print(f"   Classe: {p4.classe or '❌ MISSING'}")
                print(f"   Localização: {p4.localizacao or '❌ MISSING'}")
                print(f"   Última fase: {p4.ultima_fase or '❌ MISSING'}")

            if with_expanded == len(precatorios):
                print(f"\n✅ SUCCESS: All records have expanded fields!")
            elif with_expanded > 0:
                print(f"\n⚠️  PARTIAL: {with_expanded}/{len(precatorios)} records have expanded fields")
            else:
                print(f"\n❌ FAILED: No records have expanded fields")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            input("\n⏸  Press Enter to close browser and exit...")
            browser.close()

if __name__ == '__main__':
    test_single_page()
