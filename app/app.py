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

from app.integration import EntityLoader, ExtractionRunner, FullMemoryExtractionRunner
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
    page_title="Totality Precatórios Extração TJRJ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit menu, header and footer completely */
    #MainMenu {display: none;}
    footer {display: none;}
    header {display: none;}
    
    /* Remove top padding from main content */
    .block-container {
        padding-top: 1rem !important;
    }
    
    /* Remove deploy button area */
    .stDeployButton {display: none;}
    
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
        padding: 1rem;
        text-align: center;
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
    
    # V5 Full Memory Mode
    if 'use_v5' not in st.session_state:
        st.session_state.use_v5 = False
    
    if 'v5_runner' not in st.session_state:
        st.session_state.v5_runner = None

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
    
    # Check if showing success (check this FIRST)
    if st.session_state.show_success:
        render_success_view()
        return
    
    # Check if extraction is running
    if st.session_state.extraction_running:
        # Use V5 progress view if V5 mode is active
        if st.session_state.use_v5:
            render_v5_progress_view()
        else:
            render_progress_view()
        return
    
    # Normal extraction setup view
    render_setup_view()


def render_setup_view():
    """Render the simplified extraction setup view"""
    
    # Regime selection
    regime = st.radio(
        "Regime",
        options=["especial", "geral"],
        format_func=lambda x: x.capitalize(),
        horizontal=True,
        key="regime_selector"
    )
    
    # Process button below
    if st.button("Processar", type="primary"):
        start_all_entities_extraction(regime)


