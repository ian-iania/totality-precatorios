# Totality Precatórios - TJRJ Web Scraper

**Production-ready web scraper** for extracting court-ordered payment (precatório) data from the Rio de Janeiro Court of Justice (TJRJ) portal using browser automation.

## 🌐 VPS Access (Production)

| Item | Value |
|------|-------|
| **URL** | http://209.126.12.243:8501 |
| **SSH** | `ssh root@209.126.12.243` |
| **Project Path** | `/root/charles/totality-precatorios` |

## 🎯 Features

- ✅ **V6 Orchestrator**: Complete workflow with gap detection and recovery
- ✅ **Decoupled UI V2**: Streamlit UI that doesn't interfere with extraction
- ✅ **1-20 Parallel Workers**: Configurable concurrent workers
- ✅ **Real-time Progress**: Log-based progress tracking
- ✅ **Excel Export**: Auto-filter, styled headers, freeze panes
- ✅ **Gap Recovery**: Automatic detection and recovery of failed entities
- ✅ **Comprehensive Coverage**: Both regime GERAL (56) and ESPECIAL (41)
- ✅ **Robust Error Handling**: Per-worker timeouts and graceful degradation
- ✅ **Data Validation**: Pydantic models ensure data integrity
- ✅ **CSV + Excel Export**: Brazilian format standards

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

### Option 1: Streamlit Web Interface V2 (Recommended)

```bash
# Start the Streamlit V2 app (decoupled UI)
streamlit run app/app_v2.py --server.port 8501

# Open http://localhost:8501 in your browser
```

The Streamlit V2 UI provides:
- Regime selection (ESPECIAL/GERAL) with radio buttons
- Configurable workers (1-20)
- Real-time progress via log polling (no interference)
- Metrics: Entities, Records, Time, Workers
- Terminal view with last 15 log lines
- Downloads tab with file filters
- Process runs independently (survives browser close)

### Option 2: Command Line (V6 Orchestrator)

```bash
# Extract all entities with V6 orchestrator (includes gap recovery)
python main_v6_orchestrator.py --regime especial --num-processes 10 --timeout 60

# Extract GERAL with 15 workers
python main_v6_orchestrator.py --regime geral --num-processes 15 --timeout 60
```

The V6 Orchestrator provides:
- **Phase 1**: Main extraction with parallel workers
- **Phase 2**: Gap detection (finds failed entities)
- **Phase 3**: Gap recovery (re-extracts failed entities)
- **Phase 4**: Merge & finalize (creates COMPLETE file)

### Option 3: Legacy Scripts (V5/V4)

```bash
# V5 All Entities (without gap recovery)
python main_v5_all_entities.py --regime especial --num-processes 10

# V4 Memory Mode (single entity)
python main_v4_memory.py \
  --entity-id 1 \
  --entity-name "Estado do Rio de Janeiro" \
  --regime especial \
  --total-pages 2984 \
  --num-processes 12
```

## ⚡ Performance

### V6 Benchmarks (VPS - 4 vCPU, 8GB RAM)

| Regime | Entities | Records | Workers | Time |
|--------|----------|---------|---------|------|
| ESPECIAL | 41 | ~40,243 | 10 | ~85 min |
| GERAL | 56 | ~5,384 | 10 | ~15 min |
| ESPECIAL | 41 | ~40,243 | 15 | ~60 min |
| ESPECIAL | 41 | ~40,243 | 20 | ~45 min |

### Version Comparison

| Aspect | V5 | V6 | UI V2 |
|--------|----|----|-------|
| Gap Recovery | ❌ | ✅ | ✅ |
| Decoupled UI | ❌ | ❌ | ✅ |
| Workers | 1-20 | 1-20 | 1-20 |
| Hang Risk | Medium | Low | None |

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

**Version**: 2.0.0
**Last Updated**: 2025-12-02
**Status**: Production Ready - V6 Orchestrator + UI V2 Decoupled
