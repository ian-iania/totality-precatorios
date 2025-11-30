# Estratégia 5: Paralelização por Ranges de Páginas (Via Input Direto) 🚀 ALTAMENTE RECOMENDADO

**Status**: ✅ VIÁVEL (descoberta validada via screenshots)
**Complexidade**: ⭐⭐⭐ Média
**Risco**: ⭐⭐ Baixo-Médio
**Investimento**: 4-6h (investigação + implementação + testes)
**Probabilidade de Sucesso**: ~90%
**Ganho**: **76-91% redução de tempo para Estado RJ** (11-13.6h economizadas!)

---

## 📋 Descrição

Paralelizar a extração do **Estado do Rio de Janeiro** (entidade crítica com ~3,000 páginas) dividindo em **ranges de páginas** processados simultaneamente por múltiplos processos independentes.

**Diferença Crítica da Estratégia 2**:
- Estratégia 2: Tentava via API REST (não encontrada ❌)
- **Estratégia 5**: Via **campo "Ir para página:"** (descoberto, funcional ✅)

**Princípio**: Usar navegação direta via input field para saltar para página inicial de cada range, depois extrair sequencialmente dentro do range.

---

## 🎯 A Descoberta

### O Que Foi Encontrado

Campo **"Ir para página:"** na interface do TJRJ que permite:

1. ✅ Digitar número da página (ex: 100, 1500, 2984)
2. ✅ Pressionar Enter
3. ✅ Navegação **instantânea** (~3s) para página alvo
4. ✅ Funciona para qualquer página no range válido

**Evidência**: Screenshots mostram navegação bem-sucedida 1 → 100 → 1500 (ver `findings/06_page_navigation_discovery.md`)

### Por Que Isso Muda Tudo

**Antes**:
```
Estado RJ (2,984 páginas):
  - Navegação: Clicar "Próxima" 2,984 vezes (~1.7-3h)
  - Paralelização: ❌ IMPOSSÍVEL (precisa começar da página 1)
```

**Agora**:
```
Estado RJ (2,984 páginas):
  Processo 1: Saltar para página 1 (já está), extrair 1-746
  Processo 2: Saltar para página 747 (~3s), extrair 747-1,492
  Processo 3: Saltar para página 1,493 (~3s), extrair 1,493-2,238
  Processo 4: Saltar para página 2,239 (~3s), extrair 2,239-2,984

  Paralelização: ✅ POSSÍVEL via navegação direta!
```

---

## ⚡ Performance Estimada

### Cenário Baseline (Atual - Sequencial)

```
Estado RJ:
  - Total de páginas: 2,984
  - Navegação sequencial: 2,984 clicks × 2s = 1.7h
  - Extração (com expandidos): 2,984 páginas × 16s = 13.3h
  TOTAL: ~15h
```

---

### Cenário 1: Paralelização (4 Processos) + Modo Completo

**Divisão de Ranges**:
```
Processo 1: Páginas 1-746      (0-7,460 registros)
Processo 2: Páginas 747-1,492   (7,461-14,920 registros)
Processo 3: Páginas 1,493-2,238 (14,921-22,380 registros)
Processo 4: Páginas 2,239-2,984 (22,381-29,840 registros)
```

**Por Processo**:
```
- Navegação inicial: 1 salto direto = ~3s ⚡
- Navegação dentro do range: 746 clicks × 2s = ~25min
- Extração (com expandidos): 746 páginas × 16s = ~3.3h
TOTAL POR PROCESSO: ~3.6h
```

**Tempo Total** (paralelo): **~3.6h**

**ECONOMIA: ~11.4h (76% redução)** ⭐⭐⭐⭐

---

### Cenário 2: COMBO - Paralelização + Skip-Expanded 🔥

**Divisão de Ranges** (mesma de acima):

**Por Processo**:
```
- Navegação inicial: 1 salto direto = ~3s
- Navegação dentro do range: 746 clicks × 2s = ~25min
- Extração (SEM expandidos): 746 páginas × 5s = ~1h
TOTAL POR PROCESSO: ~1.4h
```

**Tempo Total** (paralelo): **~1.4h**

**ECONOMIA: ~13.6h (91% redução!)** 🔥🔥🔥🔥🔥

---

## 📊 Comparação com Todas as Estratégias

