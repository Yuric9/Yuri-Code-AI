# Yuri Code AI

Agente de IA para programação, desenvolvido por Yuri.

## Objetivo

A Yuri Code AI é um agente de programação com autonomia para pesquisar na internet, entender projetos, criar e editar código, executar comandos, testar, corrigir erros e continuar iterando até concluir uma tarefa.

## Capacidades atuais

- **Programação:** leitura, criação, edição e organização de arquivos.
- **Execução:** terminal, instalação de dependências, testes e comandos de desenvolvimento.
- **Pesquisa web:** navegador integrado para pesquisar sites, documentação, GitHub e outras fontes públicas.
- **Pesquisa adicional:** integração opcional com Tavily para buscas estruturadas e conteúdo extraído.
- **Memória persistente:** SQLite por padrão ou PostgreSQL configurável.
- **Banco de dados:** projetos, conversas, mensagens, memórias, histórico de pesquisas e tarefas.
- **Orquestração:** tarefas persistentes com estado, fase, resultado, erro e cancelamento.
- **Execução desacoplada:** a interface web cria uma tarefa e o backend Python executa o agente em segundo plano.
- **Iteração:** pode pesquisar, implementar, testar, analisar falhas e corrigir novamente.

## Política de capacidade

Não existe quota diária, mensal ou por conversa implementada pela Yuri Code AI. Também não existe um limite artificial de arquivos, pesquisas ou número de iterações por tarefa.

Isso **não** significa burlar limites externos. Modelo de IA, APIs, navegador, hospedagem, sistema operacional, serviços de terceiros e contas utilizadas podem possuir limites técnicos, de segurança ou de cobrança. A aplicação não adiciona uma quota própria por cima desses limites.

## Arquitetura autônoma

A V0.3 adiciona uma camada persistente entre a interface e o agente:

```text
Next.js
   │
   ▼
/api/chat ───────► FastAPI
                     │
                     ▼
               TaskOrchestrator
                     │
                     ▼
               OpenHands Agent
                 │   │   │
                 ▼   ▼   ▼
              Files Terminal Web
                     │
                     ▼
                  Workspace
```

O estado da tarefa é salvo no banco. A interface pode consultar `GET /tasks/{id}` e acompanhar a fase sem depender de uma única requisição HTTP longa.

### Iniciar o backend

```bash
yuri-code-ai-api
```

Ou:

```bash
uvicorn server.main:app --host 127.0.0.1 --port 8000
```

### API

- `GET /health` — verifica o serviço.
- `POST /tasks` — cria uma tarefa autônoma e retorna imediatamente com o ID.
- `GET /tasks/{id}` — consulta o estado e o resultado.
- `POST /tasks/{id}/cancel` — marca a tarefa como cancelada.

O Next.js usa `AGENT_API_URL` para encaminhar o chat para esse backend.

## Base tecnológica

O motor usa o **OpenHands Software Agent SDK**, que permite agentes de programação com ferramentas, workspaces e ferramentas personalizadas. O SDK também possui integração de navegador para navegar, interagir com páginas e extrair conteúdo.

## Banco e memória

O banco é inicializado automaticamente quando o agente inicia.

Por padrão:

```text
.yuri-data/yuri_code_ai.db
```

Para produção, configure `DATABASE_URL` com PostgreSQL. A camada de persistência separa projetos, conversas, mensagens, memórias, pesquisas e tarefas.

## Pesquisa na internet

A Yuri Code AI pode usar o `BrowserToolSet` do OpenHands para navegar diretamente na web. O próprio agente decide quando pesquisar, pode visitar várias páginas e extrair informações.

Também existe uma camada opcional com Tavily. O provedor externo pode aplicar seus próprios créditos e limites de conta.

## Configuração rápida

1. Copie `config/.env.example` para `.env`.
2. Configure `LLM_API_KEY` e `LLM_MODEL`.
3. Instale as dependências Python.
4. Defina `YURI_WORKSPACE` para o projeto que a IA poderá trabalhar.
5. Configure `AGENT_API_URL` para o backend Python usado pelo Next.js.
6. Opcionalmente configure `TAVILY_API_KEY`.
7. Execute `yuri-code-ai-api` e depois o frontend Next.js.

## Próximas camadas planejadas

A arquitetura agora permite evoluir sem depender do chat HTTP para cada passo. As próximas camadas naturais são: worker durável com recuperação após reinício, streaming de eventos, memória semântica/indexação do projeto, GitHub/branches/PRs, checkpoints e rollback, testes/revisão automáticos, deploy e monitoramento e, posteriormente, múltiplos agentes especializados.

## Princípio

A Yuri Code AI deve entender antes de alterar, pesquisar quando necessário, implementar de forma completa, testar o resultado e continuar corrigindo quando encontrar problemas.
