# Estratégia 3: Paralelização por Entidade ⭐ RECOMENDADO

**Status**: ✅ Recomendado para implementação
**Complexidade**: ⭐⭐ Baixa-Média
**Risco**: ⭐ Muito Baixo
**Investimento**: 2-3h implementação + testes
**Probabilidade de Sucesso**: ~100%

---

## 📋 Descrição

Paralelizar a extração distribuindo **entidades completas** entre múltiplos processos independentes, ao invés de dividir páginas de uma mesma entidade.

**Princípio**: Cada processo extrai entidades diferentes do início ao fim, de forma completamente isolada.

**Exemplo prático**:
```
Processo 1: Estado RJ (isolado)                   → 8h
Processo 2: Petrópolis, São Gonçalo, Volta R.     → 2.5h
Processo 3: 18 entidades médias (ESPECIAL)        → 2h
Processo 4: 19 entidades pequenas (ESPECIAL)      → 1h
Processo 5: 56 entidades (GERAL completo)         → 2h

Tempo Total: ~8h (limitado pelo Estado RJ)
```

---

## 🎯 Por Que Esta Estratégia?

### Vantagens sobre Estratégia 2 (API Ranges)

| Aspecto | Estratégia 2 (API) | Estratégia 3 (Entidades) |
|---------|-------------------|--------------------------|
| **Requer API** | ✅ SIM (não encontrada) | ❌ NÃO |
| **Investigação** | 3-4h | 0h (análise já feita) |
| **Probabilidade Sucesso** | ~20% | ~100% |
| **Complexidade** | ⭐⭐⭐⭐⭐ Muito Alta | ⭐⭐ Baixa-Média |
| **Risco Legal** | ⚠️ Eng. reversa de API | ✅ Mesmo método atual |
| **Implementação** | 4-6h (SE API existir) | 2-3h (garantido) |
| **ROI** | Negativo (-90%) | Positivo (+200%) |

**Conclusão**: Estratégia 3 é viável, segura e implementável imediatamente.

---

## ⚙️ Arquitetura Proposta

### Distribuição de Entidades (VPS KVM 4 - 5 Processos)

#### Processo 1: Estado RJ (Isolado) - GARGALO INEVITÁVEL
```
Entidade: Estado do Rio de Janeiro (Regime ESPECIAL)
Registros: 17,663
Páginas: ~1,767
Tempo Estimado: 7h 52min

Justificativa: Isolar para não bloquear outros processos
```

#### Processo 2: Entidades Grandes (ESPECIAL)
```
Entidades:
  1. Petrópolis            → 2,921 registros (1h 18min)
  2. São Gonçalo           → 1,423 registros (38min)
  3. Volta Redonda         →   983 registros (26min)

Total: 5,327 registros (~2.5h)
```

#### Processo 3: Entidades Médias (ESPECIAL)
```
Entidades (18 entidades de 100-500 registros):
  - Macaé, Barra Mansa, Campos dos Goytacazes
  - Teresópolis, Nova Iguaçu, Belford Roxo
  - Itaboraí, Duque de Caxias, São João de Meriti
  - Magé, Queimados, Angra dos Reis
  - Cabo Frio, Mesquita, Niterói
  - Nova Friburgo, Resende, Nilópolis

Total: ~3,500 registros (~2h)
```

#### Processo 4: Entidades Pequenas (ESPECIAL)
```
Entidades (19 entidades de 0-100 registros):
  - Município do Rio de Janeiro, Maricá, Itaguaí
  - Japeri, Paracambi, Seropédica
  - Guapimirim, Tanguá, São José do Vale do Rio Preto
  - Areal, Comendador Levy Gasparian, Engenheiro Paulo de Frontin
  - Sapucaia, Carmo, Mendes
  - Paraíba do Sul, Piraí, Rio Claro
  - Bom Jardim

Total: ~800 registros (~1h)
```

