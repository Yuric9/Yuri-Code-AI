"use client";

import { FormEvent, useEffect, useState } from "react";

type Message = { role: "user" | "ai"; text: string };
type Task = { id: number; status: string; phase: string; result?: string | null; error?: string | null };
type EventItem = { id: number; phase: string; message: string; created_at: string };
type GitState = { branch: string; commit: string; dirty: boolean; changes: string[]; root: string };

const terminal = ["completed", "failed", "cancelled"];

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [task, setTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [git, setGit] = useState<GitState | null>(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState("chat");

  useEffect(() => {
    fetch("/api/git-status", { cache: "no-store" }).then(async (r) => r.ok && setGit(await r.json())).catch(() => undefined);
  }, []);

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
          fetch("/api/git-status", { cache: "no-store" }).then(async (r) => r.ok && setGit(await r.json())).catch(() => undefined);
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
    setView("chat");
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

  const nav = [
    ["chat", "⌘ Chat"],
    ["projects", "▣ Projetos"],
    ["files", "◫ Arquivos"],
    ["git", "⑂ Git"],
    ["settings", "⚙ Configurações"],
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><div className="logo">Y</div><div><strong>Yuri Code AI</strong><span>AI Coding Agent</span></div></div>
        <nav className="nav">{nav.map(([id, label]) => <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)}>{label}</button>)}</nav>
        <div className="project"><small>PROJETO ATUAL</small><strong>{task ? `Tarefa #${task.id}` : "Nenhuma tarefa ativa"}</strong><span>{git ? `${git.branch} · ${git.dirty ? "alterado" : "limpo"}` : "Git não conectado"}</span></div>
      </aside>

      <main className="main">
        <header className="header"><h1>{view === "chat" ? "Assistente de programação" : nav.find(([id]) => id === view)?.[1] ?? "Yuri Code AI"}</h1><span className="status">● {task ? `${task.status} · ${task.phase}` : "Agente pronto"}</span></header>
        <section className="content">
          {view === "chat" && <>
            {messages.length === 0 ? <div className="hero"><h2>O que vamos programar?</h2><p>Descreva uma tarefa. A Yuri Code AI cria uma tarefa persistente e executa o agente no workspace.</p></div> : <div className="messages">{messages.map((message, index) => <div key={index} className={`message ${message.role}`}>{message.text}</div>)}{busy && <div className="message ai">Executando autonomamente… {task?.phase ?? "iniciando"}</div>}{task && events.length > 0 && <div className="message ai"><strong>Execução</strong><div>{events.slice(-8).map((item) => <div key={item.id}>• {item.phase}: {item.message}</div>)}</div>{!terminal.includes(task.status) && <button type="button" onClick={cancelTask}>Solicitar cancelamento</button>}</div>}</div>}
            <form className="composer" onSubmit={sendMessage}><textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ex.: analise meu projeto e encontre os erros..." /><div className="composer-footer"><span className="hint">Fila persistente · memória · pesquisa · validação · Git</span><button className="send" type="submit" disabled={busy}>{busy ? "Executando..." : "Enviar ↑"}</button></div></form>
          </>}

          {view === "git" && <div className="panel"><h2>Estado do Git</h2>{git ? <><p><b>Branch:</b> {git.branch}</p><p><b>Commit:</b> {git.commit.slice(0, 12)}</p><p><b>Workspace:</b> {git.root}</p><p><b>Status:</b> {git.dirty ? `${git.changes.length} alteração(ões)` : "limpo"}</p>{git.changes.length > 0 && <div className="changes">{git.changes.map((change) => <div key={change}>{change}</div>)}</div>}</> : <p>O workspace ainda não está disponível ou não é um repositório Git.</p>}</div>}
          {view === "projects" && <div className="panel"><h2>Projetos</h2><p>O workspace configurado é o ambiente de execução do agente. A gestão de múltiplos projetos entra nesta área sem misturar repositórios.</p></div>}
          {view === "files" && <div className="panel"><h2>Arquivos</h2><p>O agente indexa o workspace e usa a busca persistente para localizar arquivos relevantes antes de executar tarefas.</p></div>}
          {view === "settings" && <div className="panel"><h2>Configurações</h2><p>Modelo, workspace, banco, pesquisa web e integrações Git são configurados por variáveis de ambiente no servidor do agente.</p></div>}
        </section>
      </main>
    </div>
  );
}
