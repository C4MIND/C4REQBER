import { FormEvent, useCallback, useEffect, useState } from "react";

type Health = {
  status: string;
  version?: string;
  uptime_seconds?: number;
};

type Ready = {
  status: string;
  services?: Record<string, { status: string; error?: string | null }>;
};

type ToolInfo = {
  name: string;
  description: string;
  inputSchema?: Record<string, unknown>;
};

const API_BASE = import.meta.env.VITE_API_URL || "";

const MODES = [
  { value: "flash", label: "Flash", path: "/api/v8/discover/flash", body: (p: string, d: string) => ({ problem: p, domain: d }) },
  { value: "solve", label: "Solve", path: "/api/v8/discover/solve", body: (p: string, d: string) => ({ problem: p, domain: d }) },
  { value: "turbo", label: "Turbo", path: "/api/v8/discover/turbo", body: (p: string, _d: string) => ({ topic: p }) },
] as const;

type Mode = typeof MODES[number]["value"];

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [ready, setReady] = useState<Ready | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [problem, setProblem] = useState("How can we reduce CRISPR off-target effects?");
  const [domain, setDomain] = useState("science");
  const [mode, setMode] = useState<Mode>("flash");
  const [result, setResult] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [tools, setTools] = useState<ToolInfo[] | null>(null);
  const [toolsError, setToolsError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const [hRes, rRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/health`),
        fetch(`${API_BASE}/api/v1/health/ready`),
      ]);
      setHealth(hRes.ok ? await hRes.json() : { status: "error" });
      setReady(rRes.ok ? await rRes.json() : await rRes.json().catch(() => ({ status: "not_ready" })));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "API unreachable");
      setHealth(null);
      setReady(null);
    }
  }, []);

  const fetchTools = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/mcp/tools`);
      if (!res.ok) {
        // /api/v1/mcp/tools may not exist on this build — that's OK
        setToolsError(`MCP tools endpoint: HTTP ${res.status}`);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data.tools)) {
        setTools(data.tools as ToolInfo[]);
        setToolsError(null);
      }
    } catch (e) {
      setToolsError(e instanceof Error ? e.message : "MCP tools unreachable");
    }
  }, []);

  useEffect(() => {
    void fetchStatus();
    void fetchTools();
    const id = window.setInterval(() => void fetchStatus(), 15000);
    return () => window.clearInterval(id);
  }, [fetchStatus, fetchTools]);

  const selectedMode = MODES.find((m) => m.value === mode) ?? MODES[0];

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setResult("");
    try {
      const res = await fetch(`${API_BASE}${selectedMode.path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(selectedMode.body(problem, domain)),
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.detail ? JSON.stringify(body.detail) : `HTTP ${res.status}`);
      }
      if (body.job_id) {
        const polled = await pollJob(String(body.job_id));
        setResult(JSON.stringify(polled, null, 2));
      } else {
        setResult(JSON.stringify(body, null, 2));
      }
    } catch (err) {
      setResult(err instanceof Error ? err.message : `${selectedMode.label} failed`);
    } finally {
      setBusy(false);
    }
  }

  async function pollJob(jobId: string) {
    for (let i = 0; i < 45; i++) {
      const res = await fetch(`${API_BASE}/api/v8/discover/status/${jobId}`, {
        credentials: "include",
      });
      const data = await res.json();
      if (data.status === "complete" || data.status === "failed" || data.status === "partial") {
        return data;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    return { job_id: jobId, status: "timeout" };
  }

  return (
    <div className="app">
      <header>
        <h1>c4reqber Web v2</h1>
        <p>Discovery cockpit — health, readiness, multi-mode probe, MCP tool catalog</p>
      </header>

      <section className="panel">
        <h2>API status</h2>
        {error && <p className="status-error">{error}</p>}
        {!error && health && (
          <p>
            Health: <span className={health.status === "healthy" ? "status-ok" : "status-error"}>{health.status}</span>
            {health.version ? ` · v${health.version}` : ""}
            {health.uptime_seconds != null ? ` · uptime ${health.uptime_seconds}s` : ""}
          </p>
        )}
        {!error && ready && (
          <p>
            Ready: <span className={ready.status === "ready" ? "status-ok" : "status-error"}>{ready.status}</span>
          </p>
        )}
        <button type="button" onClick={() => void fetchStatus()}>
          Refresh
        </button>
      </section>

      <section className="panel">
        <h2>Discovery</h2>
        <form onSubmit={onSubmit}>
          <label>
            Mode
            <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
              {MODES.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </label>
          <label>
            Problem / Topic
            <textarea rows={4} value={problem} onChange={(e) => setProblem(e.target.value)} required />
          </label>
          <label>
            Domain
            <select value={domain} onChange={(e) => setDomain(e.target.value)}>
              <option value="science">science</option>
              <option value="engineering">engineering</option>
              <option value="business">business</option>
              <option value="humanities">humanities</option>
            </select>
          </label>
          <button type="submit" disabled={busy}>
            {busy ? `Running ${selectedMode.label}…` : `Run ${selectedMode.label}`}
          </button>
        </form>
        {result && (
          <pre style={{ marginTop: "1rem" }}>{result}</pre>
        )}
      </section>

      <section className="panel">
        <h2>MCP tool catalog</h2>
        {toolsError && (
          <p className="status-error">
            {toolsError}
            <br />
            <small>Backend does not expose /api/v1/mcp/tools. See <code>docs/mcp_registry.md</code> for the canonical 21-tool list.</small>
          </p>
        )}
        {tools && tools.length > 0 && (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {tools.map((t) => (
              <li key={t.name} style={{ marginBottom: "8px", padding: "8px", background: "rgba(255,255,255,.04)", borderRadius: "6px" }}>
                <code style={{ color: "#60a5fa" }}>{t.name}</code>
                {t.description && <span style={{ marginLeft: "8px", color: "var(--fg-3)" }}>{t.description}</span>}
              </li>
            ))}
          </ul>
        )}
        {!tools && !toolsError && <p style={{ color: "var(--fg-3)" }}>Loading tool catalog…</p>}
        <button type="button" onClick={() => void fetchTools()}>
          Refresh catalog
        </button>
      </section>
    </div>
  );
}