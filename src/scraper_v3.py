"""
Main scraper implementation for TJRJ Precatórios using Playwright (V3 with page range parallelization)

This module implements browser automation to extract precatório data
from the TJRJ portal, handling dynamic content and pagination.

V3 Changes (based on V2):
- Added goto_page_direct() method for direct page navigation via "Ir para página:" input field
- Added extract_page_range() method for extracting specific page ranges
- Enables parallelization by dividing large entities (e.g., Estado RJ) into page ranges
- Expected performance: 76-91% reduction in time for Estado RJ (15h -> 1.4-3.6h)

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


class TJRJPrecatoriosScraperV3:
    """
    V3 scraper with page range parallelization support

    This class extends V2 functionality with:
    - Direct page navigation via "Ir para página:" input field
    - Page range extraction for parallelization
    - Support for multi-process extraction of large datasets

    Example:
        >>> # Sequential extraction (V2 behavior)
        >>> scraper = TJRJPrecatoriosScraperV3()
        >>> df = scraper.scrape_regime('geral')

        >>> # Range extraction for parallelization
        >>> precatorios = scraper.extract_page_range(
        ...     entidade=estado_rj,
        ...     start_page=1,
        ...     end_page=746,
        ...     skip_expanded=True,
        ...     process_id=1
        ... )
    """

    def __init__(self, config: Optional[ScraperConfig] = None, skip_expanded: bool = False):
        """
        Initialize scraper with configuration

        Args:
            config: Optional ScraperConfig instance. If None, loads from environment.
            skip_expanded: If True, skip extraction of 7 expanded fields (reduces time by ~68.7%)
        """
        self.config = config or get_config()
        self.skip_expanded = skip_expanded
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logger.add(
            "logs/scraper_v3.log",
            rotation="10 MB",
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )

        logger.info(f"🚀 Initializing TJRJ Scraper V3 for regime: {self.config.regime}")
        logger.info(f"⚙️  Config: headless={self.config.headless}, "
                   f"retries={self.config.max_retries}, cache={self.config.enable_cache}")
        if skip_expanded:
            logger.info(f"⚡ Fast mode: skip_expanded=True (extracts 11 columns, ~68% faster)")

    # ============================================================================
    # V3 NEW METHODS - Page Range Navigation
    # ============================================================================

    def goto_page_direct(self, page: Page, page_number: int) -> bool:
        """
        Navigate directly to a specific page using "Ir para página:" input field

        This is the KEY V3 feature that enables parallelization by page ranges.

        Args:
            page: Playwright Page instance
            page_number: Target page number (1-based, e.g., 1, 100, 1500, 2984)

        Returns:
            True if navigation succeeded, False otherwise

        Implementation:
            1. Find "Ir para página:" input field
            2. Clear existing value and fill with page_number
            3. Press Enter to trigger navigation
            4. Wait for page to load and AngularJS to stabilize

        TODO: Selector needs investigation! Current selector is a PLACEHOLDER.
              Before production use, run this in browser console to find correct selector:

              document.querySelector('input[type="text"]')  // Generic - too broad
              document.querySelector('input[aria-label*="página"]')  // If aria-label exists
              document.querySelector('.pagination input')  // If wrapped in pagination div

              Recommended approach:
              1. Open TJRJ in browser with DevTools
              2. Inspect "Ir para página:" input field
              3. Test selector in console: document.querySelector('YOUR_SELECTOR')
              4. Update PAGE_INPUT_SELECTOR constant below
        """

        # ✅ CONFIRMED WORKING SELECTOR (tested 2025-11-26)
        # The page input field uses AngularJS ng-model="vm.PaginaText"
        # This is the MOST RELIABLE selector:
        PAGE_INPUT_SELECTORS = [
            'input[ng-model="vm.PaginaText"]',  # ✅ PRIMARY - AngularJS model (CONFIRMED)
            'input.text-center.input-width-40-important',  # ✅ BACKUP - CSS classes
            '.pagination input[type="text"]',  # Fallback - inside pagination
            'input[type="text"]'  # Last resort - generic
        ]

        logger.debug(f"Attempting direct navigation to page {page_number}")

        try:
            # Wait for any loading overlay to disappear first
            try:
                page.wait_for_selector('.block-ui-overlay', state='hidden', timeout=2000)
            except:
                pass

            # Try each selector until one works
            page_input = None
            used_selector = None

            for selector in PAGE_INPUT_SELECTORS:
                try:
                    page_input = page.query_selector(selector)
                    if page_input:
                        # Verify it's visible and enabled
                        if page_input.is_visible() and page_input.is_enabled():
                            used_selector = selector
                            logger.debug(f"Found page input with selector: {selector}")
                            break
                except:
                    continue

            if not page_input:
                logger.error("❌ Page input field not found! Selector needs investigation.")
                logger.error("   Run with --no-headless and inspect the 'Ir para página:' field")
                logger.error("   Update PAGE_INPUT_SELECTORS in scraper_v3.py")
                return False

            # Clear existing value
            page_input.click()
            page_input.fill('')  # Clear

            # Fill with target page number
            page_input.fill(str(page_number))

            # Press Enter to navigate
            page_input.press('Enter')

            # Wait for navigation to complete
            logger.debug(f"Waiting for page {page_number} to load...")
            page.wait_for_timeout(2000)  # AngularJS stabilization
            page.wait_for_load_state('networkidle')

            # Wait for table data to populate
            try:
                page.wait_for_selector('tbody tr[ng-repeat-start]', timeout=5000)
                logger.debug(f"✅ Page {page_number} loaded successfully")
            except:
                logger.warning(f"⚠️  Table rows not found after navigation to page {page_number}")
                return False

            # Extra wait for AngularJS digest cycle
            page.wait_for_timeout(1000)

            logger.info(f"✅ Successfully navigated to page {page_number}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to navigate to page {page_number}: {e}")
            return False

    def extract_page_range(
        self,
        page: Page,
        entidade: EntidadeDevedora,
        start_page: int,
        end_page: int,
        process_id: Optional[int] = None
    ) -> List[Precatorio]:
        """
        Extract precatórios from a specific page range

        This method is designed for parallel processing. Multiple processes can extract
        different page ranges simultaneously.

        Args:
            page: Playwright Page instance (should be already navigated to entity)
            entidade: EntidadeDevedora instance
            start_page: Starting page number (1-based, inclusive)
            end_page: Ending page number (1-based, inclusive)
            process_id: Optional process identifier for logging

        Returns:
            List of Precatorio instances extracted from the range

        Example:
            >>> # Process 1: Pages 1-746
            >>> precatorios_p1 = scraper.extract_page_range(page, estado_rj, 1, 746, process_id=1)

            >>> # Process 2: Pages 747-1492
            >>> precatorios_p2 = scraper.extract_page_range(page, estado_rj, 747, 1492, process_id=2)

        Performance:
            - Sequential (V2): ~2,984 pages × 16s = ~13.3h (with expanded fields)
            - Parallel V3 (4 proc): ~746 pages × 16s = ~3.3h per process (concurrent)
            - Parallel V3 + skip: ~746 pages × 5s = ~1h per process (FASTEST)
        """

        proc_label = f"[P{process_id}]" if process_id is not None else ""
        logger.info(f"{proc_label} Starting range extraction: pages {start_page}-{end_page}")
        logger.info(f"{proc_label} 🔧 Using OPTION A: Full direct navigation (most reliable)")

        all_precatorios = []

        try:
            # OPTION A: Navigate directly to EACH page (most reliable for large ranges)
            # This avoids sequential click issues with overlay timeouts
            current_page = start_page

            while current_page <= end_page:
                logger.info(f"{proc_label} Extracting page {current_page}/{end_page} "
                          f"({(current_page - start_page + 1)}/{end_page - start_page + 1} in range)...")

                try:
                    # Navigate directly to current page (except page 1 which is default)
                    if current_page > 1:
                        success = self.goto_page_direct(page, current_page)

                        if not success:
                            logger.error(f"{proc_label} ❌ Failed to navigate to page {current_page}")
                            logger.warning(f"{proc_label} Stopping extraction at page {current_page - 1}")
                            break

                    # Extract from current page
                    precatorios_page = self._extract_precatorios_from_page(page, entidade)
                    all_precatorios.extend(precatorios_page)

                    logger.info(f"{proc_label}   ✅ Extracted {len(precatorios_page)} precatórios "
                              f"(total: {len(all_precatorios)})")

                    current_page += 1

                except Exception as e:
                    logger.error(f"{proc_label} ❌ Error extracting page {current_page}: {e}")
                    logger.warning(f"{proc_label} Stopping extraction at page {current_page - 1}")
                    break

            logger.info(f"{proc_label} ✅ Range extraction complete: {len(all_precatorios)} precatórios "
                      f"from pages {start_page}-{current_page - 1}")

        except Exception as e:
            logger.error(f"{proc_label} ❌ Range extraction failed: {e}")

        return all_precatorios

    # ============================================================================
    # V2 METHODS (Inherited from scraper_v2.py with minor adaptations)
    # ============================================================================

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
        (Same as V2 implementation)
        """
        logger.info(f"📋 Fetching entities for regime: {regime}")

        # Navigate to regime page directly
        if regime == 'geral':
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral"
        else:
            url = "https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-especial"

        logger.info(f"Navigating to {url}")
        page.goto(url, wait_until='networkidle')

        # Wait for AngularJS to render
        logger.info("Waiting for entity cards to load...")
        try:
            page.wait_for_selector("text=Precatórios Pagos", timeout=15000)
            logger.info("✅ Entity cards loaded")
        except:
            logger.warning("⚠️  Timeout waiting for entity cards")

        page.wait_for_timeout(3000)

        # Extract entities
        logger.info("Extracting entity data...")
        entidades = []

        try:
            page_text = page.inner_text('body')
            links = page.query_selector_all('a[href*="idEntidadeDevedora"]')
            logger.info(f"Found {len(links)} entity links")

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
                logger.warning("No cards found, using text-based parsing")
                entidades = self._parse_entities_from_text(page_text, links, regime)
            else:
                for i, card in enumerate(cards):
                    try:
                        card_text = card.inner_text()
                        entity_link = card.query_selector('a[href*="idEntidadeDevedora"]')
                        if not entity_link:
                            continue

                        href = entity_link.get_attribute('href')
                        id_match = re.search(r'idEntidadeDevedora=(\d+)', href)
                        if not id_match:
                            continue

                        entity_id = int(id_match.group(1))
                        entidade = self._parse_entity_from_card_text(card_text, entity_id, regime)

                        if entidade:
                            entidades.append(entidade)

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
        nome = lines[0] if lines else f"Entity {entity_id}"

        precatorios_pagos = 0
        precatorios_pendentes = 0
        valor_prioridade = Decimal('0.00')
        valor_rpv = Decimal('0.00')

        for i, line in enumerate(lines):
            if 'Precatórios Pagos:' in line:
                value_text = line.split(':')[-1].strip()
                if value_text:
                    precatorios_pagos = self._parse_integer(value_text)
                elif i + 1 < len(lines):
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
            return EntidadeDevedora(
                id_entidade=entity_id,
                nome_entidade=nome,
                regime=regime,
                precatorios_pagos=precatorios_pagos,
                precatorios_pendentes=precatorios_pendentes,
                valor_prioridade=valor_prioridade,
                valor_rpv=valor_rpv
            )
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
                id_match = re.search(r'idEntidadeDevedora=(\d+)', href)
                if not id_match:
                    continue

                entity_id = int(id_match.group(1))
                nome = link.inner_text().strip() or f"Entity {entity_id}"

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
        (Same as V2 implementation - sequential)

        For page range extraction, use extract_page_range() instead.
        """
        logger.info(f"🔄 Extracting precatórios for: {entidade.nome_entidade}")

        all_precatorios = []

        # Navigate to precatório list page for this entity
        url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entidade.id_entidade}"
        logger.info(f"Navigating to: {url}")

        page.goto(url, wait_until='networkidle')

        # Wait for content to load
        try:
            page.wait_for_selector("text=/Número.*Precatório/i", timeout=10000)
            page.wait_for_selector("tbody tr td", timeout=10000)
            page.wait_for_timeout(3000)

            try:
                page.wait_for_function("""
                    () => {
                        const cells = document.querySelectorAll('tbody tr td');
                        return cells.length > 0 &&
                               Array.from(cells).some(cell => cell.innerText.trim().length > 0);
                    }
                """, timeout=5000)
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
                precatorios_page = self._extract_precatorios_from_page(page, entidade)
                all_precatorios.extend(precatorios_page)

                logger.info(f"  Extracted {len(precatorios_page)} precatórios from page {page_num}")

                # Check for next page button
                next_button = None

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

                logger.info("  Clicking next page...")
                next_button.click()

                page.wait_for_timeout(2000)
                page.wait_for_load_state('networkidle')

                page_num += 1

                if page_num > 5000:
                    logger.warning("  ⚠️  Reached safety limit (5000 pages = 50,000 records), stopping")
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
        """Extract precatórios from current page (same as V2)"""
        precatorios = []

        try:
            try:
                page.wait_for_selector('.block-ui-overlay', state='hidden', timeout=5000)
            except:
                pass

            page.wait_for_timeout(1500)

            rows = page.query_selector_all('tbody tr[ng-repeat-start]')

            if not rows or len(rows) == 0:
                logger.warning("No precatório rows found")
                return precatorios

            for idx in range(len(rows)):
                try:
                    fresh_rows = page.query_selector_all('tbody tr[ng-repeat-start]')

                    if idx >= len(fresh_rows):
                        continue

                    row = fresh_rows[idx]
                    row_text = row.inner_text()

                    if not row_text.strip() or 'Número' in row_text:
                        continue

                    precatorio = self._parse_precatorio_from_row(
                        row, row_text, entidade,
                        page if not self.skip_expanded else None,
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
        """Parse precatório from table row (same as V2)"""
        try:
            cells = row.query_selector_all('td')

            if len(cells) < 15:
                return None

            cell_texts = [cell.inner_text().strip() for cell in cells]

            ordem = cell_texts[2] if len(cell_texts) > 2 else ""
            entidade_devedora_especifica = cell_texts[6] if len(cell_texts) > 6 else ""
            numero_precatorio = cell_texts[7] if len(cell_texts) > 7 else ""

            if not numero_precatorio:
                return None

            situacao = cell_texts[8] if len(cell_texts) > 8 else ""
            natureza = cell_texts[9] if len(cell_texts) > 9 else ""
            orcamento = cell_texts[10] if len(cell_texts) > 10 else ""

            valor_historico_text = cell_texts[12] if len(cell_texts) > 12 else ""
            valor_historico = self._parse_currency(valor_historico_text) if valor_historico_text else Decimal('0.00')

            saldo_atualizado_text = cell_texts[14] if len(cell_texts) > 14 else ""
            saldo_atualizado = self._parse_currency(saldo_atualizado_text) if saldo_atualizado_text else valor_historico

            # Extract expanded details (V2: only if page is provided)
            if page is not None:
                expanded_details = self._extract_expanded_details(row, page, row_index)
            else:
                expanded_details = {}

            precatorio = Precatorio(
                entidade_grupo=entidade.nome_entidade,
                id_entidade_grupo=entidade.id_entidade,
                entidade_devedora=entidade_devedora_especifica,
                regime=entidade.regime,
                ordem=ordem,
                numero_precatorio=numero_precatorio,
                situacao=situacao,
                natureza=natureza,
                orcamento=orcamento,
                valor_historico=valor_historico,
                saldo_atualizado=saldo_atualizado,
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
        """Extract expanded details by clicking + button (same as V2)"""
        details = {}
        max_retries = 3

        for attempt in range(max_retries):
            try:
                try:
                    page.wait_for_selector('.block-ui-overlay', state='hidden', timeout=2000)
                except:
                    pass

                fresh_rows = page.query_selector_all('tbody tr[ng-repeat-start]')

                if row_index >= len(fresh_rows):
                    return details

                fresh_row = fresh_rows[row_index]
                toggle_btn = fresh_row.query_selector('td.toggle-preca')

                if not toggle_btn:
                    return details

                try:
                    toggle_btn.click()
                    page.wait_for_timeout(1000)
                except Exception as click_error:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(500 * (attempt + 1))
                        continue
                    else:
                        raise click_error

                detail_containers = page.query_selector_all('td[colspan] .row-detail-container')

                if len(detail_containers) > 0:
                    detail_div = detail_containers[0]
                    detail_table = detail_div.query_selector('table.table-condensed')

                    if detail_table:
                        detail_rows = detail_table.query_selector_all('tbody tr')

                        for detail_row in detail_rows:
                            cells = detail_row.query_selector_all('td')
                            if len(cells) >= 2:
                                label = cells[0].inner_text().strip()
                                value = cells[1].inner_text().strip()
                                details[label] = value if value else None

                fresh_rows_collapse = page.query_selector_all('tbody tr[ng-repeat-start]')
                if row_index < len(fresh_rows_collapse):
                    fresh_row_collapse = fresh_rows_collapse[row_index]
                    toggle_btn_collapse = fresh_row_collapse.query_selector('td.toggle-preca')
                    if toggle_btn_collapse:
                        try:
                            toggle_btn_collapse.click()
                            page.wait_for_timeout(300)
                        except:
                            pass

                break

            except Exception as e:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(500 * (attempt + 1))
                else:
                    logger.debug(f"Row {row_index}: Failed after {max_retries} attempts: {e}")

        return details

    def scrape_regime(self, regime: str) -> pd.DataFrame:
        """
        Scrapes ALL data for a regime (main entry point for sequential extraction)

        For parallel extraction by page ranges, use main_v3_parallel.py instead.
        """
        logger.info(f"🎯 Starting full scrape for regime: {regime}")
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        perf_log_file = Path(f"logs/performance_v3_{regime}_{timestamp}.log")
        perf_log_file.parent.mkdir(parents=True, exist_ok=True)

        all_data = []
        entity_times = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config.headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            try:
                entidades = self.get_entidades(page, regime)

                if not entidades:
                    logger.warning("⚠️  No entities found!")
                    return pd.DataFrame()

                logger.info(f"\n📊 Total entities to process: {len(entidades)}")
                logger.info(f"💾 Performance log: {perf_log_file}\n")

                for i, entidade in enumerate(entidades, 1):
                    entity_start = time.time()

                    progress_pct = (i-1) / len(entidades) * 100
                    elapsed_total = time.time() - start_time

                    if len(entity_times) > 0:
                        avg_time_per_entity = sum(entity_times) / len(entity_times)
                        remaining_entities = len(entidades) - i + 1
                        estimated_remaining = avg_time_per_entity * remaining_entities
                        eta_minutes = estimated_remaining / 60
                        eta_hours = eta_minutes / 60

                        eta_str = f"{eta_hours:.1f}h" if eta_hours >= 1 else f"{eta_minutes:.1f}min"
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

                        for p in precatorios:
                            all_data.append(p.model_dump())

                        with open(perf_log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{datetime.now().isoformat()}|{regime}|{entidade.id_entidade}|"
                                   f"{entidade.nome_entidade}|{len(precatorios)}|{entity_elapsed:.2f}s\n")

                        logger.info(f"✅ Extracted {len(precatorios)} precatórios in {entity_elapsed:.1f}s "
                                  f"({len(precatorios)/entity_elapsed:.1f} rec/s)")

                    except Exception as e:
                        logger.error(f"❌ Failed to process {entidade.nome_entidade}: {e}")
                        continue

            except Exception as e:
                logger.error(f"❌ Scraping failed: {e}")
                raise
            finally:
                browser.close()

        df = pd.DataFrame(all_data)

        elapsed = time.time() - start_time
        logger.info(f"\n✅ Scraping complete: {len(df)} records in {elapsed/3600:.2f}h")

        return df

    def save_to_csv(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None
    ) -> str:
        """Saves DataFrame to CSV (same as V2)"""
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
            df.to_csv(
                filepath,
                index=False,
                encoding='utf-8-sig',
                sep=';',
                decimal=',',
                date_format='%Y-%m-%d'
            )

        logger.info(f"💾 Saved to: {filepath}")
        logger.info(f"   Size: {filepath.stat().st_size / 1024:.1f} KB")

        return str(filepath)
