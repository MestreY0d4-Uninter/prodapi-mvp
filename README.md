# ProdAPI

API de produtividade para automações com execução sob demanda e agendamento via cron.

> **Desenvolvido com Claude Code** — Este projeto foi construído utilizando [Claude Code](https://claude.ai/code), aplicando técnicas de *vibe coding* com foco em qualidade, tipagem estrita e cobertura de testes.

## Características

- **Autenticação via API Keys** (SHA-256, criar/revogar)
- **CRUD de Automações** com validação de configuração por tipo
- **Execução Assíncrona** com lifecycle (queued → running → success/failed)
- **Idempotência** via `X-Idempotency-Key` header
- **Agendamento Cron** com suporte a timezones (APScheduler)
- **Histórico de Runs** com paginação cursor-based
- **Webhooks** com retry automático e backoff exponencial
- **2 Automações Built-in:**
  - **daily_digest**: Resume execuções do sistema e envia para webhook
  - **github_monitor**: Monitora repositórios GitHub e alerta sobre novos eventos

## Stack Tecnológica

- **Python 3.12+** com tipagem estrita (`mypy` + `pyright`)
- **FastAPI** para API async
- **SQLAlchemy 2.x** async ORM com `Mapped[]`
- **Alembic** para migrações
- **APScheduler 3.x** para cron jobs
- **PostgreSQL** (produção) / **SQLite** (dev/testes)
- **Docker + docker-compose**

## Qualidade

Todos os checks de qualidade passam:
- ✅ **ruff** (linting + imports)
- ✅ **mypy** (tipagem strict)
- ✅ **pyright** (tipagem strict)
- ✅ **pytest** (34 testes)
- ✅ **coverage** (84% branch coverage)
- ✅ **deptry** (dependências)
- ✅ **pip-audit** (vulnerabilidades)

## Início Rápido

### Com Docker (Recomendado)

```bash
# Subir aplicação + Postgres
docker compose up -d

# Verificar health
curl http://localhost:8000/health
```

### Desenvolvimento Local

```bash
# Instalar dependências
uv sync --dev

# Rodar migrações
uv run alembic upgrade head

# Iniciar servidor
uv run uvicorn prodapi.app:app --reload

# Rodar testes
uv run pytest -v

# Verificar cobertura
uv run coverage run --branch -m pytest
uv run coverage report -m
```

## Uso da API

### 1. Criar API Key

```bash
curl -X POST http://localhost:8000/apikeys \
  -H "Content-Type: application/json" \
  -d '{"label":"my-key"}'

# Resposta:
{
  "api_key": {"id": "...", "label": "my-key", ...},
  "raw_key": "HJd0MJGtzNRPPlEOUz9gHk7MTHvESpvWWSS1951uK9A"
}
```

⚠️ **Guarde a `raw_key`** — ela só aparece uma vez!

### 2. Criar Automação

```bash
curl -X POST http://localhost:8000/automations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: HJd0MJGtzNRPPlEOUz9gHk7MTHvESpvWWSS1951uK9A" \
  -d '{
    "name": "Daily Summary",
    "type": "daily_digest",
    "config_json": {
      "webhook_url": "https://your-webhook.com/hook",
      "timezone": "America/Sao_Paulo",
      "only_failures": true
    }
  }'
```

### 3. Executar Manualmente

```bash
curl -X POST http://localhost:8000/automations/{automation_id}/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: HJd0MJGtzNRPPlEOUz9gHk7MTHvESpvWWSS1951uK9A" \
  -d '{
    "idempotency_key": "unique-key-123"
  }'
```

### 4. Agendar Execução (Cron)

```bash
curl -X PUT http://localhost:8000/automations/{automation_id}/schedule \
  -H "Content-Type: application/json" \
  -H "X-API-Key: HJd0MJGtzNRPPlEOUz9gHk7MTHvESpvWWSS1951uK9A" \
  -d '{
    "cron": "0 9 * * *",
    "timezone": "America/Sao_Paulo"
  }'
```

### 5. Listar Runs

```bash
curl http://localhost:8000/runs?status=failed&limit=10 \
  -H "X-API-Key: HJd0MJGtzNRPPlEOUz9gHk7MTHvESpvWWSS1951uK9A"
```

## Configuração de Automações

### daily_digest

Resume execuções do sistema e envia para webhook.

```json
{
  "webhook_url": "https://example.com/webhook",  // obrigatório
  "timezone": "UTC",                             // default: UTC
  "title": "Daily Digest",                       // default: "Daily Digest"
  "runs_window_hours": 24,                       // default: 24
  "only_failures": false,                        // default: false
  "format": "json",                              // "json" | "text"
  "max_items": 50                                // default: 50
}
```

**Payload do webhook:**
```json
{
  "event": "run.completed",
  "automation_id": "...",
  "run_id": "...",
  "status": "success",
  "type": "daily_digest",
  "summary": {
    "title": "Daily Digest",
    "period_start": "2026-02-10T20:00:00Z",
    "period_end": "2026-02-11T20:00:00Z",
    "total_runs": 42,
    "success": 40,
    "failed": 2,
    "failures": [...]
  }
}
```

### github_monitor

Monitora repositório GitHub por novos eventos.

```json
{
  "repo": "owner/name",                          // obrigatório
  "events": ["issues", "pulls", "releases", "commits"],
  "github_token": "ghp_...",                     // recomendado (evita rate limit)
  "webhook_url": "https://example.com/webhook"   // obrigatório
}
```

**Anti-duplicação:** O estado (`state`) é mantido automaticamente no `config_json` e armazena cursores por tipo de evento.

**Payload do webhook:**
```json
{
  "event": "run.completed",
  "type": "github_monitor",
  "summary": {
    "repo": "owner/name",
    "checked_at": "2026-02-11T20:00:00Z",
    "new_items": [
      {
        "type": "issues",
        "title": "Bug fix",
        "url": "https://github.com/owner/name/issues/123",
        "author": "username",
        "created_at": "2026-02-11T19:30:00Z"
      }
    ],
    "counts_by_type": {"issues": 1}
  }
}
```

## Estrutura do Projeto

```
novo_projeto/
├── prodapi/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # FastAPI endpoints
│   ├── services/        # Lógica de negócio
│   ├── automations/     # Executores de automações
│   ├── app.py           # FastAPI app factory
│   ├── config.py        # Configurações
│   └── database.py      # SQLAlchemy setup
├── alembic/             # Migrações
├── tests/               # Testes (34 testes, 84% coverage)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Variáveis de Ambiente

```bash
DATABASE_URL=sqlite+aiosqlite:///./prodapi.db  # ou postgresql+asyncpg://...
ENVIRONMENT=development                         # development | production
LOG_LEVEL=INFO                                  # DEBUG | INFO | WARNING | ERROR
```

## Documentação Interativa

Após iniciar o servidor:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Desenvolvimento

### Rodar Checks de Qualidade

```bash
# Todos os checks
uv run --with ruff ruff check .
uv run --with mypy mypy .
uv run --with pyright pyright
uv run --with coverage coverage run --branch -m pytest
uv run --with coverage coverage report -m
uv run --with deptry deptry .
uv run --with pip-audit pip-audit
```

### Criar Nova Migração

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Limitações Conhecidas

- Rate limiting não implementado (recomendado adicionar via middleware)
- Fila robusta (Redis/Celery) não incluída — runs executam via `asyncio.create_task()`
- Multi-tenancy limitado a API keys (sem organizações)

## Licença

MIT

---

**Desenvolvido com transparência:** Este projeto foi criado utilizando [Claude Code](https://claude.ai/code) da Anthropic, seguindo práticas modernas de desenvolvimento assistido por IA com foco em qualidade, testes e código legível.
