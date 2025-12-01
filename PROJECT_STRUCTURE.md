# Charles - TJRJ Precatórios Scraper V5
## Project Structure

```
Charles/
├── README.md                          # Main documentation
├── QUICKSTART.md                      # Quick start guide (UPDATED)
├── PROJECT_STRUCTURE.md               # This file
├── CLAUDE.MD                          # Claude Code context
├── AGENTS.md                          # AI agent rules
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
│
├── main_v5_all_entities.py            # V5 extraction script (MAIN)
├── main_v4_memory.py                  # V4 per-entity extraction
│
├── app/                               # Streamlit Web UI
│   ├── __init__.py
│   ├── app.py                         # Main Streamlit application
│   ├── integration.py                 # UI-scraper integration
│   ├── utils.py                       # Helper utilities
│   └── requirements.txt               # App-specific dependencies
│
├── src/                               # Core scraper modules
│   ├── __init__.py
│   ├── config.py                      # Configuration
│   ├── models.py                      # Data models (Pydantic)
│   ├── scraper.py                     # Original scraper
│   ├── scraper_v2.py                  # V2 with improvements
│   └── scraper_v3.py                  # V3 fast mode (CURRENT)
│
├── output/                            # Extraction outputs
│   ├── precatorios_*.csv              # Final CSV files
│   └── partial/                       # Worker partial files
│
├── logs/                              # Application logs
│   ├── scraper_v3.log                 # Main extraction log
│   ├── extraction_v5_*.log            # V5 session logs
│   └── screenshots/                   # Debug screenshots
│
├── tests/                             # Unit tests
│   └── *.py
│
├── docs/                              # Documentation
│   ├── SETUP_GUIDE.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── QUICK_REFERENCE.md
│
├── data/                              # Legacy data directory
│   └── processed/                     # Old extractions
│
└── archive/                           # Historical files
    ├── docs/                          # Old documentation
    ├── scripts/                       # Debug/test scripts
    └── data/                          # Debug data
```

## V5 Architecture

### Extraction Flow
```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│  Streamlit UI   │────▶│ main_v5_all_entities │────▶│  Output CSV │
│   (app.py)      │     │   (12 workers)       │     │             │
└─────────────────┘     └──────────────────────┘     └─────────────┘
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────────┐
│ integration.py  │     │    scraper_v3.py     │
│ (log parsing)   │     │   (page extraction)  │
└─────────────────┘     └──────────────────────┘
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **V5 Script** | `main_v5_all_entities.py` | Processes all entities sequentially |
| **Streamlit UI** | `app/app.py` | Web interface with progress tracking |
| **Integration** | `app/integration.py` | Manages subprocess, parses logs |
| **Scraper V3** | `src/scraper_v3.py` | Fast extraction (11 columns) |

### Parallel Processing
- **12 workers** per entity (configurable)
- Each worker handles a page range
- Workers run in separate processes
- Data accumulated in memory, saved at end

## Current Data

### Regime Especial
- **Entities**: 41
- **Total Pendentes**: ~40,252 records
- **Total Pages**: ~4,041

### Regime Geral
- **Entities**: 56
- **Total Pendentes**: ~30,000 records

## CSV Structure (11 Columns - Fast Mode)

| Column | Description |
|--------|-------------|
| `ordem` | Order position |
| `entidade_devedora` | Debtor entity |
| `numero_precatorio` | Precatório number |
| `situacao` | Status |
| `natureza` | Nature (Comum/Alimentícia) |
| `orcamento` | Budget year |
| `valor_historico` | Historical value (BRL) |
| `saldo_atualizado` | Updated balance (BRL) |
| `regime` | Regime type |
| `id_entidade` | Entity ID |
| `timestamp_extracao` | Extraction timestamp |

## Key Features

✅ **V5 All-Entities Mode** - Single run for all entities
✅ **12 Parallel Workers** - Fast extraction per entity
✅ **Streamlit UI** - Real-time progress monitoring
✅ **ETA Calculation** - Based on total pendentes
✅ **Navigation Fallbacks** - Multiple selectors + page input
✅ **Memory Accumulation** - No disk I/O during extraction
✅ **Graceful Shutdown** - Clean process termination

## Performance

| Metric | Value |
|--------|-------|
| **Speed** | ~150-200 records/second |
| **Regime Especial** | ~15-20 minutes |
| **Regime Geral** | ~12-15 minutes |
| **Workers** | 12 (configurable) |

## Navigation Strategy

When clicking "Próxima" button fails:
1. Try `a[ng-click="vm.ProximaPagina()"]`
2. Try `a:has-text("Próxima")`
3. Try `text=Próxima`
4. **Fallback**: Use "Ir para página" input box
