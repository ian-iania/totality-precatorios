# Estratégia 2: Paralelização por Ranges (Requer API)

**Status**: ❌ API REST não encontrada (investigação concluída)
**Complexidade**: ⭐⭐⭐⭐⭐ Muito Alta
**Risco**: ⭐⭐⭐⭐⭐ Muito Alto
**Investimento**: 3-4h investigação + 4-6h implementação = **7-10h total**
**Probabilidade de Sucesso**: ~20%

---

## 📋 Descrição

Paralelizar a extração de **ranges de páginas da MESMA entidade**, distribuindo entre múltiplos processos.

**Pré-requisito crítico**: API REST com suporte a paginação direta.

**Exemplo teórico**:
```
Estado RJ (17,663 registros = 1,767 páginas):
  Processo 1: Páginas 1-442    (0-4,420 registros)
  Processo 2: Páginas 443-884  (4,421-8,840 registros)
  Processo 3: Páginas 885-1,326 (8,841-13,260 registros)
  Processo 4: Páginas 1,327-1,767 (13,261-17,663 registros)

Tempo: 8h ÷ 4 = 2h ✨
```

---

## 🔍 Status da Investigação de API

### Resultados (ver `findings/01_api_investigation.md`)

**URLs Testadas**:
```
❌ /PortalConhecimento/precatorio/api/precatorios?idEntidadeDevedora=1
❌ /api/precatorios?entidade=1
❌ /api/precatorios?page=10
❌ /rest/precatorios
```

**Todos retornaram**: 404 Not Found

**Confirmado**:
- ✅ Site é AngularJS SPA
- ✅ Paginação client-side (DOM manipulation)
- ❌ Sem endpoints REST públicos

**Conclusão**: **API REST pública NÃO existe**

---

## 🔬 Investigação Profunda Necessária

Para confirmar 100% se existe API interna:

### Método: Interceptação via CDP

**Script necessário**:
```python
from playwright.sync_api import sync_playwright

def intercept_network(page):
    requests_log = []

    # Interceptar TODAS as requisições
    page.on("request", lambda req: requests_log.append({
        "url": req.url,
        "method": req.method,
        "headers": req.headers
    }))

    page.on("response", lambda res: print(
        f"{res.status} {res.url}"
    ))

    # Navegar e clicar "Próxima" 5x
    url = "https://www3.tjrj.jus.br/precatorio/...&idEntidadeDevedora=1"
    page.goto(url)

    for i in range(5):
        next_btn = page.query_selector("text=Próxima")
        next_btn.click()
        page.wait_for_timeout(2000)

    # Analisar requests_log para identificar padrões
    return requests_log
```

**Recursos necessários**:
- Abrir browser adicional com CDP habilitado
- 15-20 minutos de execução
- Análise manual de ~50-100 requests

**Risco**: Consumo de RAM (~400 MB adicional)

---

## 💡 Cenários Possíveis

### Cenário 1: API REST com Paginação (Probabilidade: 5%)

**Se encontrado endpoint como**:
```
GET /api/precatorios?entidade=1&page=500&per_page=10
```

**Implementação**:
```python
def extract_range(entidade_id, start_page, end_page):
    for page_num in range(start_page, end_page + 1):
        url = f"/api/precatorios?entidade={entidade_id}&page={page_num}"
        data = requests.get(url).json()
        # Parse JSON para Precatorio objects
```

**Ganho**: 60-70% redução de tempo (8h → 2-3h)

---

### Cenário 2: API Interna com Offset (Probabilidade: 15%)

**Se descoberto via interceptação**:
```javascript
// AngularJS internal call
$http.get('/internal/precatorios', {
    params: { idEntidade: 1, offset: 5000, limit: 10 }
})
```

**Desafios**:
- Pode requerer autenticação/CSRF tokens
- Pode ter anti-bot detection
- Pode não funcionar fora do contexto AngularJS

**Implementação**: Mais complexa, requer emular headers

**Ganho**: 50-60% redução (8h → 3-4h)

---

### Cenário 3: Sem API Útil (Probabilidade: 80%)

**Se**:
- AngularJS carrega TODOS os dados de uma vez
- Paginação é puramente client-side (JavaScript local)
- Sem chamadas AJAX para novos dados

**Resultado**: Paralelização por ranges **IMPOSSÍVEL**

**Alternativa**: Seguir para Estratégia 3

---

## ⚙️ Implementação Teórica (SE API Existir)

### Arquitetura

```
main_parallel.py
├── Dividir entidades em grupos
├── Para cada entidade GRANDE (> 1000 páginas):
│   ├── Calcular ranges (ex: 4 chunks de 442 páginas)
│   ├── Spawn 4 processos paralelos
│   └── Cada processo extrai 1 range
└── Para entidades PEQUENAS:
    └── Processar sequencialmente (atual)
```

