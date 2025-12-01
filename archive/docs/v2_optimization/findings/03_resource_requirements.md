# Requisitos de Recursos - VPS para Paralelização

**Data**: 2025-11-26
**Objetivo**: Estimar recursos necessários para execução paralela otimizada
**Target**: VPS Hostinger KVM

---

## 🖥️ Consumo por Processo Individual

### Browser Chromium (Playwright)

**Modo Headless** (recomendado):
- RAM inicial: ~150 MB
- RAM pico: ~300 MB
- RAM média: ~220 MB
- CPU: 15-30% de 1 core (picos durante rendering)

**Modo Visual**:
- RAM inicial: ~300 MB
- RAM pico: ~500 MB
- RAM média: ~400 MB
- CPU: 20-35% de 1 core

### Processo Python + Playwright

- Interpreter Python: ~50 MB
- Bibliotecas (Playwright, Pandas, etc): ~30 MB
- Data structures (precatórios em memória): ~20 MB
- **Total overhead**: ~100 MB

### Total por Processo

| Modo | RAM Mínima | RAM Média | RAM Pico | CPU Médio |
|------|------------|-----------|----------|-----------|
| Headless | 200 MB | 320 MB | 420 MB | 20-25% |
| Visual | 350 MB | 500 MB | 650 MB | 25-35% |

---

## 📊 VPS Hostinger - Análise de Capacidade

### VPS KVM 2 (2 vCPUs, 8GB RAM)

**Especificações**:
- **CPU**: 2 cores (vCPUs)
- **RAM**: 8 GB (8,192 MB)
- **SO**: Ubuntu (~1 GB reservado)
- **Disponível**: ~7,000 MB

#### Cenário Headless

**Capacidade teórica (RAM)**:
```
7,000 MB disponível ÷ 320 MB por processo = 21 processos
```

**Capacidade teórica (CPU)**:
```
2 cores ÷ 0.25 CPU por processo = 8 processos
```

**LIMITANTE**: CPU (2 cores)

**Recomendação Conservadora**: **2-3 processos**

| Processos | RAM Usada | CPU Usada | Margem Segurança |
|-----------|-----------|-----------|------------------|
| 2 | ~640 MB | ~50% | ✅ Alta |
| 3 | ~960 MB | ~75% | ⚠️ Média |
| 4 | ~1,280 MB | ~100% | ❌ Baixa (throttling) |

**Conclusão KVM 2**: Ganho marginal vs configuração atual (2 processos)

---

### VPS KVM 4 (4 vCPUs, 16GB RAM) ⭐ RECOMENDADO

**Especificações**:
- **CPU**: 4 cores (vCPUs)
- **RAM**: 16 GB (16,384 MB)
- **SO**: Ubuntu (~1.5 GB reservado)
- **Disponível**: ~14,500 MB

#### Cenário Headless

**Capacidade teórica (RAM)**:
```
14,500 MB disponível ÷ 320 MB por processo = 45 processos
```

**Capacidade teórica (CPU)**:
```
4 cores ÷ 0.25 CPU por processo = 16 processos
```

**LIMITANTE**: CPU (4 cores)

**Recomendação Otimizada**: **5-6 processos**

| Processos | RAM Usada | CPU Usada | Margem Segurança | Status |
|-----------|-----------|-----------|------------------|--------|
| 4 | ~1,280 MB | ~80% | ✅ Alta | Subutilizado |
| 5 | ~1,600 MB | ~100% | ✅ Ótima | ⭐ **IDEAL** |
| 6 | ~1,920 MB | ~120% | ⚠️ Média | Tolerável |
| 7 | ~2,240 MB | ~140% | ❌ Baixa | Não recomendado |

**Conclusão KVM 4**: **5 processos** é o sweet spot

---

## ⚠️ Limitações Adicionais

### 1. Rate Limiting do Site TJRJ

**Risco**: Múltiplas conexões simultâneas do mesmo IP

**Testes realizados**:
- ✅ 2 processos paralelos: Funcionando (24-26 Nov)
- ⏳ 5-6 processos: Não testado

**Sinais de throttling**:
- Respostas HTTP 429 (Too Many Requests)
- Timeouts aumentados
- Bloqueio temporário de IP

**Mitigação**:
- Usar IPs diferentes (múltiplas VPS) - CARO
- Adicionar delays randomizados entre requests
- Monitorar logs para detectar throttling

**Recomendação**: Testar com 3-4 processos antes de escalar para 5-6

### 2. Distribuição Desigual de Carga

**Problema**: Estado RJ leva ~8h, outras entidades < 30min

