#!/usr/bin/env python3
"""
Map ALL columns (visible + non-visible) from TJRJ table
"""

from playwright.sync_api import sync_playwright
import time

def map_all_columns():
    """Map every single column to its cell index"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1"
        print(f"\n🔍 Mapping ALL columns from: {url}\n")

        page.goto(url, wait_until='networkidle')
        time.sleep(5)

        # Get ALL headers (visible and non-visible)
        headers = page.query_selector_all('thead th')

        print("=" * 80)
        print("ALL HEADERS (VISIBLE + NON-VISIBLE)")
        print("=" * 80)

        header_map = []
        for i, header in enumerate(headers):
            text = header.inner_text().strip()
            is_visible = page.evaluate('(element) => element.offsetParent !== null', header)
            header_map.append({
                'index': i,
                'name': text,
                'visible': is_visible
            })
            vis_mark = "👁️ " if is_visible else "🔒"
            print(f"  {vis_mark} Header {i:2d}: '{text}'")

        # Get first data row with ALL cells
        print("\n" + "=" * 80)
        print("SAMPLE DATA ROW (ALL 18 CELLS)")
        print("=" * 80)

        rows = page.query_selector_all('tbody tr')
        if rows and len(rows) > 0:
            first_row = rows[0]
            cells = first_row.query_selector_all('td')

            print(f"\nTotal cells: {len(cells)}\n")

            cell_data = []
            for i, cell in enumerate(cells):
                text = cell.inner_text().strip()
                is_visible = page.evaluate('(element) => element.offsetParent !== null', cell)

                cell_data.append({
                    'index': i,
                    'value': text,
                    'visible': is_visible
                })

                vis_mark = "👁️ " if is_visible else "🔒"
                preview = text[:50] + '...' if len(text) > 50 else text
                print(f"  {vis_mark} Cell {i:2d}: '{preview}'")

        # Create mapping
        print("\n" + "=" * 80)
        print("PROPOSED COLUMN MAPPING (Entity First)")
        print("=" * 80)

        print("\n📋 CSV Column Order:\n")
        print("  1. entidade_devedora         <- Cell 6")
        print("  2. id_entidade               <- From entity list")
        print("  3. regime                    <- From config")
        print("  4. ordem                     <- Cell 2")
        print("  5. numero_precatorio         <- Cell 7")
        print("  6. situacao                  <- Cell 8")
        print("  7. natureza                  <- Cell 9")
        print("  8. orcamento                 <- Cell 10")
        print("  9. valor_historico           <- Cell 12")
        print(" 10. saldo_atualizado          <- Cell 14")
        print(" 11. prioridade                <- Cell 11 (non-visible)")
        print(" 12. valor_parcela             <- Cell 13 (non-visible)")
        print(" 13. valor_pagamento           <- Cell ?? (non-visible)")
        print(" 14. saldo_residual            <- Cell ?? (non-visible)")
        print(" 15. parcelas_pagas            <- Cell 15 (non-visible)")
        print(" 16. previsao_pagamento        <- Cell 16 (non-visible)")
        print(" 17. quitado                   <- Cell 17 (non-visible)")
        print(" 18. timestamp_extracao        <- Generated")

        # Get multiple rows to understand pattern
        print("\n" + "=" * 80)
        print("FIRST 3 ROWS (to verify pattern)")
        print("=" * 80)

        for row_idx in range(min(3, len(rows))):
            row = rows[row_idx]
            cells = row.query_selector_all('td')
            print(f"\nRow {row_idx + 1}:")
            print(f"  Entidade: {cells[6].inner_text().strip() if len(cells) > 6 else 'N/A'}")
            print(f"  Precatório: {cells[7].inner_text().strip() if len(cells) > 7 else 'N/A'}")
            print(f"  Ordem: {cells[2].inner_text().strip() if len(cells) > 2 else 'N/A'}")
            print(f"  Orçamento: {cells[10].inner_text().strip() if len(cells) > 10 else 'N/A'}")
            print(f"  Parcelas: {cells[15].inner_text().strip() if len(cells) > 15 else 'N/A'}")
            print(f"  Quitado: {cells[17].inner_text().strip() if len(cells) > 17 else 'N/A'}")

        time.sleep(2)
        browser.close()

if __name__ == '__main__':
    map_all_columns()
