# 🔥 FireWatch Orbital

**Monitoramento de queimadas em tempo real com dados orbitais da NASA FIRMS**

Sistema web que integra dados de satélites (NOAA, SNPP, Aqua, Terra) para detectar e monitorar focos de queimadas na América Latina, com foco no Brasil. Dashboard interativo com mapa em tempo real, estatísticas agregadas e alertas por nível de criticidade.

---

## 🚀 Início Rápido

### Pré-requisitos
- **Python 3.11+**
- **NASA FIRMS API Key** → [Obter em https://firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov)

### Instalação Local

#### 1. Clone e configure o ambiente
```bash
git clone <seu-repo>
cd FireWatchOrbital

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env com sua chave NASA API
```

#### 2. Executar a aplicação
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

---

## 🐳 Docker

### Build e run
```bash
docker build -t firewatch .
docker run -e NASA_API_KEY=your_key -p 8000:8000 firewatch
```

---

## 📚 Estrutura do Projeto

```
FireWatchOrbital/
├── app/                           # Código fonte da aplicação
│   ├── __init__.py
│   ├── main.py                    # FastAPI app & rotas
│   ├── config.py                  # Configurações (Pydantic Settings)
│   ├── models.py                  # Schemas Pydantic
│   ├── constants.py               # Constantes (estados, biomas, bounds)
│   └── services/
│       ├── __init__.py
│       ├── nasa_firms.py          # Integração NASA FIRMS
│       ├── fire_classifier.py     # Classificação de alertas
│       └── geo_utils.py           # Utilitários geográficos
├── templates/                     # Templates HTML
│   └── index.html                 # Dashboard
├── static/                        # Assets estáticos
│   ├── css/
│   └── js/
├── .github/workflows/             # CI/CD (GitHub Actions)
│   └── deploy.yml
├── main.py                        # Entry point (wrapper)
├── requirements.txt               # Dependências produção
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔌 API Endpoints

### Health Check
```http
GET /health
```
**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2026-06-02T10:30:45.123456",
  "version": "1.0.0",
  "nasa_key_configured": true
}
```

### Listar Focos de Queimada
```http
GET /api/fires?days=5&confidence=high&min_frp=100
```

**Parâmetros:**
- `days` (int, 1-5): Dias históricos [default: 5]
- `confidence` (string): "low" | "nominal" | "high" [opcional]
- `min_frp` (float): FRP mínimo em MW [default: 0]

**Resposta:**
```json
{
  "total": 245,
  "data_source": "nasa_firms",
  "period_days": 5,
  "fires": [
    {
      "id": 1,
      "latitude": -15.5432,
      "longitude": -47.2134,
      "brightness": 345.2,
      "frp": 234.5,
      "confidence": "high",
      "biome": "Cerrado",
      "state": "GO",
      "alert_level": "high",
      "acq_date": "2026-06-02",
      "acq_time": "1430",
      "satellite": "NOAA-20",
      "source": "nasa_firms"
    }
  ],
  "updated_at": "2026-06-02T10:30:45.123456"
}
```

### Estatísticas Agregadas
```http
GET /api/stats
```

**Resposta:**
```json
{
  "total_fires": 245,
  "data_source": "nasa_firms",
  "avg_frp": 156.3,
  "max_frp": 789.4,
  "critical_count": 12,
  "high_count": 45,
  "by_biome": {
    "Cerrado": 89,
    "Amazônia": 67,
    "Caatinga": 45
  },
  "by_alert": {
    "critical": 12,
    "high": 45,
    "medium": 98,
    "low": 90
  },
  "by_satellite": {
    "NOAA-20": 120,
    "SNPP": 85,
    "Aqua": 40
  },
  "top_states": {
    "GO": 45,
    "MT": 38,
    "BA": 32
  },
  "by_day": {
    "2026-06-02": 45,
    "2026-06-01": 56
  },
  "updated_at": "2026-06-02T10:30:45.123456"
}
```

### Debug NASA FIRMS
```http
GET /api/debug
```
Mostra a resposta bruta da API NASA para diagnóstico.

---

## 🛠️ Desenvolvimento

### Lint & Format
```bash
# Format com Black
black app/

# Lint com Ruff
ruff check app/

# Type check com MyPy
mypy app/
```

### Executar com hot-reload
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 Características

### 🗺️ Dashboard Interativo
- **Mapa em tempo real** com Leaflet.js
- **Marcadores de queimada** coloridos por nível de alerta
- **Filtros dinâmicos** (dias, confiança, FRP mínimo)
- **Popup com detalhes** ao clicar em marcador

### 📈 Gráficos Interativos
- **Focos por bioma** (doughnut chart)
- **Série temporal** (últimos 7 dias)
- **Top 5 estados** (bar chart)

### 🚨 Alertas
Classificação automática por FRP (Fire Radiative Power):
- 🔴 **CRÍTICO**: FRP ≥ 300 MW
- 🟠 **ALTO**: FRP ≥ 100 MW
- 🟡 **MÉDIO**: FRP ≥ 30 MW
- 🟢 **BAIXO**: FRP < 30 MW

### 🌍 Dados Geográficos
- Detecção automática de **estado** por coordenadas
- Inferência de **bioma dominante** por estado
- Suporte aos **27 estados brasileiros**
- 6 biomas principais

### 📡 Fallback Inteligente
Se NASA FIRMS estiver indisponível, sistema:
- Gera dados sintéticos realistas
- Mantém aplicação funcionando
- Loga o motivo da falha

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# Obrigatório
NASA_API_KEY=your_api_key_here

# Opcional
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
HOST=0.0.0.0            # Host do servidor
PORT=8000               # Porta
```

---

## 🔒 Segurança

- ✅ **CORS habilitado** (análise de produção recomendada)
- ✅ **API Key protegida** (nunca exibida em logs públicos)
- ✅ **Input validation** com Pydantic
- ✅ **Type hints** para segurança estática
- ⚠️ **HTTPS recomendado** em produção (use reverse proxy)

---

## 📦 Dependências

### Produção
- **FastAPI 0.111+**: Framework web assíncrono
- **Uvicorn 0.29+**: ASGI server
- **Pydantic 2+**: Validação de dados
- **httpx 0.27+**: Cliente HTTP assíncrono
- **python-dotenv 1+**: Carregamento de .env

### Desenvolvimento
- **Black 24+**: Formatter de código
- **Ruff 0.5+**: Linter rápido
- **MyPy 1.11+**: Type checker

---

## 🚀 Deploy

### Azure App Service
```bash
# Configurar secrets no GitHub
# - AZURE_CREDENTIALS
# - AZURE_APP_NAME
# - NASA_API_KEY

# Push para main dispara deploy automático
git push origin main
```

Ver `.github/workflows/deploy.yml` para detalhes.

### Heroku (alternativa)
```bash
heroku login
heroku create firewatch-orbital
heroku config:set NASA_API_KEY=your_key
git push heroku main
```

---

## 📝 Logs

Logs estruturados com timestamp:
```
2026-06-02 10:30:45,123 [INFO] firewatch - Chamando NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/...***KEY***
2026-06-02 10:30:47,456 [INFO] firewatch - NASA FIRMS respondeu 15234 chars
2026-06-02 10:30:47,890 [INFO] firewatch - NASA FIRMS: 234 focos carregados
```

---

## 🤝 Contribuindo

1. Fork o repositório
2. Crie branch feature (`git checkout -b feature/nova-feature`)
3. Commit mudanças (`git commit -am 'Add nova feature'`)
4. Push para branch (`git push origin feature/nova-feature`)
5. Abra Pull Request

---

## 📄 Licença

Projeto licenciado sob MIT License.

---

## 🔗 Recursos

- **NASA FIRMS**: https://firms.modaps.eosdis.nasa.gov
- **FastAPI**: https://fastapi.tiangolo.com
- **Leaflet.js**: https://leafletjs.com
- **Chart.js**: https://www.chartjs.org

---

## 📧 Suporte

Para dúvidas ou problemas, abra uma **issue** no repositório.

---

**Última atualização**: junho/2026
