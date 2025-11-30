# V2 Optimization - TJRJ Precatórios Scraper

## 📋 Visão Geral

Este diretório contém toda a análise, findings e estratégias para otimização da extração de precatórios do TJRJ.

**Data da Análise**: 26 de Novembro de 2025
**Versão Atual**: v1 (scraper funcional com correções aplicadas)
**Objetivo**: Reduzir tempo de extração de ~7-8h para ~2-4h (se viável)

---

## 🎯 Problema Principal

**Gargalo Identificado**: Estado do Rio de Janeiro (Regime Especial)
- **Registros**: 17,663 precatórios
- **Páginas**: ~1,767 páginas (10 registros/página)
- **Tempo**: ~7-8 horas SOZINHO
- **Impacto**: 70-80% do tempo total do Regime Especial

---

## 📊 Status Atual (V1)

### ✅ Bugs Corrigidos
1. **Limite de 10k registros**: Aumentado de 1,000 → 5,000 páginas
2. **Campos expandidos falhando**: DOM stale + loading overlay resolvido
3. **Cobertura**: 100% dos campos expandidos extraídos ✅

### ⏱️ Performance Atual
- **Velocidade**: ~16s por página (com campos expandidos)
- **GERAL**: 56 entidades, ~5,444 registros, ~1.5-2h
- **ESPECIAL**: 41 entidades, ~27,000 registros, ~7-8h
- **Total Paralelo**: ~7-8h (2 processos)

---

## 📂 Estrutura da Documentação

### `/findings/`
Resultados da investigação técnica:
- `01_api_investigation.md` - Tentativa de encontrar API REST
- `02_performance_analysis.md` - Análise de gargalos
- `03_resource_requirements.md` - Estimativas CPU/RAM para VPS
- `04_current_bugs_fixed.md` - Histórico de correções aplicadas

### `/strategies/`
Opções de otimização avaliadas:
- `option1_maintain_current.md` - Manter como está
- `option2_api_ranges.md` - Paralelizar ranges (requer API)
- `option3_entity_parallelization.md` - Paralelizar entidades ⭐ **RECOMENDADO**

### `/implementation/`
Código e configurações para implementação:
- *A ser criado após aprovação da estratégia*

---

## 🔍 Principais Conclusões

### 1. API REST Não Encontrada
- Site usa AngularJS SPA com paginação client-side
- Não há endpoints `/api/` ou `/rest/` funcionais
- Navegação sequencial obrigatória (cliques em "Próxima")
- **Conclusão**: Paralelizar ranges da mesma entidade é INVIÁVEL

### 2. Paralelização Viável: Por Entidade
- Dividir 97 entidades entre múltiplos processos
- Cada processo extrai entidades completas (sequencialmente)
- Ganho: Resiliência + melhor uso de recursos
- **Tempo esperado**: Similar (~7-8h), MAS mais robusto

### 3. Recursos Necessários
**VPS KVM 4 (4 vCPUs, 16GB RAM)** - RECOMENDADO:
- 5-6 processos paralelos (headless)
- Cada processo: ~300 MB RAM, ~25% CPU
- Distribuição balanceada de entidades

---

## 🎯 Recomendação Final

**Estratégia 3**: Paralelizar por Entidade

**Razão**:
- ✅ API não existe (investigação concluída)
- ✅ Implementação relativamente simples (2-3h)
- ✅ Ganho em resiliência (se uma entidade falha, outras continuam)
- ✅ Útil para re-execuções futuras
- ✅ Melhor uso de recursos em VPS multi-core

**Próximos Passos**:
1. ✅ Documentar findings (CONCLUÍDO)
2. ⏳ Aguardar feedback do usuário
3. 🔜 Implementar `parallel_by_entity.py` (se aprovado)
4. 🔜 Testar localmente com 2 entidades
5. 🔜 Deploy e configuração na VPS

---

## 📈 Ganhos Esperados

| Métrica | Atual (V1) | Com Paralelização (V2) |
|---------|------------|------------------------|
| Tempo Total | ~7-8h | ~7-8h (mesmo) |
| Processos | 2 | 5-6 |
| Resiliência | Baixa | **Alta** ⭐ |
| Uso CPU | ~50% (2 cores) | ~80-90% (4 cores) |
| Re-execução | Tudo do zero | Apenas entidades falhadas |

**Nota**: Tempo similar, MAS muito mais robusto e eficiente no uso de recursos.

---

## 🚀 Status

- **V1**: ✅ Funcional, 100% cobertura de campos
- **V2**: 📋 Planejamento completo
- **Jobs Atuais**: ⏳ Rodando (GERAL + ESPECIAL em paralelo)

---

**Última Atualização**: 2025-11-26 00:30 UTC
**Responsável**: Análise técnica completa realizada
