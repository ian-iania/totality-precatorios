# TJRJ Precatórios Web Scraper - API-Based Solution

## PROJECT CONTEXT & OVERVIEW

This project implements a robust, production-ready web scraper for extracting precatório (court-ordered payment) data from the Rio de Janeiro Court of Justice (TJRJ) portal. The scraper follows an API-first approach (Alternative 1), prioritizing direct API calls over browser automation for optimal performance, reliability, and scalability.

**Project Goal**: Build a Python-based scraper that extracts all precatório data from TJRJ's portal across both payment regimes (common and special), handling pagination automatically, and outputs structured CSV data for analysis.

**Target Website**: https://www.tjrj.jus.br/web/precatorios

**Technical Approach**: API discovery and direct HTTP requests using the requests library, avoiding browser automation overhead while maintaining robustness and error handling.

---

## PROJECT ARCHITECTURE & DATA FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                     TJRJ Web Portal                             │
│           https://www.tjrj.jus.br/web/precatorios               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │   AngularJS SPA (Frontend)        │
         │   - Hash-based routing (#!/)      │
         │   - Dynamic content loading       │
         └───────────────┬───────────────────┘
                         │
                         │ AJAX/Fetch Requests
                         ▼
         ┌───────────────────────────────────┐
         │     Backend REST API              │
         │  (To be discovered via DevTools)  │
         └───────────────┬───────────────────┘
                         │
                         │ JSON Responses
                         ▼
         ┌───────────────────────────────────┐
         │   Our Python Scraper              │
         │   1. API Discovery Phase          │
         │   2. Data Extraction Phase        │
         │   3. CSV Output Phase             │
         └───────────────┬───────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │   Structured CSV Output           │
         │   - precatorios_regime_geral.csv  │
         │   - precatorios_regime_especial.csv│
         └───────────────────────────────────┘
```

---

## DATA STRUCTURE & NAVIGATION FLOW

### Website Navigation Hierarchy

1. **Entry Point**: `https://www.tjrj.jus.br/web/precatorios`
   - Two main buttons: "Regime Comum" and "Regime Especial"

2. **Regime Pages**:
   - Regime Geral: `https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-geral`
   - Regime Especial: `https://www3.tjrj.jus.br/PortalConhecimento/precatorio/#!/entes-devedores/regime-especial`

3. **Entity Cards** (Entes Devedores):
   - Each page displays multiple entity cards (municipalities/institutions)
   - Example entities: INSS, Município de Angra dos Reis, Município de Araruama, etc.
   - Each card contains:
     - Entity name
     - Precatórios Pagos (paid): count
     - Precatórios Pendentes (pending): count
     - Valor Prioridade (priority value): currency
     - Valor RPV (RPV value): currency
     - Multiple clickable links to different views

4. **Precatório Lists**:
   - Example URL: `https://www3.tjrj.jus.br/PortalConhecimento/precatorio#!/ordem-cronologica?idEntidadeDevedora=86`
   - Contains paginated table with precatório records
   - Multiple action links per entity:
     - Pagamentos realizados (completed payments)
     - Consulte a sua posição (check position)
     - Precatórios pendentes de pagamento (pending payments)
     - Superpreferências pendentes de pagamento (super-priority pending)
     - Ordem de rateio de pagamento (payment distribution order)
     - Certidão de adimplência (compliance certificate)
     - Certidão de regularidade (regularity certificate)
     - Precatórios parcelados (installment payments)

### Expected Data Schema

**Entity Metadata**:
```python
{
    'id_entidade': int,
    'nome_entidade': str,
    'regime': str,  # 'geral' or 'especial'
    'precatorios_pagos': int,
    'precatorios_pendentes': int,
    'valor_prioridade': float,
    'valor_rpv': float,
    'timestamp_extracao': datetime
}
```

**Precatório Record**:
```python
{
    'numero_precatorio': str,
    'numero_processo': str,
    'beneficiario': str,
    'valor_original': float,
    'valor_atualizado': float,
    'data_requisicao': date,
    'tipo': str,  # 'comum', 'alimentar', 'superpreferencia'
    'status': str,  # 'pendente', 'pago', 'parcelado'
    'entidade_devedora': str,
    'id_entidade': int,
    'regime': str,
    'ordem_cronologica': int,
    'timestamp_extracao': datetime
}
```

---

## DEVELOPMENT RULES & CONSTRAINTS

### Code Quality Standards

1. **Python Version**: Python 3.9+
2. **Code Style**: 
   - Follow PEP 8 with line length of 88 (Black formatter standard)
   - Use type hints for all function signatures
   - Write docstrings for all classes and public methods (Google style)
   
3. **Error Handling**:
   - Never use bare `except:` clauses
   - Always specify exception types
   - Log all exceptions with full context
   - Implement retry logic with exponential backoff for network requests
   
4. **Security**:
   - Never hardcode credentials or API keys
   - Use environment variables for configuration
   - Validate and sanitize all data before processing
   - Respect robots.txt (check first)
   
5. **Performance**:
   - Implement rate limiting (max 1 request per second by default)
   - Use connection pooling with requests.Session()
   - Implement caching for repeated API calls
   - Support parallel processing for multiple entities (optional, with threading/asyncio)

### Ethical & Legal Constraints

1. **Rate Limiting**: MUST implement respectful rate limiting
   - Default: 1 request per second
   - Configurable via environment variable
   - Add exponential backoff on rate limit errors

2. **Robots.txt Compliance**: 
   - Check robots.txt before first run
   - Respect crawl delays specified
   - Document findings in README

3. **User-Agent**: 
   - Use descriptive User-Agent string
   - Include contact information
   - Example: `TJRJPrecatoriosScraper/1.0 (Educational Purpose; contact@example.com)`

4. **Data Privacy**:
   - Only extract publicly available data
   - Do not attempt to bypass authentication
   - Include disclaimer about public data usage

---

## REQUIRED DEPENDENCIES

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.31.0"
pandas = "^2.2.0"
python-dotenv = "^1.0.0"
loguru = "^0.7.2"
tenacity = "^8.2.3"  # For retry logic
pydantic = "^2.6.0"  # For data validation
aiohttp = "^3.9.0"  # Optional: for async support
playwright = "^1.41.0"  # Only for API discovery phase

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
black = "^24.1.0"
mypy = "^1.8.0"
ruff = "^0.2.0"
```

### Installation Command
```bash
poetry install
# OR using pip
pip install requests pandas python-dotenv loguru tenacity pydantic
```

---

## STEP-BY-STEP IMPLEMENTATION GUIDE

### Phase 1: Project Setup & API Discovery

#### Step 1.1: Initialize Project Structure
```bash
mkdir -p tjrj-precatorios-scraper/{src,tests,data,logs,docs}
cd tjrj-precatorios-scraper
poetry init  # or create requirements.txt
```

**Expected Directory Structure**:
```
tjrj-precatorios-scraper/
├── src/
│   ├── __init__.py
│   ├── api_discovery.py      # API endpoint discovery tool
│   ├── scraper.py             # Main scraper class
│   ├── models.py              # Pydantic data models
│   ├── utils.py               # Helper functions
│   └── config.py              # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_api_discovery.py
├── data/
│   ├── raw/                   # Raw API responses
│   ├── processed/             # Processed CSV files
│   └── cache/                 # Cached responses
├── logs/
│   └── scraper.log
├── docs/
│   ├── api_endpoints.md       # Documented API endpoints
│   └── data_dictionary.md     # Data field descriptions
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
└── main.py                    # CLI entry point
```

#### Step 1.2: API Discovery Using Browser DevTools

**CRITICAL**: Before writing the main scraper, we MUST discover the actual API endpoints.

Create `src/api_discovery.py`:
```python
"""
API Discovery Tool for TJRJ Precatórios Portal

This module uses Playwright to intercept network requests and discover
the actual REST API endpoints used by the AngularJS frontend.

Usage:
    python src/api_discovery.py --regime geral --output docs/api_endpoints.json
"""

from playwright.sync_api import sync_playwright, Page
import json
from typing import List, Dict
from loguru import logger
from pathlib import Path

class APIDiscovery:
    """Discovers and documents API endpoints used by TJRJ portal"""
    
    def __init__(self):
        self.discovered_apis: List[Dict] = []
        self.base_url = "https://www.tjrj.jus.br/web/precatorios"
        
    def intercept_request(self, request) -> None:
        """Intercepts and logs all network requests"""
        url = request.url
        
        # Filter for API calls
        if any(keyword in url.lower() for keyword in [
            '/api/', '/rest/', '/service/', 'precatorio', 
            'entidade', 'ordem-cronologica'
        ]):
            api_info = {
                'url': url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data if request.method == 'POST' else None,
                'resource_type': request.resource_type
            }
            self.discovered_apis.append(api_info)
            logger.info(f"📡 API Call: {request.method} {url}")
    
    def intercept_response(self, response) -> None:
        """Intercepts and logs API responses"""
        if any(keyword in response.url.lower() for keyword in [
            '/api/', '/rest/', 'precatorio'
        ]):
            try:
                # Try to parse as JSON
                if 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    logger.info(f"✅ Response: {response.status} - {response.url}")
                    logger.debug(f"Sample data: {json.dumps(data, indent=2)[:500]}")
            except Exception as e:
                logger.warning(f"Could not parse response: {e}")
    
    def discover_endpoints(self, regime: str = 'geral') -> List[Dict]:
        """
        Discovers API endpoints by navigating through the portal
        
        Args:
            regime: 'geral' or 'especial'
            
        Returns:
            List of discovered API endpoints with metadata
        """
        logger.info(f"🔍 Starting API discovery for regime: {regime}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Set up interceptors
            page.on('request', self.intercept_request)
            page.on('response', self.intercept_response)
            
            try:
                # Step 1: Navigate to main page
                logger.info("Navigating to main page...")
                page.goto(self.base_url, wait_until='networkidle')
                page.wait_for_timeout(2000)
                
                # Step 2: Click on regime button
                logger.info(f"Clicking on regime {regime}...")
                if regime == 'geral':
                    page.click('text=/.*regime.*comum.*/i')
                else:
                    page.click('text=/.*regime.*especial.*/i')
                
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(3000)
                
                # Step 3: Wait for entity cards to load
                logger.info("Waiting for entity cards...")
                page.wait_for_selector('[class*="card"], [class*="entidade"]', timeout=10000)
                
                # Step 4: Click on first entity link
                logger.info("Clicking on first entity...")
                first_link = page.query_selector('a[href*="ordem-cronologica"]')
                if first_link:
                    first_link.click()
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(3000)
                    
                    # Step 5: Try pagination
                    logger.info("Testing pagination...")
                    next_button = page.query_selector('button:has-text("Próxima"), a:has-text("Próxima")')
                    if next_button:
                        next_button.click()
                        page.wait_for_timeout(2000)
                
                logger.info(f"✅ Discovery complete! Found {len(self.discovered_apis)} API calls")
                
            except Exception as e:
                logger.error(f"Error during discovery: {e}")
            finally:
                browser.close()
        
        return self.discovered_apis
    
    def save_discoveries(self, output_path: str = 'docs/api_endpoints.json') -> None:
        """Saves discovered APIs to JSON file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Remove duplicates based on URL
        unique_apis = {api['url']: api for api in self.discovered_apis}
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(list(unique_apis.values()), f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(unique_apis)} unique APIs to {output_path}")
        
        # Also create a readable markdown documentation
        self._create_documentation(unique_apis, output_path.replace('.json', '.md'))
    
    def _create_documentation(self, apis: Dict, output_path: str) -> None:
        """Creates human-readable API documentation"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# TJRJ Precatórios API Endpoints\n\n")
            f.write(f"Discovered: {len(apis)} unique endpoints\n\n")
            
            for url, api in apis.items():
                f.write(f"## {api['method']} {url}\n\n")
                f.write(f"**Resource Type**: {api['resource_type']}\n\n")
                
                if api['post_data']:
                    f.write(f"**POST Data**:\n```json\n{api['post_data']}\n```\n\n")
                
                f.write("---\n\n")
        
        logger.info(f"📝 Created documentation at {output_path}")

# CLI for running discovery
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover TJRJ API endpoints')
    parser.add_argument('--regime', choices=['geral', 'especial'], default='geral')
    parser.add_argument('--output', default='docs/api_endpoints.json')
    
    args = parser.parse_args()
    
    discovery = APIDiscovery()
    apis = discovery.discover_endpoints(regime=args.regime)
    discovery.save_discoveries(output_path=args.output)
```

**Action Required**: Run API discovery FIRST:
```bash
python src/api_discovery.py --regime geral --output docs/api_endpoints.json
python src/api_discovery.py --regime especial --output docs/api_endpoints_especial.json
```

**Expected Outcomes**:
1. JSON file with all discovered API endpoints
2. Markdown documentation of APIs
3. Understanding of:
   - Base API URL
   - Authentication requirements (if any)
   - Request/response formats
   - Pagination mechanism
   - Available query parameters

---

### Phase 2: Core Scraper Implementation

#### Step 2.1: Define Data Models

Create `src/models.py`:
```python
"""
Pydantic models for TJRJ Precatórios data validation

These models ensure data integrity and provide automatic validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class EntidadeDevedora(BaseModel):
    """Entity (municipality/institution) owing precatórios"""
    
    id_entidade: int = Field(..., description="Unique entity identifier")
    nome_entidade: str = Field(..., min_length=1, max_length=500)
    regime: str = Field(..., pattern='^(geral|especial)$')
    precatorios_pagos: int = Field(ge=0)
    precatorios_pendentes: int = Field(ge=0)
    valor_prioridade: Decimal = Field(ge=0, decimal_places=2)
    valor_rpv: Decimal = Field(ge=0, decimal_places=2)
    timestamp_extracao: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class Precatorio(BaseModel):
    """Individual precatório record"""
    
    numero_precatorio: str = Field(..., min_length=1)
    numero_processo: Optional[str] = None
    beneficiario: str = Field(..., min_length=1)
    cpf_cnpj_beneficiario: Optional[str] = None
    valor_original: Decimal = Field(ge=0, decimal_places=2)
    valor_atualizado: Decimal = Field(ge=0, decimal_places=2)
    data_requisicao: Optional[date] = None
    data_atualizacao: Optional[date] = None
    tipo: str = Field(..., pattern='^(comum|alimentar|superpreferencia|rpv)$')
    status: str = Field(..., pattern='^(pendente|pago|parcelado|cancelado)$')
    entidade_devedora: str
    id_entidade: int
    regime: str = Field(..., pattern='^(geral|especial)$')
    ordem_cronologica: Optional[int] = Field(None, ge=1)
    observacoes: Optional[str] = None
    timestamp_extracao: datetime = Field(default_factory=datetime.now)
    
    @validator('cpf_cnpj_beneficiario')
    def validate_cpf_cnpj(cls, v):
        """Validates CPF/CNPJ format if present"""
        if v:
            # Remove formatting
            v = ''.join(filter(str.isdigit, v))
            if len(v) not in [11, 14]:  # CPF or CNPJ
                raise ValueError('CPF must have 11 digits or CNPJ must have 14 digits')
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class ScraperConfig(BaseModel):
    """Configuration for scraper behavior"""
    
    base_url: str = "https://www3.tjrj.jus.br/PortalConhecimento"
    regime: str = Field(default='geral', pattern='^(geral|especial)$')
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=2.0, ge=0.5, le=60.0)
    rate_limit_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    timeout: int = Field(default=30, ge=5, le=300)
    enable_cache: bool = True
    cache_dir: str = "data/cache"
    output_dir: str = "data/processed"
    log_level: str = Field(default="INFO", pattern='^(DEBUG|INFO|WARNING|ERROR)$')
    
    class Config:
        env_prefix = 'TJRJ_'  # Environment variables prefix
```

#### Step 2.2: Implement Configuration Manager

Create `src/config.py`:
```python
"""
Configuration management using environment variables and .env files
"""

from pathlib import Path
from dotenv import load_dotenv
import os
from src.models import ScraperConfig

# Load environment variables from .env file
load_dotenv()

def get_config() -> ScraperConfig:
    """
    Loads configuration from environment variables
    
    Returns:
        ScraperConfig instance with all settings
    """
    return ScraperConfig(
        base_url=os.getenv('TJRJ_BASE_URL', 'https://www3.tjrj.jus.br/PortalConhecimento'),
        regime=os.getenv('TJRJ_REGIME', 'geral'),
        max_retries=int(os.getenv('TJRJ_MAX_RETRIES', '3')),
        retry_delay=float(os.getenv('TJRJ_RETRY_DELAY', '2.0')),
        rate_limit_delay=float(os.getenv('TJRJ_RATE_LIMIT_DELAY', '1.0')),
        timeout=int(os.getenv('TJRJ_TIMEOUT', '30')),
        enable_cache=os.getenv('TJRJ_ENABLE_CACHE', 'true').lower() == 'true',
        cache_dir=os.getenv('TJRJ_CACHE_DIR', 'data/cache'),
        output_dir=os.getenv('TJRJ_OUTPUT_DIR', 'data/processed'),
        log_level=os.getenv('TJRJ_LOG_LEVEL', 'INFO')
    )

# Create example .env file
def create_env_example():
    """Creates .env.example file with all configuration options"""
    env_example = """
# TJRJ Precatórios Scraper Configuration

# Base URL of the TJRJ portal
TJRJ_BASE_URL=https://www3.tjrj.jus.br/PortalConhecimento

# Regime to scrape: 'geral' or 'especial'
TJRJ_REGIME=geral

# Maximum number of retry attempts for failed requests
TJRJ_MAX_RETRIES=3

# Delay between retries (seconds)
TJRJ_RETRY_DELAY=2.0

# Delay between requests to respect rate limiting (seconds)
TJRJ_RATE_LIMIT_DELAY=1.0

# Request timeout (seconds)
TJRJ_TIMEOUT=30

# Enable response caching
TJRJ_ENABLE_CACHE=true

# Cache directory
TJRJ_CACHE_DIR=data/cache

# Output directory for CSV files
TJRJ_OUTPUT_DIR=data/processed

# Logging level: DEBUG, INFO, WARNING, ERROR
TJRJ_LOG_LEVEL=INFO
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_example.strip())
```

#### Step 2.3: Implement Main Scraper Class

Create `src/scraper.py`:
```python
"""
Main scraper implementation for TJRJ Precatórios

This module implements the core scraping logic using direct API calls
discovered in Phase 1.

Best Practices Applied:
- Session reuse for connection pooling
- Exponential backoff retry logic
- Comprehensive error handling
- Response caching
- Rate limiting
- Detailed logging
"""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pandas as pd
from typing import List, Dict, Optional, Tuple
from loguru import logger
import time
import json
from pathlib import Path
from datetime import datetime
import hashlib

