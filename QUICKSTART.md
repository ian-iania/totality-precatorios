# ⚡ Quick Start Guide

Get started with TJRJ Precatórios Scraper V5 in 5 minutes.

## 🚀 Installation (5 minutes)

```bash
# 1. Navigate to project
cd /Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install Playwright browsers
playwright install chromium
```

## 🎯 Running the Scraper

### Option 1: Web Interface (Recommended)

```bash
# Start the Streamlit UI
streamlit run app/app.py --server.port 8501
```

Then open http://localhost:8501 in your browser.

**Features**:
- Select regime (Especial or Geral)
- Real-time progress tracking
- Worker status monitoring
- ETA calculation based on total records
- Download results as CSV

### Option 2: Command Line

```bash
# Run V5 extraction for all entities
python main_v5_all_entities.py --regime especial --workers 12

# Options:
#   --regime: especial or geral
#   --workers: number of parallel workers (default: 12)
#   --headless: run without browser UI (default: True)
```

## 📊 What the UI Shows

- **Processando**: Current entity being extracted
- **Registros**: Records extracted / Total expected
- **Tempo restante**: ETA based on extraction speed
- **Workers em Processamento**: Status of each parallel worker
- **Progresso geral**: Overall percentage complete

## 📁 Output Files

```
output/
├── precatorios_especial_YYYYMMDD_HHMMSS.csv  # Full extraction
├── partial_p1_*.csv                           # Worker partial files
└── ...

logs/
├── scraper_v3.log                             # Main extraction log
├── extraction_v5_*.log                        # V5 session logs
└── screenshots/                               # Debug screenshots
```

## 🔧 Architecture

### V5 All-Entities Mode
- Processes all 41 entities sequentially in one run
- Uses 12 parallel workers per entity
- Accumulates data in memory (no disk I/O during extraction)
- Saves single consolidated CSV at the end

### Key Files
```
main_v5_all_entities.py   # V5 extraction script
app/app.py                # Streamlit UI
app/integration.py        # UI-scraper integration
src/scraper_v3.py         # Core scraper class
```

## 🆘 Common Issues

### Workers stuck at 96-99%
The "Próxima" button may be below viewport. V5 includes:
1. Multiple button selectors
2. Scroll to button before click
3. Fallback: use "Ir para página" input box

### Old data showing in UI
Delete old logs before new run:
```bash
rm -f logs/scraper_v3.log
```

### "playwright: command not found"
```bash
python -m playwright install chromium
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📞 Monitoring Progress

### Via UI
The Streamlit interface shows real-time progress with:
- Per-worker page progress
- Total records extracted
- Speed (records/second)
- Estimated time remaining

### Via Logs
```bash
# Watch live extraction
tail -f logs/scraper_v3.log

# Check for errors
grep -i "error\|warning" logs/scraper_v3.log
```

## 🎉 Success Criteria

You'll know it's working when:

- ✅ UI shows "Processando: [Entity Name]"
- ✅ Workers show increasing page counts
- ✅ Records counter increases steadily
- ✅ Progress bar advances
- ✅ CSV file appears in `output/` after completion

## ⏱️ Time Estimates

| Regime | Entities | Records | Time (12 workers) |
|--------|----------|---------|-------------------|
| Especial | 41 | ~40,000 | ~15-20 min |
| Geral | 41 | ~30,000 | ~12-15 min |

## 🚦 Current Status

```
✅ V5 All-Entities Mode    COMPLETE
✅ Parallel Workers        COMPLETE  
✅ Streamlit UI            COMPLETE
✅ Progress Tracking       COMPLETE
✅ ETA Calculation         COMPLETE
✅ Navigation Fallbacks    COMPLETE
```

---

**Ready to start?** Run `streamlit run app/app.py` 🚀
