import { NextResponse } from "next/server";

const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const message = typeof body.message === "string" ? body.message.trim() : "";
  const workspace = typeof body.workspace === "string" ? body.workspace.trim() : undefined;

  if (!message) {
    return NextResponse.json({ message: "Envie uma tarefa para o agente." }, { status: 400 });
  }

  try {
    const response = await fetch(`${AGENT_API_URL}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, workspace }),
      cache: "no-store",
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return NextResponse.json({ message: data.detail ?? "O backend do agente recusou a tarefa." }, { status: response.status });
    }

    return NextResponse.json({ task: data });
  } catch {
    return NextResponse.json(
      { message: "Não foi possível conectar ao backend Python. Inicie o servidor da Yuri Code AI API." },
      { status: 503 },
    );
  }
}
