"use client";

import { FormEvent, useState } from "react";

type Message = { role: "user" | "ai"; text: string };

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);

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
      setMessages((current) => [...current, { role: "ai", text: data.message ?? "Não foi possível obter uma resposta." }]);
    } catch {
      setMessages((current) => [...current, { role: "ai", text: "A interface está pronta, mas o agente ainda precisa ser conectado ao backend." }]);
    } finally {
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
        <div className="project"><small>PROJETO ATUAL</small><strong>Nenhum projeto conectado</strong></div>
      </aside>

      <main className="main">
        <header className="header">
          <h1>Assistente de programação</h1>
          <span className="status">● Agente pronto</span>
        </header>

        <section className="content">
          {messages.length === 0 ? (
            <div className="hero">
              <h2>O que vamos programar?</h2>
              <p>Descreva uma tarefa. A Yuri Code AI vai analisar, criar, editar e testar o código.</p>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>{message.text}</div>
              ))}
              {busy && <div className="message ai">Analisando sua tarefa…</div>}
            </div>
          )}

          <form className="composer" onSubmit={sendMessage}>
            <textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ex.: analise meu projeto e encontre os erros..." />
            <div className="composer-footer">
              <span className="hint">Enter envia • Shift + Enter quebra linha</span>
              <button className="send" type="submit" disabled={busy}>{busy ? "Executando..." : "Enviar ↑"}</button>
            </div>
          </form>
        </section>
      </main>
    </div>
  );
}
