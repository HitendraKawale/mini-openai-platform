import { useEffect, useRef, useState } from "react";
import { chatCompletion, getHealth, ragQuery, uploadDocument } from "./api.js";

const KEY_STORAGE = "mini-openai-api-key";

function Badge({ tone = "gray", children }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function RoutingBadges({ routing, model }) {
  if (!routing) {
    return model ? <Badge tone="blue">{model}</Badge> : null;
  }

  const tone =
    routing.decision === "routed_small"
      ? "green"
      : routing.decision === "routed_large"
        ? "amber"
        : "blue";

  return (
    <>
      <Badge tone="blue">{model}</Badge>
      <Badge tone={tone}>
        {routing.decision.replace("_", " ")}
        {routing.difficulty != null && ` · difficulty ${routing.difficulty}`}
      </Badge>
      {routing.fallback_used && <Badge tone="red">fallback</Badge>}
    </>
  );
}

function Sources({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <details className="sources">
      <summary>
        {sources.length} source{sources.length > 1 ? "s" : ""}
      </summary>
      {sources.map((source) => (
        <div className="source" key={source.chunk_id}>
          <div className="source-head">
            <span>{source.chunk_id}</span>
            <span>score {source.score.toFixed(3)}</span>
          </div>
          <p>{source.text}</p>
        </div>
      ))}
    </details>
  );
}

function Message({ message }) {
  if (message.role === "user") {
    return <div className="msg msg-user">{message.text}</div>;
  }

  if (message.role === "error") {
    return <div className="msg msg-error">{message.text}</div>;
  }

  if (message.role === "info") {
    return <div className="msg msg-info">{message.text}</div>;
  }

  const meta = message.meta || {};
  return (
    <div className="msg msg-assistant">
      <p className="answer">{message.text}</p>
      <div className="meta">
        {meta.cached === true && <Badge tone="green">⚡ semantic cache</Badge>}
        {meta.cached === false && <Badge tone="gray">generated</Badge>}
        <RoutingBadges routing={meta.routing} model={meta.model} />
        {meta.latencyMs != null && (
          <Badge tone="gray">{(meta.latencyMs / 1000).toFixed(2)}s</Badge>
        )}
      </div>
      <Sources sources={meta.sources} />
    </div>
  );
}

export default function App() {
  const [apiKey, setApiKey] = useState(
    () => localStorage.getItem(KEY_STORAGE) || "dev-secret-key"
  );
  const [mode, setMode] = useState("rag");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [healthy, setHealthy] = useState(null);
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(KEY_STORAGE, apiKey);
  }, [apiKey]);

  useEffect(() => {
    let cancelled = false;
    const check = () =>
      getHealth()
        .then((h) => !cancelled && setHealthy(h.status === "ok"))
        .catch(() => !cancelled && setHealthy(false));
    check();
    const interval = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const append = (message) => setMessages((prev) => [...prev, message]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;

    setInput("");
    append({ role: "user", text });
    setBusy(true);

    const started = performance.now();
    try {
      if (mode === "rag") {
        const result = await ragQuery({ apiKey, query: text });
        append({
          role: "assistant",
          text: result.answer,
          meta: {
            cached: result.cached,
            sources: result.sources,
            latencyMs: performance.now() - started,
          },
        });
      } else {
        const result = await chatCompletion({ apiKey, content: text });
        append({
          role: "assistant",
          text: result.choices[0].message.content,
          meta: {
            model: result.model,
            routing: result.routing,
            latencyMs: performance.now() - started,
          },
        });
      }
    } catch (err) {
      const hint =
        err.status === 401
          ? " — check the API key in the top bar"
          : err.status === 429
            ? " — rate limited, slow down"
            : "";
      append({ role: "error", text: `${err.message}${hint}` });
    } finally {
      setBusy(false);
    }
  }

  async function onUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setBusy(true);
    try {
      const result = await uploadDocument({ apiKey, file });
      append({
        role: "info",
        text: `Indexed ${result.filename} as ${result.document_id} (${result.chunk_count} chunks). Semantic cache invalidated.`,
      });
    } catch (err) {
      append({ role: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <div className="brand">
          <span
            className={`dot ${healthy == null ? "dot-unknown" : healthy ? "dot-ok" : "dot-bad"}`}
            title={healthy ? "gateway healthy" : "gateway unreachable"}
          />
          <h1>Mini OpenAI Platform</h1>
        </div>
        <div className="controls">
          <div className="mode">
            <button
              className={mode === "rag" ? "active" : ""}
              onClick={() => setMode("rag")}
            >
              RAG
            </button>
            <button
              className={mode === "chat" ? "active" : ""}
              onClick={() => setMode("chat")}
            >
              Chat
            </button>
          </div>
          <input
            className="key"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API key"
            title="API key (stored in this browser only)"
          />
        </div>
      </header>

      <main>
        {messages.length === 0 && (
          <div className="empty">
            <p>
              {mode === "rag"
                ? "Upload a document, then ask questions about it. Watch answers come back with sources — and instantly when the semantic cache recognises a paraphrase."
                : "Ask anything. Easy questions are routed to a small model, hard ones to a larger one — every answer shows the routing verdict."}
            </p>
          </div>
        )}
        {messages.map((message, i) => (
          <Message key={i} message={message} />
        ))}
        {busy && <div className="msg msg-info pulse">thinking…</div>}
        <div ref={bottomRef} />
      </main>

      <footer>
        <button
          className="upload"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          title="Upload a document for RAG"
        >
          + doc
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.md,.pdf"
          hidden
          onChange={onUpload}
        />
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={mode === "rag" ? "Ask about your documents…" : "Ask anything…"}
          disabled={busy}
        />
        <button className="send" onClick={send} disabled={busy || !input.trim()}>
          Send
        </button>
      </footer>
    </div>
  );
}
