# Yuri Code AI

Agente autônomo de engenharia de software desenvolvido por Yuri.

## Fundação atual

- OpenHands para programação.
- FastAPI + fila persistente + worker desacoplado.
- Recuperação após reinício.
- Memória persistente e histórico de pesquisa.
- Indexação persistente do workspace para contexto relevante.
- Pesquisa web via Tavily quando configurada.
- Checkpoint Git local antes da execução.
- Quality gate adaptativo com validação inicial e final.
- Cancelamento cooperativo entre etapas da execução.
- Eventos persistentes de ciclo de vida por tarefa.
- Interface Next.js acompanhando tarefas.

A aplicação não impõe quotas artificiais de pesquisas, arquivos ou iterações. Limites externos de modelo, sistema operacional, credenciais, serviços e cobrança continuam sendo infraestrutura.

## Execução

```bash
yuri-code-ai-api
python -m agent.worker
```

Para produção, prefira `YURI_API_RUN_LOCAL_WORKER=false` e um worker separado.

## API

- `GET /health`
- `POST /tasks`
- `GET /tasks/{id}`
- `GET /tasks/{id}/events`
- `POST /tasks/{id}/cancel`

Os eventos são persistidos no banco e podem alimentar streaming no frontend sem depender de memória do processo.

## Próxima evolução

Integração explícita com GitHub (clone/branch/commit/PR), streaming em tempo real, revisão especializada, deploy/monitoramento e roteamento entre modelos.