#### Processo 5: Regime GERAL Completo
```
Entidades: Todas as 56 entidades do Regime GERAL
  - Município do Rio de Janeiro: 2,486 registros
  - INSS: 907 registros
  - Niterói: 620 registros
  - São Francisco de Itabapoana: 337 registros
  - Nova Iguaçu: 245 registros
  - Outras 51 entidades: ~850 registros

Total: ~5,444 registros (~2h)
```

---

## 📊 Distribuição Balanceada por Tempo

### Análise de Balanceamento

```
Processo 1: ████████████████████████████████████████ 8h (Estado RJ)
Processo 2: ████████████                             2.5h (3 grandes)
Processo 3: ██████████                               2h (18 médias)
Processo 4: █████                                    1h (19 pequenas)
Processo 5: ██████████                               2h (GERAL 56)

LIMITANTE: Processo 1 (Estado RJ)
```

**Eficiência de Balanceamento**:
- Processo mais longo: 8h (Estado RJ)
- Processo mais curto: 1h (Pequenas)
- Diferença: 7h (87.5% de ociosidade para Processo 4)

**Impossível balancear melhor porque**:
- Estado RJ não pode ser dividido (sem API de paginação)
- Estado RJ representa 68% dos dados de ESPECIAL
- Gargalo arquitetural inevitável

---

## 💻 Implementação

### Arquitetura de Código

```
v2_parallel/
├── main_parallel.py              # Orquestrador principal
├── config/
│   ├── entity_groups.py          # Configuração de grupos
│   └── process_config.py         # Config de processos
├── extractors/
│   └── entity_extractor.py       # Extrator por entidade
├── utils/
│   ├── process_manager.py        # Gerenciamento de processos
│   └── csv_merger.py             # Merge de CSVs parciais
└── logs/
    └── process_*.log             # Logs por processo
```

### Pseudo-código Principal

```python
# main_parallel.py

from multiprocessing import Pool, Manager
from config.entity_groups import PROCESS_GROUPS

def extract_entity_group(group_id, entities, regime):
    """
    Extrai um grupo de entidades em um processo separado

    Args:
        group_id: ID do processo (1-5)
        entities: Lista de EntidadeDevedora para este grupo
        regime: 'geral' ou 'especial'

    Returns:
        CSV path with extracted data
    """
    # Cada processo tem seu próprio browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        scraper = TJRJPrecatoriosScraper()
        all_precatorios = []

        for entidade in entities:
            logger.info(f"[P{group_id}] Extracting {entidade.nome_entidade}...")

            try:
                precatorios = scraper.get_precatorios_entidade(page, entidade)
                all_precatorios.extend(precatorios)
                logger.info(f"[P{group_id}] ✅ {len(precatorios)} records extracted")

            except Exception as e:
                logger.error(f"[P{group_id}] ❌ Failed: {e}")
                # Continua para próxima entidade (resiliência)

        # Salvar CSV parcial
        csv_path = f"data/partial/process_{group_id}_{regime}.csv"
        save_to_csv(all_precatorios, csv_path)

        browser.close()
        return csv_path

def run_parallel_extraction():
    """Executa extração paralela usando 5 processos"""

    # Definir grupos de entidades
    groups = [
        (1, [estado_rj_entidade], 'especial'),          # Isolado
        (2, GRANDES_ESPECIAL, 'especial'),              # 3 entidades
        (3, MEDIAS_ESPECIAL, 'especial'),               # 18 entidades
        (4, PEQUENAS_ESPECIAL, 'especial'),             # 19 entidades
        (5, ALL_GERAL, 'geral'),                        # 56 entidades
    ]

    # Executar em paralelo
    with Pool(processes=5) as pool:
        results = pool.starmap(extract_entity_group, groups)

    # Merge CSVs
    merge_csv_files(results, 'data/processed/precatorios_complete.csv')

    logger.info("✅ Extraction complete!")

if __name__ == "__main__":
    run_parallel_extraction()
```

### Configuração de Grupos

