import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const message = typeof body.message === "string" ? body.message.trim() : "";

  if (!message) {
    return NextResponse.json({ message: "Envie uma tarefa para o agente." }, { status: 400 });
  }

  // V1: endpoint preparado para o backend Python/OpenHands.
  // A próxima integração substituirá esta resposta pela execução real do agente.
  return NextResponse.json({
    message: `Recebi sua tarefa: “${message}”. A interface está conectada ao endpoint /api/chat; agora vamos ligar este endpoint ao agente OpenHands.`,
  });
}
