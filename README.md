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
- Eventos persistentes de execução.
- Operações GitHub: clone, branch, commit, push e Pull Request via API quando configurado.
- Interface Next.js acompanhando tarefas.

Sem quotas artificiais de pesquisas, arquivos ou iterações. Limites externos de modelo, sistema, permissões, serviços e cobrança permanecem válidos.

## Execução

```bash
yuri-code-ai-api
python -m agent.worker
```

Produção: `YURI_API_RUN_LOCAL_WORKER=false` e worker separado.

## API

`GET /health` · `POST /tasks` · `GET /tasks/{id}` · `GET /tasks/{id}/events` · `POST /tasks/{id}/cancel`

## GitHub

Configure `GITHUB_TOKEN` somente no ambiente de execução quando a automação GitHub for necessária. O fluxo documentado está em `docs/GITHUB-AUTOMATION.md`.

## Próxima evolução

Revisão especializada, deploy/monitoramento, rollback automatizado, roteamento entre modelos e execução multiagente.