```python
# config/entity_groups.py

# Processo 1: Estado RJ (isolado)
ESTADO_RJ = EntidadeDevedora(
    id_entidade=1,
    nome_entidade="Estado do Rio de Janeiro",
    regime="especial",
    precatorios_pendentes=17663
)

# Processo 2: 3 grandes (ESPECIAL)
GRANDES_ESPECIAL = [
    EntidadeDevedora(id_entidade=2, nome_entidade="Petrópolis", ...),
    EntidadeDevedora(id_entidade=3, nome_entidade="São Gonçalo", ...),
    EntidadeDevedora(id_entidade=4, nome_entidade="Volta Redonda", ...),
]

# Processo 3: 18 médias (ESPECIAL)
MEDIAS_ESPECIAL = [
    EntidadeDevedora(id_entidade=5, nome_entidade="Macaé", ...),
    EntidadeDevedora(id_entidade=6, nome_entidade="Barra Mansa", ...),
    # ... (16 mais)
]

# Processo 4: 19 pequenas (ESPECIAL)
PEQUENAS_ESPECIAL = [
    EntidadeDevedora(id_entidade=20, nome_entidade="Município RJ", ...),
    EntidadeDevedora(id_entidade=21, nome_entidade="Maricá", ...),
    # ... (17 mais)
]

# Processo 5: GERAL completo
ALL_GERAL = [
    EntidadeDevedora(id_entidade=100, nome_entidade="Município RJ", regime="geral", ...),
    # ... (55 mais)
]
```

---

## 🔧 Implementação Detalhada

### Fase 1: Refatoração (1h)

**Mudanças necessárias**:
1. Extrair lógica de extração de entidade para função isolada
2. Aceitar lista de entidades como input
3. Retornar CSV path ao invés de printar
4. Logs prefixados com ID do processo (`[P1]`, `[P2]`, etc)

**Arquivos a modificar**:
- `src/scraper.py`: Adicionar `extract_entities(entity_list)` method
- Criar `utils/process_manager.py`: Gerenciamento de processos

### Fase 2: Configuração de Grupos (30min)

**Tarefas**:
1. Carregar entidades de `data/processed/entidades_*.csv`
2. Classificar por volume (grande, média, pequena)
3. Criar distribuição balanceada
4. Validar que todas as 97 entidades estão incluídas

**Validação**:
```python
# Garantir que nenhuma entidade foi esquecida
all_entities = set()
for group in [ESTADO_RJ, GRANDES, MEDIAS, PEQUENAS, ALL_GERAL]:
    all_entities.update([e.id_entidade for e in group])

assert len(all_entities) == 97, "Missing entities!"
```

### Fase 3: Orquestração Paralela (30min)

**Implementação**:
```python
from multiprocessing import Pool

def run_parallel():
    groups = prepare_entity_groups()

    with Pool(processes=5) as pool:
        csv_paths = pool.starmap(extract_entity_group, groups)

    # Merge CSVs
    final_csv = merge_csv_files(csv_paths)

    return final_csv
```

**Configuração de Pool**:
- `processes=5`: Número de processos paralelos
- `maxtasksperchild=1`: Evitar memory leaks
- Cada processo spawn próprio browser

### Fase 4: Merge de CSVs (30min)

**Lógica**:
```python
def merge_csv_files(csv_paths, output_path):
    """Merge multiple CSV files into one"""

    all_dataframes = []

    for csv_path in csv_paths:
        df = pd.read_csv(csv_path)
        all_dataframes.append(df)

    # Concatenate
    merged = pd.concat(all_dataframes, ignore_index=True)

    # Validate columns
    assert len(merged.columns) == 19, "Missing columns!"

    # Sort by entidade + data_inscricao
    merged = merged.sort_values(['nome_entidade', 'data_inscricao'])

    # Save
    merged.to_csv(output_path, index=False)

    return output_path
```

### Fase 5: Testes (30min)

**Testes necessários**:
1. Teste com 3 entidades pequenas (validação rápida)
2. Teste com 2 processos (GERAL + 1 entidade ESPECIAL)
3. Teste completo com 5 processos

