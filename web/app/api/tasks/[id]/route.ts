import { NextResponse } from "next/server";

const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://127.0.0.1:8000";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  try {
    const response = await fetch(`${AGENT_API_URL}/tasks/${encodeURIComponent(id)}`, { cache: "no-store" });
    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ message: "Backend do agente indisponível." }, { status: 503 });
  }
}
