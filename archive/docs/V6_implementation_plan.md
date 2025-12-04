# V6 Implementation Plan - Automatic Gap Recovery & Full Integration

**Created:** December 1, 2025  
**Base Version:** V5-STABLE (tag: `v5-stable`)  
**Goal:** Fully automated extraction with gap detection, recovery, and merge

---

## Executive Summary

V6 will transform the current semi-manual workflow into a fully automated pipeline where:
1. User clicks "Processar" in UI
2. System extracts all entities
3. System automatically detects gaps
4. System automatically recovers failed entities
5. System merges and formats final output
6. User receives complete CSV + Excel files

---

## Implementation Phases

### Phase 1: Backend Gap Detection (No UI Changes)
**Objective:** Create standalone gap detection that can be tested independently

**Files to Create:**
- `gap_recovery.py` - New module with gap detection and recovery functions

**Functions to Implement:**
```python
def detect_failed_entities(log_file: str, start_time: str) -> List[Dict]:
    """
    Parse log to find entities with:
    - 0 records extracted
    - Timeout errors
    - Page.goto timeout errors
    
    Returns: [{"id": 62, "name": "Município X", "reason": "timeout"}]
    """

def get_extraction_summary(log_file: str, start_time: str) -> Dict:
    """
    Returns: {
        "total_entities": 41,
        "successful_entities": 39,
        "failed_entities": 2,
        "total_records": 40120,
        "failed_list": [...]
    }
    """
```

**Testing:**
```bash
# Test with existing log from especial regime run
python -c "from gap_recovery import detect_failed_entities; print(detect_failed_entities('logs/scraper_v3.log', '2025-12-01 19:38'))"
```

**Success Criteria:**
- Correctly identifies entities with 0 records
- Correctly identifies timeout errors
- Returns structured data for next phase

---

### Phase 2: Backend Gap Recovery (No UI Changes)
**Objective:** Add recovery function that re-extracts failed entities

**Add to `gap_recovery.py`:**
```python
def recover_failed_entities(
    failed_entities: List[Dict],
    regime: str,
    num_processes: int = 5,
    timeout_minutes: int = 10
) -> Tuple[List[Dict], str]:
    """
    Re-extract records for failed entities.
    Uses extract_single_entity from main_v5_all_entities.
    
    Returns: (records_list, partial_csv_path)
    """
```

**Testing:**
```bash
# Test recovery of known failed entities from especial regime
python -c "
from gap_recovery import recover_failed_entities
failed = [{'id': 62, 'name': 'Município de Valença'}, {'id': 18, 'name': 'Município de Miracema'}]
records, path = recover_failed_entities(failed, 'especial')
print(f'Recovered {len(records)} records to {path}')
"
```

**Success Criteria:**
- Successfully re-extracts records for failed entities
- Saves partial CSV with recovered records
- Handles errors gracefully

---

### Phase 3: Backend Merge & Finalize (No UI Changes)
**Objective:** Combine main extraction with recovered gaps

**Add to `gap_recovery.py`:**
```python
def merge_and_finalize(
    main_csv: str,
    gaps_csv: str,
    output_path: str
) -> Dict:
    """
    1. Load both CSVs
    2. Concatenate
    3. Remove duplicates (by numero_precatorio or unique key)
    4. Apply clean_ordem_column()
    5. Apply format_monetary_columns()
    6. Sort by entidade_devedora, ordem
    7. Save CSV + Excel
    
    Returns: {"total_records": N, "duplicates_removed": M, "output_file": path}
    """
```

**Testing:**
```bash
# Test merge with existing files
python -c "
from gap_recovery import merge_and_finalize
result = merge_and_finalize(
    'output/precatorios_especial_ALL_20251201_193851.csv',
    'output/partial/especial_gaps_fixed.csv',
    'output/test_merge.csv'
)
print(result)
"
```

**Success Criteria:**
- Correctly merges CSVs
- Removes duplicates
- Applies all formatting
- Generates both CSV and Excel

---

### Phase 4: Orchestrator Function (No UI Changes)
**Objective:** Single function that runs the complete pipeline

**Add to `gap_recovery.py`:**
```python
def run_complete_extraction(
    regime: str,
    num_processes: int = 10,
    timeout_minutes: int = 60,
    auto_recover: bool = True
) -> Dict:
    """
    Complete extraction pipeline:
    1. Run main_v5_all_entities.py
    2. Detect gaps
    3. If gaps and auto_recover: recover them
    4. Merge results
    5. Return final statistics
    
    Returns: {
        "success": True,
        "total_records": N,
        "entities_processed": M,
        "gaps_recovered": K,
        "output_file": path,
        "excel_file": path,
        "duration_seconds": T
    }
    """
```

