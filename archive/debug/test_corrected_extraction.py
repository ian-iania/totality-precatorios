#!/usr/bin/env python3
"""
Test the CORRECTED extraction with ALL columns
"""

from playwright.sync_api import sync_playwright
from src.models_corrected import Precatorio, EntidadeDevedora
from decimal import Decimal
import time

def parse_currency(value_str: str) -> Decimal:
    """Parse Brazilian currency format"""
    if not value_str:
        return Decimal('0.00')
    try:
        value_str = value_str.replace('R$', '').replace(' ', '').strip()
        value_str = value_str.replace('.', '')
        value_str = value_str.replace(',', '.')
        return Decimal(value_str)
    except:
        return Decimal('0.00')


def test_extraction():
    """Test extraction with corrected column mapping"""

    # Create a test entity (this is the GROUP/PARENT entity from the card)
    test_entity = EntidadeDevedora(
        id_entidade=1,
        nome_entidade="Estado do Rio de Janeiro e Afins",  # Note: "e Afins" = "and related"
        regime="especial",
        precatorios_pagos=0,
        precatorios_pendentes=10000,
        valor_prioridade=Decimal('0.00'),
        valor_rpv=Decimal('0.00')
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1"
        print(f"\n🧪 Testing corrected extraction from: {url}\n")

        page.goto(url, wait_until='networkidle')
        time.sleep(5)

        # Get first row
        rows = page.query_selector_all('tbody tr')

        if rows and len(rows) > 0:
            print("=" * 80)
            print("TESTING FIRST 3 ROWS")
            print("=" * 80)

            for row_idx in range(min(3, len(rows))):
                row = rows[row_idx]
                cells = row.query_selector_all('td')

                if len(cells) < 15:
                    print(f"\nRow {row_idx + 1}: Skipped (only {len(cells)} cells)")
                    continue

                cell_texts = [cell.inner_text().strip() for cell in cells]

                # Extract using corrected mapping
                try:
                    precatorio = Precatorio(
                        # Entity - TWO LEVELS (FIRST columns)
                        entidade_grupo=test_entity.nome_entidade,  # From card
                        id_entidade_grupo=test_entity.id_entidade,  # From card
                        entidade_devedora=cell_texts[6] if len(cell_texts) > 6 else "",  # From Cell 6
                        regime=test_entity.regime,

                        # Visible columns
                        ordem=cell_texts[2] if len(cell_texts) > 2 else "",
                        numero_precatorio=cell_texts[7] if len(cell_texts) > 7 else "",
                        situacao=cell_texts[8] if len(cell_texts) > 8 else "",
                        natureza=cell_texts[9] if len(cell_texts) > 9 else "",
                        orcamento=cell_texts[10] if len(cell_texts) > 10 else "",
                        valor_historico=parse_currency(cell_texts[12]) if len(cell_texts) > 12 else Decimal('0.00'),
                        saldo_atualizado=parse_currency(cell_texts[14]) if len(cell_texts) > 14 else Decimal('0.00'),

                        # Non-visible columns
                        prioridade=cell_texts[11] if len(cell_texts) > 11 and cell_texts[11] else None,
                        valor_parcela=parse_currency(cell_texts[13]) if len(cell_texts) > 13 and cell_texts[13] else None,
                        parcelas_pagas=cell_texts[15] if len(cell_texts) > 15 and cell_texts[15] else None,
                        previsao_pagamento=cell_texts[16] if len(cell_texts) > 16 and cell_texts[16] else None,
                        quitado=cell_texts[17] if len(cell_texts) > 17 and cell_texts[17] else None
                    )

                    print(f"\n✅ Row {row_idx + 1} - Extraction SUCCESS:")
                    print(f"   🏛️  Entidade Grupo: {precatorio.entidade_grupo}")
                    print(f"   🏢 Entidade Devedora: {precatorio.entidade_devedora}")
                    print(f"   Ordem: {precatorio.ordem}")
                    print(f"   Precatório: {precatorio.numero_precatorio}")
                    print(f"   Situação: {precatorio.situacao}")
                    print(f"   Natureza: {precatorio.natureza}")
                    print(f"   Orçamento: {precatorio.orcamento}")
                    print(f"   Valor Histórico: R$ {float(precatorio.valor_historico):,.2f}")
                    print(f"   Saldo Atualizado: R$ {float(precatorio.saldo_atualizado):,.2f}")
                    print(f"   Parcelas Pagas: {precatorio.parcelas_pagas}")
                    print(f"   Quitado: {precatorio.quitado}")

                except Exception as e:
                    print(f"\n❌ Row {row_idx + 1} - Extraction FAILED:")
                    print(f"   Error: {e}")
                    print(f"   Cells: {len(cell_texts)}")

        else:
            print("❌ No rows found")

        time.sleep(2)
        browser.close()

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)


if __name__ == '__main__':
    test_extraction()
