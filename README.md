# Yuri Code AI

Agente autônomo de engenharia de software desenvolvido por Yuri.

## Fundação atual

- OpenHands para programação.
- FastAPI + fila persistente + worker.
- Recuperação após reinício.
- Memória persistente e histórico de pesquisa.
- Indexação do workspace para contexto relevante.
- Pesquisa web integrada e Tavily opcional.
- Checkpoint Git antes de alterações quando possível.
- Quality gate com validação antes e depois da correção.
- Interface Next.js acompanhando tarefas.

Sem quotas artificiais de pesquisas, arquivos ou iterações. Limites externos de modelo, sistema, permissões, serviços e cobrança permanecem válidos.

## Execução

```bash
yuri-code-ai-api
python -m agent.worker
```

Produção: `YURI_API_RUN_LOCAL_WORKER=false` e worker separado.

## API

`GET /health` · `POST /tasks` · `GET /tasks/{id}` · `POST /tasks/{id}/cancel`

## Próxima evolução

Streaming de eventos, GitHub/branches/PRs, revisão especializada, deploy/monitoramento e roteamento entre modelos.
