#!/usr/bin/env python3
"""
Test script to re-extract Estado do Rio de Janeiro (Especial)
This entity has 17,663 precatórios but was limited to 10,000 in previous extraction
"""

import sys
sys.path.insert(0, '/Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles')

from src.scraper import TJRJPrecatoriosScraper
from src.models import ScraperConfig, EntidadeDevedora
from decimal import Decimal
from playwright.sync_api import sync_playwright
import pandas as pd

def test_estado_rj_especial():
    """Re-extract Estado do Rio de Janeiro from Regime Especial (17,663 expected)"""

    print("\n" + "="*80)
    print("RE-EXTRACTING: Estado do Rio de Janeiro - Regime Especial")
    print("Expected: 17,663 precatórios (previous extraction stopped at 10,000)")
    print("Limit increased from 1,000 pages (10k records) to 5,000 pages (50k records)")
    print("="*80 + "\n")

    config = ScraperConfig(
        regime='especial',
        headless=False,  # Show browser to monitor progress
        log_level='INFO'
    )

    scraper = TJRJPrecatoriosScraper(config)

    # Manually create the Estado do Rio de Janeiro entity
    estado_rj = EntidadeDevedora(
        id_entidade=1,
        nome_entidade="Estado do Rio de Janeiro",
        regime="especial",
        precatorios_pagos=0,
        precatorios_pendentes=17663,  # From website
        valor_prioridade=Decimal('0.00'),
        valor_rpv=Decimal('0.00')
    )

    with sync_playwright() as p:
        # Launch browser
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
            print(f"   ID: {estado_rj.id_entidade}")
            print(f"   Expected Records: {estado_rj.precatorios_pendentes:,}\n")

            # Extract all precatórios using the correct method
            precatorios = scraper.get_precatorios_entidade(page, estado_rj)

            print(f"\n{'='*80}")
            print(f"✅ Extraction Complete!")
            print(f"{'='*80}")
            print(f"📊 Total extracted: {len(precatorios):,} precatórios")

            if len(precatorios) >= 17663:
                print("✅ SUCCESS: All records extracted!")
            elif len(precatorios) >= 10000:
                print(f"⚠️  WARNING: Still limited? Expected 17,663 but got {len(precatorios):,}")
                print(f"    Missing: {17663 - len(precatorios):,} records")
            else:
                print(f"❌ ERROR: Expected 17,663 but only got {len(precatorios):,}")

            # Save to CSV
            if len(precatorios) > 0:
                # Convert to DataFrame
                data = [p.model_dump() for p in precatorios]
                df = pd.DataFrame(data)

                output_file = 'data/processed/precatorios_estado_rj_especial_FULL.csv'
                scraper.save_to_csv(df, output_file)

                print(f"\n💾 Saved to: {output_file}")
                print(f"📏 File size: {len(data):,} rows × 19 columns")

                # Show sample
                print(f"\n📄 First record:")
                print(f"   Número: {precatorios[0].numero_precatorio}")
                print(f"   Situação: {precatorios[0].situacao}")
                print(f"   Valor: R$ {precatorios[0].saldo_atualizado:,.2f}")

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
    test_estado_rj_especial()
