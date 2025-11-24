"""
Unit tests for TJRJ Scraper

Run with: pytest tests/ -v --cov=src
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.models import EntidadeDevedora, Precatorio, ScraperConfig
from src.scraper import TJRJPrecatoriosScraper


class TestDataModels:
    """Tests for Pydantic data models"""

    def test_entidade_model_valid(self):
        """Test EntidadeDevedora model with valid data"""
        entidade = EntidadeDevedora(
            id_entidade=1,
            nome_entidade="Test Entity",
            regime="geral",
            precatorios_pagos=10,
            precatorios_pendentes=5,
            valor_prioridade=Decimal("1000.50"),
            valor_rpv=Decimal("500.25")
        )

        assert entidade.id_entidade == 1
        assert entidade.nome_entidade == "Test Entity"
        assert entidade.regime == "geral"
        assert entidade.precatorios_pagos == 10
        assert entidade.precatorios_pendentes == 5

    def test_entidade_model_invalid_regime(self):
        """Test EntidadeDevedora validation fails with invalid regime"""
        with pytest.raises(ValueError):
            EntidadeDevedora(
                id_entidade=1,
                nome_entidade="Test",
                regime="invalid",  # Should fail
                precatorios_pagos=0,
                precatorios_pendentes=0,
                valor_prioridade=Decimal("0"),
                valor_rpv=Decimal("0")
            )

    def test_precatorio_model_valid(self):
        """Test Precatorio model with valid data"""
        precatorio = Precatorio(
            numero_precatorio="001/2024",
            beneficiario="Test Beneficiary",
            valor_original=Decimal("1000.00"),
            valor_atualizado=Decimal("1100.00"),
            tipo="comum",
            status="pendente",
            entidade_devedora="Test Entity",
            id_entidade=1,
            regime="geral"
        )

        assert precatorio.numero_precatorio == "001/2024"
        assert precatorio.tipo == "comum"
        assert precatorio.status == "pendente"
        assert precatorio.regime == "geral"

    def test_precatorio_cpf_validation(self):
        """Test CPF validation"""
        # Valid CPF (11 digits)
        precatorio = Precatorio(
            numero_precatorio="001/2024",
            beneficiario="Test",
            cpf_cnpj_beneficiario="12345678901",
            valor_original=Decimal("1000"),
            valor_atualizado=Decimal("1100"),
            tipo="comum",
            status="pendente",
            entidade_devedora="Test",
            id_entidade=1,
            regime="geral"
        )
        assert precatorio.cpf_cnpj_beneficiario == "12345678901"

        # Valid CNPJ (14 digits)
        precatorio = Precatorio(
            numero_precatorio="002/2024",
            beneficiario="Test",
            cpf_cnpj_beneficiario="12345678901234",
            valor_original=Decimal("1000"),
            valor_atualizado=Decimal("1100"),
            tipo="comum",
            status="pendente",
            entidade_devedora="Test",
            id_entidade=1,
            regime="geral"
        )
        assert precatorio.cpf_cnpj_beneficiario == "12345678901234"

    def test_config_model_defaults(self):
        """Test ScraperConfig default values"""
        config = ScraperConfig()

        assert config.regime == "geral"
        assert config.max_retries == 3
        assert config.enable_cache is True
        assert config.headless is True


class TestScraperUtilities:
    """Tests for scraper utility functions"""

    def test_parse_currency(self):
        """Test currency parsing"""
        scraper = TJRJPrecatoriosScraper()

        assert scraper._parse_currency("R$ 1.000,50") == Decimal("1000.50")
        assert scraper._parse_currency("R$ 100,00") == Decimal("100.00")
        assert scraper._parse_currency("1.234.567,89") == Decimal("1234567.89")
        assert scraper._parse_currency("-") == Decimal("0.00")
        assert scraper._parse_currency("") == Decimal("0.00")

    def test_parse_integer(self):
        """Test integer parsing"""
        scraper = TJRJPrecatoriosScraper()

        assert scraper._parse_integer("123") == 123
        assert scraper._parse_integer("1.234") == 1234
        assert scraper._parse_integer("-") == 0
        assert scraper._parse_integer("") == 0


class TestConfiguration:
    """Tests for configuration management"""

    def test_config_creation(self):
        """Test configuration can be created"""
        config = ScraperConfig(
            regime="especial",
            max_retries=5,
            headless=False
        )

        assert config.regime == "especial"
        assert config.max_retries == 5
        assert config.headless is False


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
