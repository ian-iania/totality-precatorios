# ⚡ Quick Start Guide

Get started with TJRJ Precatórios Scraper in 5 minutes.

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

# 6. Verify installation
pytest tests/ -v
```

**Expected output**: All tests pass ✅

## 🎯 First Run (2 minutes)

```bash
# Run with visible browser to see what happens
python main.py --regime geral --no-headless --log-level DEBUG
```

**What you'll see**:
- Chrome browser opens
- Navigates to TJRJ portal
- Attempts to extract data
- Shows placeholder message (expected!)

**This is normal!** The framework is working. It just needs HTML selectors.

## 🔧 What to Do Next

### Option 1: Quick Test (Just verify it works)

The framework is complete and working. You can stop here if you just wanted to review the code structure.

### Option 2: Complete Implementation (3-4 hours)

Follow these steps to make it actually scrape data:

1. **Open development guide**:
   ```bash
   open docs/DEVELOPMENT_GUIDE.md
   # or on Linux: xdg-open docs/DEVELOPMENT_GUIDE.md
   ```

2. **Inspect the TJRJ website**:
   - Run: `python main.py --regime geral --no-headless`
   - Press F12 in browser to open DevTools
   - Click "Elements" tab
   - Find entity card elements and note their CSS classes

3. **Update `src/scraper.py`**:
   - Line ~105: Update `get_entidades()` with real selectors
   - Line ~145: Implement `get_precatorios_entidade()`

4. **Test incrementally**:
   ```bash
   python main.py --regime geral --no-headless --log-level DEBUG
   ```

5. **Run full scrape**:
   ```bash
   python main.py --regime geral
   ```

## 📁 Where to Find Things

```
✅ Main scraper code:     src/scraper.py
✅ Data models:            src/models.py
✅ Configuration:          .env (copy from .env.example)
✅ Test results:           logs/scraper.log
✅ CSV outputs:            data/processed/
✅ Documentation:          docs/
```

## 🎓 Learning Path

### Beginner (Just exploring)
1. Read `README.md`
2. Run `pytest tests/ -v` to see tests
3. Browse code in `src/`

### Intermediate (Want to use it)
1. Follow installation above
2. Read `docs/SETUP_GUIDE.md`
3. Read `docs/DEVELOPMENT_GUIDE.md`
4. Complete HTML selector implementation

### Advanced (Want to extend it)
1. Read `PROJECT_SUMMARY.md` for architecture
2. Review `src/scraper.py` for extensibility points
3. Add new features (async, database export, etc.)

## 🆘 Common Issues

### "playwright: command not found"
```bash
python -m playwright install chromium
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied"
```bash
chmod +x main.py
```

### Tests fail
Expected on first run! The framework is complete, just needs site-specific selectors.

## 📞 Getting Help

1. Check logs: `tail -f logs/scraper.log`
2. Read docs: `docs/DEVELOPMENT_GUIDE.md`
3. Review errors: Run with `--log-level DEBUG`

## 🎉 Success Criteria

You'll know it's working when:

- ✅ Installation completes without errors
- ✅ Tests pass
- ✅ Browser opens when you run the scraper
- ✅ You see log messages in terminal
- ✅ After adding selectors: CSV file appears in `data/processed/`

## ⏱️ Time Estimates

- **Installation**: 5 minutes
- **First run**: 2 minutes
- **Reading docs**: 30 minutes
- **Site inspection**: 1 hour
- **Implementation**: 2-3 hours
- **Testing**: 1 hour
- **Total**: ~4-5 hours to fully working scraper

## 🚦 Current Status

```
Phase 1: Project Setup      ✅ COMPLETE
Phase 2: Framework Build    ✅ COMPLETE
Phase 3: Documentation      ✅ COMPLETE
Phase 4: HTML Selectors     ⏳ PENDING (your task!)
Phase 5: Testing            ⏳ PENDING
Phase 6: Production Use     ⏳ PENDING
```

---

**Ready to start? Run the installation commands above!** 🚀

For detailed instructions, see:
- 📘 **README.md** - Full documentation
- 🔧 **docs/SETUP_GUIDE.md** - Installation details
- 💻 **docs/DEVELOPMENT_GUIDE.md** - Implementation guide
- ⚡ **docs/QUICK_REFERENCE.md** - Command cheat sheet
