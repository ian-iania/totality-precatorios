"""
CORRECTED Pydantic models for TJRJ Precatórios data
Based on ACTUAL columns available on the website
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class EntidadeDevedora(BaseModel):
    """Entity (municipality/institution) owing precatórios"""

    id_entidade: int = Field(..., description="Unique entity identifier")
    nome_entidade: str = Field(..., min_length=1, max_length=500)
    regime: str = Field(..., pattern=r'^(geral|especial)$')
    precatorios_pagos: int = Field(ge=0)
    precatorios_pendentes: int = Field(ge=0)
    valor_prioridade: Decimal = Field(ge=0, decimal_places=2)
    valor_rpv: Decimal = Field(ge=0, decimal_places=2)
    timestamp_extracao: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_encoders": {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    }


class Precatorio(BaseModel):
    """
    Individual precatório record

    CORRECTED to match ACTUAL website columns:
    - 8 visible columns
    - 5 non-visible columns (hidden in UI but in HTML)
    - TWO entity levels (grupo + devedora)
    """

    # === ENTITY INFORMATION (TWO LEVELS) ===
    entidade_grupo: str = Field(..., description="Parent/Group entity name (from card clicked)")
    id_entidade_grupo: int = Field(..., description="Parent/Group entity ID")
    entidade_devedora: str = Field(..., description="Specific entity responsible (from table Cell 6)")
    regime: str = Field(..., pattern=r'^(geral|especial)$', description="Regime type")

    ordem: str = Field(..., description="Order position (e.g., '2º', '4º') - Cell 2")
    numero_precatorio: str = Field(..., min_length=1, description="Precatório number - Cell 7")
    situacao: str = Field(..., description="Status/Situation - Cell 8")
    natureza: str = Field(..., description="Nature (Comum/Alimentícia) - Cell 9")
    orcamento: str = Field(..., description="Budget year - Cell 10")
    valor_historico: Decimal = Field(ge=0, decimal_places=2, description="Historical value - Cell 12")
    saldo_atualizado: Decimal = Field(ge=0, decimal_places=2, description="Updated balance - Cell 14")

    # === NON-VISIBLE COLUMNS (hidden in UI but available in HTML) ===
    prioridade: Optional[str] = Field(None, description="Priority - Cell 11 (hidden)")
    valor_parcela: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Installment value - Cell 13 (hidden)")
    parcelas_pagas: Optional[str] = Field(None, description="Installments paid (e.g., '5/5') - Cell 15 (hidden)")
    previsao_pagamento: Optional[str] = Field(None, description="Payment forecast - Cell 16 (hidden)")
    quitado: Optional[str] = Field(None, description="Settled (Sim/Não) - Cell 17 (hidden)")

    # === METADATA ===
    timestamp_extracao: datetime = Field(default_factory=datetime.now, description="Extraction timestamp")

    model_config = {
        "json_encoders": {
            Decimal: lambda v: float(v) if v else None,
            datetime: lambda v: v.isoformat()
        }
    }


class ScraperConfig(BaseModel):
    """Configuration for scraper behavior"""

    base_url: str = "https://www.tjrj.jus.br/web/precatorios"
    regime: str = Field(default='geral', pattern=r'^(geral|especial)$')
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=2.0, ge=0.5, le=60.0)
    page_load_timeout: int = Field(default=30000, ge=5000, le=120000)
    enable_cache: bool = True
    cache_dir: str = "data/cache"
    output_dir: str = "data/processed"
    log_level: str = Field(default="INFO", pattern=r'^(DEBUG|INFO|WARNING|ERROR)$')
    headless: bool = True

    model_config = {
        "env_prefix": 'TJRJ_'
    }
