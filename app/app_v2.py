"""
Totality Precatórios - UI V2 (Desacoplada)

Arquitetura:
- UI apenas dispara o processo e lê logs
- Zero interferência na extração
- Processo sobrevive a refresh/fechamento do browser
"""

import streamlit as st
import subprocess
import time
import re
import os
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd

# Page config
st.set_page_config(
    page_title="Totality Precatórios",
    page_icon="⚖️",
    layout="wide"
)

# Reduce top padding
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    [data-testid="stMetricValue"] {font-size: 1.2rem;}
</style>
""", unsafe_allow_html=True)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"
PID_FILE = LOGS_DIR / "extraction.pid"
REGIME_FILE = LOGS_DIR / "extraction.regime"
START_TIME_FILE = LOGS_DIR / "extraction.start_time"
SCRAPER_LOG = LOGS_DIR / "scraper_v3.log"
ORCHESTRATOR_LOG = LOGS_DIR / "orchestrator_v6.log"

# Ensure dirs exist
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def read_last_lines(filepath: Path, n: int = 50) -> List[str]:
    """Read last N lines from a file"""
    try:
        if not filepath.exists():
            return []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return [line.rstrip() for line in lines[-n:]]
    except Exception:
        return []


def parse_log_summary(lines: List[str]) -> Dict:
    """Extract metrics from log lines"""
    summary = {
        'entities_current': 0,
        'entities_total': 0,
        'total_records': 0,
        'current_entity': '',
        'elapsed_minutes': 0,
        'phase': 'idle',
        'phase_message': '',
        'active_workers': [],
        'is_complete': False,
        'final_output': None
    }
    
    for line in reversed(lines):
        # Progress pattern: "Progress: 10/56 entities | 500 total records | 5.0min elapsed"
        match = re.search(r'Progress:\s*(\d+)/(\d+)\s*entities\s*\|\s*([\d,]+)\s*total records\s*\|\s*([\d.]+)min', line)
        if match and summary['entities_current'] == 0:
            summary['entities_current'] = int(match.group(1))
            summary['entities_total'] = int(match.group(2))
            summary['total_records'] = int(match.group(3).replace(',', ''))
            summary['elapsed_minutes'] = float(match.group(4))
        
        # Entity complete pattern: "Entity complete: 100 records in 0.5min"
        match = re.search(r'Entity complete:\s*([\d,]+)\s*records', line)
        if match and summary['total_records'] == 0:
            summary['total_records'] = int(match.group(1).replace(',', ''))
        
        # Worker records pattern: "[P1] ✅ 10 records (total: 100)"
        match = re.search(r'\[P\d+\].*total:\s*([\d,]+)', line)
        if match:
            records = int(match.group(1).replace(',', ''))
            if records > summary['total_records']:
                summary['total_records'] = records
        
        # Elapsed time pattern: "X.Xmin elapsed" or "(X.Xmin elapsed)"
        match = re.search(r'(\d+\.?\d*)min elapsed', line)
        if match and summary['elapsed_minutes'] == 0:
            summary['elapsed_minutes'] = float(match.group(1))
        
        # Current entity: "ENTITY: ESTADO DO RIO DE JANEIRO (ID: 1)"
        match = re.search(r'ENTITY:\s*(.+?)\s*\(ID:', line)
        if match and not summary['current_entity']:
            summary['current_entity'] = match.group(1).strip()
        
        # Entity count from "Pages: X | Workers: Y"
        match = re.search(r'Pages:\s*(\d+)\s*\|\s*Workers:', line)
        if match and summary['entities_total'] == 0:
            # This is per-entity, not total - skip
            pass
        
        # Phase detection
        if 'PHASE 4: MERGE' in line or 'MERGE & FINALIZE' in line:
            summary['phase'] = 'merge'
            summary['phase_message'] = '📦 Mesclando dados e gerando arquivo final...'
        elif 'PHASE 3: GAP RECOVERY' in line:
            summary['phase'] = 'recovery'
            summary['phase_message'] = '🔄 Recuperando entidades com falha...'
        elif 'PHASE 2: GAP DETECTION' in line:
            summary['phase'] = 'detection'
            summary['phase_message'] = '🔍 Verificando gaps na extração...'
        elif 'WORKFLOW COMPLETE' in line:
            summary['phase'] = 'complete'
            summary['phase_message'] = '✅ Extração completa!'
            summary['is_complete'] = True
        elif 'Starting extraction' in line or 'MAIN EXTRACTION' in line:
            summary['phase'] = 'extraction'
            summary['phase_message'] = '⚡ Extraindo dados...'
        
        # Final output
        match = re.search(r'Final output:\s*(.+\.csv)', line)
        if match:
            summary['final_output'] = match.group(1)
        
        # Active workers: "[P1] Page 100/299"
        match = re.search(r'\[P(\d+)\]\s*Page\s*(\d+)/(\d+)', line)
        if match:
            worker_id = int(match.group(1))
            if worker_id not in [w['id'] for w in summary['active_workers']]:
                summary['active_workers'].append({
                    'id': worker_id,
                    'current_page': int(match.group(2)),
                    'total_pages': int(match.group(3))
                })
    
    # Default phase if extraction is running
    if summary['phase'] == 'idle' and summary['entities_current'] > 0:
        summary['phase'] = 'extraction'
        summary['phase_message'] = '⚡ Extraindo dados...'
    
    return summary


def is_process_running() -> bool:
    """Check if extraction process is running"""
    if not PID_FILE.exists():
        return False
    
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        # Process doesn't exist, clean up PID file
        PID_FILE.unlink(missing_ok=True)
        return False


def get_elapsed_time() -> float:
    """Get elapsed time in minutes from start_time file or log file creation time"""
    # Try start_time file first
    if START_TIME_FILE.exists():
        try:
            start_ts = float(START_TIME_FILE.read_text().strip())
            elapsed_seconds = time.time() - start_ts
            return elapsed_seconds / 60.0
        except:
            pass
    
    # Fallback: use log file creation time
    if SCRAPER_LOG.exists():
        try:
            start_ts = SCRAPER_LOG.stat().st_mtime - (SCRAPER_LOG.stat().st_size / 100)  # Approximate start
            # Better: use file creation time if available
            start_ts = SCRAPER_LOG.stat().st_ctime  # Creation time
            elapsed_seconds = time.time() - start_ts
            return elapsed_seconds / 60.0
        except:
            pass
    
    return 0.0


def start_extraction(regime: str, num_processes: int = 10, timeout: int = 60, entity_id: int = None):
    """Start extraction process (desacoplado)"""
    # Reset entity counter in session state
    st.session_state.last_entity_count = 0
    st.session_state.seen_entity_lines = set()
    st.session_state.entity_counter_initialized = True  # Mark as initialized with 0
    
    # Save start timestamp
    START_TIME_FILE.write_text(str(time.time()))
    
    # Clear old logs
    for log_file in [SCRAPER_LOG, ORCHESTRATOR_LOG]:
        if log_file.exists():
            log_file.unlink()
    
    # Start process with start_new_session=True (fully independent)
    # Use sys.executable to get the correct Python path (works in venv)
    import sys
    cmd = [
        sys.executable, 'main_v6_orchestrator.py',
        '--regime', regime,
        '--num-processes', str(num_processes),
        '--timeout', str(timeout)
    ]
    
    # Add entity_id for single entity extraction (e.g., Estado do RJ)
    if entity_id:
        cmd.extend(['--entity-id', str(entity_id)])
    
    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        start_new_session=True,  # Fully independent from Streamlit
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Save PID and regime for tracking
    PID_FILE.write_text(str(process.pid))
    REGIME_FILE.write_text(regime)
    
    return process.pid


def stop_extraction():
    """Stop extraction process"""
    if not PID_FILE.exists():
        return False
    
    try:
        pid = int(PID_FILE.read_text().strip())
        # Kill process group
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        time.sleep(1)
        # Force kill if still running
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        PID_FILE.unlink(missing_ok=True)
        return True
    except Exception:
        PID_FILE.unlink(missing_ok=True)
        return False


def count_csv_lines(filepath: str) -> int:
    """Count lines in CSV file (excluding header)"""
    try:
        if filepath.endswith('.csv'):
            with open(filepath, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f) - 1  # Exclude header
        elif filepath.endswith('.xlsx'):
            # For Excel, try to read corresponding CSV or estimate
            csv_path = filepath.replace('.xlsx', '.csv')
            if Path(csv_path).exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    return sum(1 for _ in f) - 1
        return 0
    except:
        return 0


def list_output_files() -> List[Dict]:
    """List available output files"""
    files = []
    for ext in ['csv', 'xlsx']:
        for f in OUTPUT_DIR.glob(f'*.{ext}'):
            stat = f.stat()
            files.append({
                'name': f.name,
                'path': str(f),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'lines': count_csv_lines(str(f))
            })
    
    # Sort by modified date (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files


def format_size(size_bytes: int) -> str:
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(minutes: float) -> str:
    """Format duration"""
    if minutes < 1:
        return f"{int(minutes * 60)}s"
    elif minutes < 60:
        return f"{minutes:.1f}min"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}min"


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    """Render page header"""
    st.title("⚖️ Totality Precatórios Extração TJRJ")


def render_extraction_tab():
    """Render extraction tab"""
    is_running = is_process_running()
    
    if is_running:
        render_progress_view()
    else:
        render_setup_view()


def render_setup_view():
    """Render extraction setup view"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        regime_option = st.radio(
            "Regime",
            options=["especial", "especial_rj", "geral"],
            format_func=lambda x: {
                'especial': "🔷 ESPECIAL (41 entidades)",
                'especial_rj': "🏛️ ESPECIAL - Estado do RJ",
                'geral': "🔶 GERAL (56 entidades)"
            }.get(x, x),
            horizontal=True
        )
    
    with col2:
        num_workers = st.number_input("Workers", min_value=1, max_value=20, value=15)
    
    if st.button("▶️ Iniciar"):
        with st.spinner("Iniciando..."):
            # Parse regime and entity_id from option
            if regime_option == "especial_rj":
                regime = "especial"
                entity_id = 1  # Estado do Rio de Janeiro
            else:
                regime = regime_option
                entity_id = None
            
            pid = start_extraction(regime, num_processes=int(num_workers), entity_id=entity_id)
            time.sleep(2)
            st.rerun()


