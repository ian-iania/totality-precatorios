#!/usr/bin/env python3
"""Quick validation: Extract 3 pages (30 records) to verify expanded fields fix"""
import sys
sys.path.insert(0, '/Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles')

from src.scraper import TJRJPrecatoriosScraper
from src.models import ScraperConfig, EntidadeDevedora
from decimal import Decimal
from playwright.sync_api import sync_playwright

config = ScraperConfig(regime='especial', headless=False, log_level='INFO')
scraper = TJRJPrecatoriosScraper(config)

estado_rj = EntidadeDevedora(
    id_entidade=1, nome_entidade="Estado do Rio de Janeiro",
    regime="especial", precatorios_pagos=0, precatorios_pendentes=17663,
    valor_prioridade=Decimal('0.00'), valor_rpv=Decimal('0.00')
)

print("\n" + "="*80)
print("VALIDATING EXPANDED FIELDS FIX - 3 PAGES (30 RECORDS)")
print("="*80 + "\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=config.headless)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()

    try:
        url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={estado_rj.id_entidade}"
        page.goto(url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        all_precatorios = []
        for page_num in range(1, 4):  # Pages 1-3
            print(f"\n📄 PAGE {page_num}")
            precatorios = scraper._extract_precatorios_from_page(page, estado_rj)

            with_expanded = sum(1 for p in precatorios if p.classe or p.localizacao or p.ultima_fase)
            print(f"   Extracted: {len(precatorios)} | With expanded fields: {with_expanded}/{len(precatorios)}")

            all_precatorios.extend(precatorios)

            if page_num < 3:
                next_btn = page.query_selector('text=Próxima')
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(2000)

        total = len(all_precatorios)
        with_expanded = sum(1 for p in all_precatorios if p.classe or p.localizacao or p.ultima_fase)
        coverage = (with_expanded / total * 100) if total else 0

        print(f"\n{'='*80}")
        print(f"RESULTS: {with_expanded}/{total} records with expanded fields ({coverage:.1f}%)")

        if coverage >= 90:
            print("✅ SUCCESS: Fix working correctly!")
        elif coverage >= 50:
            print("⚠️  PARTIAL: Some records still missing expanded fields")
        else:
            print("❌ FAILED: Most records missing expanded fields")

        # Show samples from different pages
        if total >= 3:
            print(f"\n📄 Page 1, Record 1: Classe={all_precatorios[0].classe or 'MISSING'}")
            print(f"📄 Page 2, Record 11: Classe={all_precatorios[10].classe or 'MISSING'}" if total > 10 else "")
            print(f"📄 Page 3, Record 21: Classe={all_precatorios[20].classe or 'MISSING'}" if total > 20 else "")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

print("\n" + "="*80 + "\n")
