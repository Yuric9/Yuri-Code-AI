import { NextRequest, NextResponse } from "next/server";

const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const id = request.nextUrl.searchParams.get("id");
  if (!id) return NextResponse.json({ message: "id é obrigatório" }, { status: 400 });
  try {
    const response = await fetch(`${AGENT_API_URL}/tasks/${encodeURIComponent(id)}/cancel`, { method: "POST" });
    const body = await response.text();
    return new NextResponse(body, { status: response.status, headers: { "content-type": "application/json" } });
  } catch {
    return NextResponse.json({ message: "Backend do agente indisponível" }, { status: 502 });
  }
}