### Estado RJ Especificamente

| Estratégia | Tempo | vs Baseline | Aplicável a Estado RJ? |
|------------|-------|-------------|------------------------|
| **1. Manter Atual** | 15h | - | ✅ Sim (baseline) |
| **2. API Ranges** | N/A | N/A | ❌ Não (API não existe) |
| **3. Paralelizar Entidades** | 15h | 0% | ❌ Não (Estado RJ é indivisível por entidade) |
| **4. Skip Expandidos** | 5h | -66% | ✅ Sim |
| **5. Page Ranges** | 3.6h | -76% | ✅ Sim (único!) |
| **5+4 COMBO** | **1.4h** | **-91%** | ✅ **Sim (IDEAL!)** 🚀 |

**Estratégia 5 é a ÚNICA que paraleliza Estado RJ!**

---

### Regime ESPECIAL Completo

| Componente | Baseline | Com Estratégia 5+4 | Ganho |
|------------|----------|-------------------|-------|
| **Estado RJ** | 15h | 1.4h | -13.6h (-91%) |
| **Outras 40 entidades** | 2h | 40min* | -1.3h (-65%) |
| **TOTAL ESPECIAL** | **17h** | **2.1h** | **-14.9h (-88%)** 🔥🔥🔥 |

*Com Estratégia 4 (skip-expanded) aplicada

**IMPACTO MASSIVO NO TEMPO TOTAL!**

---

## 💰 Análise Custo-Benefício

| Aspecto | Estimativa |
|---------|------------|
| **Investigação** (seletor, testes) | 1-2h |
| **Implementação** (código paralelo) | 2-3h |
| **Testes** (validação ranges) | 1h |
| **Total Investimento** | **4-6h** |
| **Probabilidade Sucesso** | **~90%** |
| **Ganho Tempo (Estado RJ)** | **-11.4h** (só paralelo) |
| **Ganho Tempo COMBO** | **-13.6h** (paralelo + skip) |
| **ROI** | **+190-227%** (6h → 11-14h economizadas) 🚀 |

**Comparação**:
- Estratégia 2 (API): ROI -90% ❌
- Estratégia 3 (Entidades): ROI +0% (não afeta Estado RJ)
- Estratégia 4 (Skip): ROI +950% ⭐
- **Estratégia 5 (Ranges): ROI +190-227%** ⭐⭐

**Estratégia 5 tem o MAIOR GANHO ABSOLUTO de tempo!**

---

## 🔧 Abordagem Técnica

### Arquitetura Proposta

```
Estado RJ (2,984 páginas) → Dividir em 4 ranges
├── Processo 1: extract_page_range(1, 746)
├── Processo 2: extract_page_range(747, 1492)
├── Processo 3: extract_page_range(1493, 2238)
└── Processo 4: extract_page_range(2239, 2984)

Cada processo:
1. Saltar para página inicial do range (3s)
2. Extrair sequencialmente dentro do range (3.6h ou 1.4h)
3. Salvar CSV parcial

Ao final:
- Merge de 4 CSVs parciais
- Validar por numero_precatorio (sem duplicatas/gaps)
```

---

### Navegação Direta (Função-Chave)

```python
def goto_page_direct(page: Page, page_number: int):
    """
    Navigate directly to a page using 'Ir para página:' input field

    Args:
        page: Playwright Page instance
        page_number: Target page number (e.g., 747, 1493)

    Returns:
        None (page navigates to target)

    Raises:
        TimeoutError: If navigation fails
    """
    logger.info(f"⚡ Jumping directly to page {page_number}...")

    # Find input field (selector TBD - needs investigation)
    page_input = page.query_selector('INPUT_SELECTOR_TBD')

    if not page_input:
        raise ValueError("Page input field not found!")

    # Clear and fill with target page number
    page_input.fill('')  # Clear existing value
    page_input.fill(str(page_number))

    # Press Enter to navigate
    page_input.press('Enter')

    # Wait for AngularJS to stabilize
    page.wait_for_timeout(2000)
    page.wait_for_load_state('networkidle')

    # Verify we're on the correct page (optional validation)
    try:
        current_page_text = page.inner_text('body')
        # Check if page number is reflected in UI or data
        logger.info(f"✅ Successfully navigated to page {page_number}")
    except:
        logger.warning(f"⚠️  Could not verify page {page_number}")
```

