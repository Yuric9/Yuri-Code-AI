"""Entry point for Yuri Code AI with coding, browser research and persistence."""

from __future__ import annotations

import os
from pathlib import Path

from openhands.sdk import Agent, Conversation, LLM, Tool
from openhands.tools.browser_use import BrowserToolSet
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool

from .database import init_db


RESEARCH_INSTRUCTIONS = """
You are Yuri Code AI, an autonomous software engineering agent.

CAPABILITIES:
- Inspect, create, edit, move and delete project files inside the configured workspace.
- Execute commands, install dependencies, run tests and fix failures.
- Research the public internet whenever current information, documentation, examples, package versions,
  errors, standards or external project context would improve reliability.
- Perform as many research steps and source comparisons as the task requires; there is no application quota.
- Prefer official/primary documentation for programming questions and verify version-specific APIs.
- Use persistent project context supplied by the orchestrator, but verify important details directly in the workspace.
- Preserve reversible work when Git is available and validate changes before declaring completion.

WORK STYLE:
- Understand the existing project before changing it.
- Plan complex work, implement it, test it, inspect failures and iterate until the task is actually complete.
- Create supporting tests, scripts, documentation and modules when they are part of a robust solution.
- Never fabricate sources, test results, files or completed actions.

INFRASTRUCTURE NOTE:
Yuri Code AI has no artificial application-level limit on research, files or iterations. Model providers,
operating systems, permissions, external services and billing can still impose infrastructure constraints.
"""


def build_agent() -> Agent:
    """Create the coding agent with broad research and engineering tools."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("Defina LLM_API_KEY antes de iniciar a Yuri Code AI.")

    model = os.getenv("LLM_MODEL", "gpt-5.5")
    llm = LLM(model=model, api_key=api_key, base_url=os.getenv("LLM_BASE_URL"))

    return Agent(
        llm=llm,
        tools=[
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
            Tool(name=BrowserToolSet.name),
        ],
        system_message_suffix=RESEARCH_INSTRUCTIONS,
    )


def main() -> None:
    """Run a local interactive coding session."""
    init_db()
    workspace = Path(os.getenv("YURI_WORKSPACE", ".")).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    agent = build_agent()
    conversation = Conversation(agent=agent, workspace=str(workspace))

    print("Yuri Code AI iniciada.")
    print(f"Workspace: {workspace}")
    print("Pesquisa web: ATIVA")
    print("Banco/memória: ATIVOS")
    print("Sem limite artificial de pesquisas, arquivos ou iterações. Ctrl+C para sair.\n")

    while True:
        try:
            request = input("Você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nYuri Code AI encerrada.")
            break
        if not request:
            continue
        conversation.send_message(request)
        conversation.run()
        print("\nTarefa processada.\n")


if __name__ == "__main__":
    main()
