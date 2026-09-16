# Yuri Code AI

Agente de IA para programação, desenvolvido por Yuri.

## Objetivo

Criar um assistente de programação capaz de entender projetos, analisar código, propor e executar alterações, rodar testes e ajudar no desenvolvimento de aplicações.

## Base tecnológica

A primeira versão será construída sobre o **OpenHands Software Agent SDK**, uma base open source para criação de agentes que trabalham com código. O SDK oferece APIs Python, TypeScript e REST e suporta agentes, ferramentas, conversas e workspaces. citeturn0search0

## Visão da V1

- Conversa com o agente
- Leitura de projetos
- Criação e edição de arquivos
- Execução de comandos
- Execução de testes
- Análise e correção de erros
- Contexto do projeto
- Integração futura com GitHub
- Interface web própria
- Controle antes de alterações destrutivas

## Estrutura inicial

```text
Yuri-Code-AI/
├── agent/
│   ├── __init__.py
│   └── main.py
├── config/
│   └── .env.example
├── tests/
├── .gitignore
├── README.md
└── pyproject.toml
```

## Desenvolvimento

O projeto será construído em etapas. Primeiro teremos um agente local funcional; depois adicionaremos a interface, GitHub, gerenciamento de projetos e recursos avançados.

## Princípio

A Yuri Code AI deve **entender antes de alterar**, explicar o que pretende fazer e priorizar alterações verificáveis por testes.