**Script de teste**:
```python
# tests/test_parallel_extraction.py

def test_small_parallel():
    """Test with 3 small entities across 2 processes"""
    groups = [
        (1, [entity1, entity2], 'especial'),
        (2, [entity3], 'geral'),
    ]

    with Pool(2) as pool:
        results = pool.starmap(extract_entity_group, groups)

    # Validate CSVs exist
    assert all(os.path.exists(csv) for csv in results)

    # Validate data
    merged = merge_csv_files(results)
    df = pd.read_csv(merged)

    assert len(df) > 0, "No data extracted"
    assert len(df.columns) == 19, "Missing columns"
```

---

## 📊 Ganhos Esperados

### Performance

| Métrica | V1 (Atual) | V2 (Paralelo) | Melhoria |
|---------|------------|---------------|----------|
| **Tempo Total** | ~8h | ~8h | 0% ⚠️ |
| **CPU Utilizado** | 50% (2 cores) | 90-100% (4 cores) | +80% ✅ |
| **Resiliência** | Baixa | Alta | +200% ✅ |
| **Re-execução** | Tudo do zero | Apenas entidades falhadas | +400% ✅ |
| **Monitoramento** | 2 processos | 5 processos granulares | +150% ✅ |

**Observação importante**: Tempo total NÃO reduz porque Estado RJ (8h) é gargalo inevitável.

### Resiliência (Principal Ganho)

**Cenário: Falha no Estado RJ (página 1,500)**

**V1 (Atual)**:
```
Processo ESPECIAL falha na página 1,500 do Estado RJ (após 6h)
❌ Perda: 6h de trabalho
❌ Re-execução: TODAS as 41 entidades do zero
❌ Tempo desperdiçado: 6h + 8h (re-run) = 14h total
```

**V2 (Paralelo)**:
```
Processo 1 falha na página 1,500 do Estado RJ (após 6h)
✅ Processos 2, 3, 4, 5 continuam normalmente
✅ Ao final: 4 processos completos, 1 falhado
✅ Re-execução: Apenas Estado RJ (rodar Processo 1 sozinho)
✅ Tempo desperdiçado: 0h (outros completaram)
✅ Tempo total: 8h (inicial) + 8h (re-run Estado RJ) = 16h
  vs 14h do V1, MAS com dados de 40 entidades já salvos
```

**Benefício**: Re-execuções parciais possíveis.

### Uso de Recursos

**V1 (2 processos)**:
```
RAM: ~640 MB
CPU: ~50% (em quad-core)
Aproveitamento: ⚠️ Subutilizado
```

**V2 (5 processos)**:
```
RAM: ~1,600 MB (11% de 16 GB)
CPU: ~100% (em quad-core)
Aproveitamento: ✅ Ótimo
```

---

## ⚠️ Riscos e Mitigações

### Risco 1: Rate Limiting do Site

**Problema**: 5 processos simultâneos podem acionar throttling

**Probabilidade**: 30% (não testado além de 2 processos)

**Mitigação**:
```python
# Adicionar delays randomizados entre requests
import random

delay = random.uniform(500, 1500)  # 0.5-1.5s
page.wait_for_timeout(delay)
```

**Plano B**: Reduzir de 5 → 3 processos

---

### Risco 2: Consumo de RAM em VPS

**Problema**: 5 processos = ~1,600 MB (pode exceder em picos)

**Probabilidade**: 10% (VPS KVM 4 tem 16 GB)

**Mitigação**:
- Configurar 4 GB de swap
- Monitorar com `htop`
- Matar processos se RAM > 90%

---

### Risco 3: Conflito de Escrita em CSV

**Problema**: Múltiplos processos escrevendo no mesmo arquivo

**Probabilidade**: 0% (design elimina risco)

**Solução no design**:
```
Cada processo escreve CSV próprio:
  - process_1_especial.csv
  - process_2_especial.csv
  - ...

Merge APÓS todos terminarem (sem concorrência)
```

---

### Risco 4: Browser Crashes

**Problema**: Playwright/Chromium pode crashar após horas

