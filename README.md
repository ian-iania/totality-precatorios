# TJRJ Precatórios Web Scraper

**Production-ready web scraper** for extracting court-ordered payment (precatório) data from the Rio de Janeiro Court of Justice (TJRJ) portal using browser automation.

## 🎯 Features

- ✅ **V4 Memory Mode**: Full in-memory extraction with no intermediate I/O
- ✅ **12 Parallel Workers**: Configurable concurrent workers for maximum speed
- ✅ **Streamlit UI**: User-friendly web interface with real-time progress
- ✅ **Excel Export**: Auto-filter, styled headers, freeze panes
- ✅ **Data Formatting**: Numeric ordem, formatted monetary values
- ✅ **Comprehensive Coverage**: Both regime geral and especial
- ✅ **Automatic Pagination**: Direct page navigation for any page
- ✅ **Robust Error Handling**: Per-worker timeouts and graceful degradation
- ✅ **Data Validation**: Pydantic models ensure data integrity
- ✅ **CSV Export**: Excel-compatible format with Brazilian standards
- ✅ **Real-time Progress**: Workers table with page/records tracking

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

### Option 1: Streamlit Web Interface (Recommended)

```bash
# Start the Streamlit app
streamlit run app/app.py

# Open http://localhost:8501 in your browser
```

The Streamlit UI provides:
- Regime selection (Especial/Geral)
- One-click extraction of all entities
- Real-time progress tracking with workers table
- 12 parallel workers with page/records status
- Overall progress in bold red
- ETA calculation and completion time
- CSV + Excel output with formatting
- Success animation and download management

### Option 2: Command Line (V4 Memory Mode)

```bash
# Extract single entity with 12 parallel workers (full memory mode)
python main_v4_memory.py \
  --entity-id 1 \
  --entity-name "Estado do Rio de Janeiro" \
  --regime especial \
  --total-pages 2984 \
  --num-processes 12 \
  --timeout 30

# Extract with visible browser for debugging
python main_v4_memory.py \
  --entity-id 1 \
  --entity-name "Estado do Rio de Janeiro" \
  --regime especial \
  --total-pages 100 \
  --num-processes 4 \
  --no-headless
```

### Option 3: Legacy Scripts

```bash
# V4 Fast (with intermediate files - deprecated)
python main_v4_fast.py \
  --entity-id 1 \
  --total-pages 2984 \
  --num-processes 8

# V3 parallel extraction (may hang on large extractions)
python main_v3_parallel.py \
  --entity-id 1 \
  --total-pages 2984 \
  --num-processes 4 \
  --skip-expanded
```

## ⚡ Performance

### V4 Memory Mode Benchmarks

| Metric | Value |
|--------|-------|
| Workers | 12 parallel (configurable) |
| Speed per page | ~2 seconds |
| Effective speed (12 workers) | ~0.17 seconds/page |
| Estado do RJ (2,984 pages) | ~10-15 minutes |
| Timeout protection | 30 min per worker |
| Storage | Full in-memory (no I/O) |

### Version Comparison

| Aspect | V3 | V4 Fast | V4 Memory |
|--------|----|---------|-----------|
| Workers | 4 | 8 | 12 |
| Pool method | `pool.map()` | `apply_async()` | `apply_async()` |
| Intermediate I/O | Yes | Yes | **No** |
| Data formatting | No | No | **Yes** |
| Excel output | No | No | **Yes** |
| Hang risk | High | Low | Low |

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
├── app/                    # Streamlit Web Interface
│   ├── app.py              # Main Streamlit application
│   ├── integration.py      # Backend integration layer
│   ├── utils.py            # UI utility functions
│   └── requirements.txt    # App-specific dependencies
├── src/
│   ├── __init__.py
│   ├── scraper_v3.py       # V3 Scraper with expanded fields
│   ├── models.py           # Data models (Pydantic)
│   ├── config.py           # Configuration management
│   └── utils.py            # Helper functions
├── output/                 # CSV output files
├── logs/                   # Application logs
├── main_v4_memory.py       # V4 Memory Mode (recommended)
├── main_v4_fast.py         # V4 Fast (with intermediate files)
├── main_v3_parallel.py     # V3 Parallel (deprecated)
├── requirements.txt        # Python dependencies
└── README.md
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

**Version**: 4.1.0
**Last Updated**: 2025-12-01
**Status**: Production Ready - V4 Memory Mode with 12 Workers
