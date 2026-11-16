# ASCOM WhatsApp Channel Automation

Sistema de automação para captura e publicação de notícias e editais do portal oficial da **UENF (Universidade Estadual do Norte Fluminense Darcy Ribeiro)** diretamente no Canal Oficial de WhatsApp da ASCOM.

O projeto consome o feed RSS do portal da UENF, filtra publicações inéditas utilizando o **Supabase (PostgreSQL)** para controle de idempotência (evitando duplicatas) e realiza o disparo formatado com imagem e resumo através do **WAHA (WhatsApp HTTP API)** utilizando a engine leve **GOWS**.

---

## Arquitetura e Tecnologias

- **Backend / Orquestrador:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.14+)
- **Integração WhatsApp:** [WAHA (`devlikeapro/waha:gows`)](https://waha.devlike.pro/)
- **Banco de Dados & Storage:** [Supabase](https://supabase.com/) (persistência de posts enviados, imagens padrão e sessão PostgreSQL do WAHA)
- **Extração e Parsing:** `feedparser` + `BeautifulSoup4` + `httpx`
- **Gerenciador de Pacotes:** [uv](https://docs.astral.sh/uv/)
- **Infraestrutura / Deploy:** Docker (container unificado FastAPI + WAHA) & [Fly.io](https://fly.io/)

---

## Estrutura do Projeto

```text
.
├── src/
│   └── backend/
│       ├── main.py            # Rotas da API FastAPI (/ e /sync) e autenticação
│       ├── dependencies.py    # Inicialização do cliente assíncrono do Supabase
│       └── services/
│           ├── db.py          # Consultas e inserções de posts enviados no Supabase
│           └── messages.py    # Leitura do RSS, formatação e envio para o WAHA
├── Dockerfile                 # Imagem unificada (WAHA GOWS + Python/FastAPI via uv)
├── entrypoint.sh              # Script de inicialização simultânea (WAHA + Uvicorn)
├── docker-compose.yml         # Ambiente local isolado para a instância do WAHA
├── fly.toml                   # Configuração de deploy para o Fly.io
└── pyproject.toml             # Dependências e metadados do projeto Python
```

---

## Como Executar Localmente

### Pré-requisitos
- [uv](https://docs.astral.sh/uv/) instalado
- [Docker](https://www.docker.com/) e Docker Compose instalados

### 1. Subir a instância do WAHA
```bash
docker compose up -d
```
Acesse `http://localhost:3000/dashboard` para autenticar a sessão do WhatsApp.

### 2. Instalar dependências e rodar a API FastAPI
```bash
uv sync
uv run fastapi dev src/backend/main.py --port 8000
```

---

## Endpoints da API

### `GET /`
Verifica a saúde da API e a conectividade com o banco de dados no Supabase.
- **Resposta (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "services": {
      "api": "healthy",
      "database": "healthy"
    }
  }
  ```

### `POST /sync`
Aciona a leitura do feed RSS da UENF, filtra notícias ainda não registradas na tabela `posts` do Supabase, envia para o canal do WhatsApp via WAHA e persiste os IDs enviados.
- **Autenticação obrigatória:** Header `Authorization: Bearer <CRON_SECRET>`
- **Exemplo de chamada:**
  ```bash
  curl -X POST http://localhost:8000/sync \
    -H "Authorization: Bearer seu_token_secreto"
  ```