from src.models import EntidadeDevedora, Precatorio, ScraperConfig
from src.config import get_config

class TJRJPrecatoriosScraper:
    """
    Production-ready scraper for TJRJ precatórios data
    
    This class handles all aspects of data extraction including:
    - API endpoint discovery and validation
    - Entity listing
    - Precatório data extraction with pagination
    - Error handling and retries
    - Data validation and cleaning
    - CSV export
    
    Example:
        >>> scraper = TJRJPrecatoriosScraper()
        >>> df = scraper.scrape_regime('geral')
        >>> df.to_csv('precatorios.csv')
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize scraper with configuration
        
        Args:
            config: Optional ScraperConfig instance. If None, loads from environment.
        """
        self.config = config or get_config()
        self.session = self._create_session()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            "logs/scraper.log",
            rotation="10 MB",
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        logger.info(f"🚀 Initializing TJRJ Scraper for regime: {self.config.regime}")
        logger.info(f"⚙️  Config: rate_limit={self.config.rate_limit_delay}s, "
                   f"retries={self.config.max_retries}, cache={self.config.enable_cache}")
    
    def _create_session(self) -> requests.Session:
        """
        Creates a requests Session with retry logic and connection pooling
        
        Best Practice: Use Session for connection pooling and automatic retries
        Reference: https://requests.readthedocs.io/en/latest/user/advanced/
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'TJRJPrecatoriosScraper/1.0 (Educational Purpose; Research)',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.tjrj.jus.br/web/precatorios/'
        })
        
        return session
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generates cache key from URL and parameters"""
        cache_string = url + json.dumps(params or {}, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Retrieves cached response if available and valid"""
        if not self.config.enable_cache:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    # Check if cache is less than 24 hours old
                    cache_time = datetime.fromisoformat(cached['timestamp'])
                    age_hours = (datetime.now() - cache_time).total_seconds() / 3600
                    
                    if age_hours < 24:
                        logger.debug(f"📦 Cache hit: {cache_key} (age: {age_hours:.1f}h)")
                        return cached['data']
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        return None
    
    def _cache_response(self, cache_key: str, data: Dict) -> None:
        """Caches API response"""
        if not self.config.enable_cache:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _make_request(
        self, 
        url: str, 
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Makes HTTP request with caching, rate limiting, and error handling
        
        Args:
            url: Target URL
            method: HTTP method (GET or POST)
            params: Query parameters
            data: POST data
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.RequestException: On network errors
        """
        # Check cache
        cache_key = self._get_cache_key(url, params)
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        # Rate limiting
        time.sleep(self.config.rate_limit_delay)
        
        try:
            logger.debug(f"🌐 {method} {url}")
            
            if method == 'GET':
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout
                )
            else:
                response = self.session.post(
                    url,
                    json=data,
                    params=params,
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Cache successful response
            self._cache_response(cache_key, result)
            
            return result
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error: {e.response.status_code} - {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response: {e}")
            raise
    
    def get_entidades(self, regime: str) -> List[EntidadeDevedora]:
        """
        Fetches list of entities (municipalities/institutions) for a regime
        
        Args:
            regime: 'geral' or 'especial'
            
        Returns:
            List of EntidadeDevedora instances
            
        Note:
            The actual endpoint URL will be discovered in Phase 1 and needs
            to be updated here based on api_discovery.py findings.
        """
        logger.info(f"📋 Fetching entities for regime: {regime}")
        
        # TODO: Update this URL based on API discovery results
        # This is a placeholder that needs to be replaced with actual endpoint
        url = f"{self.config.base_url}/api/entidades-devedoras"
        params = {'regime': regime}
        
        try:
            response = self._make_request(url, params=params)
            
            # Parse response into EntidadeDevedora instances
            entidades = []
            for item in response.get('entidades', []):  # Adjust key based on actual response
                entidade = EntidadeDevedora(
                    id_entidade=item['id'],
                    nome_entidade=item['nome'],
                    regime=regime,
                    precatorios_pagos=item.get('precatoriosPagos', 0),
                    precatorios_pendentes=item.get('precatoriosPendentes', 0),
                    valor_prioridade=item.get('valorPrioridade', 0),
                    valor_rpv=item.get('valorRPV', 0)
                )
                entidades.append(entidade)
            
            logger.info(f"✅ Found {len(entidades)} entities")
            return entidades
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch entities: {e}")
            raise
    
    def get_precatorios_page(
        self, 
        id_entidade: int,
        pagina: int = 1,
        tamanho_pagina: int = 50
    ) -> Tuple[List[Dict], bool]:
        """
        Fetches a single page of precatórios for an entity
        
        Args:
            id_entidade: Entity ID
            pagina: Page number (1-indexed)
            tamanho_pagina: Records per page
            
        Returns:
            Tuple of (precatorios_list, has_next_page)
        """
        # TODO: Update this URL based on API discovery results
        url = f"{self.config.base_url}/api/precatorios"
        params = {
            'idEntidadeDevedora': id_entidade,
            'pagina': pagina,
            'tamanhoPagina': tamanho_pagina
        }
        
        try:
            response = self._make_request(url, params=params)
            
            precatorios = response.get('dados', [])  # Adjust based on actual response
            has_next = response.get('temProximaPagina', False)
            
            logger.debug(f"📄 Page {pagina}: {len(precatorios)} records, "
                        f"has_next={has_next}")
            
            return precatorios, has_next
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch page {pagina}: {e}")
            raise
    
    def get_all_precatorios_entidade(
        self,
        entidade: EntidadeDevedora
    ) -> List[Precatorio]:
        """
        Fetches ALL precatórios for an entity (handles pagination automatically)
        
        Args:
            entidade: EntidadeDevedora instance
            
        Returns:
            List of Precatorio instances
        """
        logger.info(f"🔄 Extracting precatórios for: {entidade.nome_entidade}")
        
        all_precatorios = []
        pagina = 1
        
        while True:
            try:
                precatorios_raw, has_next = self.get_precatorios_page(
                    entidade.id_entidade,
                    pagina
                )
                
                # Parse and validate each precatório
                for item in precatorios_raw:
                    try:
                        precatorio = Precatorio(
                            numero_precatorio=item['numeroPrecatorio'],
                            numero_processo=item.get('numeroProcesso'),
                            beneficiario=item['beneficiario'],
                            cpf_cnpj_beneficiario=item.get('cpfCnpj'),
                            valor_original=item['valorOriginal'],
                            valor_atualizado=item['valorAtualizado'],
                            data_requisicao=item.get('dataRequisicao'),
                            tipo=item['tipo'],
                            status=item['status'],
                            entidade_devedora=entidade.nome_entidade,
                            id_entidade=entidade.id_entidade,
                            regime=entidade.regime,
                            ordem_cronologica=item.get('ordem')
                        )
                        all_precatorios.append(precatorio)
                    except Exception as e:
                        logger.warning(f"⚠️  Invalid precatório record: {e}")
                        continue
                
                logger.info(f"  Page {pagina}: {len(precatorios_raw)} records "
                          f"(total: {len(all_precatorios)})")
                
                if not has_next:
                    break
                
                pagina += 1
                
            except Exception as e:
                logger.error(f"❌ Error on page {pagina}: {e}")
                break
        
        logger.info(f"✅ Extracted {len(all_precatorios)} precatórios from "
                   f"{entidade.nome_entidade}")
        
        return all_precatorios
    
    def scrape_regime(self, regime: str) -> pd.DataFrame:
        """
        Scrapes ALL data for a regime (main entry point)
        
        Args:
            regime: 'geral' or 'especial'
            
        Returns:
            DataFrame with all precatórios
        """
        logger.info(f"🎯 Starting full scrape for regime: {regime}")
        start_time = time.time()
        
        # Step 1: Get all entities
        entidades = self.get_entidades(regime)
        
        if not entidades:
            logger.warning("⚠️  No entities found!")
            return pd.DataFrame()
        
        # Step 2: Extract precatórios from each entity
        all_data = []
        
        for i, entidade in enumerate(entidades, 1):
            logger.info(f"\n[{i}/{len(entidades)}] Processing: {entidade.nome_entidade}")
            
            try:
                precatorios = self.get_all_precatorios_entidade(entidade)
                
                # Convert to dict for DataFrame
                for p in precatorios:
                    all_data.append(p.dict())
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {entidade.nome_entidade}: {e}")
                continue
        
        # Step 3: Create DataFrame
        df = pd.DataFrame(all_data)
        
        elapsed = time.time() - start_time
        logger.info(f"\n✅ Scraping complete!")
        logger.info(f"   Total records: {len(df)}")
        logger.info(f"   Entities processed: {len(entidades)}")
        logger.info(f"   Time elapsed: {elapsed:.1f}s")
        logger.info(f"   Records/second: {len(df)/elapsed:.1f}")
        
        return df
    
    def save_to_csv(
        self, 
        df: pd.DataFrame, 
        filename: Optional[str] = None
    ) -> str:
        """
        Saves DataFrame to CSV with proper formatting
        
        Args:
            df: DataFrame to save
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"precatorios_{self.config.regime}_{timestamp}.csv"
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        # Save with UTF-8 encoding and proper formatting
        df.to_csv(
            filepath,
            index=False,
            encoding='utf-8-sig',  # BOM for Excel compatibility
            sep=';',  # Semicolon for better Excel support in Brazil
            decimal=',',  # Brazilian decimal format
            date_format='%Y-%m-%d'
        )
        
        logger.info(f"💾 Saved to: {filepath}")
        logger.info(f"   Size: {filepath.stat().st_size / 1024:.1f} KB")
        
        return str(filepath)
    
    def close(self):
        """Closes session and cleanup"""
        self.session.close()
        logger.info("👋 Scraper session closed")
```

#### Step 2.4: Implement CLI Interface

Create `main.py`:
```python
"""
Command-line interface for TJRJ Precatórios Scraper

Usage:
    # Scrape regime geral
    python main.py --regime geral
    
    # Scrape regime especial with custom output
    python main.py --regime especial --output meu_arquivo.csv
    
    # Enable debug logging
    python main.py --regime geral --log-level DEBUG
    
    # Disable caching
    python main.py --regime geral --no-cache
"""

import argparse
import sys
from pathlib import Path
from loguru import logger

from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config, create_env_example
from src.models import ScraperConfig

def setup_logging(log_level: str):
    """Configure logging"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )

def main():
    parser = argparse.ArgumentParser(
        description='TJRJ Precatórios Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --regime geral
  python main.py --regime especial --output resultado.csv
  python main.py --regime geral --log-level DEBUG --no-cache
        """
    )
    
    parser.add_argument(
        '--regime',
        choices=['geral', 'especial'],
        default='geral',
        help='Regime to scrape (default: geral)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV filename (auto-generated if not specified)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable response caching'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        help='Rate limit delay in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--create-env',
        action='store_true',
        help='Create .env.example file and exit'
    )
    
    args = parser.parse_args()
    
    # Handle --create-env flag
    if args.create_env:
        create_env_example()
        logger.info("✅ Created .env.example file")
        return 0
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = get_config()
    
    # Override config with CLI arguments
    if args.no_cache:
        config.enable_cache = False
    if args.rate_limit:
        config.rate_limit_delay = args.rate_limit
    
    config.regime = args.regime
    config.log_level = args.log_level
    
    logger.info("=" * 60)
    logger.info("🚀 TJRJ Precatórios Scraper")
    logger.info("=" * 60)
    logger.info(f"Regime: {config.regime}")
    logger.info(f"Cache: {'Enabled' if config.enable_cache else 'Disabled'}")
    logger.info(f"Rate Limit: {config.rate_limit_delay}s")
    logger.info("=" * 60)
    
    try:
        # Initialize scraper
        scraper = TJRJPrecatoriosScraper(config=config)
        
        # Scrape data
        df = scraper.scrape_regime(config.regime)
        
        if df.empty:
            logger.warning("⚠️  No data extracted!")
            return 1
        
        # Save to CSV
        output_path = scraper.save_to_csv(df, filename=args.output)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records: {len(df)}")
        logger.info(f"Entities: {df['entidade_devedora'].nunique()}")
        logger.info(f"Total value: R$ {df['valor_atualizado'].sum():,.2f}")
        logger.info(f"Output file: {output_path}")
        logger.info("=" * 60)
        logger.info("✅ SUCCESS!")
        
        scraper.close()
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.exception("Full traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

### Phase 3: Testing & Validation

#### Step 3.1: Create Unit Tests

Create `tests/test_scraper.py`:
```python
"""
Unit tests for TJRJ Scraper

Run with: pytest tests/ -v --cov=src
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from decimal import Decimal

from src.scraper import TJRJPrecatoriosScraper
from src.models import EntidadeDevedora, Precatorio, ScraperConfig

@pytest.fixture
def mock_config():
    """Fixture providing test configuration"""
    return ScraperConfig(
        base_url="https://test.example.com",
        regime="geral",
        enable_cache=False,
        rate_limit_delay=0.1
    )

@pytest.fixture
def scraper(mock_config):
    """Fixture providing scraper instance"""
    return TJRJPrecatoriosScraper(config=mock_config)

class TestScraperInitialization:
    """Tests for scraper initialization"""
    
    def test_scraper_init_default_config(self):
        """Test scraper initializes with default config"""
        scraper = TJRJPrecatoriosScraper()
        assert scraper.config is not None
        assert scraper.session is not None
    
    def test_scraper_init_custom_config(self, mock_config):
        """Test scraper initializes with custom config"""
        scraper = TJRJPrecatoriosScraper(config=mock_config)
        assert scraper.config.base_url == "https://test.example.com"
        assert scraper.config.enable_cache is False

class TestEntityFetching:
    """Tests for entity fetching functionality"""
    
    @patch('src.scraper.TJRJPrecatoriosScraper._make_request')
    def test_get_entidades_success(self, mock_request, scraper):
        """Test successful entity fetching"""
        mock_request.return_value = {
            'entidades': [
                {
                    'id': 1,
                    'nome': 'Test Entity',
                    'precatoriosPagos': 10,
                    'precatoriosPendentes': 5,
                    'valorPrioridade': 1000.50,
                    'valorRPV': 500.25
                }
            ]
        }
        
        entidades = scraper.get_entidades('geral')
        
        assert len(entidades) == 1
        assert entidades[0].nome_entidade == 'Test Entity'
        assert entidades[0].precatorios_pagos == 10
    
    @patch('src.scraper.TJRJPrecatoriosScraper._make_request')
    def test_get_entidades_empty_response(self, mock_request, scraper):
        """Test handling of empty entity list"""
        mock_request.return_value = {'entidades': []}
        
        entidades = scraper.get_entidades('geral')
        
        assert len(entidades) == 0

class TestPrecatorioExtraction:
    """Tests for precatório extraction"""
    
    @patch('src.scraper.TJRJPrecatoriosScraper._make_request')
    def test_get_precatorios_page(self, mock_request, scraper):
        """Test single page extraction"""
        mock_request.return_value = {
            'dados': [
                {
                    'numeroPrecatorio': '001/2024',
                    'beneficiario': 'Test Beneficiary',
                    'valorOriginal': 1000.00,
                    'valorAtualizado': 1100.00,
                    'tipo': 'comum',
                    'status': 'pendente'
                }
            ],
            'temProximaPagina': False
        }
        
        precatorios, has_next = scraper.get_precatorios_page(1, 1)
        
        assert len(precatorios) == 1
        assert has_next is False

class TestDataValidation:
    """Tests for data validation"""
    
    def test_entidade_model_validation(self):
        """Test EntidadeDevedora model validation"""
        entidade = EntidadeDevedora(
            id_entidade=1,
            nome_entidade="Test",
            regime="geral",
            precatorios_pagos=10,
            precatorios_pendentes=5,
            valor_prioridade=Decimal("1000.50"),
            valor_rpv=Decimal("500.25")
        )
        
        assert entidade.id_entidade == 1
        assert entidade.regime == "geral"
    
    def test_precatorio_model_validation(self):
        """Test Precatorio model validation"""
        precatorio = Precatorio(
            numero_precatorio="001/2024",
            beneficiario="Test",
            valor_original=Decimal("1000.00"),
            valor_atualizado=Decimal("1100.00"),
            tipo="comum",
            status="pendente",
            entidade_devedora="Test Entity",
            id_entidade=1,
            regime="geral"
        )
        
        assert precatorio.tipo == "comum"
        assert precatorio.status == "pendente"

class TestCSVExport:
    """Tests for CSV export functionality"""
    
    def test_save_to_csv(self, scraper, tmp_path):
        """Test CSV saving"""
        df = pd.DataFrame([
            {
                'numero_precatorio': '001/2024',
                'beneficiario': 'Test',
                'valor_atualizado': 1000.00
            }
        ])
        
        scraper.config.output_dir = str(tmp_path)
        filepath = scraper.save_to_csv(df, filename='test.csv')
        
        assert Path(filepath).exists()
        
        # Verify content
        df_loaded = pd.read_csv(filepath, sep=';', decimal=',', encoding='utf-8-sig')
        assert len(df_loaded) == 1

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
```

#### Step 3.2: Create Integration Test

Create `tests/test_integration.py`:
```python
"""
Integration tests (requires actual network access)

These tests hit the real TJRJ API and should be run sparingly.
Run with: pytest tests/test_integration.py -v -m integration
"""

import pytest
from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config

@pytest.mark.integration
@pytest.mark.slow
class TestIntegration:
    """Integration tests with real API"""
    
    def test_full_scrape_small_sample(self):
        """Test full scrape with limited data (smoke test)"""
        config = get_config()
        config.rate_limit_delay = 2.0  # Be respectful
        
        scraper = TJRJPrecatoriosScraper(config=config)
        
        # Get first entity only
        entidades = scraper.get_entidades('geral')
        assert len(entidades) > 0
        
        # Extract from first entity only
        first_entidade = entidades[0]
        precatorios = scraper.get_all_precatorios_entidade(first_entidade)
        
        assert len(precatorios) >= 0  # May be empty but shouldn't error
        
        scraper.close()
```

---

### Phase 4: Documentation & Deployment

#### Step 4.1: Create Comprehensive README

Create `README.md`:
```markdown
# TJRJ Precatórios Web Scraper

**Production-ready web scraper** for extracting court-ordered payment (precatório) data from the Rio de Janeiro Court of Justice (TJRJ) portal.

## 🎯 Features

- ✅ **API-First Approach**: Direct API calls (no browser overhead)
- ✅ **Comprehensive Coverage**: Both regime geral and especial
- ✅ **Automatic Pagination**: Handles multi-page results automatically
- ✅ **Robust Error Handling**: Retries with exponential backoff
- ✅ **Response Caching**: Reduces load on target server
- ✅ **Rate Limiting**: Respectful scraping with configurable delays
- ✅ **Data Validation**: Pydantic models ensure data integrity
- ✅ **CSV Export**: Excel-compatible format with Brazilian standards
- ✅ **Comprehensive Logging**: Detailed logs for monitoring and debugging
- ✅ **Production Ready**: Type hints, tests, CI/CD ready

## 📊 Extracted Data

### Entity-Level Data
- Entity name and ID
- Count of paid/pending precatórios
- Priority and RPV values
- Regime type

### Precatório-Level Data
- Precatório number and process number
- Beneficiary information
- Original and updated values
- Requisition date
- Type and status
- Chronological order

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd tjrj-precatorios-scraper

# Install dependencies
pip install -r requirements.txt
# OR using poetry
poetry install
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your preferences (optional - defaults work out of the box)

### Basic Usage

```bash
# Scrape regime geral
python main.py --regime geral

# Scrape regime especial
python main.py --regime especial

# Custom output filename
python main.py --regime geral --output meus_precatorios.csv

# Enable debug logging
python main.py --regime geral --log-level DEBUG
```

## 📖 Advanced Usage

### Python API

```python
from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config

# Initialize scraper
config = get_config()
scraper = TJRJPrecatoriosScraper(config=config)

# Scrape regime
df = scraper.scrape_regime('geral')

# Save to CSV
scraper.save_to_csv(df, filename='precatorios.csv')

# Access data
print(f"Total records: {len(df)}")
print(f"Total value: R$ {df['valor_atualizado'].sum():,.2f}")

scraper.close()
```

### Custom Configuration

```python
from src.models import ScraperConfig
from src.scraper import TJRJPrecatoriosScraper

config = ScraperConfig(
    regime='geral',
    rate_limit_delay=2.0,  # 2 seconds between requests
    max_retries=5,
    enable_cache=True
)

scraper = TJRJPrecatoriosScraper(config=config)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run only unit tests (fast)
pytest tests/test_scraper.py -v

# Run integration tests (slow, hits real API)
pytest tests/test_integration.py -v -m integration
```

## 📁 Project Structure

```
tjrj-precatorios-scraper/
├── src/
│   ├── __init__.py
│   ├── api_discovery.py      # API endpoint discovery
│   ├── scraper.py             # Main scraper implementation
│   ├── models.py              # Data models (Pydantic)
│   ├── utils.py               # Helper functions
│   └── config.py              # Configuration management
├── tests/
│   ├── test_scraper.py        # Unit tests
│   └── test_integration.py    # Integration tests
├── data/
│   ├── raw/                   # Raw API responses
│   ├── processed/             # CSV outputs
│   └── cache/                 # Cached API responses
├── logs/                      # Application logs
├── docs/
│   ├── api_endpoints.md       # Documented APIs
│   └── data_dictionary.md     # Field descriptions
├── .env.example               # Configuration template
├── .gitignore
├── README.md
├── pyproject.toml
└── main.py                    # CLI entry point
```

## 🔧 Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `TJRJ_BASE_URL` | `https://www3.tjrj.jus.br/PortalConhecimento` | Base API URL |
| `TJRJ_REGIME` | `geral` | Regime to scrape |
| `TJRJ_MAX_RETRIES` | `3` | Max retry attempts |
| `TJRJ_RETRY_DELAY` | `2.0` | Delay between retries (seconds) |
| `TJRJ_RATE_LIMIT_DELAY` | `1.0` | Delay between requests (seconds) |
| `TJRJ_TIMEOUT` | `30` | Request timeout (seconds) |
| `TJRJ_ENABLE_CACHE` | `true` | Enable response caching |
| `TJRJ_LOG_LEVEL` | `INFO` | Logging level |

## 📝 Best Practices

### Ethical Scraping
- ✅ Respects robots.txt
- ✅ Implements rate limiting (1 req/sec default)
- ✅ Uses descriptive User-Agent
- ✅ Caches responses to minimize load
- ✅ Only accesses public data

### Error Handling
- ✅ Automatic retries with exponential backoff
- ✅ Graceful degradation on failures
- ✅ Comprehensive error logging
- ✅ Validation of all data

### Performance
- ✅ Connection pooling
- ✅ Response caching
- ✅ Efficient pagination
- ✅ Optional parallel processing

## 🐛 Troubleshooting

### "No entities found"
- Check if website structure changed
- Run API discovery again: `python src/api_discovery.py`
- Verify network connectivity

### "Rate limited"
- Increase `TJRJ_RATE_LIMIT_DELAY` in `.env`
- Check if IP is blocked (use different network)

### "Invalid data format"
- API response format may have changed
- Check logs for details
- Update data models in `src/models.py`

## 📜 License

[MIT License](LICENSE)

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Users are responsible for:
- Complying with TJRJ's terms of service
- Respecting rate limits and server load
- Using data ethically and legally
- Verifying data accuracy before use

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request

## 📧 Support

For issues or questions:
- Create an issue on GitHub
- Check existing documentation
- Review logs in `logs/scraper.log`
```

---

## CRITICAL NOTES FOR CLAUDE CODE

### Workflow for Implementation

**YOU MUST FOLLOW THIS SEQUENCE**:

1. **FIRST**: Run API Discovery
   ```bash
   python src/api_discovery.py --regime geral
   ```
   - This will discover the actual API endpoints
   - DO NOT proceed without completing this step
   - Update `src/scraper.py` with discovered endpoints

2. **SECOND**: Analyze API Responses
   - Review `docs/api_endpoints.json`
   - Understand response structure
   - Update data models if needed

3. **THIRD**: Implement Core Scraper
   - Update placeholder URLs in `scraper.py`
   - Adjust response parsing based on actual API structure
   - Test with single entity first

4. **FOURTH**: Test Incrementally
   - Test with one entity
   - Test with one page
   - Test full scrape with small dataset
   - Run full scrape

5. **FIFTH**: Validate & Document
   - Run test suite
   - Verify CSV output
   - Update documentation with findings

### Common Pitfalls to Avoid

❌ **DON'T**:
- Skip API discovery phase
- Hardcode endpoint URLs without verification
- Assume response structure without checking
- Run full scrape before testing with small dataset
- Ignore rate limiting
- Forget to handle edge cases (empty responses, missing fields)

✅ **DO**:
- Always test incrementally
- Log extensively during development
- Handle all error cases gracefully
- Validate data with Pydantic models
- Document any deviations from plan
- Keep track of API changes

### Success Criteria

The implementation is COMPLETE when:

1. ✅ API discovery successfully identifies all endpoints
2. ✅ Scraper extracts data from at least one entity
3. ✅ Pagination works correctly
4. ✅ All data validates against Pydantic models
5. ✅ CSV export works with Brazilian format
6. ✅ Error handling covers all known scenarios
7. ✅ Tests pass with >80% coverage
8. ✅ README is accurate and complete
9. ✅ Logging provides clear progress feedback
10. ✅ Full scrape completes without errors

### Environment Setup Commands

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requests pandas python-dotenv loguru tenacity pydantic playwright pytest pytest-cov black mypy

# Install Playwright browsers
playwright install chromium

# Create directory structure
mkdir -p src tests data/{raw,processed,cache} logs docs

# Create .env file
cp .env.example .env

# Run API discovery
python src/api_discovery.py --regime geral
```

### Testing Strategy

```bash
# 1. Unit tests (fast, no network)
pytest tests/test_scraper.py -v

# 2. Integration tests (slow, real API)
pytest tests/test_integration.py -v -m integration

# 3. Full test suite with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# 4. Smoke test (quick validation)
python main.py --regime geral --log-level DEBUG
```

---

## ADDITIONAL REFERENCES

### Python Best Practices
- PEP 8: https://pep8.org/
- Type Hints: https://docs.python.org/3/library/typing.html
- Pydantic: https://docs.pydantic.dev/

### Web Scraping Best Practices
- Requests library: https://requests.readthedocs.io/
- Ethical Scraping: https://www.scrapehero.com/web-scraping-best-practices/
- robots.txt: https://www.robotstxt.org/

### Testing Best Practices
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/

---

## VERSION HISTORY

- **v1.0.0** (2025-01-18): Initial specification
  - API-first approach
  - Complete implementation guide
  - Comprehensive testing strategy
  - Production-ready standards

---

**END OF SPECIFICATION**

This CLAUDE.md file provides complete context for implementing the TJRJ Precatórios scraper using Alternative 1 (API-based approach). Follow the step-by-step guide and test incrementally. Good luck! 🚀