def get_current_regime() -> str:
    """Get current extraction regime"""
    try:
        if REGIME_FILE.exists():
            return REGIME_FILE.read_text().strip().upper()
    except:
        pass
    return ""


def get_regime_entity_count(regime: str) -> int:
    """Get total entities for regime"""
    if regime.upper() == "ESPECIAL":
        return 41
    elif regime.upper() == "GERAL":
        return 56
    return 0


def count_completed_entities_from_log() -> int:
    """Count all completed entities directly from log file (for refresh recovery)"""
    if not SCRAPER_LOG.exists():
        return 0
    try:
        with open(SCRAPER_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Count unique "Entity complete:" occurrences
        matches = re.findall(r'📊 Entity complete:', content)
        return len(matches) // 2  # Each line appears twice in log (duplicate logging)
    except:
        return 0


def get_total_records_from_log() -> int:
    """Sum all records from Entity complete lines"""
    if not SCRAPER_LOG.exists():
        return 0
    try:
        with open(SCRAPER_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Sum records from "Entity complete: X records" lines
        matches = re.findall(r'📊 Entity complete:\s*(\d+)\s*records', content)
        total = sum(int(m) for m in matches)
        return total // 2  # Each line appears twice in log
    except:
        return 0


def count_completed_entities(lines: List[str]) -> int:
    """Count completed entities using session state, with refresh recovery"""
    # Initialize session state on first load (or after refresh)
    if 'entity_counter_initialized' not in st.session_state:
        # Recover count from full log on refresh
        st.session_state.last_entity_count = count_completed_entities_from_log()
        st.session_state.seen_entity_lines = set()
        st.session_state.entity_counter_initialized = True
        # Mark all current lines as seen
        for line in lines:
            if 'Entity complete:' in line or '📊 Entity complete:' in line:
                st.session_state.seen_entity_lines.add(hash(line.strip()))
        return st.session_state.last_entity_count
    
    # Count new entity completions (incremental)
    for line in lines:
        if 'Entity complete:' in line or '📊 Entity complete:' in line:
            line_hash = hash(line.strip())
            if line_hash not in st.session_state.seen_entity_lines:
                st.session_state.seen_entity_lines.add(line_hash)
                st.session_state.last_entity_count += 1
    
    return st.session_state.last_entity_count


def render_progress_view():
    """Render progress view (polling logs)"""
    
    # Read logs - last 500 lines for entity counting (session_state persists count)
    scraper_lines_full = read_last_lines(SCRAPER_LOG, 500)
    scraper_lines = scraper_lines_full[-100:]  # Last 100 for parsing
    orchestrator_lines = read_last_lines(ORCHESTRATOR_LOG, 50)
    all_lines = orchestrator_lines + scraper_lines  # For phase detection
    
    # Parse summary
    summary = parse_log_summary(all_lines)
    regime = get_current_regime()
    
    # Check if complete
    if summary['is_complete']:
        render_complete_view(summary)
        return
    
    # Header with cancel button aligned right
    col1, col2 = st.columns([6, 1])
    with col1:
        phase_text = summary['phase_message'] or 'Processando...'
        if regime:
            st.markdown(f"**⚡ {phase_text} - {regime}**")
        else:
            st.markdown(f"**⚡ {phase_text}**")
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            stop_extraction()
            st.rerun()
    
    # Current entity (between header and metrics)
    if summary['current_entity']:
        st.info(f"**Processando:** {summary['current_entity']}")
    
    # Get entity counts independently
    total_entities = get_regime_entity_count(regime)
    completed_entities = count_completed_entities(scraper_lines_full)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏛️ Entidades processadas", f"{completed_entities}/{total_entities}")
    
    with col2:
        # Get total records from full log (more accurate than parsing last lines)
        total_records = get_total_records_from_log()
        if total_records == 0:
            total_records = summary['total_records']
        st.metric("📄 Registros capturados", f"{total_records:,}")
    
    with col3:
        # Calculate elapsed time from start timestamp (survives refresh)
        elapsed = get_elapsed_time()
        st.metric("⏱️ Tempo decorrido", format_duration(elapsed))
    
    with col4:
        active = len(summary['active_workers'])
        st.metric("🔄 Workers ativos", f"{active}")
    
    # Progress bar
    if total_entities > 0:
        progress = completed_entities / total_entities
        st.progress(progress, text=f"{progress*100:.1f}%")
    
    # Terminal view
    st.markdown("**📟 Terminal**")
    
    # Show last 15 lines from scraper log only
    terminal_lines = scraper_lines[-15:] if scraper_lines else ["Aguardando logs..."]
    terminal_text = '\n'.join(terminal_lines)
    st.code(terminal_text, language='log')
    
    # Auto-refresh
    time.sleep(3)
    st.rerun()


def render_complete_view(summary: Dict):
    """Render completion view"""
    # Clean up tracking files since extraction is complete
    PID_FILE.unlink(missing_ok=True)
    REGIME_FILE.unlink(missing_ok=True)
    # Keep START_TIME_FILE for final elapsed time display
    
    st.balloons()
    
    st.success("## ✅ Extração Completa!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 Total de Registros", f"{summary['total_records']:,}")
    
    with col2:
        st.metric("🏛️ Entidades", f"{summary['entities_current']}/{summary['entities_total']}")
    
    with col3:
        # Use calculated elapsed time
        elapsed = get_elapsed_time()
        st.metric("⏱️ Tempo Total", format_duration(elapsed if elapsed > 0 else summary['elapsed_minutes']))
    
    if summary['final_output']:
        st.info(f"**Arquivo gerado:** `{summary['final_output']}`")
    
    st.markdown("---")
    
    if st.button("🔄 Nova Extração", type="primary"):
        PID_FILE.unlink(missing_ok=True)
        st.rerun()


def render_downloads_tab():
    """Render downloads tab"""
    
    # Show message if extraction is running
    if is_process_running():
        st.info("⏳ Extração em andamento. Os arquivos estarão disponíveis após a conclusão.")
        return
    
    files = list_output_files()
    
    if not files:
        st.info("Nenhum arquivo disponível. Execute uma extração primeiro.")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.radio("Tipo", ["Todos", "CSV", "Excel"], horizontal=True)
    with col2:
        filter_regime = st.radio("Regime", ["Todos", "GERAL", "ESPECIAL"], horizontal=True)
    
    # Filter files
    filtered = files
    if filter_type == "CSV":
        filtered = [f for f in filtered if f['name'].endswith('.csv')]
    elif filter_type == "Excel":
        filtered = [f for f in filtered if f['name'].endswith('.xlsx')]
    
    if filter_regime == "GERAL":
        filtered = [f for f in filtered if 'geral' in f['name'].lower()]
    elif filter_regime == "ESPECIAL":
        filtered = [f for f in filtered if 'especial' in f['name'].lower()]
    
    st.markdown("---")
    
    # Column headers
    col1, col2, col3, col4, col5 = st.columns([1.2, 0.8, 3, 0.8, 0.5])
    with col1:
        st.caption("**Data/Hora**")
    with col2:
        st.caption("**Linhas**")
    with col3:
        st.caption("**Arquivo**")
    with col4:
        st.caption("**Tamanho**")
    with col5:
        st.caption("")
    
    # File list
    for file in filtered[:20]:  # Limit to 20 files
        col1, col2, col3, col4, col5 = st.columns([1.2, 0.8, 3, 0.8, 0.5])
        
        with col1:
            st.caption(file['modified'].strftime("%d/%m %H:%M"))
        
        with col2:
            lines = file.get('lines', 0)
            st.caption(f"{lines:,}" if lines > 0 else "-")
        
        with col3:
            icon = "📊" if file['name'].endswith('.xlsx') else "📄"
            st.markdown(f"{icon} {file['name']}")
        
        with col4:
            st.caption(format_size(file['size']))
        
        with col5:
            with open(file['path'], 'rb') as f:
                st.download_button(
                    "⬇️",
                    data=f.read(),
                    file_name=file['name'],
                    mime="application/octet-stream",
                    key=file['name']
                )


def render_footer():
    """Render footer"""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from version import __version__
    except ImportError:
        __version__ = "2.0.0"
    st.markdown("---")
    st.caption(
        f"Totality Precatórios v{__version__} | "
        "Dados extraídos do Portal de Precatórios do TJRJ"
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    render_header()
    
    # Track selected tab
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = 0
    
    tab1, tab2 = st.tabs(["📊 Extração", "📥 Downloads"])
    
    with tab1:
        render_extraction_tab()
    
    with tab2:
        render_downloads_tab()
    
    render_footer()


if __name__ == "__main__":
    main()
