#!/usr/bin/env python3
"""
HY-MT1.5-1.8B translation pipeline for TUI v9.
Reads EN source strings, translates to 6 languages (RU/ZH/JA/DE/AR/HI)
using HY-MT1.5-1.8B via mlx-lm with glossary intervention.

Usage:
    python3 translate_hymt.py --src en.toml --glossary c4_science_terms.json
                              --out-dir ./src/tui/v9/i18n/   # or $HOME/.../c4reqber/... 
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from mlx_lm import load, generate

LANG_MAP = {
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "de": "German",
    "ar": "Arabic",
    "hi": "Hindi",
}

# HY-MT1.5-1.8B chat template format
# Tencent HY-MT expects: <|start|>role: system\n...role: user\n...role: assistant\n<|end|>
def build_prompt(src_text: str, target_lang: str, glossary: dict) -> list:
    """Build chat messages for HY-MT with glossary intervention."""
    relevant_glossary = {}
    src_lower = src_text.lower()
    for term, translations in glossary.items():
        if term.lower() in src_lower or any(t.lower() in src_lower for t in translations.values() if t):
            relevant_glossary[term] = translations.get(target_lang, "")

    # Glossary in system prompt
    glossary_text = ""
    if relevant_glossary:
        glossary_lines = [f"{term}={trans}" for term, trans in relevant_glossary.items() if trans]
        if glossary_lines:
            glossary_text = "Terms: " + ", ".join(glossary_lines) + ". "

    system = (
        f"Translate English → {LANG_MAP[target_lang]}. "
        f"NEVER prefix with 'Translation:' or similar. "
        f"NEVER echo the source. "
        f"Output ONLY the translated text, no quotes. "
        f"{glossary_text}"
    )
    user = src_text
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_toml(filepath: Path) -> dict:
    """Parse flat or sectioned TOML. Flat keys (with dots) go in '_root' section."""
    result = {}
    current = "_root"
    result[current] = {}
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            if current not in result:
                result[current] = {}
        elif "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            result[current][key] = val
    return result


def write_toml(out_path: Path, sections: dict):
    """Write flat TOML preserving dotted keys."""
    lines = []
    for section, kv in sections.items():
        for k, v in kv.items():
            v_esc = v.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{k} = "{v_esc}"')
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="Path to en.toml")
    p.add_argument("--out-dir", required=True, help="Output dir for ru/zh/ja/de/ar/hi.toml")
    p.add_argument("--glossary", required=True, help="c4_science_terms.json")
    default_model = os.path.expanduser("~/.c4reqber/models/hy-mt")
    p.add_argument("--model", default=default_model, help="HY-MT1.5-1.8B MLX path")
    p.add_argument("--max-tokens", type=int, default=512)
    args = p.parse_args()

    print(f"Loading HY-MT1.5-1.8B from {args.model}...")
    t0 = time.time()
    model, tokenizer = load(args.model)
    print(f"  loaded in {time.time() - t0:.1f}s")

    print(f"Loading glossary from {args.glossary}...")
    glossary = json.loads(Path(args.glossary).read_text(encoding="utf-8"))
    print(f"  {len(glossary)} terms")

    src = parse_toml(Path(args.src))
    total_keys = sum(len(kv) for kv in src.values())
    print(f"Loaded {total_keys} keys in {len(src)} sections from {args.src}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for lang in ["ru", "zh", "ja", "de", "ar", "hi"]:
        print(f"\n=== Translating to {lang.upper()} ({LANG_MAP[lang]}) ===")
        translated = {}
        t0 = time.time()
        for section, kv in src.items():
            translated[section] = {}
            for key, val in kv.items():
                # Special case: app.lang should be the lang code itself
                if key == "app.lang":
                    translated[section][key] = lang.upper()
                    print(f"  [{lang}] {key} = {lang.upper()} (lang code)")
                    continue
                # Use existing translation as seed if present
                messages = build_prompt(val, lang, glossary)
                try:
                    prompt_text = tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                    out = generate(
                        model,
                        tokenizer,
                        prompt=prompt_text,
                        max_tokens=args.max_tokens,
                        verbose=False,
                    )
                    out_clean = out.strip().strip('"').strip("'").strip()
                    # Take only the first line of output (HY-MT sometimes continues)
                    if "\n" in out_clean:
                        out_clean = out_clean.split("\n")[0].strip()
                    # Strip "Translation:" / "Übersetzung:" / etc. prefixes
                    for prefix in ["Translation:", "Übersetzung:", "Перевод:", "翻訳:",
                                   "翻译:", "ترجمة:", "अनुवाद:", "번역:"]:
                        if out_clean.startswith(prefix):
                            out_clean = out_clean[len(prefix):].strip()
                    # If the source is a lang code (2 uppercase letters) — keep verbatim
                    if val.upper() in ("EN", "RU", "ZH", "JA", "DE", "AR", "HI") and len(val) <= 3:
                        out_clean = val
                    # If source is brand / version, keep verbatim
                    elif "DeepSeek" in val or "C4REQBER" in val:
                        out_clean = val
                    # Reject garbage (echoed prompt, "NEVER" rules, etc.)
                    elif (out_clean.startswith("NEVER ") or out_clean.startswith("الإنجليزية")
                          or "Translation:" in out_clean or "Перевод:" in out_clean
                          or "。" in out_clean[:8] or "します" in out_clean[:8]
                          or "应当" in out_clean[:8] or "应" in out_clean[:5]
                          or len(out_clean) > 200):
                        out_clean = val
                    if not out_clean:
                        out_clean = val
                    translated[section][key] = out_clean
                    print(f"  [{lang}] {key} = {out_clean[:60]}")
                except Exception as e:
                    print(f"  [{lang}] {key} FAILED: {e}", file=sys.stderr)
                    translated[section][key] = val
        elapsed = time.time() - t0
        out_path = out_dir / f"{lang}.toml"
        write_toml(out_path, translated)
        print(f"  -> wrote {out_path} ({total_keys} keys, {elapsed:.1f}s)")

    print("\n✓ All 6 languages translated")


if __name__ == "__main__":
    main()
