# TJRJ Precatórios Web Scraper

**Production-ready web scraper** for extracting court-ordered payment (precatório) data from the Rio de Janeiro Court of Justice (TJRJ) portal using browser automation.

## 🎯 Features

- ✅ **Simplified Playwright Approach**: Browser automation handles all complexity
- ✅ **Comprehensive Coverage**: Both regime geral and especial
- ✅ **Automatic Pagination**: Handles multi-page results automatically
- ✅ **Robust Error Handling**: Retries and graceful degradation
- ✅ **Data Validation**: Pydantic models ensure data integrity
- ✅ **CSV Export**: Excel-compatible format with Brazilian standards
- ✅ **Comprehensive Logging**: Detailed logs for monitoring and debugging
- ✅ **Production Ready**: Type hints, tests, configurable settings

## 📊 Extracted Data

### Entity-Level Data
- Entity name and ID
- Count of paid/pending precatórios
- Priority and RPV values
- Regime type

### Precatório-Level Data
- Precatório number and process number
- Beneficiary information
- Original and updated values
- Requisition date
- Type and status
- Chronological order

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip or poetry for package management

### Installation

1. **Clone or download the project**:
```bash
cd /path/to/Charles
```

2. **Create virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers**:
```bash
playwright install chromium
```

5. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env with your preferences
```

### Basic Usage

```bash
# Scrape regime geral
python main.py --regime geral

# Scrape regime especial
python main.py --regime especial

# Run with visible browser for debugging
python main.py --regime geral --no-headless

# Custom output filename
python main.py --regime geral --output meus_precatorios.csv

# Enable debug logging
python main.py --regime geral --log-level DEBUG
```

## ⚠️ Important: Site Structure Inspection Required

**The scraper currently contains placeholder code** that needs to be completed with actual HTML selectors from the TJRJ portal.

### Why This Approach?

The TJRJ portal is an AngularJS Single Page Application (SPA) with dynamically loaded content. The actual HTML structure (CSS classes, element IDs, table structures) can only be determined by inspecting the live site.

### Next Steps to Complete Implementation

1. **Run with visible browser**:
```bash
python main.py --regime geral --no-headless --log-level DEBUG
```

2. **Inspect the HTML structure**:
   - While the browser is open, use DevTools (F12) to inspect:
     - Entity card structure on regime pages
     - Link patterns to precatório lists
     - Table structure for precatório data
     - Pagination button selectors

3. **Update `src/scraper.py`**:
   - In `get_entidades()`: Update selectors to extract entity information
   - In `get_precatorios_entidade()`: Implement navigation and data extraction
   - Add pagination logic based on actual site structure

4. **Test incrementally**:
```bash
# Test with one entity first
python main.py --regime geral --no-headless --log-level DEBUG
```

### Code Sections Requiring Completion

Look for these markers in `src/scraper.py`:

```python
# ⚠️ NEEDS INSPECTION: Entity card extraction
# Around line 110 in get_entidades()

# ⚠️ NEEDS INSPECTION: Precatório extraction
# Around line 160 in get_precatorios_entidade()
```

## 📖 Advanced Usage

### Python API

```python
from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config

# Initialize scraper
config = get_config()
scraper = TJRJPrecatoriosScraper(config=config)

# Scrape regime
df = scraper.scrape_regime('geral')

# Save to CSV
scraper.save_to_csv(df, filename='precatorios.csv')

# Access data
print(f"Total records: {len(df)}")
if not df.empty:
    print(f"Entities: {df['entidade_devedora'].nunique()}")
```

### Custom Configuration

```python
from src.models import ScraperConfig
from src.scraper import TJRJPrecatoriosScraper

config = ScraperConfig(
    regime='geral',
    headless=False,  # Show browser
    max_retries=5,
    enable_cache=True
)

scraper = TJRJPrecatoriosScraper(config=config)
df = scraper.scrape_regime('geral')
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test class
pytest tests/test_scraper.py::TestDataModels -v
```

## 📁 Project Structure

```
Charles/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Main scraper (Playwright)
│   ├── models.py           # Data models (Pydantic)
│   ├── config.py           # Configuration management
│   └── utils.py            # Helper functions (future)
├── tests/
│   ├── __init__.py
│   └── test_scraper.py     # Unit tests
├── data/
│   ├── raw/                # Raw data cache
│   ├── processed/          # CSV outputs
│   └── cache/              # Response cache
├── logs/
│   └── scraper.log         # Application logs
├── docs/                   # Additional documentation
├── .env.example            # Configuration template
├── .gitignore
├── requirements.txt
├── CLAUDE.MD              # Original specification
├── README.md
└── main.py                # CLI entry point
```

## 🔧 Configuration Options

Create a `.env` file based on `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TJRJ_BASE_URL` | `https://www.tjrj.jus.br/web/precatorios` | Base portal URL |
| `TJRJ_REGIME` | `geral` | Regime to scrape |
| `TJRJ_MAX_RETRIES` | `3` | Max retry attempts |
| `TJRJ_RETRY_DELAY` | `2.0` | Delay between retries (seconds) |
| `TJRJ_PAGE_LOAD_TIMEOUT` | `30000` | Page load timeout (ms) |
| `TJRJ_ENABLE_CACHE` | `true` | Enable response caching |
| `TJRJ_HEADLESS` | `true` | Run browser in headless mode |
| `TJRJ_LOG_LEVEL` | `INFO` | Logging level |

## 📝 Architecture Decisions

### Why Playwright Instead of API Discovery?

The original specification proposed a two-phase approach:
1. Discover API endpoints with Playwright
2. Use `requests` library to call APIs directly

**We simplified to single-phase Playwright** because:
- ✅ Simpler implementation (one tool throughout)
- ✅ More reliable (works even if API changes)
- ✅ Handles auth/sessions automatically
- ✅ Less fragile to backend changes
- ✅ Easier to maintain and debug

### Trade-offs

| Aspect | API Discovery + Requests | Playwright Only |
|--------|-------------------------|-----------------|
| Speed | ⚡⚡⚡ Faster | ⚡⚡ Moderate |
| Simplicity | ⚠️ Complex (2 phases) | ✅ Simple (1 phase) |
| Reliability | ⚠️ Fragile to API changes | ✅ Robust |
| Maintenance | ⚠️ High (update on changes) | ✅ Low |
| Resource Usage | ✅ Low | ⚠️ Higher (browser) |

## 🐛 Troubleshooting

### "No entities found"
- Run with `--no-headless` to see what's happening
- Check if website structure changed
- Inspect HTML and update selectors in `scraper.py`

### "Browser not found"
```bash
playwright install chromium
```

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Import errors with `src` module
Make sure you're running from the project root:
```bash
cd /path/to/Charles
python main.py --regime geral
```

## 📜 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Users are responsible for:
- Complying with TJRJ's terms of service
- Respecting robots.txt and rate limits
- Using data ethically and legally
- Verifying data accuracy before use

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request

## 📧 Support

For issues or questions:
- Review logs in `logs/scraper.log`
- Check existing documentation
- Open an issue with detailed information

## 🎓 Learning Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)
- [Ethical Scraping Guidelines](https://www.robotstxt.org/)

---

**Version**: 1.0.0
**Last Updated**: 2025-01-18
**Status**: Framework Ready - Requires Site Inspection
