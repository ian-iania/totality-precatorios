# Development Guide

Guide for completing the scraper implementation and contributing to the project.

## Current Status

The project provides a **production-ready framework** with:
- ✅ Complete project structure
- ✅ Data models and validation
- ✅ Configuration management
- ✅ Logging infrastructure
- ✅ Error handling
- ✅ CSV export
- ✅ CLI interface
- ✅ Tests

**What's missing**: HTML selector implementation (requires site inspection)

## Completing the Implementation

### Step 1: Inspect the Site Structure

1. Run with visible browser:
```bash
python main.py --regime geral --no-headless --log-level DEBUG
```

2. Open Chrome DevTools (F12 or Cmd+Option+I)

3. Inspect these elements:

#### Entity Cards (on regime page)
Look for:
- Container div with entity cards
- Entity name element
- Precatórios pagos/pendentes counts
- Valor prioridade/RPV values
- Links to precatório lists

Example questions to answer:
- What CSS class contains entity cards?
- What attribute contains the entity ID?
- How are the statistics displayed?

#### Precatório Lists
Look for:
- Table structure
- Column headers
- Pagination buttons
- Data rows

#### Example Selectors to Find

```python
# Examples (actual selectors will vary):
entity_card_selector = "div.entity-card"
entity_name_selector = "h3.entity-name"
entity_link_selector = "a[href*='ordem-cronologica']"
precatorio_table_selector = "table.precatorios"
pagination_next_selector = "button.pagination-next"
```

### Step 2: Update `src/scraper.py`

#### In `get_entidades()` method

Around line 105, replace the placeholder:

```python
# BEFORE (placeholder):
entidade = EntidadeDevedora(
    id_entidade=0,
    nome_entidade="PLACEHOLDER - Manual Inspection Needed",
    regime=regime,
    precatorios_pagos=0,
    precatorios_pendentes=0,
    valor_prioridade=Decimal('0.00'),
    valor_rpv=Decimal('0.00')
)

# AFTER (example with actual selectors):
cards = page.query_selector_all("div.entity-card")  # Update selector!
for card in cards:
    # Extract data from card
    nome = card.query_selector("h3.name").inner_text()
    id_str = card.get_attribute("data-entity-id")  # Update attribute!
    pagos_text = card.query_selector("span.pagos").inner_text()
    pendentes_text = card.query_selector("span.pendentes").inner_text()
    prioridade_text = card.query_selector("span.prioridade").inner_text()
    rpv_text = card.query_selector("span.rpv").inner_text()

    entidade = EntidadeDevedora(
        id_entidade=int(id_str),
        nome_entidade=nome,
        regime=regime,
        precatorios_pagos=self._parse_integer(pagos_text),
        precatorios_pendentes=self._parse_integer(pendentes_text),
        valor_prioridade=self._parse_currency(prioridade_text),
        valor_rpv=self._parse_currency(rpv_text)
    )
    entidades.append(entidade)
```

#### In `get_precatorios_entidade()` method

Around line 145, implement:

```python
def get_precatorios_entidade(self, page: Page, entidade: EntidadeDevedora) -> List[Precatorio]:
    """Extract all precatórios for an entity"""
    all_precatorios = []

    # 1. Find and click entity link
    # Update with actual selector:
    link = page.query_selector(f"a[data-entity-id='{entidade.id_entidade}']")
    if link:
        link.click()
        page.wait_for_load_state('networkidle')

    # 2. Extract table data
    page_num = 1
    while True:
        # Wait for table to load
        page.wait_for_selector("table.precatorios")  # Update selector!

        # Extract rows
        rows = page.query_selector_all("table.precatorios tbody tr")  # Update!

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) < 5:  # Adjust based on actual table
                continue

            precatorio = Precatorio(
                numero_precatorio=cells[0].inner_text(),
                beneficiario=cells[1].inner_text(),
                valor_original=self._parse_currency(cells[2].inner_text()),
                valor_atualizado=self._parse_currency(cells[3].inner_text()),
                tipo=self._classify_tipo(cells[4].inner_text()),
                status=self._classify_status(cells[5].inner_text()),
                entidade_devedora=entidade.nome_entidade,
                id_entidade=entidade.id_entidade,
                regime=entidade.regime
            )
            all_precatorios.append(precatorio)

        # 3. Check for next page
        next_button = page.query_selector("button.next:not([disabled])")  # Update!
        if not next_button:
            break

        next_button.click()
        page.wait_for_timeout(1000)
        page_num += 1

    return all_precatorios
```

