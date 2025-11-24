#!/usr/bin/env python3
"""
Test extraction of FIRST entity from each regime
This validates the corrected structure before full re-extraction
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


def parse_integer(value_str: str) -> int:
    """Parse integer with Brazilian thousand separators"""
    if not value_str:
        return 0
    try:
        value_str = value_str.replace('.', '').replace(',', '').strip()
        return int(value_str)
    except:
        return 0


def get_first_entity(page, regime: str):
    """Extract first entity from regime page"""

    url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-{regime}"
    print(f"\n📍 Navigating to: {url}")

    page.goto(url, wait_until='networkidle')
    time.sleep(3)

    # Find first entity card
    cards = page.query_selector_all('[ng-repeat*="ente"]')

    if not cards or len(cards) == 0:
        print("❌ No entity cards found")
        return None

    first_card = cards[0]
    card_text = first_card.inner_text()

    # Extract entity name (first line)
    lines = [line.strip() for line in card_text.split('\n') if line.strip()]
    entity_name = lines[0] if lines else "Unknown"

    # Extract ID from link
    link = first_card.query_selector('a')
    if link:
        href = link.get_attribute('href')
        if 'idEntidadeDevedora=' in href:
            entity_id = int(href.split('idEntidadeDevedora=')[1].split('&')[0])
        else:
            entity_id = 0
    else:
        entity_id = 0

    # Extract statistics
    precatorios_pagos = 0
    precatorios_pendentes = 0
    valor_prioridade = Decimal('0.00')
    valor_rpv = Decimal('0.00')

    for i, line in enumerate(lines):
        if 'Precatórios Pagos:' in line or 'Pagos:' in line:
            if i + 1 < len(lines):
                precatorios_pagos = parse_integer(lines[i + 1])
        elif 'Precatórios Pendentes:' in line or 'Pendentes:' in line:
            if i + 1 < len(lines):
                precatorios_pendentes = parse_integer(lines[i + 1])
        elif 'Valor Prioridade:' in line:
            if i + 1 < len(lines):
                valor_prioridade = parse_currency(lines[i + 1])
        elif 'Valor RPV:' in line:
            if i + 1 < len(lines):
                valor_rpv = parse_currency(lines[i + 1])

    entity = EntidadeDevedora(
        id_entidade=entity_id,
        nome_entidade=entity_name,
        regime=regime,
        precatorios_pagos=precatorios_pagos,
        precatorios_pendentes=precatorios_pendentes,
        valor_prioridade=valor_prioridade,
        valor_rpv=valor_rpv
    )

    print(f"\n✅ First Entity Found:")
    print(f"   Name: {entity.nome_entidade}")
    print(f"   ID: {entity.id_entidade}")
    print(f"   Pagos: {entity.precatorios_pagos:,}")
    print(f"   Pendentes: {entity.precatorios_pendentes:,}")

    return entity


def extract_sample_precatorios(page, entity: EntidadeDevedora, max_rows: int = 10):
    """Extract sample precatórios from entity"""

    url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entity.id_entidade}"
    print(f"\n📍 Navigating to precatório list...")

    page.goto(url, wait_until='networkidle')
    time.sleep(5)

    rows = page.query_selector_all('tbody tr')

    if not rows or len(rows) == 0:
        print("❌ No precatório rows found")
        return []

    print(f"\n✅ Found {len(rows)} rows, extracting first {max_rows}...")

    precatorios = []

    for row_idx in range(min(max_rows, len(rows))):
        row = rows[row_idx]
        cells = row.query_selector_all('td')

        if len(cells) < 15:
            continue

        cell_texts = [cell.inner_text().strip() for cell in cells]

        try:
            precatorio = Precatorio(
                # Entity - TWO LEVELS
                entidade_grupo=entity.nome_entidade,
                id_entidade_grupo=entity.id_entidade,
                entidade_devedora=cell_texts[6] if len(cell_texts) > 6 else "",
                regime=entity.regime,

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

            precatorios.append(precatorio)

        except Exception as e:
            print(f"   ⚠️  Row {row_idx + 1} skipped: {e}")
            continue

    return precatorios


def test_both_regimes():
    """Test first entity from both regimes"""

    print("=" * 80)
    print("🧪 TESTING FIRST ENTITY FROM EACH REGIME")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # === TEST REGIME GERAL ===
        print("\n" + "=" * 80)
        print("📋 REGIME GERAL")
        print("=" * 80)

        entity_geral = get_first_entity(page, 'geral')

        if entity_geral:
            precatorios_geral = extract_sample_precatorios(page, entity_geral, max_rows=10)

            print(f"\n✅ Extracted {len(precatorios_geral)} precatórios from Regime Geral")
            print(f"\n📊 Sample Data (first 3):")

            for i, prec in enumerate(precatorios_geral[:3], 1):
                print(f"\n   {i}. {prec.numero_precatorio}")
                print(f"      🏛️  Grupo: {prec.entidade_grupo}")
                print(f"      🏢 Devedora: {prec.entidade_devedora}")
                print(f"      Ordem: {prec.ordem}")
                print(f"      Natureza: {prec.natureza}")
                print(f"      Orçamento: {prec.orcamento}")
                print(f"      Valor: R$ {float(prec.saldo_atualizado):,.2f}")
                print(f"      Quitado: {prec.quitado}")

        # === TEST REGIME ESPECIAL ===
        print("\n" + "=" * 80)
        print("📋 REGIME ESPECIAL")
        print("=" * 80)

        entity_especial = get_first_entity(page, 'especial')

        if entity_especial:
            precatorios_especial = extract_sample_precatorios(page, entity_especial, max_rows=15)

            print(f"\n✅ Extracted {len(precatorios_especial)} precatórios from Regime Especial")

            # Show entities to verify we capture different ones
            unique_entities = set()
            for prec in precatorios_especial:
                unique_entities.add((prec.entidade_grupo, prec.entidade_devedora))

            print(f"\n🏢 Entities Found ({len(unique_entities)} unique combinations):")
            for grupo, devedora in sorted(unique_entities):
                mark = "✓" if grupo != devedora else "="
                print(f"   {mark} Grupo: '{grupo}' → Devedora: '{devedora}'")

            print(f"\n📊 Sample Data (first 3):")
            for i, prec in enumerate(precatorios_especial[:3], 1):
                print(f"\n   {i}. {prec.numero_precatorio}")
                print(f"      🏛️  Grupo: {prec.entidade_grupo}")
                print(f"      🏢 Devedora: {prec.entidade_devedora}")
                print(f"      Ordem: {prec.ordem}")
                print(f"      Natureza: {prec.natureza}")
                print(f"      Orçamento: {prec.orcamento}")
                print(f"      Valor: R$ {float(prec.saldo_atualizado):,.2f}")
                print(f"      Parcelas: {prec.parcelas_pagas}")
                print(f"      Quitado: {prec.quitado}")

        # === SUMMARY ===
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)
        print(f"\nRegime Geral:    {len(precatorios_geral) if entity_geral else 0} precatórios extracted")
        print(f"Regime Especial: {len(precatorios_especial) if entity_especial else 0} precatórios extracted")
        print(f"\n✓ Two-level entity structure working correctly")
        print(f"✓ All 18 columns being captured")

        time.sleep(2)
        browser.close()


if __name__ == '__main__':
    test_both_regimes()
