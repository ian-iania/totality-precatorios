# Análise de Performance - TJRJ Precatórios Scraper

**Data**: 2025-11-26
**Versão Analisada**: V1 (com correções de campos expandidos aplicadas)
**Período de Medição**: Extrações de 24-26 Nov 2025

---

## 📊 Performance Atual (V1)

### Velocidade de Extração
```
⏱️ Tempo por página: ~16 segundos
📄 Registros por página: 10 precatórios
📈 Taxa de extração: ~0.625 registros/segundo
✅ Cobertura de campos: 100% (incluindo expandidos)
```

**Breakdown do tempo por página**:
- 1.5s: Espera por loading overlay + estabilização AngularJS
- 1.0s: Extração de 7 campos visíveis (10 registros)
- 10-12s: Extração de 7 campos expandidos (10 × clicks + waits)
- 2.0s: Click "Próxima" + navegação
- 0.5s: Overhead Python/Playwright

---

## 🎯 Gargalos Identificados

### Gargalo Crítico: Estado do Rio de Janeiro (Especial)

| Métrica | Valor | Impacto |
|---------|-------|---------|
| **Total de Registros** | 17,663 | 68% dos registros de ESPECIAL |
| **Total de Páginas** | ~1,767 | 68% das páginas de ESPECIAL |
| **Tempo Estimado** | 7h 52min | 78% do tempo de ESPECIAL |
| **% do Tempo Total** | 70-80% | Gargalo crítico |

**Cálculo**:
```
17,663 registros ÷ 10 por página = 1,766.3 páginas
1,767 páginas × 16s/página = 28,272 segundos = 7h 51min 12s
```

### Outras Entidades Grandes (Especial)

| Entidade | Registros | Páginas | Tempo Estimado |
|----------|-----------|---------|----------------|
| Petrópolis | 2,921 | 293 | 1h 18min |
| São Gonçalo | 1,423 | 143 | 38min |
| Volta Redonda | 983 | 99 | 26min |
| Macaé | 803 | 81 | 22min |
| Barra Mansa | 560 | 56 | 15min |
| **Outras 35 entidades** | ~3,000 | ~300 | 1h 20min |

---

## 📈 Distribuição de Entidades

### Regime GERAL (56 entidades)

**Estatísticas**:
- Total de registros: ~5,444
- Total de páginas: ~545
- Tempo estimado: **1h 32min** (2h com overhead)

**Distribuição**:
- Entidade maior: Município do Rio de Janeiro (2,486 registros)
- Entidade menor: 0 registros (várias)
- Mediana: ~40 registros

**Top 5 Entidades**:
1. Município do Rio de Janeiro: 2,486 registros
2. Niterói: 620 registros
3. INSS: 907 registros
4. São Francisco de Itabapoana: 337 registros
5. Nova Iguaçu: 245 registros

### Regime ESPECIAL (41 entidades)

**Estatísticas**:
- Total de registros: ~27,000 (estimado)
- Total de páginas: ~2,600
- Tempo estimado: **10h 26min** (7-8h com paralelização)

**Distribuição**:
- Entidade maior: Estado do Rio de Janeiro (17,663 registros) ⚠️
- Entidade menor: 0 registros (ESTADO DO TOCANTINS)
- Mediana: ~100 registros

**Top 10 Entidades**:
1. Estado do Rio de Janeiro: 17,663 registros 🔴
2. Petrópolis: 2,921 registros
3. São Gonçalo: 1,423 registros
4. Volta Redonda: 983 registros
5. Macaé: 803 registros
6. Barra Mansa: 560 registros
7. Campos dos Goytacazes: 454 registros
8. Teresópolis: 376 registros
9. Nova Iguaçu: 245 registros
10. Belford Roxo: 260 registros

---

## ⏱️ Tempos Medidos (Performance Real)

### Log de Performance - Regime GERAL (24 Nov 2025)
```
Fonte: logs/performance_geral_20251124_022205.log

Total records: 5,444
Entities processed: 56
Entities failed: 0
Total time: 1.83h (109.5min)
Records/second: 0.83
Avg time per entity: 117.3s
```

**Observações**:
- ✅ Performance conforme esperado
- ✅ Taxa de extração: 0.83 rec/s ≈ estimado (0.625 rec/s)
- ✅ Sem falhas

### Log de Performance - Regime ESPECIAL (24 Nov 2025 - INCOMPLETO)
```
Fonte: logs/performance_especial_20251124_065708.log

Total records: 20,403 (LIMITADO A 10K para Estado RJ!)
Entities processed: 41
Entities failed: 0
Total time: 6.40h (383.9min)
Records/second: 0.89
Avg time per entity: 561.7s
```

