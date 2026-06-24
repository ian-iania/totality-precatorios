from decimal import Decimal

from src.models import EntidadeDevedora, ScraperConfig
from src.scraper_v3 import TJRJPrecatoriosScraperV3


class FakeCell:
    def __init__(self, text):
        self.text = text

    def inner_text(self):
        return self.text


class FakeRow:
    def __init__(self, texts):
        self.cells = [FakeCell(text) for text in texts]

    def query_selector_all(self, selector):
        assert selector == "td"
        return self.cells


def test_parse_precatorio_compact_nine_cell_layout():
    scraper = TJRJPrecatoriosScraperV3(
        config=ScraperConfig(regime="especial", log_level="ERROR"),
        skip_expanded=True,
    )
    entidade = EntidadeDevedora(
        id_entidade=1,
        nome_entidade="Estado do Rio de Janeiro",
        regime="especial",
        precatorios_pagos=0,
        precatorios_pendentes=20124,
        valor_prioridade=Decimal("0.00"),
        valor_rpv=Decimal("0.00"),
    )
    row = FakeRow(
        [
            "",
            "2o",
            "Estado do Rio de Janeiro",
            "1998.03464-7",
            "Dispensa de Provisionamento",
            "Comum",
            "1999",
            "R$ 131.089.991,20",
            "R$ 1.099.754.334,39",
        ]
    )

    precatorio = scraper._parse_precatorio_from_row(
        row=row,
        row_text="Estado do Rio de Janeiro 1998.03464-7",
        entidade=entidade,
        page=None,
        row_index=0,
    )

    assert precatorio is not None
    assert precatorio.ordem == "2o"
    assert precatorio.entidade_devedora == "Estado do Rio de Janeiro"
    assert precatorio.numero_precatorio == "1998.03464-7"
    assert precatorio.situacao == "Dispensa de Provisionamento"
    assert precatorio.natureza == "Comum"
    assert precatorio.orcamento == "1999"
    assert precatorio.valor_historico == Decimal("131089991.20")
    assert precatorio.saldo_atualizado == Decimal("1099754334.39")

