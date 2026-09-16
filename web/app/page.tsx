"use client";

import { FormEvent, useEffect, useState } from "react";

type Message = { role: "user" | "ai"; text: string };
type Task = { id: number; status: string; phase: string; result?: string | null; error?: string | null };

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [task, setTask] = useState<Task | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!task || ["completed", "failed", "cancelled"].includes(task.status)) return;
    const timer = window.setInterval(async () => {
      const response = await fetch(`/api/task-status?id=${task.id}`, { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      setTask(data);
      if (["completed", "failed", "cancelled"].includes(data.status)) {
        setBusy(false);
        if (data.result) setMessages((current) => [...current, { role: "ai", text: data.result }]);
        if (data.error) setMessages((current) => [...current, { role: "ai", text: `Erro: ${data.error}` }]);
      }
    }, 1200);
    return () => window.clearInterval(timer);
  }, [task]);

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;

    setMessages((current) => [...current, { role: "user", text }]);
    setInput("");
    setBusy(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message ?? "Falha ao criar tarefa");
      setTask(data.task);
      setMessages((current) => [...current, { role: "ai", text: `Tarefa #${data.task.id} iniciada. Fase: ${data.task.phase}.` }]);
    } catch (error) {
      setMessages((current) => [...current, { role: "ai", text: error instanceof Error ? error.message : "Não foi possível iniciar a tarefa." }]);
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">Y</div>
          <div><strong>Yuri Code AI</strong><span>AI Coding Agent</span></div>
        </div>
        <nav className="nav">
          <button className="active">⌘ Chat</button>
          <button>▣ Projetos</button>
          <button>◫ Arquivos</button>
          <button>⑂ Git</button>
          <button>⚙ Configurações</button>
        </nav>
        <div className="project"><small>PROJETO ATUAL</small><strong>{task ? `Tarefa #${task.id}` : "Nenhuma tarefa ativa"}</strong></div>
      </aside>

      <main className="main">
        <header className="header">
          <h1>Assistente de programação</h1>
          <span className="status">● {task ? `${task.status} · ${task.phase}` : "Agente pronto"}</span>
        </header>

        <section className="content">
          {messages.length === 0 ? (
            <div className="hero">
              <h2>O que vamos programar?</h2>
              <p>Descreva uma tarefa. A Yuri Code AI cria uma tarefa persistente e executa o agente no workspace.</p>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>{message.text}</div>
              ))}
              {busy && <div className="message ai">Executando autonomamente… {task?.phase ?? "iniciando"}</div>}
            </div>
          )}

          <form className="composer" onSubmit={sendMessage}>
            <textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ex.: analise meu projeto e encontre os erros..." />
            <div className="composer-footer">
              <span className="hint">A tarefa é persistida e pode ser recuperada pelo worker.</span>
              <button className="send" type="submit" disabled={busy}>{busy ? "Executando..." : "Enviar ↑"}</button>
            </div>
          </form>
        </section>
      </main>
    </div>
  );
}
