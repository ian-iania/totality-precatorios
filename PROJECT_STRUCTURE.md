# Charles - TJRJ Precatórios Scraper
## Final Clean Project Structure

```
Charles/
├── README.md                          # Main documentation
├── QUICKSTART.md                      # Quick start guide
├── CLAUDE.MD                          # Claude Code context
├── requirements.txt                   # Python dependencies
├── main.py                            # CLI entry point
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
│
├── src/                               # Source code
│   ├── __init__.py
│   ├── models.py                      # Data models (CORRECTED)
│   ├── scraper.py                     # Core scraper logic
│   └── config.py                      # Configuration
│
├── tests/                             # Unit tests
│   ├── __init__.py
│   └── test_scraper.py
│
├── data/                              # Data directory
│   ├── processed/                     # Final CSVs (CURRENT)
│   │   ├── precatorios_geral_20251119_013857.csv      (5,444 records)
│   │   └── precatorios_especial_20251119_030948.csv   (20,239 records)
│   ├── backup/                        # Previous extractions
│   │   ├── precatorios_geral_20251118_225720.csv
│   │   └── precatorios_especial_20251119_002534.csv
│   ├── cache/                         # Runtime cache
│   │   └── .gitkeep
│   └── debug/                         # Debug assets
│       └── table_structure.png
│
├── docs/                              # Documentation
│   ├── SETUP_GUIDE.md                 # Installation guide
│   ├── DEVELOPMENT_GUIDE.md           # Developer guide
│   ├── QUICK_REFERENCE.md             # Command reference
│   └── FINAL_CORRECTED_EXTRACTION_REPORT.md  # Extraction report
│
├── archive/                           # Historical files
│   ├── docs/                          # Old documentation (7 files)
│   │   ├── SUCCESS_REPORT.md
│   │   ├── FINAL_STATUS.md
│   │   ├── EXTRACTION_COMPLETE_REPORT.md
│   │   ├── IMPLEMENTATION_COMPLETE.md
│   │   ├── PROJECT_SUMMARY.md
│   │   ├── ARCHITECTURE_COMPARISON.md
│   │   └── TEST_RESULTS.md
│   ├── debug/                         # Debug scripts (12 files)
│   │   ├── test_live_scrape.py
│   │   ├── test_corrected_extraction.py
│   │   ├── test_first_entity_each_regime.py
│   │   ├── test_scraper_now.py
│   │   ├── test_url_routes.py
│   │   ├── capture_html.py
│   │   ├── capture_html_auto.py
│   │   ├── inspect_table_columns.py
│   │   ├── inspect_rendered_dom.py
│   │   ├── map_all_columns.py
│   │   ├── verify_actual_columns.py
│   │   └── scraper_corrected_extraction.py
│   └── data/                          # Debug data
│       └── raw/                       # Raw HTML captures
│           ├── HTML/
│           └── rendered/
│
└── logs/                              # Application logs
    ├── .gitkeep
    └── scraper.log

```

## Current Data Extraction

**Total Records**: 25,683 precatórios
**Total Unique Entities**: 187 (77 from Regime Geral + 110 from Regime Especial)
**Total Entity Groups**: 97 (56 Geral + 41 Especial)

### Regime Geral
- **File**: `data/processed/precatorios_geral_20251119_013857.csv`
- **Records**: 5,444 precatórios
- **Entity Groups**: 56
- **Unique Entities**: 77 (21 sub-entities discovered)

### Regime Especial
- **File**: `data/processed/precatorios_especial_20251119_030948.csv`
- **Records**: 20,239 precatórios
- **Entity Groups**: 41
- **Unique Entities**: 110 (69 sub-entities discovered)

## CSV Structure (17 Columns)

### Entity Information (4 columns)
1. `entidade_grupo` - Parent/Group entity (from card clicked)
2. `id_entidade_grupo` - Parent entity ID
3. `entidade_devedora` - Specific entity responsible (from table Cell 6)
4. `regime` - Regime type (geral/especial)

### Visible Columns (8 columns)
5. `ordem` - Order position (e.g., "2º", "4º")
6. `numero_precatorio` - Precatório number
7. `situacao` - Status/Situation
8. `natureza` - Nature (Comum/Alimentícia)
9. `orcamento` - Budget year
10. `valor_historico` - Historical value (BRL)
11. `saldo_atualizado` - Updated balance (BRL)

### Non-Visible Columns (5 columns)
12. `prioridade` - Priority
13. `valor_parcela` - Installment value (BRL)
14. `parcelas_pagas` - Installments paid (e.g., "5/5")
15. `previsao_pagamento` - Payment forecast
16. `quitado` - Settled (Sim/Não)

### Metadata (1 column)
17. `timestamp_extracao` - Extraction timestamp (ISO 8601)

## Key Features

✅ **Two-Level Entity Hierarchy** - Captures both parent group and specific entity
✅ **Complete Column Extraction** - All 17 actual columns from website
✅ **Non-Visible Data** - Includes 5 hidden columns from HTML
✅ **Accurate Column Names** - Matches website terminology exactly
✅ **Large Dataset Handling** - Successfully processed 25,683 records
✅ **Data Validation** - Pydantic models ensure type safety
✅ **Brazilian Format** - CSV with UTF-8 BOM, semicolon separator, comma decimal

## Cleanup Summary

**Moved to Archive**: 19 files (7 docs + 12 debug scripts)
**Deleted**: 2 duplicate model files
**Organized**: Clean structure with core files in root/src, historical in archive
**Preserved**: All working code, tests, documentation, and current data