def start_all_entities_extraction(regime: str):
    """Start extraction of all entities for a regime using V5 Full Memory Mode"""
    from loguru import logger
    
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
    
    # Filter entities with pending > 0 (keep original order from site)
    entities = [e for e in entities if e['precatorios_pendentes'] > 0]
    
    if not entities:
        st.warning("Nenhuma entidade com precatórios pendentes encontrada.")
        return
    
    # Calculate totals
    total_pendentes = sum(e['precatorios_pendentes'] for e in entities)
    total_paginas = sum((e['precatorios_pendentes'] + 9) // 10 for e in entities)
    
    # Store in session state
    st.session_state.entities_to_process = entities
    st.session_state.processing_regime = regime
    st.session_state.total_stats = {
        "pendentes": total_pendentes,
        "paginas": total_paginas,
        "entities": len(entities)
    }
    st.session_state.extraction_running = True
    st.session_state.show_success = False
    st.session_state.use_v5 = True  # Flag for V5 mode
    
    # Create consolidated output file name for this regime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"output/precatorios_{regime}_{timestamp}.csv"
    st.session_state.output_file = output_file
    st.session_state.extraction_start_time = datetime.now()
    
    # Start V5 Full Memory Extraction (ALL entities at once)
    logger.info(f"Starting V5 Full Memory Extraction: {len(entities)} entities, {total_paginas} pages")
    
    runner = FullMemoryExtractionRunner()
    runner.start_full_extraction(
        entities=entities,
        regime=regime,
        max_concurrent=10,  # 10 concurrent workers (hybrid mode)
        timeout_minutes=60,  # 60 min timeout per worker
        output_file=output_file
    )
    
    st.session_state.v5_runner = runner
    
    st.rerun()


def start_next_entity():
    """Start extraction of the next entity in queue"""
    from loguru import logger
    
    entities = st.session_state.entities_to_process
    current_idx = st.session_state.current_entity_index
    
    logger.info(f"start_next_entity: idx={current_idx}, total={len(entities)}")
    
    if current_idx >= len(entities):
        # All done!
        logger.info("All entities processed!")
        return False
    
    entity = entities[current_idx]
    regime = st.session_state.processing_regime
    
    pendentes = entity.get('precatorios_pendentes', 0)
    total_pages = (pendentes + 9) // 10
    
    logger.info(f"Starting entity: {entity['nome']} (id={entity['id']}, pages={total_pages})")
    
    if total_pages == 0:
        # Skip entities with no pending
        logger.info(f"Skipping entity with 0 pages: {entity['nome']}")
        st.session_state.completed_entities.add(entity['id'])
        st.session_state.current_entity_index += 1
        return start_next_entity()
    
    # Create runner and start extraction
    runner = ExtractionRunner()
    
    # Get consolidated output file
    output_file = st.session_state.get('output_file')
    is_first_entity = (current_idx == 0)
    
    try:
        runner.start_extraction(
            entity_id=entity['id'],
            entity_name=entity['nome'],
            regime=regime,
            total_pages=total_pages,
            num_processes=8,  # 8 parallel workers
            output_file=output_file,
            append_mode=not is_first_entity  # Append after first entity
        )
        
        st.session_state.extraction_runner = runner
        logger.info(f"Successfully started extraction for {entity['nome']}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to start extraction for {entity['nome']}: {e}")
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


def render_v5_progress_view():
    """Render progress view for V5 Full Memory Mode with entity status"""
    
    runner = st.session_state.v5_runner
    total_stats = st.session_state.total_stats
    regime = st.session_state.processing_regime
    entities = st.session_state.get('entities_to_process', [])
    
    if not runner:
        st.error("Runner não encontrado")
        st.session_state.extraction_running = False
        st.rerun()
        return
    
    # Get progress
    progress = runner.get_progress()
    entity_status = progress.get('entity_status', {})
    
    # Check if finished
    if not progress.get('is_running', False):
        st.session_state.extraction_running = False
        st.session_state.show_success = True
        st.session_state.extraction_result = {
            "success": True,
            "total_entities": total_stats.get('entities', 0),
            "records": progress.get('records', 0),
            "expected_records": progress.get('expected_records', 0)
        }
        st.rerun()
        return
    
    # === HEADER ===
    st.markdown("## 🚀 Extração V5 - Full Memory Mode")
    st.markdown(f"**Regime:** {regime.upper()} | **Workers:** 10 simultâneos (modo híbrido)")
    
    # === PROGRESS METRICS ===
    col1, col2, col3 = st.columns(3)
    
    entities_done = progress.get('entities_done', 0)
    total_entities = total_stats.get('entities', len(entities))
    
    with col1:
        st.metric("📊 Entidades", f"{entities_done} / {total_entities}")
    
    with col2:
        st.metric("📝 Registros em Memória", f"{progress.get('records', 0):,}")
    
    with col3:
        elapsed = progress.get('elapsed_seconds', 0)
        st.metric("⏱️ Tempo", format_duration(elapsed))
    
    # Progress bar
    percent = progress.get('percent', 0) / 100
    st.progress(percent, text=f"Progresso: {percent*100:.1f}%")
    
    # === ENTITY STATUS LIST ===
    st.markdown("---")
    st.markdown("### 📋 Status das Entidades")
    
    # Count by status
    completed = [e for e in entities if entity_status.get(e['id']) == 'done']
    processing = [e for e in entities if entity_status.get(e['id']) == 'processing']
    pending = [e for e in entities if entity_status.get(e['id']) not in ['done', 'processing', 'error']]
    errors = [e for e in entities if entity_status.get(e['id']) == 'error']
    
    # Show processing first (max 4)
    if processing:
        st.markdown("**⏳ Processando:**")
        for e in processing[:4]:
            pages = (e.get('precatorios_pendentes', 0) + 9) // 10
            st.caption(f"  🔄 {e['nome']} ({pages} págs)")
    
    # Show recent completed (max 5)
    if completed:
        with st.expander(f"✅ Concluídas ({len(completed)})", expanded=False):
            for e in completed[-10:]:  # Last 10
                pages = (e.get('precatorios_pendentes', 0) + 9) // 10
                records = entity_status.get(f"{e['id']}_records", '?')
                st.caption(f"✓ {e['nome']} - {records} registros")
    
    # Show pending count
    if pending:
        st.caption(f"⏸️ Aguardando: {len(pending)} entidades")
    
    # Show errors
    if errors:
        st.error(f"❌ Erros: {len(errors)} entidades")
    
    st.markdown("---")
    st.info("💾 **Modo Full Memory**: Todos os dados são acumulados em memória. CSV + Excel serão gravados no final.")
    
    # Auto-refresh
    time.sleep(3)
    st.rerun()


def render_progress_view():
    """Render the progress view during extraction with entity tracking"""
    
    runner = st.session_state.extraction_runner
    entities = st.session_state.entities_to_process
    current_idx = st.session_state.current_entity_index
    completed = st.session_state.completed_entities
    total_stats = st.session_state.total_stats
    
    # Safety check: if entities list is empty, reset to setup view
    if not entities:
        st.warning("Lista de entidades vazia. Reiniciando...")
        st.session_state.extraction_running = False
        st.session_state.show_success = False
        time.sleep(2)
        st.rerun()
        return
    
    # Check if runner exists
    if not runner and current_idx < len(entities):
        # Need to start next entity
        st.info(f"Iniciando próxima entidade: {entities[current_idx]['nome']}...")
        if not start_next_entity():
            # Error starting - but don't mark as success, try to continue
            st.error(f"Erro ao iniciar entidade {current_idx + 1}. Tentando próxima...")
            st.session_state.current_entity_index += 1
            time.sleep(2)
            st.rerun()
            return
    
    if not runner:
        # No runner and no more entities - check if we completed any
        if len(completed) > 0:
            st.session_state.extraction_running = False
            st.session_state.show_success = True
            st.session_state.extraction_result = {
                "success": True,
                "total_entities": len(entities),
                "completed_entities": len(completed)
            }
        else:
            st.session_state.extraction_running = False
            st.session_state.show_success = False
        st.rerun()
        return
    
    # Get progress for current entity
    progress = runner.get_progress()
    
    # Check if current entity finished
    if not progress.get('is_running', False):
        from loguru import logger
        logger.info(f"Entity {current_idx} finished. Moving to next...")
        
        # Mark current entity as complete
        if current_idx < len(entities):
            completed.add(entities[current_idx]['id'])
            st.session_state.completed_entities = completed
        
        runner.cleanup()
        st.session_state.extraction_runner = None
        
        # Move to next entity
        next_idx = current_idx + 1
        st.session_state.current_entity_index = next_idx
        logger.info(f"Next entity index: {next_idx} / {len(entities)}")
        
        if next_idx >= len(entities):
            # All entities done!
            logger.info("All entities completed!")
            st.session_state.extraction_running = False
            st.session_state.show_success = True
            st.session_state.extraction_result = {
                "success": True,
                "total_entities": len(entities),
                "completed_entities": len(completed)
            }
        else:
            # Start next entity immediately
            logger.info(f"Starting next entity: {entities[next_idx]['nome']}")
            start_next_entity()
        
        st.rerun()
        return
    
    # === CURRENT ENTITY INFO ===
    current_entity = entities[current_idx] if current_idx < len(entities) else None
    current_progress = progress.get('percent', 0) / 100
    records_extracted = progress.get('records', 0)
    expected_records = progress.get('expected_records', 0)
    
    if current_entity:
        # Compact header
        st.caption(f"Processando: **{current_entity['nome']}** — Entidade {current_idx + 1} de {len(entities)}")
        
        # === TWO-COLUMN LAYOUT ===
        col_status, col_workers = st.columns(2)
        
        with col_status:
            # Progress bar for current entity
            st.progress(current_progress)
            
            # Compact stats line with speed
            elapsed_seconds = progress.get('elapsed_seconds', 0)
            if elapsed_seconds > 0 and records_extracted > 0:
                speed = records_extracted / elapsed_seconds
                st.caption(f"Registros: {format_number(records_extracted)} / {format_number(expected_records)} ({current_progress * 100:.0f}%) — {speed:.1f} rec/s")
            else:
                st.caption(f"Registros: {format_number(records_extracted)} / {format_number(expected_records)} ({current_progress * 100:.0f}%)")
            
            # Estimated time remaining for current entity
            if elapsed_seconds > 10 and current_progress > 0.01:
                remaining_progress = 1.0 - current_progress
                estimated_remaining = (elapsed_seconds / current_progress) * remaining_progress
                if estimated_remaining > 60:
                    st.caption(f"⏱️ Entidade atual: ~{estimated_remaining / 60:.0f} min restantes")
                elif estimated_remaining > 0:
                    st.caption(f"⏱️ Entidade atual: ~{estimated_remaining:.0f} seg restantes")
            
            # Status messages for high progress (finalization phase)
            if current_progress >= 0.98:
                st.info("📦 Finalizando extração e consolidando dados dos workers paralelos...")
            elif current_progress >= 0.95:
                st.info("⏳ Aguardando workers finalizarem...")
        
        with col_workers:
            # Workers status table
            workers = progress.get('workers', [])
            if workers:
                st.caption("**Workers em Processamento:**")
                
                # Build table data
                table_data = []
                for w in workers:
                    status = "✅" if w['progress'] >= 100 else "🔄"
                    table_data.append({
                        "Worker": w['id'],
                        "Página": f"{w['current_page']}/{w['end_page']}",
                        "Progresso": f"{w['progress']:.0f}%",
                        "Records": format_number(w['records'])
                    })
                
                # Display as dataframe (compact)
                import pandas as pd
                df_workers = pd.DataFrame(table_data)
                st.dataframe(
                    df_workers,
                    hide_index=True,
                    use_container_width=True,
                    height=min(35 * len(workers) + 38, 300)  # Dynamic height
                )
                
                # Total parcial
                total_partial = sum(w['records'] for w in workers)
                avg_progress = sum(w['progress'] for w in workers) / len(workers) if workers else 0
                st.caption(f"**Total parcial:** {format_number(total_partial)} records ({avg_progress:.0f}% médio)")
    
    # === OVERALL PROGRESS (based on pages) ===
    # Calculate pages done from completed entities
    completed_pages = sum(
        (e['precatorios_pendentes'] + 9) // 10 for e in entities 
        if e['id'] in completed
    )
    
    # Add pages done from current entity
    current_pages_done = progress.get('pages_done', 0)
    total_pages_done = completed_pages + current_pages_done
    
    # Total pages for all entities
    total_pages_all = total_stats.get('paginas', 1)
    
    # Calculate overall progress
    overall_progress = total_pages_done / total_pages_all if total_pages_all > 0 else 0
    overall_progress = min(0.99, overall_progress)  # Cap at 99%
    
    # Calculate total elapsed time (from session start)
    total_elapsed = st.session_state.get('extraction_start_time')
    if total_elapsed:
        total_elapsed_seconds = (datetime.now() - total_elapsed).total_seconds()
    else:
        total_elapsed_seconds = progress.get('elapsed_seconds', 0)
    
    # Estimate total remaining time based on overall progress
    if overall_progress > 0.01 and total_elapsed_seconds > 30:
        total_estimated_remaining = (total_elapsed_seconds / overall_progress) * (1.0 - overall_progress)
        if total_estimated_remaining > 3600:
            time_str = f"~{total_estimated_remaining / 3600:.1f}h restantes"
        elif total_estimated_remaining > 60:
            time_str = f"~{total_estimated_remaining / 60:.0f} min restantes"
        else:
            time_str = f"~{total_estimated_remaining:.0f} seg restantes"
        st.markdown(f"<p style='color: #ff6b6b; font-weight: bold;'>📊 Progresso geral: {overall_progress * 100:.1f}% ({total_pages_done}/{total_pages_all} páginas) — {time_str}</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color: #ff6b6b; font-weight: bold;'>📊 Progresso geral: {overall_progress * 100:.1f}% ({total_pages_done}/{total_pages_all} páginas)</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === ENTITY TRACKING LIST ===
    st.caption("Entidades:")
    
    # Compact entity list
    entity_lines = []
    for idx, entity in enumerate(entities):
        entity_id = entity['id']
        nome = entity['nome']
        pendentes = entity['precatorios_pendentes']
        
        if entity_id in completed:
            entity_lines.append(f"✓ {nome} ({format_number(pendentes)})")
        elif idx == current_idx:
            entity_lines.append(f"→ **{nome}** ({format_number(pendentes)})")
        else:
            entity_lines.append(f"· {nome} ({format_number(pendentes)})")
    
    # Show in expander to save space
    with st.expander(f"Ver todas ({len(completed)}/{len(entities)} concluídas)", expanded=False):
        for line in entity_lines:
            st.caption(line)
    
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
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()


def render_success_view():
    """Render the success view after extraction of all entities"""
    
    result = st.session_state.get('extraction_result', {})
    entities = st.session_state.get('entities_to_process', [])
    total_stats = st.session_state.get('total_stats', {})
    regime = st.session_state.get('processing_regime', 'geral')
    output_file = st.session_state.get('output_file', '')
    start_time = st.session_state.get('extraction_start_time')
    use_v5 = st.session_state.get('use_v5', False)
    
    # Calculate duration
    if start_time:
        duration = datetime.now() - start_time
        duration_str = f"{int(duration.total_seconds() // 60)}min {int(duration.total_seconds() % 60)}s"
    else:
        duration_str = "N/A"
    
    # For V5, all entities are processed together
    if use_v5:
        total_entities = total_stats.get('entities', len(entities))
        completed_count = total_entities  # V5 processes all at once
        records_count = result.get('records', total_stats.get('pendentes', 0))
    else:
        completed = st.session_state.get('completed_entities', set())
        completed_count = len(completed)
        total_entities = len(entities)
        records_count = total_stats.get('pendentes', 0)
    
    # Show confetti animation
    show_confetti()
    
    # Success header
    st.success("✅ Extração Concluída!")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Entidades Processadas", f"{completed_count}/{total_entities}")
    with col2:
        st.metric("Registros", format_number(records_count))
    with col3:
        st.metric("Duração", duration_str)
    
    # Details
    regime_label = "Especial" if regime == "especial" else "Geral"
    st.caption(f"Regime: {regime_label} — Arquivo: {output_file}")
    
    st.markdown("---")
    
    # Show entities in expander
    with st.expander(f"Ver entidades processadas ({completed_count})", expanded=False):
        for entity in entities:
            st.caption(f"✓ {entity['nome']} ({format_number(entity['precatorios_pendentes'])})")
    
    st.markdown("---")
    
    # File available message
    st.info("📁 O arquivo gerado está disponível na aba **Downloads**.")
    
    # OK button to reset
    if st.button("OK", type="primary"):
        # Reset all state
        st.session_state.show_success = False
        st.session_state.extraction_result = None
        st.session_state.extraction_complete = False
        st.session_state.entities_to_process = []
        st.session_state.current_entity_index = 0
        st.session_state.completed_entities = set()
        st.session_state.processing_regime = None
        st.session_state.use_v5 = False
        st.session_state.v5_runner = None
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
        col_check, col_date, col_name, col_size, col_records = st.columns([0.5, 1.5, 3, 1, 1])
        
        with col_check:
            is_selected = st.checkbox(
                "sel",
                value=select_all,
                key=f"file_{file_info['name']}",
                label_visibility="collapsed"
            )
            if is_selected:
                selected_files.append(file_info)
        
        with col_date:
            st.text(file_info['modified_formatted'])
        
        with col_name:
            st.text(file_info['name'])
        
        with col_size:
            st.text(file_info['size_formatted'])
        
        with col_records:
            st.text(f"{format_number(file_info['records'])} reg.")
    
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
    st.title("⚖️ Totality Precatórios Extração TJRJ")
    
    # Tabs
    tab1, tab2 = st.tabs(["📥 Extração", "📁 Downloads"])
    
    with tab1:
        render_extraction_tab()
    
    with tab2:
        render_downloads_tab()
    
    # Footer
    st.markdown("---")
    st.caption(
        "Totality Precatórios v1.0 | "
        "Dados extraídos do Portal de Precatórios do TJRJ"
    )


if __name__ == "__main__":
    main()