**Observações**:
- ⚠️ Estado RJ parou em 10,000 (bug do limite de páginas)
- ⚠️ Faltam ~7,663 registros do Estado RJ
- ✅ Outras entidades completas

---

## 🔍 Análise de Bottlenecks

### 1. Extração de Campos Expandidos (~75% do tempo)

**Processo atual**:
```python
Para cada registro (10 por página):
    1. Re-query row (evitar stale DOM)           ~50ms
    2. Esperar loading overlay                   ~100ms
    3. Click botão "+"                           ~200ms
    4. Esperar expansão (800ms)                  ~800ms
    5. Extrair 7 campos do DOM                   ~100ms
    6. Re-query row para collapse                ~50ms
    7. Click "-" para collapse                   ~200ms
    8. Esperar collapse (300ms)                  ~300ms

    Total por registro: ~1,800ms
    Total para 10 registros: ~18 segundos
```

**Otimizações já aplicadas**:
- ✅ Re-query de elementos (evita DOM stale)
- ✅ Espera por loading overlay
- ✅ Retry logic com exponential backoff
- ✅ Uso de índice [0] correto para detail container

**Otimizações possíveis (não implementadas)**:
- ⚠️ Não colapsar após cada extração (economia: ~500ms × 10 = 5s/página)
- ⚠️ Extrair múltiplos expandidos sem colapsar (risco: DOM pollution)
- ⚠️ Aumentar timeouts pode reduzir retries (trade-off: mais tempo base)

### 2. Navegação de Páginas (~12% do tempo)

**Processo**:
- Click "Próxima": ~200ms
- wait_for_timeout(2000): 2s
- wait_for_load_state('networkidle'): variável

**Total**: ~2.5s por transição de página

**Otimizações possíveis**:
- Reduzir timeout de 2000ms → 1500ms (risco: perder dados)

### 3. Overhead Python/Playwright (~8% do tempo)

**Componentes**:
- Parsing de dados: ~200ms
- Criação de objetos Precatorio: ~100ms
- Logging: ~100ms

**Total**: ~400ms por página

**Não otimizável significativamente**

---

## 📊 Estimativas de Tempo

### Cenário Atual (2 Processos Paralelos)

| Processo | Regime | Tempo | Status |
|----------|--------|-------|--------|
| 1 | GERAL (56 entidades) | ~2h | ⏳ Rodando |
| 2 | ESPECIAL (41 entidades) | ~8h | ⏳ Rodando |

**Tempo Total (paralelo)**: ~8h

### Cenário Otimizado (5 Processos - VPS KVM 4)

| Processo | Entidades | Tempo | Ganho |
|----------|-----------|-------|-------|
| 1 | Estado RJ (isolado) | ~8h | Gargalo inevitável |
| 2 | 3 entidades grandes (ESPECIAL) | ~2.5h | - |
| 3 | 19 entidades médias (ESPECIAL) | ~2h | - |
| 4 | 19 entidades pequenas (ESPECIAL) | ~1h | - |
| 5 | 56 entidades (GERAL) | ~2h | - |

**Tempo Total (paralelo)**: ~8h (mesmo tempo!)

**Ganho Real**:
- ✅ Resiliência (se entidade falha, outras continuam)
- ✅ Melhor uso de CPU (80-90% vs 50%)
- ✅ Re-execuções parciais possíveis

---

## 🎯 Conclusão

### Gargalo Inalterável
**Estado do Rio de Janeiro** é o limitante absoluto:
- 68% dos registros de ESPECIAL
- ~8h de processamento sequencial obrigatório
- Sem API, paralelização de ranges é inviável

### Otimizações Aplicadas (V1)
1. ✅ Correção do limite de 10k registros
2. ✅ Extração de campos expandidos (100% cobertura)
3. ✅ Handling de DOM stale elements
4. ✅ Retry logic robusto

### Próximas Otimizações Possíveis
1. 🔧 Paralelização por entidade (Estratégia 3)
2. 🔧 Otimização de collapse (economia: ~30%)
3. 🔧 Redução de timeouts (risco médio)

### Recomendação Final
**Implementar Estratégia 3** (Paralelização por Entidade):
- Não reduz tempo do Estado RJ (impossível)
- Melhora resiliência e uso de recursos
- Permite re-execuções parciais
- Investimento razoável (2-3h implementação)

---

**Última Atualização**: 2025-11-26
**Performance Alvo V2**: ~8h (mesmo), MAS com resiliência ⭐
