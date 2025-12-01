# Plano de Implementação - TJRJ Precatórios Extractor App

## Fases de Implementação

### Fase 1: Setup e Estrutura (30 min) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 1.1 | Criar estrutura de pastas | ✅ |
| 1.2 | Criar SPEC.md | ✅ |
| 1.3 | Criar PLAN.md | ✅ |
| 1.4 | Criar requirements.txt | ✅ |
| 1.5 | Criar integration.py | ✅ |
| 1.6 | Criar utils.py | ✅ |
| 1.7 | Criar app.py (estrutura) | ✅ |

### Fase 2: Módulo de Integração (45 min) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 2.1 | `EntityLoader.get_entities()` | ✅ |
| 2.2 | `ExtractionRunner.start_extraction()` | ✅ |
| 2.3 | `ExtractionRunner.get_progress()` | ✅ |
| 2.4 | `ExtractionRunner.get_result()` | ✅ |
| 2.5 | `list_csv_files()` em utils.py | ✅ |

### Fase 3: Tab de Extração (1h) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 3.1 | Layout básico | ✅ |
| 3.2 | Seletor de regime | ✅ |
| 3.3 | Dropdown de entidades | ✅ |
| 3.4 | Card de estatísticas | ✅ |
| 3.5 | Slider de processos | ✅ |
| 3.6 | Botão PROCESSAR | ✅ |

### Fase 4: Progress Tracking (45 min) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 4.1 | Estado de processamento | ✅ |
| 4.2 | Progress bar | ✅ |
| 4.3 | Métricas em tempo real | ✅ |
| 4.4 | Cálculo de ETA | ✅ |
| 4.5 | Auto-refresh | ✅ |

### Fase 5: Sucesso e Animação (15 min) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 5.1 | Detectar conclusão | ✅ |
| 5.2 | Animação confetti | ✅ |
| 5.3 | Resumo | ✅ |
| 5.4 | Botão download | ✅ |

### Fase 6: Tab de Downloads (30 min) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 6.1 | Listar arquivos | ✅ |
| 6.2 | Tabela com checkboxes | ✅ |
| 6.3 | Informações | ✅ |
| 6.4 | Download único | ✅ |
| 6.5 | Download múltiplo (ZIP) | ✅ |

### Fase 7: Polish (15 min) ✅
| Step | Tarefa | Status |
|------|--------|--------|
| 7.1 | Tratamento de erros | ✅ |
| 7.2 | Loading states | ✅ |
| 7.3 | Estilização CSS | ✅ |
| 7.4 | Testes finais | ⏳ |

---

## Estimativa Total: 3-4 horas

---

## Comandos de Teste

```bash
# Instalar dependências
pip install -r app/requirements.txt

# Executar app
streamlit run app/app.py

# Executar em porta específica
streamlit run app/app.py --server.port 8501
```

---

## Notas de Implementação

### Session State
```python
# Estados a manter
st.session_state.extraction_running = False
st.session_state.extraction_process = None
st.session_state.extraction_start_time = None
st.session_state.entities_cache = {}
```

### Monitoramento de Progresso
- Ler arquivos `output/partial_p*_*.csv` a cada 30s
- Contar linhas para estimar progresso
- Não interfere com o subprocess

### Subprocess
```python
# Executar sem bloquear
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=project_root
)
```

---

**Última Atualização**: 2025-11-30 00:51
