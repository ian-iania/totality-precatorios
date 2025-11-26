"""
Main scraper implementation for TJRJ Precatórios using Playwright (V2 with skip_expanded)

This module implements browser automation to extract precatório data
from the TJRJ portal, handling dynamic content and pagination.

V2 Changes:
- Added skip_expanded flag to optionally skip extraction of 7 expanded fields
- Reduces extraction time by ~68.7% (16s -> 5s per page) when enabled
- CSV output: 11 columns (skip_expanded=True) vs 19 columns (skip_expanded=False)
"""

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
import pandas as pd
from typing import List, Dict, Optional, Tuple
from loguru import logger
import time
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import re

from src.models import EntidadeDevedora, Precatorio, ScraperConfig
from src.config import get_config


class TJRJPrecatoriosScraper:
    """
    Production-ready scraper for TJRJ precatórios data using Playwright

    This class handles all aspects of data extraction including:
    - Browser automation with Playwright
    - Entity card extraction from rendered HTML
    - Precatório data extraction with pagination
    - Error handling and retries
    - Data validation and cleaning
    - CSV export

    Example:
        >>> scraper = TJRJPrecatoriosScraper()
        >>> df = scraper.scrape_regime('geral')
        >>> df.to_csv('precatorios.csv')
    """

    def __init__(self, config: Optional[ScraperConfig] = None, skip_expanded: bool = False):
        """
        Initialize scraper with configuration

        Args:
            config: Optional ScraperConfig instance. If None, loads from environment.
            skip_expanded: If True, skip extraction of 7 expanded fields (reduces time by ~68.7%)
        """
        self.config = config or get_config()
        self.skip_expanded = skip_expanded  # V2: New flag for optional expanded fields
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logger.add(
            "logs/scraper.log",
            rotation="10 MB",
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )

        logger.info(f"🚀 Initializing TJRJ Scraper V2 for regime: {self.config.regime}")
        logger.info(f"⚙️  Config: headless={self.config.headless}, "
                   f"retries={self.config.max_retries}, cache={self.config.enable_cache}")
        if skip_expanded:
            logger.info(f"⚡ Fast mode: skip_expanded=True (extracts 11 columns, ~68% faster)")

    def _parse_currency(self, value: str) -> Decimal:
        """Parse Brazilian currency format to Decimal"""
        if not value or value.strip() == '-':
            return Decimal('0.00')

        # Remove R$, spaces, and convert to standard format
        value = value.replace('R$', '').strip()
        value = value.replace('.', '')  # Remove thousands separator
        value = value.replace(',', '.')  # Replace decimal comma with dot

        try:
            return Decimal(value)
        except:
            logger.warning(f"Failed to parse currency: {value}")
            return Decimal('0.00')

    def _parse_integer(self, value: str) -> int:
        """Parse integer from string"""
        if not value or value.strip() == '-':
            return 0

        # Remove any non-digit characters
        value = re.sub(r'[^\d]', '', value)

        try:
            return int(value) if value else 0
        except:
            logger.warning(f"Failed to parse integer: {value}")
            return 0

    def get_entidades(self, page: Page, regime: str) -> List[EntidadeDevedora]:
        """
        Extracts list of entities (municipalities/institutions) for a regime

        Args:
            page: Playwright Page instance
            regime: 'geral' or 'especial'

        Returns:
            List of EntidadeDevedora instances
        """
        logger.info(f"📋 Fetching entities for regime: {regime}")

        # Navigate to regime page directly
        if regime == 'geral':
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral"
        else:
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-especial"

        logger.info(f"Navigating to {url}")
        page.goto(url, wait_until='networkidle')

        # Wait for AngularJS to render - look for entity data text
        logger.info("Waiting for entity cards to load...")
        try:
            page.wait_for_selector("text=Precatórios Pagos", timeout=15000)
            logger.info("✅ Entity cards loaded")
        except:
            logger.warning("⚠️  Timeout waiting for entity cards")

        # Extra wait for full rendering
        page.wait_for_timeout(3000)

        # Extract entities using text-based parsing
        logger.info("Extracting entity data...")
        entidades = []

        try:
            # Get all text content
            page_text = page.inner_text('body')

            # Find all links with idEntidadeDevedora pattern
            links = page.query_selector_all('a[href*="idEntidadeDevedora"]')
            logger.info(f"Found {len(links)} entity links")

            # Group entities by finding patterns
            # Look for sections containing entity data
            # The page likely has repeating card structures

            # Try to find entity containers
            # Common AngularJS patterns: ng-repeat, cards, panels
            possible_selectors = [
                '[ng-repeat*="entidade"]',
                '[ng-repeat*="ente"]',
                '.card',
                '.panel',
                '[class*="entity"]',
                '[class*="card"]'
            ]

            cards = None
            for selector in possible_selectors:
                cards = page.query_selector_all(selector)
                if cards and len(cards) > 0:
                    logger.info(f"Found {len(cards)} cards with selector: {selector}")
                    break

            if not cards or len(cards) == 0:
                # Fallback: parse by text patterns
                logger.warning("No cards found, using text-based parsing")
                entidades = self._parse_entities_from_text(page_text, links, regime)
            else:
                # Extract from cards
                for i, card in enumerate(cards):
                    try:
                        card_text = card.inner_text()
                        card_html = card.inner_html()

                        # Find entity link to get ID
                        entity_link = card.query_selector('a[href*="idEntidadeDevedora"]')
                        if not entity_link:
                            logger.warning(f"Card {i}: No entity link found")
                            continue

                        href = entity_link.get_attribute('href')
                        # Extract ID from URL: ...?idEntidadeDevedora=86
                        import re
                        id_match = re.search(r'idEntidadeDevedora=(\d+)', href)
                        if not id_match:
                            logger.warning(f"Card {i}: Could not extract entity ID from {href}")
                            continue

                        entity_id = int(id_match.group(1))

                        # Parse entity data from card text
                        entidade = self._parse_entity_from_card_text(
                            card_text, entity_id, regime
                        )

                        if entidade:
                            entidades.append(entidade)
                            logger.debug(f"Extracted: {entidade.nome_entidade} (ID: {entity_id})")

                    except Exception as e:
                        logger.warning(f"Error parsing card {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            raise

        logger.info(f"✅ Found {len(entidades)} entities")
        return entidades

    def _parse_entity_from_card_text(
        self, card_text: str, entity_id: int, regime: str
    ) -> Optional[EntidadeDevedora]:
        """Parse entity data from card text content"""

        lines = [line.strip() for line in card_text.split('\n') if line.strip()]

        # First non-empty line is usually the entity name
        nome = lines[0] if lines else f"Entity {entity_id}"

        # Find statistics by looking for patterns
        precatorios_pagos = 0
        precatorios_pendentes = 0
        valor_prioridade = Decimal('0.00')
        valor_rpv = Decimal('0.00')

        for i, line in enumerate(lines):
            # Look for "Precatórios Pagos:" pattern (value on next line)
            if 'Precatórios Pagos:' in line:
                # Check if value is on same line after colon
                value_text = line.split(':')[-1].strip()
                if value_text:
                    precatorios_pagos = self._parse_integer(value_text)
                elif i + 1 < len(lines):
                    # Value is on next line
                    precatorios_pagos = self._parse_integer(lines[i + 1])

            if 'Precatórios Pendentes:' in line:
                value_text = line.split(':')[-1].strip()
                if value_text:
                    precatorios_pendentes = self._parse_integer(value_text)
                elif i + 1 < len(lines):
                    precatorios_pendentes = self._parse_integer(lines[i + 1])

            if 'Valor Prioridade:' in line:
                value_text = line.split(':')[-1].strip()
                if value_text:
                    valor_prioridade = self._parse_currency(value_text)
                elif i + 1 < len(lines):
                    valor_prioridade = self._parse_currency(lines[i + 1])

            if 'Valor RPV:' in line:
                value_text = line.split(':')[-1].strip()
                if value_text:
                    valor_rpv = self._parse_currency(value_text)
                elif i + 1 < len(lines):
                    valor_rpv = self._parse_currency(lines[i + 1])

        try:
            entidade = EntidadeDevedora(
                id_entidade=entity_id,
                nome_entidade=nome,
                regime=regime,
                precatorios_pagos=precatorios_pagos,
                precatorios_pendentes=precatorios_pendentes,
                valor_prioridade=valor_prioridade,
                valor_rpv=valor_rpv
            )
            return entidade
        except Exception as e:
            logger.warning(f"Failed to create EntidadeDevedora: {e}")
            return None

    def _parse_entities_from_text(
        self, page_text: str, links: list, regime: str
    ) -> List[EntidadeDevedora]:
        """Fallback: parse entities from page text"""
        entidades = []

        for link in links:
            try:
                href = link.get_attribute('href')
                import re
                id_match = re.search(r'idEntidadeDevedora=(\d+)', href)
                if not id_match:
                    continue

                entity_id = int(id_match.group(1))

                # Get link text as entity name (might be truncated)
                nome = link.inner_text().strip() or f"Entity {entity_id}"

                # Create basic entity (statistics will be 0)
                entidade = EntidadeDevedora(
                    id_entidade=entity_id,
                    nome_entidade=nome,
                    regime=regime,
                    precatorios_pagos=0,
                    precatorios_pendentes=0,
                    valor_prioridade=Decimal('0.00'),
                    valor_rpv=Decimal('0.00')
                )
                entidades.append(entidade)

            except Exception as e:
                logger.warning(f"Error parsing link: {e}")
                continue

        return entidades

    def get_precatorios_entidade(
        self,
        page: Page,
        entidade: EntidadeDevedora
    ) -> List[Precatorio]:
        """
        Extracts all precatórios for an entity (handles pagination)

        Args:
            page: Playwright Page instance
            entidade: EntidadeDevedora instance

        Returns:
            List of Precatorio instances
        """
        logger.info(f"🔄 Extracting precatórios for: {entidade.nome_entidade}")

        all_precatorios = []

        # Navigate to precatório list page for this entity
        url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entidade.id_entidade}"
        logger.info(f"Navigating to: {url}")

        page.goto(url, wait_until='networkidle')

        # Wait for content to load
        try:
            # Wait for table header first
            page.wait_for_selector("text=/Número.*Precatório/i", timeout=10000)
            logger.info("✅ Table header found")

            # Then wait for actual table data (cells with content)
            page.wait_for_selector("tbody tr td", timeout=10000)
            logger.info("✅ Table rows found")

            # Wait for cells to populate with data (AngularJS async)
            page.wait_for_timeout(3000)

            # Verify data is actually loaded
            try:
                page.wait_for_function("""
                    () => {
                        const cells = document.querySelectorAll('tbody tr td');
                        return cells.length > 0 &&
                               Array.from(cells).some(cell => cell.innerText.trim().length > 0);
                    }
                """, timeout=5000)
                logger.info("✅ Table data populated")
            except:
                logger.warning("⚠️  Table data may not be fully populated")

        except Exception as e:
            logger.warning(f"⚠️  Error waiting for precatório list: {e}")

        page.wait_for_timeout(1000)

        # Extract precatórios with pagination
        page_num = 1

        while True:
            logger.info(f"📄 Processing page {page_num}...")

            try:
                # Extract precatórios from current page
                precatorios_page = self._extract_precatorios_from_page(page, entidade)
                all_precatorios.extend(precatorios_page)

                logger.info(f"  Extracted {len(precatorios_page)} precatórios from page {page_num}")

                # Check for next page button
                # Look for "Próxima" or pagination buttons
                next_button = None

                # Try different selectors for next button
                next_selectors = [
                    "text=Próxima",
                    "text=Próximo",
                    "text=Next",
                    "button:has-text('Próxima')",
                    "a:has-text('Próxima')",
                    "[aria-label*='next' i]",
                    "[aria-label*='próxima' i]"
                ]

                for selector in next_selectors:
                    try:
                        next_button = page.query_selector(selector)
                        if next_button:
                            # Check if button is disabled
                            is_disabled = next_button.get_attribute('disabled')
                            is_aria_disabled = next_button.get_attribute('aria-disabled')
                            class_attr = next_button.get_attribute('class') or ''

                            if is_disabled or is_aria_disabled == 'true' or 'disabled' in class_attr:
                                logger.info(f"  Next button is disabled (selector: {selector})")
                                next_button = None
                            else:
                                logger.info(f"  Found active next button (selector: {selector})")
                                break
                    except:
                        continue

                if not next_button:
                    logger.info("  No more pages (next button not found or disabled)")
                    break

                # Click next button
                logger.info("  Clicking next page...")
                next_button.click()

                # Wait for new page to load
                page.wait_for_timeout(2000)
                page.wait_for_load_state('networkidle')

                page_num += 1

                # Safety limit to prevent infinite loops (increased for large datasets)
                if page_num > 5000:
                    logger.warning("  ⚠️  Reached safety limit (5000 pages = 50,000 records), stopping")
                    logger.warning(f"  If more records exist, please investigate pagination logic")
                    break

            except Exception as e:
                logger.error(f"  Error on page {page_num}: {e}")
                break

        logger.info(f"✅ Total extracted: {len(all_precatorios)} precatórios")
        return all_precatorios

    def _extract_precatorios_from_page(
        self,
        page: Page,
        entidade: EntidadeDevedora
    ) -> List[Precatorio]:
        """Extract precatórios from current page with expanded details"""

        precatorios = []

        try:
            # Wait for loading overlay to disappear (appears during page transitions)
            try:
                page.wait_for_selector('.block-ui-overlay', state='hidden', timeout=5000)
            except:
                pass  # Overlay may not be present

            # Wait for AngularJS to stabilize after page load/navigation
            page.wait_for_timeout(1500)

            # Find rows with ng-repeat-start (these are the main precatório rows)
            rows = page.query_selector_all('tbody tr[ng-repeat-start]')

            if not rows or len(rows) == 0:
                logger.warning("No precatório rows found")
                return precatorios

            logger.debug(f"Found {len(rows)} precatório rows on page")

            # Extract from each row
            for idx in range(len(rows)):
                try:
                    # RE-QUERY rows freshly for this iteration to avoid stale elements
                    # This is critical because AngularJS may re-render DOM during interactions
                    fresh_rows = page.query_selector_all('tbody tr[ng-repeat-start]')

                    if idx >= len(fresh_rows):
                        logger.debug(f"Row index {idx} no longer available after re-query")
                        continue

                    row = fresh_rows[idx]
                    row_text = row.inner_text()

                    # Skip empty rows or header rows
                    if not row_text.strip() or 'Número' in row_text:
                        continue

                    # Parse row with expanded details (V2: pass None if skip_expanded)
                    precatorio = self._parse_precatorio_from_row(
                        row, row_text, entidade,
                        page if not self.skip_expanded else None,  # V2: KEY CHANGE
                        idx
                    )

                    if precatorio:
                        precatorios.append(precatorio)

                except Exception as e:
                    logger.debug(f"Error parsing row {idx}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error extracting precatórios from page: {e}")

        return precatorios

    def _parse_precatorio_from_row(
        self,
        row,
        row_text: str,
        entidade: EntidadeDevedora,
        page: Page,
        row_index: int
    ) -> Optional[Precatorio]:
        """
        Parse precatório from table row with visible columns + expanded details

        CORRECTED table structure (visible columns):
        Cell 2:  Ordem (e.g., "2º", "4º")
        Cell 6:  Entidade Devedora - SPECIFIC entity (e.g., "IPERJ", "RIO-PREVIDÊNCIA")
        Cell 7:  Número Precatório (e.g., "1998.03464-7")
        Cell 8:  Situação (e.g., "Dispensa de Provisionamento")
        Cell 9:  Natureza (e.g., "Comum", "Alimentícia")
        Cell 10: Orçamento (e.g., "1999", "2011")
        Cell 12: Valor Histórico (e.g., "R$ 131.089.991,20")
        Cell 14: Saldo Atualizado (e.g., "R$ 1.129.909.880,35")

        Expanded details (from + button):
        - Classe, Localização, Petições a Juntar, Última fase
        - Possui Herdeiros, Possui Cessão, Possui Retificador

        NOTE: entidade parameter contains the GROUP/PARENT entity clicked from the card
              Cell 6 contains the SPECIFIC entity responsible for this precatório
              These can be DIFFERENT! (e.g., "Estado do RJ e Afins" vs "IPERJ")
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
            valor_historico = self._parse_currency(valor_historico_text) if valor_historico_text else Decimal('0.00')

            # Saldo Atualizado (Cell 14)
            saldo_atualizado_text = cell_texts[14] if len(cell_texts) > 14 else ""
            saldo_atualizado = self._parse_currency(saldo_atualizado_text) if saldo_atualizado_text else valor_historico

            # === EXTRACT EXPANDED DETAILS ===

            # Extract details by clicking the + button (V2: only if page is provided)
            if page is not None:
                expanded_details = self._extract_expanded_details(row, page, row_index)
            else:
                # V2: skip_expanded=True, return empty dict (faster extraction)
                expanded_details = {}

            # === CREATE PRECATORIO OBJECT ===

            precatorio = Precatorio(
                # Entity info - TWO LEVELS
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

                # Expanded details
                classe=expanded_details.get('Classe'),
                localizacao=expanded_details.get('Localização'),
                peticoes_a_juntar=expanded_details.get('Petições a Juntar'),
                ultima_fase=expanded_details.get('Última fase'),
                possui_herdeiros=expanded_details.get('Possui Herdeiros'),
                possui_cessao=expanded_details.get('Possui Cessão'),
                possui_retificador=expanded_details.get('Possui Retificador')
            )

            return precatorio

        except Exception as e:
            logger.debug(f"Error parsing precatorio from row: {e}")
            return None

    def _extract_expanded_details(
        self,
        row,
        page: Page,
        row_index: int
    ) -> dict:
        """
        Extract expanded details by clicking the + button

        Returns dict with keys:
        - Classe, Localização, Petições a Juntar, Última fase
        - Possui Herdeiros, Possui Cessão, Possui Retificador
        """

        details = {}
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Wait for any loading overlay to disappear before interacting
                try:
                    page.wait_for_selector('.block-ui-overlay', state='hidden', timeout=2000)
                except:
                    pass  # Overlay may not be present

                # Re-query the row to get fresh element handle (avoid stale references)
                fresh_rows = page.query_selector_all('tbody tr[ng-repeat-start]')

                if row_index >= len(fresh_rows):
                    logger.debug(f"Row {row_index}: Not found in fresh query")
                    return details

                fresh_row = fresh_rows[row_index]

                # Find the toggle button in this fresh row
                toggle_btn = fresh_row.query_selector('td.toggle-preca')

                if not toggle_btn:
                    logger.debug(f"Row {row_index}: Toggle button not found")
                    return details

                # Click to expand with retry
                try:
                    toggle_btn.click()
                    page.wait_for_timeout(1000)  # Wait for expansion animation + AngularJS digest
                except Exception as click_error:
                    if attempt < max_retries - 1:
                        logger.debug(f"Row {row_index}: Click failed (attempt {attempt + 1}), retrying...")
                        page.wait_for_timeout(500 * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        raise click_error

                # Find all detail containers on the page
                detail_containers = page.query_selector_all('td[colspan] .row-detail-container')

                # Since we expand/collapse one at a time, there should be only ONE visible detail
                if len(detail_containers) > 0:
                    # Take the first (and should be only) visible detail container
                    detail_div = detail_containers[0]

                    # Find the details table
                    detail_table = detail_div.query_selector('table.table-condensed')

                    if detail_table:
                        # Get all rows from details table (skip header)
                        detail_rows = detail_table.query_selector_all('tbody tr')

                        for detail_row in detail_rows:
                            cells = detail_row.query_selector_all('td')
                            if len(cells) >= 2:
                                label = cells[0].inner_text().strip()
                                value = cells[1].inner_text().strip()
                                details[label] = value if value else None
                else:
                    logger.debug(f"Row {row_index}: No detail containers found after expansion")

                # Re-query the row again before collapsing (element may be stale)
                fresh_rows_collapse = page.query_selector_all('tbody tr[ng-repeat-start]')
                if row_index < len(fresh_rows_collapse):
                    fresh_row_collapse = fresh_rows_collapse[row_index]
                    toggle_btn_collapse = fresh_row_collapse.query_selector('td.toggle-preca')
                    if toggle_btn_collapse:
                        try:
                            toggle_btn_collapse.click()
                            page.wait_for_timeout(300)
                        except:
                            pass  # Ignore collapse errors

                # Success - break retry loop
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"Row {row_index}: Error (attempt {attempt + 1}/{max_retries}): {e}")
                    page.wait_for_timeout(500 * (attempt + 1))  # Exponential backoff
                else:
                    logger.debug(f"Row {row_index}: Failed after {max_retries} attempts: {e}")

        return details

    def _parse_precatorios_from_text(
        self,
        page_text: str,
        entidade: EntidadeDevedora
    ) -> List[Precatorio]:
        """Fallback: parse precatórios from raw text"""

        precatorios = []

        # This is a very basic fallback
        # Ideally we'd have structured data

        logger.warning("Using text-based fallback for precatório extraction")

        # Split into lines and look for precatório numbers
        lines = page_text.split('\n')

        for i, line in enumerate(lines):
            if '/' in line and any(char.isdigit() for char in line):
                # Might be a precatório number
                try:
                    precatorio = Precatorio(
                        numero_precatorio=line.strip(),
                        beneficiario="Desconhecido",
                        valor_original=Decimal('0.00'),
                        valor_atualizado=Decimal('0.00'),
                        tipo='comum',
                        status='pendente',
                        entidade_devedora=entidade.nome_entidade,
                        id_entidade=entidade.id_entidade,
                        regime=entidade.regime
                    )
                    precatorios.append(precatorio)
                except:
                    continue

        return precatorios

    def scrape_regime(self, regime: str) -> pd.DataFrame:
        """
        Scrapes ALL data for a regime (main entry point) with detailed progress tracking

        Args:
            regime: 'geral' or 'especial'

        Returns:
            DataFrame with all precatórios
        """
        logger.info(f"🎯 Starting full scrape for regime: {regime}")
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create performance log file
        perf_log_file = Path(f"logs/performance_{regime}_{timestamp}.log")
        perf_log_file.parent.mkdir(parents=True, exist_ok=True)

        all_data = []
        entity_times = []  # Track time per entity for estimation

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.config.headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            try:
                # Step 1: Get all entities
                entidades = self.get_entidades(page, regime)

                if not entidades:
                    logger.warning("⚠️  No entities found!")
                    return pd.DataFrame()

                logger.info(f"\n📊 Total entities to process: {len(entidades)}")
                logger.info(f"💾 Performance log: {perf_log_file}\n")

                # Step 2: Extract precatórios from each entity
                for i, entidade in enumerate(entidades, 1):
                    entity_start = time.time()

                    # Calculate progress and estimates
                    progress_pct = (i-1) / len(entidades) * 100
                    elapsed_total = time.time() - start_time

                    # Dynamic time estimation based on actual performance
                    if len(entity_times) > 0:
                        avg_time_per_entity = sum(entity_times) / len(entity_times)
                        remaining_entities = len(entidades) - i + 1
                        estimated_remaining = avg_time_per_entity * remaining_entities
                        eta_minutes = estimated_remaining / 60
                        eta_hours = eta_minutes / 60

                        if eta_hours >= 1:
                            eta_str = f"{eta_hours:.1f}h"
                        else:
                            eta_str = f"{eta_minutes:.1f}min"
                    else:
                        eta_str = "calculating..."

                    logger.info(f"\n{'='*80}")
                    logger.info(f"[{i}/{len(entidades)}] ({progress_pct:.1f}%) {entidade.nome_entidade}")
                    logger.info(f"📈 Progress: {len(all_data)} precatórios extracted so far")
                    logger.info(f"⏱️  Elapsed: {elapsed_total/60:.1f}min | ETA: {eta_str}")
                    logger.info(f"{'='*80}")

                    try:
                        precatorios = self.get_precatorios_entidade(page, entidade)
                        entity_elapsed = time.time() - entity_start
                        entity_times.append(entity_elapsed)

                        # Convert to dict for DataFrame
                        for p in precatorios:
                            all_data.append(p.model_dump())

                        # Log performance to file
                        with open(perf_log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{datetime.now().isoformat()}|{regime}|{entidade.id_entidade}|"
                                   f"{entidade.nome_entidade}|{len(precatorios)}|{entity_elapsed:.2f}s\n")

                        logger.info(f"✅ Extracted {len(precatorios)} precatórios in {entity_elapsed:.1f}s "
                                  f"({len(precatorios)/entity_elapsed:.1f} rec/s)")

                    except Exception as e:
                        logger.error(f"❌ Failed to process {entidade.nome_entidade}: {e}")
                        entity_elapsed = time.time() - entity_start
                        with open(perf_log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{datetime.now().isoformat()}|{regime}|{entidade.id_entidade}|"
                                   f"{entidade.nome_entidade}|ERROR|{entity_elapsed:.2f}s|{str(e)}\n")
                        continue

            except Exception as e:
                logger.error(f"❌ Scraping failed: {e}")
                raise
            finally:
                browser.close()

        # Step 3: Create DataFrame
        df = pd.DataFrame(all_data)

        elapsed = time.time() - start_time
        elapsed_hours = elapsed / 3600
        elapsed_minutes = elapsed / 60

        # Write final summary to performance log
        with open(perf_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"FINAL SUMMARY - {regime.upper()}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Total records: {len(df)}\n")
            f.write(f"Entities processed: {len([t for t in entity_times])}\n")
            f.write(f"Entities failed: {len(entidades) - len([t for t in entity_times])}\n")
            f.write(f"Total time: {elapsed_hours:.2f}h ({elapsed_minutes:.1f}min)\n")
            if len(df) > 0:
                f.write(f"Records/second: {len(df)/elapsed:.2f}\n")
                f.write(f"Avg time per entity: {sum(entity_times)/len(entity_times):.1f}s\n")

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ Scraping complete for regime: {regime}")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total records: {len(df)}")
        logger.info(f"🏢 Entities processed: {len([t for t in entity_times])}/{len(entidades)}")
        logger.info(f"⏱️  Time elapsed: {elapsed_hours:.2f}h ({elapsed_minutes:.1f}min)")
        if len(df) > 0:
            logger.info(f"⚡ Records/second: {len(df)/elapsed:.2f}")
            logger.info(f"📈 Avg time per entity: {sum(entity_times)/len(entity_times):.1f}s")
        logger.info(f"💾 Performance log saved: {perf_log_file}")
        logger.info(f"{'='*80}\n")

        return df

    def save_to_csv(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None
    ) -> str:
        """
        Saves DataFrame to CSV with Brazilian formatting

        Args:
            df: DataFrame to save
            filename: Optional filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"precatorios_{self.config.regime}_{timestamp}.csv"

        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / filename

        if df.empty:
            logger.warning("⚠️  DataFrame is empty, creating empty CSV")
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        else:
            # Save with UTF-8 encoding and Brazilian formatting
            df.to_csv(
                filepath,
                index=False,
                encoding='utf-8-sig',  # BOM for Excel compatibility
                sep=';',  # Semicolon for better Excel support in Brazil
                decimal=',',  # Brazilian decimal format
                date_format='%Y-%m-%d'
            )

        logger.info(f"💾 Saved to: {filepath}")
        logger.info(f"   Size: {filepath.stat().st_size / 1024:.1f} KB")

        return str(filepath)
