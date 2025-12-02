"""
Version information for Totality Precatórios
"""

__version__ = "2.0.6"
__version_date__ = "2025-12-02"

# Changelog:
# v2.0.6 (2025-12-02) - Fix elapsed time fallback, accurate total records from log
# v2.0.5 (2025-12-02) - Elapsed time calculated from start timestamp (survives refresh)
# v2.0.4 (2025-12-02) - Entity counter survives page refresh (reads from log)
# v2.0.3 (2025-12-02) - Use session_state for entity counter (never drops)
# v2.0.2 (2025-12-02) - Fix entity counter dropping (increase log lines to 50k)
# v2.0.1 (2025-12-02) - VPS deployment fixes, sys.executable for venv, docs update
# v2.0.0 (2025-12-02) - New decoupled UI (app_v2.py) - reads logs only
# v1.1.1 (2025-12-02) - Fix networkidle hang in page navigation
# v1.1.0 (2025-12-02) - Fix worker hang issue with explicit timeouts
# v1.0.0 (2025-12-01) - Initial V6 release with gap recovery
