"""
Version information for Totality Precatórios
"""

__version__ = "2.1.1"
__version_date__ = "2025-12-02"

# Changelog:
# v2.1.1 (2025-12-02) - Fix entity count for single entity mode (shows 0/1 for RJ)
# v2.1.0 (2025-12-02) - Add "ESPECIAL - Estado do RJ" option in UI
# v2.0.9 (2025-12-02) - Add --entity-id parameter for single entity extraction
# v2.0.8 (2025-12-02) - Sort CSV/Excel by id_entidade_grupo and ordem (numeric)
# v2.0.7 (2025-12-02) - Show current entity between header and metrics
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