### Step 3: Add Helper Methods

If needed, add classification methods:

```python
def _classify_tipo(self, tipo_text: str) -> str:
    """Classify precatório type from text"""
    tipo_text = tipo_text.lower()
    if 'alimentar' in tipo_text:
        return 'alimentar'
    elif 'super' in tipo_text:
        return 'superpreferencia'
    elif 'rpv' in tipo_text:
        return 'rpv'
    else:
        return 'comum'

def _classify_status(self, status_text: str) -> str:
    """Classify precatório status from text"""
    status_text = status_text.lower()
    if 'pago' in status_text:
        return 'pago'
    elif 'parcelado' in status_text:
        return 'parcelado'
    elif 'cancelado' in status_text:
        return 'cancelado'
    else:
        return 'pendente'
```

### Step 4: Test Incrementally

```bash
# 1. Test entity extraction only
python main.py --regime geral --no-headless --log-level DEBUG

# 2. Add breakpoints or extra logging
# In scraper.py, add:
logger.info(f"Found {len(cards)} entity cards")
logger.info(f"First card HTML: {cards[0].inner_html()[:500]}")

# 3. Test full scrape with one entity
# Modify scraper to process only first entity (temporarily)

# 4. Test pagination
# Watch for "next page" clicks in browser

# 5. Full scrape
python main.py --regime geral
```

## Code Style Guidelines

### Formatting

Use Black formatter:
```bash
black src/ tests/
```

### Type Hints

Always use type hints:
```python
def extract_data(page: Page, selector: str) -> List[str]:
    """Extract text from elements"""
    elements = page.query_selector_all(selector)
    return [el.inner_text() for el in elements]
```

### Docstrings

Use Google-style docstrings:
```python
def process_entity(entity_id: int) -> EntidadeDevedora:
    """
    Process a single entity and extract metadata.

    Args:
        entity_id: Unique entity identifier

    Returns:
        EntidadeDevedora instance with extracted data

    Raises:
        ValueError: If entity_id is invalid
    """
    pass
```

### Logging

Use appropriate log levels:
```python
logger.debug("Detailed debug info")  # Development only
logger.info("Progress updates")      # Normal operation
logger.warning("Recoverable issues") # Issues that don't stop execution
logger.error("Serious problems")     # Errors that affect results
```

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html

# Specific test
pytest tests/test_scraper.py::TestDataModels::test_entidade_model_valid -v
```

### Add New Tests

When adding features, add corresponding tests:

```python
class TestNewFeature:
    """Tests for new feature"""

    def test_feature_success(self):
        """Test feature works correctly"""
        result = my_new_function("input")
        assert result == "expected"

    def test_feature_error_handling(self):
        """Test feature handles errors"""
        with pytest.raises(ValueError):
            my_new_function("invalid")
```

## Debugging Tips

### Print Page Content

```python
# In scraper.py:
logger.debug(f"Page HTML preview: {page.content()[:1000]}")
```

### Take Screenshots

```python
page.screenshot(path="debug_screenshot.png")
logger.info("Screenshot saved to debug_screenshot.png")
```

### Slow Down Execution

```python
page.wait_for_timeout(5000)  # Wait 5 seconds to observe
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

## Performance Optimization

### After Basic Implementation Works

1. **Enable Headless Mode**:
```python
config.headless = True  # Faster without GUI
```

2. **Add Caching**:
```python
# Cache entity lists
# Implement in scraper.py if not already present
```

3. **Parallel Processing** (Advanced):
```python
# Use asyncio for concurrent entity processing
# Requires rewriting with Playwright async API
```

## Contributing

### Workflow

1. Create feature branch
2. Make changes
3. Add tests
4. Run tests and formatters
5. Submit pull request

### Before Committing

```bash
# Format code
black src/ tests/

# Run tests
pytest tests/ -v

# Check types (if using mypy)
mypy src/
```

## Resources

- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [Playwright Selectors](https://playwright.dev/python/docs/selectors)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Pytest Docs](https://docs.pytest.org/)

## Getting Help

- Review error messages in logs
- Check Playwright documentation for selector syntax
- Use browser DevTools to inspect elements
- Test selectors in browser console first
