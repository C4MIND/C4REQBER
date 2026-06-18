#!/usr/bin/env python3
"""
Translation quality scorer using NLLB-200 back-translation.
For each (lang, string) pair:
  1. Take HY-MT's translation T
  2. Back-translate T → EN using NLLB-200
  3. Compute char-F1 overlap between back-translated text and original EN source
  4. Flag translations with F1 < 0.55 as low-quality

Usage:
  python3 quality_score.py --i18n-dir ../ --output quality.json
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


NLLB_TO = {
    "en": "eng_Latn", "ru": "rus_Cyrl", "zh": "zho_Hans",
    "ja": "jpn_Jpan", "de": "deu_Latn", "ar": "arb_Arab", "hi": "hin_Deva",
}
LANG_FROM_EN = {  # for back-translation, we map src → EN
    "en": "eng_Latn", "ru": "rus_Cyrl", "zh": "zho_Hans",
    "ja": "jpn_Jpan", "de": "deu_Latn", "ar": "arb_Arab", "hi": "hin_Deva",
}


def parse_toml(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line and not line.startswith("["):
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            out[k] = v
    return out


def chrf_score(a: str, b: str) -> float:
    """chRF score (0-100). Per-language metric — works for both Latin and non-Latin."""
    if not a or not b:
        return 0.0
    return sacrebleu.sentence_chrf(b, [a]).score


def word_overlap(a: str, b: str) -> float:
    """Word-level F1. Don't filter stopwords — they're meaningful for short strings."""
    if not a or not b:
        return 0.0
    a_l = re.sub(r"[^a-z0-9 ]", " ", a.lower()).split()
    b_l = re.sub(r"[^a-z0-9 ]", " ", b.lower()).split()
    a_l = [w for w in a_l if w]
    b_l = [w for w in b_l if w]
    if not a_l or not b_l:
        return 0.0
    a_set = Counter(a_l)
    b_set = Counter(b_l)
    overlap = sum((a_set & b_set).values())
    if not overlap:
        return 0.0
    prec = overlap / sum(a_set.values())
    rec = overlap / sum(b_set.values())
    return 2 * prec * rec / (prec + rec)


def length_sanity(src_en: str, back_en: str) -> float:
    """Return 0-1 based on length ratio. 1.0 if similar, 0.0 if wildly different."""
    if not src_en or not back_en:
        return 0.0
    src_len = len(src_en.split())
    back_len = len(back_en.split())
    if src_len == 0 or back_len == 0:
        return 0.0
    ratio = min(src_len, back_len) / max(src_len, back_len)
    return ratio


def quality_score(src_en: str, back_en: str, tgt_native: str) -> float:
    """Combined quality score (0-1) using word_overlap + length sanity.
    For very short strings (<=3 words), rely on word_overlap.
    For longer strings, mix word_overlap + chRF + length."""
    wo = word_overlap(src_en, back_en)
    src_words = len(src_en.split())
    if src_words <= 3:
        return wo
    chrf = chrf_score(src_en, back_en) / 100.0
    ls = length_sanity(src_en, back_en)
    # 50% word overlap, 30% chRF, 20% length sanity
    return 0.5 * wo + 0.3 * chrf + 0.2 * ls


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--i18n-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--model", default="/Users/figuramax/.c4reqber/models/nllb-200")
    p.add_argument("--threshold", type=float, default=0.55,
                   help="F1 threshold below which translations are flagged")
    args = p.parse_args()

    i18n_dir = Path(args.i18n_dir)
    en = parse_toml(i18n_dir / "en.toml")

    print(f"Loading NLLB-200 from {args.model}...")
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model, dtype=torch.float16)
    print("Loaded.")

    def back_translate(text: str, src_lang: str) -> str:
        """Translate text in src_lang → English."""
        if src_lang == "en":
            return text
        tok.src_lang = NLLB_TO[src_lang]
        encoded = tok(text, return_tensors="pt", truncation=True, max_length=512)
        generated = model.generate(
            **encoded,
            forced_bos_token_id=tok.convert_tokens_to_ids("eng_Latn"),
            max_new_tokens=512,
        )
        return tok.decode(generated[0], skip_special_tokens=True)

    results = {}
    flagged = []
    total = 0
    flagged_count = 0

    for lang in ["ru", "zh", "ja", "de", "ar", "hi"]:
        print(f"\n=== Scoring {lang.upper()} ===")
        data = parse_toml(i18n_dir / f"{lang}.toml")
        results[lang] = {}
        for key, src_en in en.items():
            tgt = data.get(key, "")
            # Skip brand names and lang codes (verbatim)
            if tgt in ("C4REQBER v9", "DeepSeek", "EN", "RU", "ZH", "JA", "DE", "AR", "HI", "$0.00", "0,00 $", "0.00 $"):
                results[lang][key] = {"score": 1.0, "skip": "verbatim", "tgt": tgt}
                total += 1
                continue
            if not tgt:
                total += 1
                continue
            total += 1
            try:
                back = back_translate(tgt, lang)
                score = quality_score(src_en, back, tgt)
                results[lang][key] = {
                    "score": round(score, 3),
                    "back": back[:80],
                    "src": src_en,
                    "tgt": tgt,
                    "flag": "low" if score < args.threshold else "ok",
                }
                if score < args.threshold:
                    flagged.append({
                        "lang": lang, "key": key,
                        "score": round(score, 3),
                        "src": src_en, "tgt": tgt[:60], "back": back[:60],
                    })
                    flagged_count += 1
                    print(f"  ⚠ {key}: score={score:.2f} — '{tgt[:40]}' → '{back[:40]}'")
                else:
                    print(f"  ✓ {key}: score={score:.2f}")
            except Exception as e:
                print(f"  ERR {key}: {e}", file=sys.stderr)
                results[lang][key] = {"score": 0.0, "error": str(e)}

    summary = {
        "total": total,
        "flagged": flagged_count,
        "threshold": args.threshold,
        "results": results,
        "flagged_details": flagged,
    }
    Path(args.output).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n=== Summary ===")
    print(f"Total scored: {total}")
    print(f"Flagged: {flagged_count} ({100*flagged_count/max(1,total):.1f}%)")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