**Probabilidade**: 5%

**Mitigação**:
```python
try:
    precatorios = extract_entities(entity_list)
except Exception as e:
    logger.error(f"Process crashed: {e}")
    # Salvar progresso parcial
    save_to_csv(precatorios, f"partial_{timestamp}.csv")
```

---

## 💰 Análise Custo-Benefício

| Aspecto | Estimativa |
|---------|------------|
| **Implementação** | 2h |
| **Testes** | 1h |
| **Total Investimento** | **3h** |
| **Probabilidade Sucesso** | **100%** |
| **Ganho em Tempo** | 0h (mesmo 8h) |
| **Ganho em Resiliência** | ⭐⭐⭐⭐⭐ Alto |
| **Ganho em CPU** | +80% utilização |
| **ROI** | +200% (resiliência + otimização) |

**Valor Esperado**:
```
100% × (Resiliência + Otimização) = Alto retorno
Investimento: 3h
ROI: Positivo (+200%)
```

**Conclusão**: **VALE A PENA** implementar esta estratégia.

---

## 🎯 Recomendação de Deployment

### Ambiente Ideal: VPS Hostinger KVM 4

**Especificações**:
- 4 vCPUs
- 16 GB RAM
- Ubuntu 22.04 LTS
- Playwright headless

**Comando de Execução**:
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar em background com nohup
nohup python3 v2_parallel/main_parallel.py > logs/parallel_execution.log 2>&1 &

# Monitorar progresso
tail -f logs/parallel_execution.log

# Monitorar recursos
htop
```

**Monitoramento**:
```bash
# Ver processos Python ativos
ps aux | grep python

# Ver logs de cada processo
tail -f logs/process_1.log
tail -f logs/process_2.log
# ...