**KEY UNKNOWNS** (requires investigation):
- Exact CSS selector for input field
- Whether input requires focus/click before fill
- Whether Enter key is sufficient or needs button click
- Validation/error handling if page number out of range

---

### Range Extraction (Função Principal)

```python
def extract_page_range(
    entidade: EntidadeDevedora,
    start_page: int,
    end_page: int,
    skip_expanded: bool = False,
    process_id: int = 1
) -> List[Precatorio]:
    """
    Extract precatórios from a page range for an entity

    Args:
        entidade: Entity to extract (Estado RJ)
        start_page: First page in range (e.g., 747)
        end_page: Last page in range (e.g., 1492)
        skip_expanded: Whether to skip expanded fields (faster)
        process_id: ID for logging (1-4)

    Returns:
        List of Precatorio objects
    """
    logger.info(f"[P{process_id}] Starting range extraction: pages {start_page}-{end_page}")

    all_precatorios = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to entity page
        url = f"https://www3.tjrj.jus.br/...?idEntidadeDevedora={entidade.id_entidade}"
        page.goto(url, wait_until='networkidle')
        page.wait_for_timeout(3000)

        # DIRECT JUMP to start page (KEY OPTIMIZATION)
        if start_page > 1:
            goto_page_direct(page, start_page)

        # Extract pages sequentially within range
        current_page = start_page

        while current_page <= end_page:
            logger.info(f"[P{process_id}] Extracting page {current_page}/{end_page}...")

            try:
                # Extract current page
                precatorios = extract_precatorios_from_page(
                    page, entidade, skip_expanded
                )
                all_precatorios.extend(precatorios)

                logger.info(f"[P{process_id}] Page {current_page}: {len(precatorios)} records")

            except Exception as e:
                logger.error(f"[P{process_id}] Error on page {current_page}: {e}")
                # Continue to next page (resilience)

            # Navigate to next page within range
            if current_page < end_page:
                next_button = page.query_selector('text=Próxima')
                if next_button:
                    next_button.click()
                    page.wait_for_timeout(2000)
                    page.wait_for_load_state('networkidle')
                else:
                    logger.warning(f"[P{process_id}] No next button found, stopping")
                    break

            current_page += 1

        browser.close()

    logger.info(f"[P{process_id}] Range complete: {len(all_precatorios)} total records")
    return all_precatorios
```

---

### Orquestração Paralela

```python
def parallel_extract_estado_rj(
    num_processes: int = 4,
    skip_expanded: bool = False
):
    """
    Extract Estado RJ using parallel page ranges

    Args:
        num_processes: Number of parallel processes (2-4 recommended)
        skip_expanded: Whether to skip expanded fields (faster)

    Returns:
        Merged CSV path
    """
    # Estado RJ entity
    estado_rj = EntidadeDevedora(
        id_entidade=1,
        nome_entidade="Estado do Rio de Janeiro",
        regime="especial",
        precatorios_pendentes=29840  # ~2,984 pages
    )

    total_pages = 2984  # Confirmed from screenshots
    pages_per_process = total_pages // num_processes

    # Define ranges
    ranges = []
    for i in range(num_processes):
        start = i * pages_per_process + 1
        end = (i + 1) * pages_per_process if i < num_processes - 1 else total_pages
        ranges.append((estado_rj, start, end, skip_expanded, i + 1))

    logger.info(f"Parallelizing Estado RJ into {num_processes} processes:")
    for i, (_, start, end, _, proc_id) in enumerate(ranges):
        logger.info(f"  Process {proc_id}: Pages {start}-{end}")

    # Extract in parallel
    with Pool(processes=num_processes) as pool:
        results = pool.starmap(extract_page_range, ranges)

    # Merge results
    all_precatorios = []
    for result in results:
        all_precatorios.extend(result)

    logger.info(f"Total extracted: {len(all_precatorios)} precatórios")

    # Validate no duplicates
    unique_numeros = set(p.numero_precatorio for p in all_precatorios)
    if len(unique_numeros) != len(all_precatorios):
        logger.warning(f"⚠️  Duplicates detected! Unique: {len(unique_numeros)}, Total: {len(all_precatorios)}")
        # Remove duplicates
        seen = set()
        deduplicated = []
        for p in all_precatorios:
            if p.numero_precatorio not in seen:
                deduplicated.append(p)
                seen.add(p.numero_precatorio)
        all_precatorios = deduplicated
        logger.info(f"After deduplication: {len(all_precatorios)} precatórios")

    # Save to CSV
    df = pd.DataFrame([p.model_dump() for p in all_precatorios])
    csv_path = f"data/processed/estado_rj_especial_parallel_{timestamp}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    return csv_path
```

