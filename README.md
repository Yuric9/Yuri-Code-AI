# Yuri Code AI

Agente de IA para programação, desenvolvido por Yuri.

## Capacidades atuais

- Programação, terminal, dependências e testes.
- Pesquisa web com navegador e Tavily opcional, com histórico persistente.
- Memória persistente em SQLite ou PostgreSQL.
- Indexação do workspace e recuperação de contexto relevante antes de cada tarefa.
- Fila persistente, worker separado e recuperação após reinício.
- Checkpoint Git local antes de alterações quando o workspace é um repositório.
- Quality gate com validação inicial e final.
- API FastAPI e interface Next.js para acompanhar tarefas.

## Autonomia

Não existe quota diária, mensal ou por conversa implementada pela Yuri Code AI, nem limite artificial de arquivos, pesquisas ou iterações. Isso não elimina limites externos do modelo/provedor, APIs, sistema operacional, permissões, serviços de terceiros ou cobrança.

## Arquitetura

```text
Next.js → FastAPI → fila persistente → Worker → OpenHands Agent
                                      │          ├─ Files
                                      │          ├─ Terminal
                                      │          └─ Web
                                      ├─ Project Index / Memory
                                      ├─ Git Checkpoint
                                      └─ Quality Gate
```

## Execução

```bash
yuri-code-ai-api
python -m agent.worker
```

Em produção, configure `YURI_API_RUN_LOCAL_WORKER=false` e rode o worker separadamente.

## API

- `GET /health`
- `POST /tasks`
- `GET /tasks/{id}`
- `POST /tasks/{id}/cancel`

## Próximas camadas

Streaming de eventos, GitHub/branches/PRs, revisão especializada, deploy/monitoramento e roteamento entre modelos.
