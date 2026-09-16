"""Entry point for the first Yuri Code AI coding agent."""

from __future__ import annotations

import os
from pathlib import Path

from openhands.sdk import Agent, Conversation, LLM, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool


def build_agent() -> Agent:
    """Create the initial coding agent with safe project tools."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("Defina LLM_API_KEY antes de iniciar a Yuri Code AI.")

    model = os.getenv("LLM_MODEL", "gpt-5.5")

    llm = LLM(model=model, api_key=api_key)

    return Agent(
        llm=llm,
        tools=[
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
        ],
    )


def main() -> None:
    """Run a local interactive coding session."""
    workspace = Path(os.getenv("YURI_WORKSPACE", ".")).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    agent = build_agent()
    conversation = Conversation(agent=agent, workspace=str(workspace))

    print("Yuri Code AI iniciada.")
    print(f"Workspace: {workspace}")
    print("Digite uma tarefa de programação. Ctrl+C para sair.\n")

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