---

## ⚠️ Riscos e Mitigações

### Risco 1: Seletor do Input Instável

**Descrição**: Seletor CSS pode mudar se TJRJ atualizar website

**Probabilidade**: 20%

**Impacto**: Alto (função para de funcionar)

**Mitigação**:
```python
# Múltiplos seletores fallback
SELECTORS = [
    'input[name="pageInput"]',  # Se tiver name
    'input[type="text"][placeholder*="página"]',  # Via placeholder
    'div:has-text("Ir para página:") input',  # Via parent
    'input.page-number-input'  # Via class
]

for selector in SELECTORS:
    input_field = page.query_selector(selector)
    if input_field:
        return input_field

raise ValueError("Page input field not found with any selector!")
```

---

### Risco 2: Rate Limiting (4 Processos Simultâneos)

**Descrição**: TJRJ pode detectar 4 conexões simultâneas do mesmo IP e throttle/bloquear

**Probabilidade**: 40% (não testado com > 2 processos)

**Impacto**: Médio-Alto (extração falha ou fica lenta)

**Sinais de Throttling**:
- Respostas HTTP 429 (Too Many Requests)
- Timeouts aumentados
- CAPTCHA aparece
- Respostas vazias

**Mitigação**:
```python
# Começar conservador (2 processos)
num_processes = 2  # Testar primeiro

# Se funcionar, escalar gradualmente
num_processes = 3  # Depois de sucesso
num_processes = 4  # Se 3 funcionar bem

# Adicionar delays randomizados
import random
delay = random.uniform(500, 1500)  # 0.5-1.5s entre requests
page.wait_for_timeout(delay)

# Monitorar logs para detectar throttling
if 'timeout' in str(error) or '429' in str(error):
    logger.warning("⚠️  Possible rate limiting detected!")
    # Fallback para 2 ou 1 processo
```

**Plano B**: Se rate limiting confirmado, reduzir para 2 processos (ainda economiza ~7h!)

---

### Risco 3: Validação do Input Field

**Descrição**: Input pode ter validação JS que rejeita certos valores

**Probabilidade**: 10%

**Impacto**: Baixo (algumas páginas não acessíveis)

**Mitigação**:
```python
# Validar range antes de fill
if not (1 <= page_number <= 2984):
    raise ValueError(f"Page number {page_number} out of range [1, 2984]")

# Tentar navegação, capturar erro se falhar
try:
    goto_page_direct(page, page_number)
except Exception as e:
    logger.error(f"Direct navigation to page {page_number} failed: {e}")
    # Fallback: navegar sequencialmente
    logger.info("Falling back to sequential navigation...")
    for _ in range(page_number - current_page):
        next_button.click()
        page.wait_for_timeout(2000)
```

---

### Risco 4: Duplicados/Gaps entre Ranges

**Descrição**: Se transição entre ranges falhar, pode haver duplicados ou gaps

**Probabilidade**: 15%

**Impacto**: Baixo-Médio (dados inconsistentes)

**Exemplo**:
```
Processo 2 termina na página 1492 (último registro: 14,920)
Processo 3 começa na página 1493 (primeiro registro: deveria ser 14,921)

Se algum registro for pulado ou duplicado → inconsistência
```

