# Windows flash / packaging acceptance checklist

For external testers on Windows 10+ with `pip install c4reqber` (post v9.20 / Zero-Asymmetry honesty lock).

## Prerequisites

1. `python -m pip install -U c4reqber`
2. Put keys in `%USERPROFILE%\.c4reqber\secrets.env` (at least an LLM key; `TAVILY_API_KEY` recommended)
3. Confirm: `where blast` → Scripts\blast.exe
4. Optional backend for TUI Flash: local API on `C4_API_URL` (default `http://127.0.0.1:8000`) with same `secrets.env`

## Flash --sources (AISI 440C) — CLI

```cmd
blast flash --sources "find exactly one real peer reviewed publication specifically about cryogenic treatment of AISI 440C steel"
```

**Pass if:**

- [ ] Does **not** crash with `flash gather failed: 'int' object is not iterable` (post-fix: `search_all` returns `sources_used` as int count — flash must use `source_names` / `source_names_from_result`)
- [ ] Log does **not** show PubChem / ClinicalTrials / UCI ML / HF datasets errors for this query
- [ ] Domain line mentions `materials_science` (or similar lit domain)
- [ ] `tavily=on` if key present, else `tavily=no_key` (not silent mystery / not always `off` when Tavily is in allowlist)
- [ ] Optional: `dedup=lexical_fallback` when `sentence-transformers` missing — quiet note, not a hard failure
- [ ] Answer does **not** say “unable to identify / not found” when verified ≥ 1
- [ ] Sources (verified) show full title + DOI and/or URL — only CitationVerifier-confirmed rows
- [ ] Unverified raw hits (if any) are labeled **not counted**
- [ ] Footer: `Search providers:` lists adapter ids when hits exist (not `(none)` solely due to gather TypeError)
- [ ] Footer: `N verified sources` matches verified cards only (status-aware: `flash success` / `flash partial`, not always “complete”)
- [ ] No `example.com` URLs; no AFLOW/PubChem spray errors for this materials query
- [ ] No `UnicodeEncodeError: 'charmap'` on PowerShell for mascot/Rich output (UTF-8 reconfigure + ASCII glyph fallback)
- [ ] On OpenRouter **429**: rotates or ends `partial` + `rate_limited` warning — never empty success

## TUI Flash (composed API — same contract as CLI)

Same question in TUI **Flash** mode against local API (`POST /v8/discover/flash` → composed `run_flash` + C4 + TRIZ + optional hypothesis).

**Pass if:**

- [ ] Answer card + verified source cards render when `verified_count ≥ 1`
- [ ] Optional hypothesis card when composer generated one from verified context
- [ ] C4/TRIZ framing present when composer attached them (not gutted to bare Q&A)
- [ ] Terminal `partial` → **no** celebration burst; `toast.partial` (not `toast.complete`)
- [ ] Terminal `success` with verified ≥ 1 **may** celebrate (burst + `toast.complete`)
- [ ] SSE job terminal event type matches `result.status` (`complete` only when success)

## Live Windows AISI 440C gate (W10)

- [x] **WAIVED 2026-07-22 by maintainer** — no Windows VM / reinstall energy available on Mac now; ship code + PyPI; external tester may re-run checklist later on real Win without blocking this release
- [ ] (optional later) live log from Windows tester: TUI Flash **and/or** CLI with sanitized log
- [ ] (optional later) Log shows materials allowlist, tavily visibility, verified≥1 **or** honest partial
- [ ] (optional later) No celebration on partial in TUI recording

## Packaging smoke

```cmd
blast config --health
blast setup --help
blast tui --help
```

**Pass if:**

- [ ] `config --health` prints key health (non-empty)
- [ ] `setup` does not fail with `unknown command "pip"`
- [ ] `tui` resolves or downloads `c4tui-v9.exe` (or clear error how to fix) — not bare WinError 2 with no hint
- [ ] `blast packages remove --id <installed_pkg>` exits non-zero when pip uninstall fails (honest returncode)

## Out of scope for this checklist

Corporate proxy / SSL interception (document in INSTALL only), DSM / other products’ `blast` shims.

**Note:** Landing `discoveries/files/*.md` may still contain legacy `scholar.google.com/scholar?q=` URLs in demo bibliographies — they are **not** counted as verified citations in product paths.
