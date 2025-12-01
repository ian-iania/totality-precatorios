# Investigação de API REST - TJRJ Precatórios

**Data**: 2025-11-26
**Objetivo**: Identificar se existe API REST para acesso direto a páginas específicas de precatórios
**Resultado**: ❌ API REST pública não encontrada

---

## 🔍 Metodologia

### 1. Análise da URL Atual
```
https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1
```

**Observações**:
- Uso de `#!` indica AngularJS routing (client-side)
- Parâmetro `idEntidadeDevedora` identifica a entidade
- Sem parâmetros de página/offset visíveis

### 2. Tentativas de Endpoints REST

| URL Testada | Método | Resultado | Código |
|-------------|--------|-----------|--------|
| `/PortalConhecimento/precatorio/api/precatorios?idEntidadeDevedora=1` | GET | ❌ Not Found | 404 |
| `/api/precatorios?entidade=1` | GET | ❌ Not Found | 404 |
| `/api/precatorios?page=10` | GET | ❌ Not Found | 404 |
| `/rest/precatorios` | GET | ❌ Not Found | 404 |

**Conclusão Inicial**: Não há endpoints REST públicos óbvios.

### 3. Análise do HTML/JavaScript

**Evidências de AngularJS SPA**:
```html
{{vm.TituloHeaderPrecatorio}}  <!-- Template binding -->
```

**Características identificadas**:
- ✅ AngularJS Single Page Application
- ✅ Paginação client-side (DOM manipulation)
- ✅ Dados carregados via AngularJS controllers
- ❌ Sem padrões de API REST visíveis no HTML

### 4. Navegação Observada no Código Atual

```python
# src/scraper.py linha 328
url = f"https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora={entidade.id_entidade}"
page.goto(url, wait_until='networkidle')

# Paginação - linhas 382-416
# Busca botão "Próxima" e clica
next_button = page.query_selector("text=Próxima")
next_button.click()
```

**Implicação**: Navegação sequencial obrigatória (não há saltos de página).

---

## 🧪 Testes Realizados

### Teste 1: WebFetch de URL com Parâmetros
```
URL: https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=1
Resultado: HTML da página principal (sem dados de precatórios)
Conclusão: Dados carregados via AJAX após page load
```

### Teste 2: Tentativa de Endpoints Comuns
```bash
GET /api/precatorios
GET /rest/precatorios
GET /v1/precatorios
GET /PortalConhecimento/api/*
```
**Todos retornaram**: 404 Not Found

### Teste 3: Análise de Padrões AngularJS
```javascript
// Padrão típico de AngularJS:
angular.module('precatorioApp')
  .controller('ListaController', function($scope, $http) {
    $http.get('/api/precatorios?page=' + pageNum)
  });
```
**Status**: Não foi possível confirmar se há chamadas AJAX (WebFetch limitado)

---

## 💡 Hipóteses Consideradas

### Hipótese 1: API Interna (Privada)
**Descrição**: Pode existir API, mas acessível apenas via AngularJS
**Probabilidade**: 30%
**Implicação**: Precisaria de engenharia reversa via interceptação de network requests

### Hipótese 2: Dados Pré-carregados no Client
**Descrição**: AngularJS carrega todos os dados de uma vez e pagina no cliente
**Probabilidade**: 40%
**Implicação**: Impossível pular páginas diretamente

### Hipótese 3: Paginação Híbrida
**Descrição**: Carrega chunks (ex: 100 registros) e pagina client-side
**Probabilidade**: 30%
**Implicação**: Poderia paralelizar chunks, mas não páginas individuais

---

## 🔬 Investigação Profunda Necessária

Para **confirmar definitivamente** se existe API:

### Método 1: Interceptação via Chrome DevTools Protocol
```python
# Usar Playwright CDP para interceptar requests
def intercept_requests(page):
    page.on("request", lambda req: print(req.url))
    page.on("response", lambda res: print(res.url, res.status))

    # Navegar e clicar "Próxima" várias vezes
    # Analisar todos os requests AJAX
```

**Recursos Necessários**:
- Abrir browser adicional (com CDP habilitado)
- 15-20 minutos de execução
- Análise manual dos logs

**Risco**: Consumo de recursos (200-400 MB RAM)

### Método 2: Análise de JavaScript Estático
- Download do arquivo `.js` principal do site
- Buscar por `$http.get`, `fetch()`, `XMLHttpRequest`
- Identificar endpoints hardcoded

**Limitação**: WebFetch retorna HTML inicial, não scripts completos

---

## 📊 Probabilidade de Existência de API Útil

| Cenário | Probabilidade | Ganho Potencial |
|---------|---------------|-----------------|
| API REST pública com paginação direta | **5%** | 60-70% redução tempo |
| API interna acessível via engenharia reversa | **15%** | 50-60% redução tempo |
| Sem API - apenas client-side | **80%** | 0% ganho |

**Probabilidade Total de Sucesso**: ~20%

---

## 🎯 Conclusão e Recomendação

### Conclusão
1. ✅ Site confirmado como AngularJS SPA
2. ❌ Endpoints REST públicos não encontrados
3. ⚠️ Possível existência de API interna (não confirmado)
4. ❌ Paginação direta via URL **não é viável** sem mais investigação

### Recomendação

**NÃO investir tempo em engenharia reversa de API neste momento**

**Razões**:
1. Probabilidade de sucesso baixa (~20%)
2. Investimento de tempo alto (3-4h investigação + implementação)
3. Alternativa viável existe (paralelização por entidade)
4. Jobs atuais já estão rodando e vão completar em ~7-8h

**Alternativa recomendada**: Estratégia 3 (Paralelização por Entidade)
- Implementação mais simples (2-3h)
- Sucesso garantido (não depende de API)
- Ganho em resiliência e uso de recursos

---

## 📝 Investigação Futura (Opcional)

**SE** houver necessidade de múltiplas re-execuções futuras:

1. Executar script de interceptação CDP (APÓS jobs atuais)
2. Analisar requests AJAX durante navegação
3. **SE** API for encontrada:
   - Implementar paralelização de ranges
   - Ganho: 50-60% redução de tempo
4. **SE NÃO** encontrar API:
   - Implementar Estratégia 3 (Paralelização por Entidade)

**Prioridade**: Baixa (a menos que haja demanda recorrente de extração)

---

**Status Final**: ❌ API REST pública não encontrada
**Ação Recomendada**: Seguir para Estratégia 3 (Paralelização por Entidade)