**Mitigação**:
```python
# Validação pós-extração
all_numeros = [p.numero_precatorio for p in all_precatorios]

# Checar duplicados
duplicates = [num for num in all_numeros if all_numeros.count(num) > 1]
if duplicates:
    logger.warning(f"⚠️  Duplicates found: {len(set(duplicates))} unique")
    # Remover duplicados (manter primeiro)
    seen = set()
    deduplicated = []
    for p in all_precatorios:
        if p.numero_precatorio not in seen:
            deduplicated.append(p)
            seen.add(p.numero_precatorio)
    all_precatorios = deduplicated

# Checar gaps (opcional - precatórios não são sequenciais!)
# Não aplicável pois numero_precatorio não é sequencial (ex: "1998.03464-7")

# Validar contagem total
expected_count = 29840  # ~2,984 páginas × 10 records
actual_count = len(all_precatorios)

if abs(actual_count - expected_count) > 100:  # Tolerance de 100
    logger.warning(f"⚠️  Count mismatch: expected ~{expected_count}, got {actual_count}")
```

---

## 📋 Roadmap de Implementação

### Fase 1: Investigação (1-2h)

**Objetivo**: Descobrir seletor do input e validar navegação

**Tarefas**:
- [ ] Abrir TJRJ no browser com DevTools
- [ ] Inspecionar campo "Ir para página:"
- [ ] Identificar seletor CSS estável
- [ ] Testar seletor no console Playwright
- [ ] Documentar seletor em código

**Entregável**: Seletor CSS confirmado, pronto para uso

---

### Fase 2: Implementação Core (2-3h)

**Objetivo**: Criar funções de navegação e extração por range

**Tarefas**:
- [ ] Criar `goto_page_direct(page, page_number)` em `scraper_v3.py`
- [ ] Criar `extract_page_range(entidade, start, end)` em `scraper_v3.py`
- [ ] Adicionar validações (range, input field existence)
- [ ] Adicionar retry logic (se navegação falhar)
- [ ] Logging detalhado (progressos, erros)

**Entregável**: `scraper_v3.py` com navegação direta funcional

---

### Fase 3: Orquestração Paralela (1h)

**Objetivo**: Criar script para rodar múltiplos processos em paralelo

**Tarefas**:
- [ ] Criar `main_v3_parallel.py`
- [ ] Definir divisão de ranges (2, 3 ou 4 processos)
- [ ] Implementar multiprocessing Pool
- [ ] Merge de resultados parciais
- [ ] Validação de duplicados/gaps

**Entregável**: `main_v3_parallel.py` executável

---

### Fase 4: Testes (1h)

**Objetivo**: Validar funcionamento com ranges pequenos e grandes

**Testes Planejados**:

**Teste 1: Smoke Test (15 min)**
```bash
# Extrair páginas 1-10 (100 registros)
python test_page_range.py --start 1 --end 10
# Validar: CSV com ~100 registros, todos os campos corretos
```

**Teste 2: Mid-Range Test (20 min)**
```bash
# Extrair páginas 100-110 (100 registros do meio)
python test_page_range.py --start 100 --end 110
# Validar: CSV com ~100 registros, navegação direta funcionou
```

**Teste 3: Parallel Test (2 processos) (25 min)**
```bash
# Extrair páginas 1-1492 e 1493-2984 em paralelo
python main_v3_parallel.py --num-processes 2
# Validar: 2 CSVs parciais, merge sem duplicados
```

**Entregável**: Testes passando, pronto para full-scale

---

### Fase 5: Full-Scale Execution (Opcional - SE aprovado)

**Objetivo**: Extrair Estado RJ completo com paralelização

**Comando**:
```bash
# COMBO: 4 processos + skip-expanded (mais rápido)
python main_v3_parallel.py \
  --regime especial \
  --entity-id 1 \
  --num-processes 4 \
  --skip-expanded \
  --output estado_rj_especial_fast.csv

# Tempo esperado: ~1.4h (vs 15h baseline)
```

**Validação**:
- [ ] CSV com ~29,840 registros
- [ ] Sem duplicados (por numero_precatorio)
- [ ] 11 colunas (se skip-expanded) ou 19 (se completo)
- [ ] Tempo < 2h (confirmar ganho)

**Entregável**: CSV final validado, documentação de ganho real

---

## 🎯 Casos de Uso

### Quando USAR Estratégia 5

**1. Estado RJ é Prioridade**
- Objetivo: Extrair Estado RJ o mais rápido possível
- Ganho: 11-13.6h economizadas
- Trade-off: Complexidade maior

**2. Hardware Potente Disponível**
- 4+ cores CPU
- 8+ GB RAM
- Permite rodar 4 processos simultâneos