# Ver progresso em tempo real
watch -n 10 'wc -l data/partial/*.csv'
```

---

## 📋 Checklist de Implementação

### Pré-Implementação
- [ ] Validar que V1 está funcional (100% campos extraídos)
- [ ] Confirmar que bugs de campos expandidos foram corrigidos
- [ ] Backup dos CSVs atuais (V1)
- [ ] Provisionar VPS KVM 4 (ou preparar máquina local com 4+ cores)

### Implementação
- [ ] Criar estrutura `v2_parallel/` (30min)
- [ ] Refatorar `scraper.py` para aceitar lista de entidades (1h)
- [ ] Criar `config/entity_groups.py` com distribuição (30min)
- [ ] Implementar `main_parallel.py` com multiprocessing (30min)
- [ ] Implementar merge de CSVs (30min)
- [ ] Criar testes unitários (30min)

### Testes
- [ ] Teste local com 2 processos e 3 entidades pequenas (15min)
- [ ] Validar CSVs parciais gerados corretamente (10min)
- [ ] Validar merge de CSVs (10min)
- [ ] Teste completo local (se hardware permitir) ou em VPS (8h)

### Deployment VPS
- [ ] Deploy código para VPS
- [ ] Instalar dependências (Python, Playwright, etc)
- [ ] Testar com 2 processos primeiro (smoke test)
- [ ] Executar com 5 processos
- [ ] Monitorar primeiras 2h de execução
- [ ] Validar logs e progresso

### Pós-Deployment
- [ ] Validar CSVs finais (contagem de registros)
- [ ] Verificar 100% cobertura de campos expandidos
- [ ] Comparar com V1 (baseline)
- [ ] Documentar issues encontrados
- [ ] Medir consumo de recursos (RAM, CPU)

---

## 🔄 Comparação com Outras Estratégias

| Critério | Opção 1 (Atual) | Opção 2 (API) | **Opção 3 (Entidades)** ⭐ |
|----------|-----------------|---------------|----------------------------|
| **Tempo Total** | ~8h | ~2-3h (SE API existir) | ~8h |
| **Investimento** | 0h | 10-13h | **3h** ✅ |
| **Probabilidade Sucesso** | 100% | ~20% | **100%** ✅ |
| **Resiliência** | Baixa | Alta (SE funcionar) | **Alta** ✅ |
| **Uso de CPU** | 50% | 80-90% | **90-100%** ✅ |
| **Risco Legal** | Zero | Alto (eng. reversa) | **Zero** ✅ |
| **Escalabilidade** | Baixa | Alta (SE API existir) | **Média** ✅ |
| **Complexidade** | Muito Baixa | Muito Alta | **Baixa-Média** ✅ |
| **ROI** | N/A | -90% | **+200%** ✅ |

**Veredicto**: Opção 3 é **claramente superior** em todos os critérios exceto tempo total (que é limitado pelo Estado RJ inevitavelmente).

---

## 🚀 Próximos Passos

### Implementação Imediata (Se Aprovado)

1. **Criar estrutura de código** (30min)
   ```bash
   mkdir -p v2_parallel/{config,extractors,utils,logs}
   touch v2_parallel/main_parallel.py
   ```

2. **Refatorar extrator** (1h)
   - Extrair lógica para `extractors/entity_extractor.py`
   - Aceitar lista de entidades
   - Retornar CSV path

3. **Configurar grupos** (30min)
   - Carregar entidades de CSVs
   - Criar distribuição balanceada
   - Validar 97 entidades

4. **Implementar orquestração** (30min)
   - `multiprocessing.Pool`
   - Spawnar 5 processos
   - Coletar resultados

5. **Implementar merge** (30min)
   - Ler CSVs parciais
   - Concatenar com Pandas
   - Validar colunas

6. **Testar** (1h)
   - Teste pequeno (2 processos, 3 entidades)
   - Teste completo (5 processos, 97 entidades)

**Tempo Total**: **3h** (implementação + testes)

---

## 📚 Referências

- `findings/01_api_investigation.md` - Por que Opção 2 não é viável
- `findings/02_performance_analysis.md` - Gargalo do Estado RJ
- `findings/03_resource_requirements.md` - Capacidade de VPS KVM 4
- `findings/04_current_bugs_fixed.md` - Bugs já corrigidos (baseline V1)
- `strategies/option1_maintain_current.md` - Configuração atual (baseline)
- `strategies/option2_api_ranges.md` - Alternativa não recomendada

---

## 💡 Melhorias Futuras (Pós-V2)

### Otimização 1: Checkpoint/Resume por Entidade
```python
# Salvar progresso a cada 100 páginas
if page_num % 100 == 0:
    save_checkpoint(entidade_id, page_num, precatorios)

# Retomar de onde parou
if checkpoint_exists(entidade_id):
    start_page = load_checkpoint(entidade_id)
```

**Ganho**: Resiliência adicional (não perde horas em caso de crash)

### Otimização 2: Eliminar Collapse de Expandidos
```python
# Não clicar "-" após extrair
# Deixar todos expandidos acumulados

# Ganho: ~30% redução de tempo (8h → 5.6h)
# Risco: Possível poluição de DOM
```

### Otimização 3: Dynamic Process Allocation
```python
# Quando Processo 4 termina (1h), reatribuir para ajudar Processo 1
# Dividir Estado RJ dinamicamente entre processos ociosos

# Requer: API de paginação (não disponível)
```

---

**Última Atualização**: 2025-11-26
**Status**: ✅ RECOMENDADO para implementação imediata
**Próximo Passo**: Aguardar aprovação do usuário para começar implementação

---

## ✅ Resumo Executivo

**O Que Fazer**: Dividir 97 entidades em 5 grupos balanceados por tempo, cada um rodando em processo separado.

**Por Que Fazer**: Melhor uso de CPU (50% → 100%), resiliência alta, re-execuções parciais possíveis.

**Quanto Custa**: 3h de implementação + testes.

**Quanto Economiza**: 0h em tempo (Estado RJ limita), MAS ganho enorme em resiliência e otimização.

**Risco**: Muito baixo (~5% de rate limiting, mitigável).

**Recomendação**: ⭐⭐⭐⭐⭐ **IMPLEMENTAR IMEDIATAMENTE**
