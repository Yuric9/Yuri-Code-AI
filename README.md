# Yuri Code AI

Agente de IA para programação, desenvolvido por Yuri.

## Objetivo

A Yuri Code AI é um agente de programação com autonomia para pesquisar na internet, entender projetos, criar e editar código, executar comandos, testar, corrigir erros e continuar iterando até concluir uma tarefa.

## Capacidades atuais

- **Programação:** leitura, criação, edição e organização de arquivos.
- **Execução:** terminal, instalação de dependências, testes e comandos de desenvolvimento.
- **Pesquisa web:** navegador integrado e camada opcional Tavily com histórico persistente.
- **Memória persistente:** SQLite por padrão ou PostgreSQL configurável.
- **Contexto de projeto:** indexação de código/configuração/documentação e busca por relevância lexical antes da execução.
- **Orquestração:** tarefas persistentes com estado, fase, resultado, erro e cancelamento.
- **Worker:** processo separado que recupera tarefas interrompidas após reinício e continua drenando a fila.
- **Checkpoints:** criação de checkpoint Git local antes de alterações quando o workspace já é um repositório.
- **Quality gate:** validação inicial e final para projetos Python e Node quando os comandos padrão estão disponíveis.
- **Execução desacoplada:** a interface web cria uma tarefa e o backend Python pode executar o agente em segundo plano.
- **Iteração:** pode pesquisar, implementar, testar, analisar falhas e corrigir novamente.

## Política de capacidade

Não existe quota diária, mensal ou por conversa implementada pela Yuri Code AI. Também não existe um limite artificial de arquivos, pesquisas ou número de iterações por tarefa.

Isso não elimina limites externos do modelo/provedor, APIs, navegador, hospedagem, sistema operacional, serviços de terceiros, permissões ou cobrança.

## Arquitetura autônoma

```text
Next.js → FastAPI → fila persistente → Worker → OpenHands Agent
                                      │          │
                                      │          ├─ Files
                                      │          ├─ Terminal
                                      │          └─ Web
                                      │
                                      ├─ Project Index / Memory
                                      ├─ Git Checkpoint
                                      └─ Quality Gate
```

O estado da tarefa é salvo no banco. Se o worker for reiniciado, tarefas que estavam `running` retornam para `queued` e podem ser executadas novamente.

## Execução

Backend:

```bash
yuri-code-ai-api
```

ou:

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Worker:

```bash
python -m agent.worker
```

Em produção, configure `YURI_API_RUN_LOCAL_WORKER=false` e rode o worker como processo separado.

## API

- `GET /health`
- `POST /tasks`
- `GET /tasks/{id}`
- `POST /tasks/{id}/cancel`

## Banco e memória

O banco é inicializado automaticamente. Por padrão:

```text
.yuri-data/yuri_code_ai.db
```

A persistência cobre projetos, conversas, mensagens, memórias, pesquisas, tarefas e arquivos indexados.

## Pesquisa na internet

O agente pode navegar diretamente na web com o `BrowserToolSet`. Quando `TAVILY_API_KEY` estiver configurada, a camada de pesquisa adicional grava os resultados no histórico persistente.

## Configuração rápida

1. Copie `config/.env.example` para `.env`.
2. Configure `LLM_API_KEY` e `LLM_MODEL`.
3. Instale as dependências Python.
4. Defina `YURI_WORKSPACE` para o projeto que a IA poderá trabalhar.
5. Configure `AGENT_API_URL` para o backend Python usado pelo Next.js.
6. Opcionalmente configure `TAVILY_API_KEY`.
7. Execute a API e o worker.
8. Execute o frontend Next.js.

## Estado da fundação

A fundação autônoma está implementada em uma branch própria e em um pull request para `main`. A próxima evolução natural é streaming de eventos, integração GitHub/PR, revisão especializada, deploy/monitoramento e roteamento entre modelos.

## Princípio

A Yuri Code AI deve entender antes de alterar, pesquisar quando necessário, implementar de forma completa, testar o resultado e continuar corrigindo quando encontrar problemas.
