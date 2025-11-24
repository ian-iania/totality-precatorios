# Quick Reference

Fast reference for common tasks and commands.

## Installation

```bash
# One-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Common Commands

```bash
# Basic scraping
python main.py --regime geral                    # Scrape regime geral
python main.py --regime especial                 # Scrape regime especial

# Debugging
python main.py --regime geral --no-headless      # Show browser
python main.py --regime geral --log-level DEBUG  # Verbose logging

# Custom output
python main.py --regime geral --output results.csv

# Without cache
python main.py --regime geral --no-cache
```

## File Locations

```
logs/scraper.log           # Application logs
data/processed/*.csv       # Output CSV files
data/cache/                # Cached responses
.env                       # Your configuration
```

## Configuration Quick Edit

```bash
# Copy template
cp .env.example .env

# Edit with nano
nano .env

# Common settings to change:
TJRJ_HEADLESS=false        # Show browser
TJRJ_LOG_LEVEL=DEBUG       # More detailed logs
TJRJ_ENABLE_CACHE=false    # Disable cache
```

## Testing

```bash
pytest tests/ -v                           # Run all tests
pytest tests/ -v --cov=src                 # With coverage
pytest tests/test_scraper.py::TestName -v  # Specific test
```

## Debugging

```bash
# View logs
tail -f logs/scraper.log

# Clear cache
rm -rf data/cache/*

# Clear output
rm -rf data/processed/*

# Start fresh
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Playwright Selectors (for implementation)

```python
# CSS Selectors
page.query_selector("div.classname")
page.query_selector("#element-id")
page.query_selector("tag[attribute='value']")

# Text Selectors
page.query_selector("text=Exact Text")
page.query_selector("text=/.*pattern.*/i")

# Multiple Elements
elements = page.query_selector_all("div.card")

# Get Text
text = element.inner_text()

# Get Attribute
value = element.get_attribute("data-id")

# Click
element.click()

# Wait
page.wait_for_selector("div.loaded")
page.wait_for_timeout(2000)  # ms
```

## Data Model Fields

### EntidadeDevedora
```python
id_entidade: int
nome_entidade: str
regime: str  # 'geral' or 'especial'
precatorios_pagos: int
precatorios_pendentes: int
valor_prioridade: Decimal
valor_rpv: Decimal
timestamp_extracao: datetime
```

### Precatorio
```python
numero_precatorio: str
numero_processo: Optional[str]
beneficiario: str
cpf_cnpj_beneficiario: Optional[str]
valor_original: Decimal
valor_atualizado: Decimal
data_requisicao: Optional[date]
tipo: str  # 'comum', 'alimentar', 'superpreferencia', 'rpv'
status: str  # 'pendente', 'pago', 'parcelado', 'cancelado'
entidade_devedora: str
id_entidade: int
regime: str
ordem_cronologica: Optional[int]
observacoes: Optional[str]
timestamp_extracao: datetime
```

## Python API

```python
from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config
from src.models import ScraperConfig

# Quick start
scraper = TJRJPrecatoriosScraper()
df = scraper.scrape_regime('geral')
scraper.save_to_csv(df)

# Custom config
config = ScraperConfig(
    regime='geral',
    headless=False,
    max_retries=5
)
scraper = TJRJPrecatoriosScraper(config=config)

# Access configuration
config = get_config()
print(config.base_url)
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Module not found | `pip install -r requirements.txt` |
| Playwright not found | `playwright install chromium` |
| Permission denied | `chmod +x main.py` |
| Import error | Check you're in project root |
| Browser won't start | `playwright install chromium --force` |
| Empty results | Run with `--no-headless --log-level DEBUG` |

## Important Files to Edit

```
src/scraper.py          # Main implementation (update selectors here)
src/models.py           # Data models (if schema changes)
.env                    # Configuration
requirements.txt        # Dependencies
```

## Git Commands (if using version control)

```bash
# Initial setup
git init
git add .
git commit -m "Initial commit"

# Daily workflow
git status
git add src/scraper.py
git commit -m "Update entity extraction"
git push

# Check history
git log --oneline
```

## Performance Tips

```bash
# Faster execution
TJRJ_HEADLESS=true              # Run headless
TJRJ_ENABLE_CACHE=true          # Enable cache
TJRJ_PAGE_LOAD_TIMEOUT=15000    # Shorter timeout

# More thorough (slower)
TJRJ_MAX_RETRIES=5              # More retries
TJRJ_RETRY_DELAY=3.0            # Longer delays
```

## CSV Output Format

- **Encoding**: UTF-8 with BOM (Excel compatible)
- **Separator**: Semicolon (;)
- **Decimal**: Comma (,)
- **Date Format**: YYYY-MM-DD
- **Location**: `data/processed/precatorios_<regime>_<timestamp>.csv`

## Getting Help

1. Check `logs/scraper.log`
2. Review README.md
3. See DEVELOPMENT_GUIDE.md for implementation details
4. See SETUP_GUIDE.md for installation issues

## Useful One-Liners

```bash
# Count output files
ls data/processed/*.csv | wc -l

# View last log entries
tail -n 50 logs/scraper.log

# Check Python version
python --version

# Check installed packages
pip list | grep -E "playwright|pandas|pydantic"

# Disk space used
du -sh data/

# Quick test run
python -c "from src.scraper import TJRJPrecatoriosScraper; print('OK')"
```