**Impacto**:
```
Processo 1: Estado RJ         → 8h ⏳⏳⏳⏳⏳⏳⏳⏳
Processo 2: 10 entidades      → 1h ⏳ (depois fica ocioso 7h)
Processo 3: 10 entidades      → 1h ⏳ (depois fica ocioso 7h)
Processo 4: 10 entidades      → 1h ⏳ (depois fica ocioso 7h)
Processo 5: 11 entidades      → 1h ⏳ (depois fica ocioso 7h)
```

**Solução**: Distribuição balanceada por tempo estimado (não por quantidade)

**Distribuição otimizada** (ver `strategies/option3_entity_parallelization.md`)

### 3. Network Bandwidth

**Download**: ~50 KB por página (HTML + assets)
**Upload**: ~5 KB por página (requests)

**Taxa por processo**:
- 1 página a cada 16s = 0.0625 páginas/s
- Download: ~3.125 KB/s por processo
- Upload: ~0.3 KB/s por processo

**Total para 5 processos**:
- Download: ~15.6 KB/s (0.125 Mbps)
- Upload: ~1.5 KB/s (0.012 Mbps)

**Conclusão**: Bandwidth NÃO é limitante (VPS tem >= 100 Mbps)

### 4. Disco (I/O)

**Escrita durante extração**: Mínima (apenas logs)
**Escrita final**: CSV consolidado

**Tamanho estimado de CSVs**:
- GERAL: ~1 MB (5,444 registros × 19 colunas)
- ESPECIAL: ~4 MB (27,000 registros × 19 colunas)
- **Total**: ~5 MB

**Conclusão**: Disco NÃO é limitante

---

## 🎯 Recomendação de Configuração

### Configuração Ideal: VPS KVM 4

**Processos**: 5 paralelos (headless)

**Distribuição de entidades**:
```
Processo 1: Estado RJ (isolado)                    → ~8h
Processo 2: 3 entidades grandes (ESPECIAL)         → ~2.5h
Processo 3: 18 entidades médias (ESPECIAL)         → ~2h
Processo 4: 19 entidades pequenas (ESPECIAL)       → ~1h
Processo 5: 56 entidades (GERAL completo)          → ~2h
```

**Recursos utilizados**:
- RAM: ~1,600 MB (11% da disponível) ✅
- CPU: ~100% (uso ótimo) ✅
- Disk: < 10 MB ✅
- Network: < 0.2 Mbps ✅

**Tempo total**: ~8h (limitado pelo Estado RJ)

---

## 📋 Configuração da VPS

### 1. Setup Inicial

```bash
# Ubuntu 22.04 LTS
sudo apt update && sudo apt upgrade -y

# Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Dependências Playwright
sudo apt install -y \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2
```

### 2. Instalação do Projeto

```bash
# Clone do repositório
git clone <repo-url> /opt/charles
cd /opt/charles

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Dependências
pip install -r requirements.txt

# Playwright browsers (headless)
playwright install chromium
```

### 3. Configuração de Recursos

```bash
# Limites de processos (security)
ulimit -n 4096  # File descriptors
ulimit -u 1024  # Max processes

# Swap (para segurança)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 4. Monitoramento

```bash
# CPU e RAM em tempo real
htop

# Processos Python
ps aux | grep python

# Network
iftop -i eth0
```

---

## 💰 Custo-Benefício

| VPS | Processos | Tempo | Custo/mês | Custo/extração |
|-----|-----------|-------|-----------|----------------|
| Atual (local) | 2 | 8h | $0 | $0 |
| KVM 2 | 2-3 | 7h | ~$15 | ~$0.04 |
| KVM 4 | 5 | 8h | ~$30 | ~$0.08 |

**Ganho KVM 2**: Marginal (economia de ~1h)
**Ganho KVM 4**: Resiliência + melhor uso de recursos

**Recomendação**:
- **Se extração é ocasional**: Usar local (atual)
- **Se extração é recorrente**: VPS KVM 4 vale a pena

---

## ✅ Checklist de Deployment

### Pré-Deployment
- [ ] Testar localmente com 3 entidades pequenas
- [ ] Validar CSV output
- [ ] Confirmar 100% cobertura de campos expandidos
- [ ] Testar recovery de falhas (kill de processo)

### Deployment VPS
- [ ] Provisionar VPS KVM 4 (Ubuntu 22.04)
- [ ] Configurar SSH keys
- [ ] Instalar dependências
- [ ] Deploy do código
- [ ] Testar com 2 processos primeiro
- [ ] Escalar para 5 processos
- [ ] Monitorar primeiras 2h de execução

### Pós-Deployment
- [ ] Validar CSVs gerados
- [ ] Verificar performance logs
- [ ] Comparar com baseline (V1)
- [ ] Documentar issues encontrados

---

**Última Atualização**: 2025-11-26
**Status**: ✅ Análise completa, pronto para implementação
