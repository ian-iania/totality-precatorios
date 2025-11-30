"""
TJRJ Precatórios Extractor App

Streamlit interface for extracting precatório data from TJRJ portal.

Usage:
    streamlit run app/app.py

Features:
    - Select regime (Geral/Especial) and entity
    - Parallel extraction with progress tracking
    - Real-time ETA calculation
    - Success animation
    - CSV download management
"""

import streamlit as st
import sys
import time
import zipfile
import io
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integration import EntityLoader, ExtractionRunner
from app.utils import (
    get_output_dir, format_number, format_duration, format_time,
    format_datetime, format_filesize, estimate_time_minutes,
    list_csv_files, count_csv_records
)

# Try to import streamlit-extras for animations
try:
    from streamlit_extras.let_it_rain import rain
    HAS_EXTRAS = True
except ImportError:
    HAS_EXTRAS = False

# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="TJRJ Precatórios Extractor",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 1rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .progress-box {
        background-color: #e7f3ff;
        border: 1px solid #b8daff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #1f4e79;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'entities_cache' not in st.session_state:
        st.session_state.entities_cache = {}
    
    if 'extraction_runner' not in st.session_state:
        st.session_state.extraction_runner = None
    
    if 'extraction_running' not in st.session_state:
        st.session_state.extraction_running = False
    
    if 'extraction_complete' not in st.session_state:
        st.session_state.extraction_complete = False
    
    if 'extraction_result' not in st.session_state:
        st.session_state.extraction_result = None
    
    if 'show_success' not in st.session_state:
        st.session_state.show_success = False
    
    # New: Multi-entity processing state
    if 'entities_to_process' not in st.session_state:
        st.session_state.entities_to_process = []
    
    if 'current_entity_index' not in st.session_state:
        st.session_state.current_entity_index = 0
    
    if 'completed_entities' not in st.session_state:
        st.session_state.completed_entities = set()
    
    if 'processing_regime' not in st.session_state:
        st.session_state.processing_regime = None
    
    if 'total_stats' not in st.session_state:
        st.session_state.total_stats = {"pendentes": 0, "paginas": 0}

init_session_state()

# =============================================================================
# Helper Functions
# =============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_entities(regime: str) -> List[Dict]:
    """Load entities from TJRJ website (cached)"""
    loader = EntityLoader(headless=True)
    return loader.get_entities(regime)


def show_confetti():
    """Show celebration animation"""
    if HAS_EXTRAS:
        rain(
            emoji="🎉",
            font_size=54,
            falling_speed=5,
            animation_length=3,
        )
    else:
        st.balloons()


