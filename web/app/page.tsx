"use client";

import { FormEvent, useEffect, useState } from "react";

type Message = { role: "user" | "ai"; text: string };
type Task = { id: number; status: string; phase: string; result?: string | null; error?: string | null };
type EventItem = { id: number; phase: string; message: string; created_at: string };

const terminal = ["completed", "failed", "cancelled"];

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [task, setTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!task) return;
    const timer = window.setInterval(async () => {
      const [statusResponse, eventsResponse] = await Promise.all([
        fetch(`/api/task-status?id=${task.id}`, { cache: "no-store" }),
        fetch(`/api/task-events?id=${task.id}`, { cache: "no-store" }),
      ]);
      if (statusResponse.ok) {
        const data = await statusResponse.json();
        setTask(data);
        if (terminal.includes(data.status)) {
          setBusy(false);
          if (data.result) setMessages((current) => [...current, { role: "ai", text: data.result }]);
          if (data.error) setMessages((current) => [...current, { role: "ai", text: `Erro: ${data.error}` }]);
        }
      }
      if (eventsResponse.ok) setEvents(await eventsResponse.json());
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
    setEvents([]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message ?? "Falha ao criar tarefa");
      setTask(data.task);
      setMessages((current) => [...current, { role: "ai", text: `Tarefa #${data.task.id} iniciada.` }]);
    } catch (error) {
      setMessages((current) => [...current, { role: "ai", text: error instanceof Error ? error.message : "Não foi possível iniciar a tarefa." }]);
      setBusy(false);
    }
  }

  async function cancelTask() {
    if (!task || terminal.includes(task.status)) return;
    await fetch(`/api/task-cancel?id=${task.id}`, { method: "POST" });
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
              {task && events.length > 0 && (
                <div className="message ai">
                  <strong>Execução</strong>
                  <div>{events.slice(-8).map((item) => <div key={item.id}>• {item.phase}: {item.message}</div>)}</div>
                  {!terminal.includes(task.status) && <button type="button" onClick={cancelTask}>Solicitar cancelamento</button>}
                </div>
              )}
            </div>
          )}

          <form className="composer" onSubmit={sendMessage}>
            <textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ex.: analise meu projeto e encontre os erros..." />
            <div className="composer-footer">
              <span className="hint">Fila persistente · memória · pesquisa · validação · eventos</span>
              <button className="send" type="submit" disabled={busy}>{busy ? "Executando..." : "Enviar ↑"}</button>
            </div>
          </form>
        </section>
      </main>
    </div>
  );
}
