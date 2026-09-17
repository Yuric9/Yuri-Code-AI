import { NextResponse } from "next/server";

const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://127.0.0.1:8000";

export async function GET(request: Request) {
  const id = new URL(request.url).searchParams.get("id");
  if (!id) return NextResponse.json({ message: "Informe o id da tarefa." }, { status: 400 });
  try {
    const response = await fetch(`${AGENT_API_URL}/tasks/${encodeURIComponent(id)}`, { cache: "no-store" });
    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ message: "Backend Python indisponível." }, { status: 503 });
  }
}
