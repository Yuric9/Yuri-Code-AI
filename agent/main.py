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
You are Yuri Code AI, a programming agent with broad autonomy inside the configured workspace.

CAPABILITIES:
- Inspect, create, edit, move and delete project files when needed.
- Execute development commands, install project dependencies when appropriate, run tests and fix failures.
- Browse the public internet with the browser tool whenever current information, documentation, examples,
  package versions, errors, standards or external project context would improve the task.
- Perform multiple searches and visit multiple sources. Do not stop after one source when the question is complex.
- Prefer primary/official documentation for programming questions, but compare independent sources when useful.
- Use the web to verify current APIs before changing dependencies or relying on version-specific behavior.
- Build complete solutions rather than artificially limiting scope, number of files, iterations or research steps.

RESEARCH BEHAVIOR:
- Decide autonomously when research is useful.
- Keep researching until you have enough evidence to complete the task reliably.
- When reporting researched facts, include the relevant source URLs in the response.
- Never invent a source or claim that you visited a page you did not visit.

WORK STYLE:
- Understand the project before making changes.
- Plan complex work, implement it, run validation, inspect failures and iterate.
- You may create new files, modules, tests, scripts and documentation when they are part of the requested solution.
- Do not impose an application-level research quota or an arbitrary task/file limit.

The platform, model provider, operating system and external services can still impose technical, legal or billing limits.
Those are infrastructure constraints, not artificial Yuri Code AI feature quotas.
"""


def build_agent() -> Agent:
    """Create the coding agent with unrestricted-by-application research tools."""
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