### Pseudo-código

```python
def parallel_extract_entity(entidade, num_processes=4):
    total_pages = entidade.precatorios_pendentes // 10

    if total_pages < 500:
        # Pequena, processar sequencialmente
        return extract_sequential(entidade)

    # Grande, dividir em ranges
    chunk_size = total_pages // num_processes
    ranges = [
        (i * chunk_size, (i+1) * chunk_size - 1)
        for i in range(num_processes)
    ]

    # Spawn processos
    with multiprocessing.Pool(num_processes) as pool:
        results = pool.starmap(
            extract_range,
            [(entidade, start, end) for start, end in ranges]
        )

    # Merge CSVs
    return merge_results(results)
```

---

## 📊 Ganho Potencial (SE Implementado)

| Entidade | Páginas | Processos | Tempo Atual | Tempo Otimizado | Ganho |
|----------|---------|-----------|-------------|-----------------|-------|
| Estado RJ | 1,767 | 4 | 8h | 2h | -75% ⭐ |
| Petrópolis | 293 | 2 | 1h 20min | 40min | -50% |
| São Gonçalo | 143 | 1 | 38min | 38min | 0% |
| Outros | < 100 | 1 | Variável | Sem mudança | 0% |

**Tempo Total Estimado**: ~2.5-3h (vs 8h atual) = **-65% ⚡**

---

## ⚠️ Riscos e Desafios

### Riscos Técnicos

1. **API pode não existir** (80% probabilidade)
   - Perda de 3-4h de investigação
   - Nenhum ganho

2. **API pode ser privada/protegida**
   - Requer engenharia reversa de auth
   - Pode violar ToS do site
   - Pode causar bloqueio de IP

3. **Paginação pode ser diferente**
   - API pode retornar chunks de 100 (não 10)
   - Pode ter limite de offset
   - Pode ter rate limiting agressivo

4. **Merge de dados complexo**
   - Duplicados entre ranges
   - Ordenação inconsistente
   - Validação de completude

### Riscos Legais/Éticos

1. **Violação de ToS**
   - Usar API não documentada pode violar termos de serviço
   - Engenharia reversa pode ser proibida

2. **Sobrecarga do servidor**
   - Múltiplos requests simultâneos podem sobrecarregar
   - Pode causar degradação de serviço para outros

3. **Bloqueio de IP**
   - Site pode detectar e bloquear IP
   - Perda de acesso temporária ou permanente

---

## 💰 Análise Custo-Benefício

| Aspecto | Estimativa |
|---------|------------|
| **Investigação de API** | 3-4h ⏱️ |
| **Implementação (se API existir)** | 4-6h ⏱️ |
| **Testes e debugging** | 2-3h ⏱️ |
| **Total Investimento** | **9-13h** |
| **Probabilidade Sucesso** | **~20%** |
| **Ganho SE Sucesso** | **-65% tempo (5h economizadas)** |

**Valor Esperado**:
```
20% × 5h economizadas = 1h de ganho esperado
Investimento: 10h
ROI: -90% (péssimo!)
```

**Conclusão**: **NÃO vale a pena** investir nesta estratégia.

---

## 🎯 Recomendação

### ❌ NÃO Implementar Esta Estratégia

**Razões**:
1. API pública não encontrada (investigação básica concluída)
2. Probabilidade de sucesso muito baixa (~20%)
3. Investimento alto (10h) vs ganho esperado (1h)
4. Riscos legais e técnicos elevados
5. Alternativa viável existe (Estratégia 3)

### ✅ Alternativa Recomendada

**Seguir para Estratégia 3** (Paralelização por Entidade):
- Probabilidade sucesso: 100%
- Investimento: 2-3h
- Ganho garantido: Resiliência + melhor uso de recursos
- Zero riscos legais/éticos

---

## 🔮 Investigação Futura (Opcional)

**SE** houver mudança de cenário:

### Condições para Reconsiderar

1. **Extração recorrente** (diária ou semanal)
   - Ganho acumulado justificaria investimento

2. **Site publicar API oficial**
   - Documentação elimina riscos de eng. reversa

3. **Estado RJ crescer para > 50k registros**
   - Gargalo ficaria ainda maior

4. **Equipe com expertise em eng. reversa**
   - Reduz tempo de investigação de 4h → 1h

**Até lá**: Manter como "não recomendado"

---

## 📚 Referências

- `findings/01_api_investigation.md` - Investigação de API (detalhado)
- `findings/02_performance_analysis.md` - Gargalos identificados
- `strategies/option3_entity_parallelization.md` - Alternativa recomendada

---

**Última Atualização**: 2025-11-26
**Status Final**: ❌ NÃO RECOMENDADO
**Próximo Passo**: Avaliar Estratégia 3