def create_zip_download(files: List[Dict]) -> bytes:
    """Create a ZIP file from multiple CSV files"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_info in files:
            filepath = Path(file_info['path'])
            if filepath.exists():
                zip_file.write(filepath, filepath.name)
    
    return zip_buffer.getvalue()


# =============================================================================
# Tab 1: Extraction
# =============================================================================

def render_extraction_tab():
    """Render the extraction tab"""
    
    # Check if extraction is running
    if st.session_state.extraction_running and st.session_state.extraction_runner:
        render_progress_view()
        return
    
    # Check if showing success
    if st.session_state.show_success and st.session_state.extraction_result:
        render_success_view()
        return
    
    # Normal extraction setup view
    render_setup_view()


def render_setup_view():
    """Render the simplified extraction setup view"""
    
    st.markdown("### 📋 Selecione o Regime")
    
    # Regime selection
    regime = st.radio(
        "Escolha o regime para processar todas as entidades:",
        options=["especial", "geral"],
        format_func=lambda x: f"{'🔵 Especial' if x == 'especial' else '🟢 Geral'}",
        horizontal=True,
        key="regime_selector",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Process button
    if st.button("🚀 PROCESSAR TODAS AS ENTIDADES", type="primary", use_container_width=True):
        start_all_entities_extraction(regime)


def start_all_entities_extraction(regime: str):
    """Start extraction of all entities for a regime"""
    
    # Load entities
    with st.spinner("Carregando entidades do TJRJ..."):
        try:
            entities = load_entities(regime)
        except Exception as e:
            st.error(f"Erro ao carregar entidades: {e}")
            return
    
    if not entities:
        st.error("Nenhuma entidade encontrada.")
        return
    
    # Sort by pending (descending) - process largest first
    entities = sorted(entities, key=lambda x: x['precatorios_pendentes'], reverse=True)
    
    # Calculate totals
    total_pendentes = sum(e['precatorios_pendentes'] for e in entities)
    total_paginas = sum((e['precatorios_pendentes'] + 9) // 10 for e in entities)
    
    # Store in session state
    st.session_state.entities_to_process = entities
    st.session_state.current_entity_index = 0
    st.session_state.completed_entities = set()
    st.session_state.processing_regime = regime
    st.session_state.total_stats = {
        "pendentes": total_pendentes,
        "paginas": total_paginas
    }
    st.session_state.extraction_running = True
    st.session_state.show_success = False
    
    # Start first entity
    start_next_entity()
    
    st.rerun()


def start_next_entity():
    """Start extraction of the next entity in queue"""
    
    entities = st.session_state.entities_to_process
    current_idx = st.session_state.current_entity_index
    
    if current_idx >= len(entities):
        # All done!
        return False
    
    entity = entities[current_idx]
    regime = st.session_state.processing_regime
    
    pendentes = entity.get('precatorios_pendentes', 0)
    total_pages = (pendentes + 9) // 10
    
    if total_pages == 0:
        # Skip entities with no pending
        st.session_state.completed_entities.add(entity['id'])
        st.session_state.current_entity_index += 1
        return start_next_entity()
    
    # Create runner and start extraction
    runner = ExtractionRunner()
    
    try:
        runner.start_extraction(
            entity_id=entity['id'],
            entity_name=entity['nome'],
            regime=regime,
            total_pages=total_pages,
            num_processes=4  # Fixed at 4 processes
        )
        
        st.session_state.extraction_runner = runner
        return True
    
    except Exception as e:
        st.error(f"Erro ao iniciar extração de {entity['nome']}: {e}")
        return False


def start_extraction(entity: Dict, regime: str, num_processes: int, pendentes: int = None):
    """Start the extraction process"""
    
    # Use pendentes (pending) count for pages calculation
    if pendentes is None:
        pendentes = entity.get('precatorios_pendentes', 0)
    
    total_pages = (pendentes + 9) // 10  # 10 records per page
    
    if total_pages == 0:
        st.error("Não foi possível determinar o número de páginas.")
        return
    
    # Create runner and start extraction
    runner = ExtractionRunner()
    
    try:
        runner.start_extraction(
            entity_id=entity['id'],
            entity_name=entity['nome'],
            regime=regime,
            total_pages=total_pages,
            num_processes=num_processes
        )
        
        st.session_state.extraction_runner = runner
        st.session_state.extraction_running = True
        st.session_state.extraction_complete = False
        st.session_state.show_success = False
        
        st.rerun()
    
    except Exception as e:
        st.error(f"Erro ao iniciar extração: {e}")


def render_progress_view():
    """Render the progress view during extraction with entity tracking"""
    
    runner = st.session_state.extraction_runner
    entities = st.session_state.entities_to_process
    current_idx = st.session_state.current_entity_index
    completed = st.session_state.completed_entities
    total_stats = st.session_state.total_stats
    
    # Check if runner exists
    if not runner and current_idx < len(entities):
        # Need to start next entity
        if not start_next_entity():
            # All done or error
            st.session_state.extraction_running = False
            st.session_state.show_success = True
            st.rerun()
            return
    
    if not runner:
        st.session_state.extraction_running = False
        st.rerun()
        return
    
    # Get progress for current entity
    progress = runner.get_progress()
    
    # Check if current entity finished
    if not progress.get('is_running', False):
        # Mark current entity as complete
        if current_idx < len(entities):
            completed.add(entities[current_idx]['id'])
            st.session_state.completed_entities = completed
        
        runner.cleanup()
        st.session_state.extraction_runner = None
        
        # Move to next entity
        st.session_state.current_entity_index += 1
        
        if st.session_state.current_entity_index >= len(entities):
            # All entities done!
            st.session_state.extraction_running = False
            st.session_state.show_success = True
            st.session_state.extraction_result = {
                "success": True,
                "total_entities": len(entities),
                "completed_entities": len(completed) + 1
            }
        
        st.rerun()
        return
    
    # === HEADER ===
    st.markdown("### ⏳ Processando...")
    
    # Total stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Total Precatórios Pendentes", format_number(total_stats['pendentes']))
    with col2:
        st.metric("📄 Total Páginas Estimadas", format_number(total_stats['paginas']))
    
    # === PROGRESS BAR ===
    # Calculate overall progress based on completed entities
    completed_pendentes = sum(
        e['precatorios_pendentes'] for e in entities 
        if e['id'] in completed
    )
    current_entity = entities[current_idx] if current_idx < len(entities) else None
    current_progress = progress.get('percent', 0) / 100
    
    if current_entity:
        current_contribution = current_entity['precatorios_pendentes'] * current_progress
    else:
        current_contribution = 0
    
    overall_progress = (completed_pendentes + current_contribution) / total_stats['pendentes'] if total_stats['pendentes'] > 0 else 0
    overall_progress = min(0.99, overall_progress)  # Cap at 99%
    
    st.progress(overall_progress)
    
    # === TIME ESTIMATES ===
    eta_seconds = progress.get('eta_seconds', 0)
    eta_time = progress.get('eta_time')
    
    # Estimate total remaining time
    remaining_entities = len(entities) - current_idx - 1
    remaining_pendentes = sum(
        e['precatorios_pendentes'] for e in entities[current_idx + 1:]
    )
    
    # Rough estimate: current ETA + remaining entities time
    if eta_seconds > 0 and remaining_pendentes > 0 and current_entity:
        # Estimate based on current speed
        current_pendentes = current_entity['precatorios_pendentes']
        if current_pendentes > 0:
            time_per_pendente = eta_seconds / (current_pendentes * (1 - current_progress)) if current_progress < 1 else 0
            total_eta_seconds = eta_seconds + (remaining_pendentes * time_per_pendente / 4)  # 4 processes
        else:
            total_eta_seconds = eta_seconds
    else:
        total_eta_seconds = eta_seconds
    
    col1, col2 = st.columns(2)
    with col1:
        if total_eta_seconds > 0:
            st.metric("⏱️ Tempo Restante Estimado", format_duration(total_eta_seconds))
        else:
            st.metric("⏱️ Tempo Restante Estimado", "Calculando...")
    
    with col2:
        if total_eta_seconds > 0:
            finish_time = datetime.now().timestamp() + total_eta_seconds
            st.metric("🏁 Conclusão às", format_time(datetime.fromtimestamp(finish_time)))
        else:
            st.metric("🏁 Conclusão às", "Calculando...")
    
    st.markdown("---")
    
    # === ENTITY TRACKING LIST ===
    st.markdown("**Entidades:**")
    
    # Create scrollable container for entities
    entity_container = st.container()
    
    with entity_container:
        for idx, entity in enumerate(entities):
            entity_id = entity['id']
            nome = entity['nome']
            pendentes = entity['precatorios_pendentes']
            
            if entity_id in completed:
                # Completed
                st.markdown(f"✅ {nome} ({format_number(pendentes)})")
            elif idx == current_idx:
                # Currently processing
                st.markdown(f"⏳ **{nome} ({format_number(pendentes)})** ← processando")
            else:
                # Pending
                st.markdown(f"⬜ {nome} ({format_number(pendentes)})")
    
    st.markdown("---")
    
    # Cancel button
    if st.button("❌ Cancelar", type="secondary"):
        runner.cancel()
        runner.cleanup()
        st.session_state.extraction_running = False
        st.session_state.extraction_runner = None
        st.session_state.entities_to_process = []
        st.session_state.current_entity_index = 0
        st.session_state.completed_entities = set()
        st.warning("Extração cancelada.")
        st.rerun()
    
    # Auto-refresh
    time.sleep(3)
    st.rerun()


def render_success_view():
    """Render the success view after extraction of all entities"""
    
    result = st.session_state.extraction_result
    entities = st.session_state.entities_to_process
    completed = st.session_state.completed_entities
    total_stats = st.session_state.total_stats
    regime = st.session_state.processing_regime
    
    # Show confetti animation
    show_confetti()
    
    # Success message
    st.markdown("""
    <div class="success-box">
        <h1>🎉 SUCESSO!</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Results summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Entidades Processadas", f"{len(completed)}/{len(entities)}")
    
    with col2:
        st.metric("📋 Total Precatórios", format_number(total_stats.get('pendentes', 0)))
    
    with col3:
        regime_label = "Especial" if regime == "especial" else "Geral"
        st.metric("📁 Regime", regime_label)
    
    st.markdown("---")
    
    # Show all entities with checkmarks
    st.markdown("**Entidades Concluídas:**")
    for entity in entities:
        if entity['id'] in completed:
            st.markdown(f"✅ {entity['nome']} ({format_number(entity['precatorios_pendentes'])})")
    
    st.markdown("---")
    
    # New extraction button
    if st.button("🔄 Nova Extração", type="primary", use_container_width=True):
        # Reset all state
        st.session_state.show_success = False
        st.session_state.extraction_result = None
        st.session_state.extraction_complete = False
        st.session_state.entities_to_process = []
        st.session_state.current_entity_index = 0
        st.session_state.completed_entities = set()
        st.session_state.processing_regime = None
        st.rerun()
    
    st.caption("Os arquivos CSV estão disponíveis na aba 'Downloads'.")


