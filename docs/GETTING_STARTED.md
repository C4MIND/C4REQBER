---
layout: default
---

<link rel="stylesheet" href="assets/css/style.css">

# Getting Started with c4reqber

## 1. Installation

```bash
pip install c4reqber
```

Requires Python 3.10+.

Verify the installation:

```bash
c4reqber --version  # should print 5.4.1
```

Run the interactive configuration wizard:

```bash
c4reqber init
```

## 2. Quick Commands

| Command | What it does |
|---------|-------------|
| `c4reqber solve "problem"` | One-shot discovery pipeline |
| `c4reqber solve "problem" --mode deep-work` | Full verification + proof export |
| `c4reqber solve "problem" --mode turbo` | Fast parallel execution |
| `c4reqber tui --cyberpunk` | Full-screen cyberpunk TUI |
| `c4reqber serve --mcp` | Start MCP server for AI agents |
| `c4reqber verify --backend lean4 theorem.lean` | Formal proof verification |

## 3. MCP Server Setup

c4reqber can be used as an MCP tool for AI agents (Claude, Cursor, etc.). Add it to your MCP configuration:

```json
// mcp-config.json
{
  "mcpServers": {
    "c4reqber": {
      "command": "python3",
      "args": ["-m", "c4reqber", "serve", "--mcp"]
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `c4_solve` | Run 10-step discovery pipeline |
| `c4_search` | Search 27 knowledge sources |
| `c4_triz` | Resolve contradictions via 40 TRIZ principles |
| `c4_verify` | Formal proof checking (Lean4/Coq/Dafny/Agda/Hoare) |
| `c4_simulate` | Physics simulation (4 engines: Newton/TorchSim/JaxSim/vast.ai) |
| `c4_bayesian` | Bayesian inference (MCMC/BMA) |
| `c4_causal` | Causal discovery (do-calculus) |
| `c4_fingerprint` | C4 state classification (Z₃³, 27 states) |
| `c4_export` | Export discovery to LaTeX or Markdown |
| `c4_transfer` | Cross-domain structural isomorphism transfer |
| `c4_autoresearch` | Autonomous multi-step research loop |
| `c4_chain` | Multi-hop reasoning chain construction |
| `c4_meta` | Meta-cognitive reflection on reasoning |

## 4. Authentication (Zero-PII)

c4reqber supports four authentication methods with **no personal data collection**.

### 4.1 Anonymous (default)

No registration. A UUID is generated locally.

```bash
c4reqber init --auth anon
```

### 4.2 Web3 (MetaMask)

```bash
c4reqber init --auth web3
```

Scan the QR code or connect MetaMask, then sign the message: `c4reqber login: {nonce}`.

### 4.3 Telegram

```bash
c4reqber init --auth telegram
```

Open `@c4reqber_bot` and click **Login**, or use the Telegram Login Widget on the web.

### 4.4 GitLab

```bash
c4reqber init --auth gitlab
```

OAuth2 via GitLab. Stores only `gitlab_id` and `username` — public data. No email required.

### 4.5 Supabase (cloud sync)

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
c4reqber init --auth supabase
```

## 5. API Keys (BYOK)

c4reqber requires your own API keys for external services:

| Service | Env Var | What for |
|---------|---------|----------|
| OpenRouter | `OPENROUTER_API_KEY` | LLM inference (15+ providers) |
| Tavily | `TAVILY_API_KEY` | Web search |
| Exa | `EXA_API_KEY` | Neural search |
| LM Studio | `LM_STUDIO_HOST` | Local LLM (MLX) |
| NVIDIA | `NVIDIA_API_KEY` | Cloud GPU |

Add them to your shell profile:

```bash
# ~/.bashrc or ~/.zshrc
export OPENROUTER_API_KEY="sk-or-..."
export TAVILY_API_KEY="tvly-..."
export EXA_API_KEY="exa-..."
export LM_STUDIO_HOST="http://localhost:1234"
export NVIDIA_API_KEY="nvapi-..."
```

Then reload: `source ~/.bashrc` or `source ~/.zshrc`.

## 6. Sending Results to Telegram

After generating a paper, proof, or report, send it directly to your Telegram:

```bash
# Export and send
c4reqber export --format latex --send-telegram

# Or after solve
c4reqber solve "..." --notify-telegram
```

Requires `TELEGRAM_BOT_TOKEN` and your Telegram ID configured during `c4reqber init`.

## 7. Buying Credits

### 7.1 Crypto (NOWPayments)

```bash
c4reqber credits buy --method crypto --amount 50
```

Select USDT, TON, or BTC. Send to the generated address. Credits are credited automatically once confirmed.

### 7.2 Card (Robokassa)

```bash
c4reqber credits buy --method card --amount 1000
```

You will be redirected to Robokassa to complete payment, then returned to c4reqber.

## 7. Docker

```bash
docker pull ghcr.io/c4reqber/c4reqber:latest
docker run -it --rm \
  -e OPENROUTER_API_KEY="..." \
  -e TAVILY_API_KEY="..." \
  c4reqber solve "your problem"
```

## 8. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'c4reqber'` | `pip install c4reqber` |
| `API key not set` error | Set env vars or use `--local` mode |
| TUI shows garbled characters | Use `--layout minimal` or increase terminal width to 80+ |
| Verification fails | Check backend is installed (`lean4 --version`, `coqc --version`, etc.) |
| MCP connection refused | Ensure `c4reqber serve --mcp` is running |
| Balance shows zero | Press `[B]` in TUI or run `c4reqber credits status` |

---

## Next Steps

- Read the [API Reference](API.md)
- Browse the [Formal Proofs](formal-proofs/)
- Run `c4reqber --help` for all commands
- Open the TUI: `c4reqber tui --cyberpunk`
