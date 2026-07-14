# Discoveries Directory

## Purpose

This directory bundles **new theorem discoveries** made during c4reqber sessions. Each discovery is a self-contained package with the theorem statement, associated hypotheses, and an initial proof attempt.

## Structure

Each discovery lives in its own directory:

```
discoveries/YYYY-MM-DD-theorem-name/
├── statement.md        -- Human-readable theorem statement
├── hypothesis.json     -- Structured hypotheses and metadata
└── proof_attempt.lean  -- Initial formal proof attempt (usually in Lean 4)
```

## Naming Convention

```
YYYY-MM-DD-theorem-name/
```

- `YYYY-MM-DD` — date of discovery
- `theorem-name` — kebab-case descriptive name

## Template Reference

See `YYYY-MM-DD-template/` for the expected bundle structure.
