"""
CORRECTED extraction method for ALL columns

This replaces the _parse_precatorio_from_row method in src/scraper.py
"""

from decimal import Decimal
from typing import Optional
from src.models_corrected import Precatorio, EntidadeDevedora
import logging

logger = logging.getLogger(__name__)


def parse_precatorio_from_row_CORRECTED(
    row,
    entidade: EntidadeDevedora
) -> Optional[Precatorio]:
    """
    Parse precatório from table row with ALL columns (visible + non-visible)

    Table structure (18 cells total):
    === VISIBLE (8) ===
    Cell 2:  Ordem (e.g., "2º", "4º")
    Cell 6:  Entidade Devedora - SPECIFIC entity (e.g., "IPERJ", "RIO-PREVIDÊNCIA")
    Cell 7:  Número Precatório (e.g., "1998.03464-7")
    Cell 8:  Situação (e.g., "Dispensa de Provisionamento")
    Cell 9:  Natureza (e.g., "Comum", "Alimentícia")
    Cell 10: Orçamento (e.g., "1999", "2011")
    Cell 12: Valor Histórico (e.g., "R$ 131.089.991,20")
    Cell 14: Saldo Atualizado (e.g., "R$ 1.129.909.880,35")

    NOTE: entidade parameter contains the GROUP/PARENT entity clicked from the card
          Cell 6 contains the SPECIFIC entity responsible for this precatório
          These can be DIFFERENT! (e.g., "Estado do RJ e Afins" vs "IPERJ")

    === NON-VISIBLE (5) ===
    Cell 11: Prioridade (often empty)
    Cell 13: Valor Parcela (often empty)
    Cell 15: Parcelas Pagas (e.g., "5/5")
    Cell 16: Previsão Pagamento (often empty)
    Cell 17: Quitado (e.g., "Sim", "Não")
    """

    try:
        # Get all cells
        cells = row.query_selector_all('td')

        if len(cells) < 15:
            logger.debug(f"Row has only {len(cells)} cells, skipping")
            return None

        # Extract text from all cells
        cell_texts = [cell.inner_text().strip() for cell in cells]

        # === EXTRACT VISIBLE COLUMNS ===

        # Ordem (Cell 2)
        ordem = cell_texts[2] if len(cell_texts) > 2 else ""

        # Entidade Devedora - SPECIFIC entity from table (Cell 6)
        entidade_devedora_especifica = cell_texts[6] if len(cell_texts) > 6 else ""

        # Número Precatório (Cell 7) - REQUIRED
        numero_precatorio = cell_texts[7] if len(cell_texts) > 7 else ""
        if not numero_precatorio:
            logger.debug("Empty precatório number, skipping row")
            return None

        # Situação (Cell 8)
        situacao = cell_texts[8] if len(cell_texts) > 8 else ""

        # Natureza (Cell 9)
        natureza = cell_texts[9] if len(cell_texts) > 9 else ""

        # Orçamento (Cell 10)
        orcamento = cell_texts[10] if len(cell_texts) > 10 else ""

        # Valor Histórico (Cell 12)
        valor_historico_text = cell_texts[12] if len(cell_texts) > 12 else ""
        valor_historico = parse_currency(valor_historico_text) if valor_historico_text else Decimal('0.00')

        # Saldo Atualizado (Cell 14)
        saldo_atualizado_text = cell_texts[14] if len(cell_texts) > 14 else ""
        saldo_atualizado = parse_currency(saldo_atualizado_text) if saldo_atualizado_text else valor_historico

        # === EXTRACT NON-VISIBLE COLUMNS ===

        # Prioridade (Cell 11)
        prioridade = cell_texts[11] if len(cell_texts) > 11 and cell_texts[11] else None

        # Valor Parcela (Cell 13)
        valor_parcela_text = cell_texts[13] if len(cell_texts) > 13 and cell_texts[13] else None
        valor_parcela = parse_currency(valor_parcela_text) if valor_parcela_text else None

        # Parcelas Pagas (Cell 15)
        parcelas_pagas = cell_texts[15] if len(cell_texts) > 15 and cell_texts[15] else None

        # Previsão Pagamento (Cell 16)
        previsao_pagamento = cell_texts[16] if len(cell_texts) > 16 and cell_texts[16] else None

        # Quitado (Cell 17)
        quitado = cell_texts[17] if len(cell_texts) > 17 and cell_texts[17] else None

        # === CREATE PRECATORIO OBJECT ===

        precatorio = Precatorio(
            # Entity info - TWO LEVELS (FIRST columns)
            entidade_grupo=entidade.nome_entidade,  # Parent/Group from card
            id_entidade_grupo=entidade.id_entidade,  # Parent/Group ID
            entidade_devedora=entidade_devedora_especifica,  # Specific from Cell 6
            regime=entidade.regime,

            # Visible columns
            ordem=ordem,
            numero_precatorio=numero_precatorio,
            situacao=situacao,
            natureza=natureza,
            orcamento=orcamento,
            valor_historico=valor_historico,
            saldo_atualizado=saldo_atualizado,

            # Non-visible columns
            prioridade=prioridade,
            valor_parcela=valor_parcela,
            parcelas_pagas=parcelas_pagas,
            previsao_pagamento=previsao_pagamento,
            quitado=quitado
        )

        return precatorio

    except Exception as e:
        logger.debug(f"Error parsing precatorio from row: {e}")
        return None


def parse_currency(value_str: str) -> Decimal:
    """
    Parse Brazilian currency format to Decimal
    Examples: 'R$ 131.089.991,20' -> Decimal('131089991.20')
    """
    if not value_str:
        return Decimal('0.00')

    try:
        # Remove currency symbol and whitespace
        value_str = value_str.replace('R$', '').replace(' ', '').strip()

        # Brazilian format: thousands separator is '.', decimal is ','
        # Convert to standard format
        value_str = value_str.replace('.', '')  # Remove thousands separator
        value_str = value_str.replace(',', '.')  # Convert decimal separator

        return Decimal(value_str)

    except Exception as e:
        logger.warning(f"Could not parse currency '{value_str}': {e}")
        return Decimal('0.00')