# =============================================================================
# Tab 2: Downloads
# =============================================================================

def render_downloads_tab():
    """Render the downloads tab"""
    
    st.markdown("### 📁 Arquivos Disponíveis")
    
    output_dir = get_output_dir()
    
    # List CSV files
    files = list_csv_files(output_dir, "precatorios_*.csv")
    
    if not files:
        st.info("Nenhum arquivo CSV encontrado na pasta de saída.")
        st.caption(f"Pasta: `{output_dir}`")
        return
    
    # Initialize selection state
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = set()
    
    # Select all checkbox
    col_select, col_count = st.columns([1, 3])
    with col_select:
        select_all = st.checkbox("Selecionar todos")
    with col_count:
        st.caption(f"{len(files)} arquivo(s) encontrado(s)")
    
    st.markdown("---")
    
    # File list
    selected_files = []
    
    for file_info in files:
        col_check, col_name, col_size, col_records, col_date = st.columns([0.5, 3, 1, 1, 1.5])
        
        with col_check:
            is_selected = st.checkbox(
                "sel",
                value=select_all,
                key=f"file_{file_info['name']}",
                label_visibility="collapsed"
            )
            if is_selected:
                selected_files.append(file_info)
        
        with col_name:
            st.text(file_info['name'])
        
        with col_size:
            st.text(file_info['size_formatted'])
        
        with col_records:
            st.text(f"{format_number(file_info['records'])} reg.")
        
        with col_date:
            st.text(file_info['modified_formatted'])
    
    st.markdown("---")
    
    # Download buttons
    if selected_files:
        col_single, col_zip = st.columns(2)
        
        if len(selected_files) == 1:
            # Single file download
            file_info = selected_files[0]
            with open(file_info['path'], 'rb') as f:
                file_data = f.read()
            
            with col_single:
                st.download_button(
                    label=f"📥 Download {file_info['name']}",
                    data=file_data,
                    file_name=file_info['name'],
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
        else:
            # Multiple files - offer ZIP
            with col_zip:
                zip_data = create_zip_download(selected_files)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    label=f"📦 Download ZIP ({len(selected_files)} arquivos)",
                    data=zip_data,
                    file_name=f"precatorios_{timestamp}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
    else:
        st.caption("Selecione arquivos para download.")


# =============================================================================
# Main App
# =============================================================================

def main():
    """Main application entry point"""
    
    # Header
    st.markdown('<p class="main-header">🏛️ TJRJ Precatórios Extractor</p>', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2 = st.tabs(["📥 Extração", "📁 Downloads"])
    
    with tab1:
        render_extraction_tab()
    
    with tab2:
        render_downloads_tab()
    
    # Footer
    st.markdown("---")
    st.caption(
        "TJRJ Precatórios Extractor v1.0 | "
        "Dados extraídos do Portal de Precatórios do TJRJ | "
        f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )


if __name__ == "__main__":
    main()
