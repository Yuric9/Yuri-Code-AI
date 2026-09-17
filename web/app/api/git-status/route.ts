import { NextResponse } from "next/server";

export async function GET() {
  const base = process.env.AGENT_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/git/status`, { cache: "no-store" });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ detail: "API do agente indisponível" }, { status: 503 });
  }
}