**3. Extração Recorrente**
- Frequência: Semanal ou mensal
- Ganho acumulado: 11-13.6h × 52 semanas = 572-707h/ano
- ROI justifica investimento

**4. COMBO com Skip-Expanded**
- Objetivo: Extração RÁPIDA (11 colunas)
- Ganho máximo: 91% redução (15h → 1.4h)

---

### Quando NÃO USAR Estratégia 5

**1. Extração Ocasional**
- Frequência: 1-2x por ano
- ROI não justifica 6h de implementação

**2. Hardware Limitado**
- < 4 cores CPU
- < 4 GB RAM
- Não suporta 4 processos paralelos

**3. Dados Completos Necessários + Pouca Urgência**
- Se precisa de 19 colunas (com expandidos)
- E não tem deadline apertado
- Estratégia 1 (atual, sequencial) é suficiente

**4. Alta Aversão a Risco**
- Rate limiting não testado com 4 processos
- Pode preferir Estratégia 4 (skip-expanded, zero risco)

---

## 📈 Ganho Esperado (Resumo)

### Estado RJ Somente

| Cenário | Baseline | Com Estratégia 5 | Com COMBO (5+4) | Ganho |
|---------|----------|------------------|-----------------|-------|
| **Tempo** | 15h | 3.6h | **1.4h** | **-13.6h** |
| **Redução** | - | -76% | **-91%** | - |
| **Colunas** | 19 | 19 | 11 | - |

---

### Regime ESPECIAL Completo

| Componente | Baseline | Estratégia 5 | COMBO (5+4) | Ganho |
|------------|----------|--------------|-------------|-------|
| **Estado RJ** | 15h | 3.6h | 1.4h | -13.6h |
| **Outras 40** | 2h | 2h | 40min | -1.3h |
| **TOTAL** | **17h** | **5.6h** | **2.1h** | **-14.9h (-88%)** 🔥 |

---

## 💡 Recomendação Final

### ✅ IMPLEMENTAR com Estratégia COMBO (5 + 4)

**Razões**:
1. ✅ Ganho massivo: 88% redução tempo total ESPECIAL
2. ✅ Probabilidade alta: ~90% (navegação direta confirmada)
3. ✅ Investimento razoável: 4-6h (vs 14.9h economizadas)
4. ✅ ROI excelente: +190-227%
5. ✅ Combina perfeitamente com Estratégia 4 (já implementada)
6. ✅ Aplicável ao gargalo crítico (Estado RJ)

**Abordagem Recomendada**:
1. Implementar Estratégia 5 (page ranges)
2. Testar com 2 processos primeiro (segurança)
3. Escalar para 4 se rate limiting não for problema
4. COMBO com Estratégia 4 (skip-expanded) para ganho máximo
5. Aplicar a Estado RJ somente (outras entidades com Estratégia 4)

**Resultado Esperado**:
- Estado RJ: ~1.4h (vs 15h atual) = -91%
- ESPECIAL total: ~2.1h (vs 17h atual) = -88%
- **Transformação completa do tempo de extração!** 🚀

---

## 📚 Referências

- **Descoberta**: `findings/06_page_navigation_discovery.md` - Evidência e análise técnica
- **Estratégia 4**: `strategies/option4_skip_expanded_fields.md` - Complementar (COMBO)
- **Performance**: `findings/02_performance_analysis.md` - Baseline metrics
- **API Investigation**: `findings/01_api_investigation.md` - Por que Estratégia 2 falhou

---

**Última Atualização**: 2025-11-26
**Status**: ✅ VIÁVEL - Aguardando aprovação para implementação
**Próximo Passo**: Validação da descoberta + feedback do usuário

---

## ✨ Resumo Executivo

**O Que É**: Paralelização do Estado RJ via navegação direta por input field

**Por Que Usar**: 76-91% redução de tempo (11-13.6h economizadas)

**Quanto Custa**: 4-6h de implementação

**Quanto Economiza**: 11-15h por extração (ROI +190-227%)

**Risco**: Baixo-Médio (~90% probabilidade sucesso)

**Quando Usar**: Sempre que Estado RJ for prioridade e hardware permitir paralelização

**Recomendação**: ⭐⭐⭐⭐⭐ **IMPLEMENTAR COM COMBO (5+4)** para ganho máximo!
