# Setup Guide

Complete step-by-step guide to set up the TJRJ Precatórios Scraper.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, for version control)

## Installation Steps

### 1. Navigate to Project Directory

```bash
cd /Users/persivalballeste/Documents/@IANIA/PROJECTS/Charles
```

### 2. Create Virtual Environment

**Why?** Isolates project dependencies from system Python.

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Expected packages:
- playwright
- pandas
- pydantic
- python-dotenv
- loguru
- pytest
- pytest-cov
- black
- mypy

### 4. Install Playwright Browsers

Playwright needs to download browser binaries:

```bash
playwright install chromium
```

This downloads Chromium (~150MB). Only needs to be done once.

### 5. Configure Environment (Optional)

```bash
cp .env.example .env
```

Edit `.env` to customize settings (optional - defaults work fine).

### 6. Verify Installation

```bash
# Test that imports work
python -c "from src.scraper import TJRJPrecatoriosScraper; print('✅ Installation successful!')"

# Run tests
pytest tests/ -v
```

## Quick Test

Run a test scrape with visible browser:

```bash
python main.py --regime geral --no-headless --log-level DEBUG
```

This will:
1. Open Chrome browser (visible)
2. Navigate to TJRJ portal
3. Show debug logs
4. Attempt to extract data (will show placeholders)

## Next Steps

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for completing the HTML extraction logic.

## Troubleshooting

### "playwright: command not found"

The playwright binary isn't in PATH. Try:

```bash
python -m playwright install chromium
```

### "ModuleNotFoundError: No module named 'playwright'"

Virtual environment not activated or dependencies not installed:

```bash
source venv/bin/activate  # Activate venv
pip install -r requirements.txt  # Install deps
```

### "Permission denied" errors

On macOS/Linux, you may need to make scripts executable:

```bash
chmod +x main.py
```

### Browser doesn't launch

Check Playwright installation:

```bash
playwright install chromium --force
```

## Uninstallation

To remove the project:

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf Charles
```

## Getting Help

- Check logs in `logs/scraper.log`
- Review README.md for usage examples
- Open an issue with error details
