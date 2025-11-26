#!/usr/bin/env python3
"""
Test extraction of a single entity with expanded details
"""

import sys
sys.path.insert(0, '/Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles')

from src.scraper import TJRJPrecatoriosScraper
from src.models import ScraperConfig
import json

def test_single_entity_geral():
    """Test extraction of first entity from Regime Geral (first page only)"""

    print("\n" + "="*80)
    print("TESTING REGIME GERAL - First Entity, First Page Only")
    print("="*80 + "\n")

    config = ScraperConfig(
        regime='geral',
        headless=False,  # Show browser for debugging
        log_level='INFO'
    )

    scraper = TJRJPrecatoriosScraper(config)

    try:
        # Get entities
        entities = scraper.get_entities()
        print(f"✅ Found {len(entities)} entities\n")

        if len(entities) > 0:
            # Test first entity only
            first_entity = entities[0]
            print(f"📋 Testing: {first_entity.nome_entidade}")
            print(f"   ID: {first_entity.id_entidade}")
            print(f"   Pendentes: {first_entity.precatorios_pendentes}\n")

            # Extract only first page
            precatorios = scraper.extract_precatorios_for_entity(first_entity, max_pages=1)

            print(f"\n✅ Extracted {len(precatorios)} precatórios from first page")

            if len(precatorios) > 0:
                # Show first precatório with all details
                first_prec = precatorios[0]
                print(f"\n📄 First Precatório:")
                print(f"   Número: {first_prec.numero_precatorio}")
                print(f"   Entidade Grupo: {first_prec.entidade_grupo}")
                print(f"   Entidade Devedora: {first_prec.entidade_devedora}")
                print(f"   Situação: {first_prec.situacao}")
                print(f"   Natureza: {first_prec.natureza}")
                print(f"   Valor Histórico: R$ {first_prec.valor_historico:,.2f}")
                print(f"   Saldo Atualizado: R$ {first_prec.saldo_atualizado:,.2f}")
                print(f"\n   Detalhes Expandidos:")
                print(f"   - Classe: {first_prec.classe}")
                print(f"   - Localização: {first_prec.localizacao}")
                print(f"   - Última fase: {first_prec.ultima_fase}")
                print(f"   - Possui Herdeiros: {first_prec.possui_herdeiros}")
                print(f"   - Possui Cessão: {first_prec.possui_cessao}")
                print(f"   - Possui Retificador: {first_prec.possui_retificador}")

                # Save to JSON for inspection
                output_file = 'tests/output_geral_sample.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    data = [p.model_dump() for p in precatorios]
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n💾 Saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_single_entity_geral()
