# TJRJ Precatórios Extractor App - Especificação

## Visão Geral

Interface Streamlit para extração de precatórios do TJRJ com:
- Seleção de regime (Geral/Especial) e entidade
- Processamento paralelo em background
- Progress bar em tempo real
- Animação de sucesso
- Download de arquivos CSV

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit App (app.py)                    │
├─────────────────────────────────────────────────────────────┤
│  Tab 1: EXTRAÇÃO                │  Tab 2: DOWNLOADS          │
│  ┌───────────────────────────┐  │  ┌─────────────────────┐   │
│  │ 🔘 Regime: Geral/Especial │  │  │ 📁 Lista de CSVs    │   │
│  │ 📋 Dropdown: Entidades    │  │  │ ☑️ arquivo1.csv     │   │
│  │ 📊 Total: X precatórios   │  │  │ ☑️ arquivo2.csv     │   │
│  │ 📄 Páginas: Y             │  │  │ [DOWNLOAD]          │   │
│  │ [PROCESSAR]               │  │  └─────────────────────┘   │
│  └───────────────────────────┘  │                            │
│                                 │                            │
│  ┌───────────────────────────┐  │                            │
│  │ ⏱️ Tempo estimado: 45min  │  │                            │
│  │ 🏁 Término: 01:20         │  │                            │
│  │ ████████░░░░░░░░ 45%      │  │                            │
│  │ 📈 1,340/2,984 páginas    │  │                            │
│  └───────────────────────────┘  │                            │
│                                 │                            │
│  🎉 SUCESSO! [confetti]         │                            │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (sem modificações)                      │
│  main_v3_parallel.py + src/scraper_v3.py                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Arquivos

```
app/
├── SPEC.md                 # Esta especificação
├── PLAN.md                 # Plano de implementação
├── app.py                  # Streamlit App (entrada principal)
├── integration.py          # Integração App ↔ Backend
├── requirements.txt        # Dependências do app
└── utils.py                # Funções utilitárias
```

---

## Funcionalidades

### Tab 1: Extração

1. **Seletor de Regime**
   - Radio buttons: Geral / Especial
   - Mostra contagem de entidades por regime

2. **Dropdown de Entidades**
   - Lista carregada do site em tempo real
   - Mostra nome e estatísticas básicas

3. **Estatísticas da Entidade Selecionada**
   - Total de precatórios
   - Páginas estimadas (10 registros/página)
   - Tempo estimado de processamento

4. **Configuração de Processos**
   - Slider: 2-6 processos paralelos
   - Recomendação baseada em CPU

5. **Botão PROCESSAR**
   - Dispara extração em subprocess
   - Desabilita controles durante processamento

6. **Progress Tracking**
   - Progress bar atualizada a cada 30s
   - Tempo decorrido
   - ETA (hora estimada de término)
   - Contagem de registros extraídos

7. **Sucesso**
   - Animação de confetti
   - Resumo da extração
   - Botão de download direto

### Tab 2: Downloads

1. **Lista de CSVs**
   - Ordenados por data (mais recente primeiro)
   - Mostra: nome, tamanho, data, registros

2. **Seleção**
   - Checkbox por arquivo
   - "Selecionar todos"

3. **Download**
   - Arquivo único: download direto
   - Múltiplos: ZIP

---

## Integração com Backend

### Carregar Entidades (rápido, ~5s)
```python
def get_entities_list(regime: str) -> List[dict]:
    """
    Navega ao site e extrai lista de entidades
    Retorna: [{"id": 1, "nome": "Estado RJ", "total": 17663}, ...]
    """
```

### Executar Extração
```python
def run_extraction(entity_id, entity_name, regime, num_processes, total_pages):
    """
    Executa main_v3_parallel.py como subprocess
    Comando: python main_v3_parallel.py --entity-id X --skip-expanded ...
    """
```

### Monitorar Progresso
```python
def get_extraction_progress(session_id: str) -> dict:
    """
    Lê arquivos partial_*.csv para calcular progresso
    Retorna: {"records": 7418, "percent": 42, "eta_minutes": 27}
    """
```

---

## Performance

| Modo | Estado RJ (2.984 páginas) | Tempo |
|------|---------------------------|-------|
| V3 Parallel + skip-expanded | 4 processos | ~45 min |
| V3 Parallel + skip-expanded | 6 processos | ~30 min |

---

## Dependências

```txt
streamlit>=1.28.0
streamlit-extras>=0.3.0
pandas>=2.0.0
```

---

## Como Executar

```bash
cd /path/to/Charles
streamlit run app/app.py
```

---

**Versão**: 1.0.0
**Data**: 2025-11-30
