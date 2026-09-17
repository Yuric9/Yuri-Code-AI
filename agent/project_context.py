"""Build concise, reusable project context for autonomous agent tasks."""
from __future__ import annotations

from .database import recall
from .project_index import index_project, search_project


def build_project_context(project_path: str, goal: str) -> str:
    """Refresh the index and return relevant files plus durable memories."""
    index_project(project_path)
    matches = search_project(project_path, goal, limit=12)
    memories = recall("project")
    lines = ["PROJECT CONTEXT", f"Workspace: {project_path}"]
    if memories:
        lines.append("Persistent memories:")
        for memory in memories[-20:]:
            lines.append(f"- {memory.key}: {memory.content}")
    if matches:
        lines.append("Relevant indexed files:")
        for match in matches:
            lines.append(f"\n--- {match.path} (score {match.score}) ---\n{match.excerpt}")
    else:
        lines.append("No indexed file matched the current goal; inspect the workspace directly.")
    return "\n".join(lines)