**Testing:**
```bash
# Full test with geral regime (smaller, faster)
python -c "
from gap_recovery import run_complete_extraction
result = run_complete_extraction('geral', num_processes=10)
print(result)
"
```

**Success Criteria:**
- Runs complete pipeline end-to-end
- Handles gaps automatically
- Returns comprehensive statistics

---

### Phase 5: Integration Layer Update
**Objective:** Connect orchestrator to existing UI infrastructure

**Modify `app/integration.py`:**

1. **Add new runner class:**
```python
class V6ExtractionRunner:
    """
    V6 runner with automatic gap recovery.
    Wraps gap_recovery.run_complete_extraction()
    """
    
    def start_extraction(self, regime: str, num_processes: int = 10):
        """Start extraction subprocess"""
    
    def get_progress(self) -> Dict:
        """
        Returns progress including:
        - phase: 'extracting' | 'checking_gaps' | 'recovering' | 'merging' | 'done'
        - current_entity, total_entities
        - records, total_pendentes
        - gaps_found, gaps_recovered
        """
    
    def get_result(self) -> Dict:
        """Final result with all statistics"""
```

**Testing:**
```bash
# Test new runner independently
python -c "
from app.integration import V6ExtractionRunner
runner = V6ExtractionRunner()
runner.start_extraction('geral', num_processes=10)
# Monitor progress...
"
```

**Success Criteria:**
- New runner works independently
- Progress includes phase information
- Result includes gap recovery stats

---

### Phase 6: UI Updates (Minimal Changes)
**Objective:** Update UI to use V6 runner and show new states

**Modify `app/app.py`:**

1. **Update `start_all_entities_extraction()`:**
   - Use `V6ExtractionRunner` instead of `AllEntitiesRunner`

2. **Update `render_progress_view()`:**
   - Add phase-based messaging:
     - "Extraindo..." (extracting)
     - "Verificando integridade..." (checking_gaps)
     - "Recuperando X entidades..." (recovering)
     - "Consolidando dados..." (merging)

3. **Update `render_success_view()`:**
   - Show gaps recovered count if > 0
   - Show final merged file info

**Testing:**
```bash
streamlit run app/app.py
# Test with both regimes
```

**Success Criteria:**
- UI shows correct phase
- Success view shows gap recovery info
- Downloads tab shows final merged file

---

## Testing Strategy

### Unit Tests (Per Phase)
Each phase includes inline testing commands that can be run independently.

### Integration Tests
After Phase 4, run full pipeline tests:
```bash
# Test 1: Geral regime (fast, ~15 min)
python -c "from gap_recovery import run_complete_extraction; print(run_complete_extraction('geral'))"

# Test 2: Especial regime (slower, ~50 min)
python -c "from gap_recovery import run_complete_extraction; print(run_complete_extraction('especial'))"
```

### UI Tests
After Phase 6, manual testing:
1. Start Streamlit
2. Select Geral, click Processar
3. Verify progress phases display correctly
4. Verify success view shows complete stats
5. Verify Downloads tab has final file
6. Repeat for Especial

---

## Rollback Plan

If V6 has issues, rollback is simple:
```bash
git checkout v5-stable
```

The V5 stable version is tagged and will continue to work.

---

## File Summary

| File | Action | Phase |
|------|--------|-------|
| `gap_recovery.py` | CREATE | 1-4 |
| `main_v5_all_entities.py` | NO CHANGE | - |
| `app/integration.py` | MODIFY (add class) | 5 |
| `app/app.py` | MODIFY (minimal) | 6 |

---

## Timeline Estimate

| Phase | Estimated Time | Cumulative |
|-------|---------------|------------|
| Phase 1 | 30 min | 30 min |
| Phase 2 | 45 min | 1h 15min |
| Phase 3 | 30 min | 1h 45min |
| Phase 4 | 30 min | 2h 15min |
| Phase 5 | 45 min | 3h |
| Phase 6 | 30 min | 3h 30min |
| Testing | 1h 30min | 5h |

**Total:** ~5 hours of development + testing

---

## Next Steps

1. **Approve this plan** - Confirm phases and approach
2. **Start Phase 1** - Create `gap_recovery.py` with detection functions
3. **Test Phase 1** - Verify detection works with existing logs
4. **Proceed to Phase 2** - Add recovery functions
5. **Continue iteratively** - Each phase builds on the previous

---

## Notes

- Each phase is independently testable
- No changes to `main_v5_all_entities.py` - we reuse its functions
- UI changes are minimal and isolated to Phase 6
- Rollback to V5 is always possible via git tag
