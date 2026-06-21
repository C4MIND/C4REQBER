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

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [ready, setReady] = useState<Ready | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [problem, setProblem] = useState("How can we reduce CRISPR off-target effects?");
  const [domain, setDomain] = useState("science");
  const [flashResult, setFlashResult] = useState<string>("");
  const [busy, setBusy] = useState(false);

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

  useEffect(() => {
    void fetchStatus();
    const id = window.setInterval(() => void fetchStatus(), 15000);
    return () => window.clearInterval(id);
  }, [fetchStatus]);

  async function onFlash(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFlashResult("");
    try {
      const res = await fetch(`${API_BASE}/api/v8/discover/flash`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ problem, domain }),
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.detail ? JSON.stringify(body.detail) : `HTTP ${res.status}`);
      }
      if (body.job_id) {
        const polled = await pollJob(String(body.job_id));
        setFlashResult(JSON.stringify(polled, null, 2));
      } else {
        setFlashResult(JSON.stringify(body, null, 2));
      }
    } catch (err) {
      setFlashResult(err instanceof Error ? err.message : "Flash failed");
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
        <p>Discovery cockpit — health, readiness, flash probe</p>
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
        <h2>Flash discovery</h2>
        <form onSubmit={onFlash}>
          <label>
            Problem
            <textarea rows={4} value={problem} onChange={(e) => setProblem(e.target.value)} required />
          </label>
          <label>
            Domain
            <select value={domain} onChange={(e) => setDomain(e.target.value)}>
              <option value="science">science</option>
              <option value="engineering">engineering</option>
              <option value="business">business</option>
            </select>
          </label>
          <button type="submit" disabled={busy}>
            {busy ? "Running…" : "Run flash"}
          </button>
        </form>
        {flashResult && (
          <pre style={{ marginTop: "1rem" }}>{flashResult}</pre>
        )}
      </section>
    </div>
  );
}