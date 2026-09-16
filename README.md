# Yuri Code AI

Agente autônomo de engenharia de software desenvolvido por Yuri.

## Fundação atual

- OpenHands para execução de programação.
- FastAPI + fila persistente + worker para tarefas longas.
- Recuperação de tarefas após reinício.
- Memória persistente e histórico de pesquisa.
- Indexação do workspace para contexto relevante.
- Pesquisa web integrada e Tavily opcional.
- Checkpoint Git antes de alterações quando possível.
- Quality gate com validação antes e depois da correção.
- Interface Next.js acompanhando tarefas.

A aplicação não cria quotas artificiais de pesquisas, arquivos ou iterações. Limites do modelo, provedor, sistema operacional, credenciais, serviços externos e cobrança continuam sendo limites de infraestrutura.

## Execução

```bash
yuri-code-ai-api
python -m agent.worker
```

Em produção, configure `YURI_API_RUN_LOCAL_WORKER=false` e mantenha o worker separado.

## API

- `GET /health`
- `POST /tasks`
- `GET /tasks/{id}`
- `POST /tasks/{id}/cancel`

## Próxima evolução

Streaming de eventos, GitHub/branches/PRs, revisão especializada, deploy/monitoramento e roteamento entre modelos.
