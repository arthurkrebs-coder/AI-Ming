#!/usr/bin/env python3
"""Generate the Brazilian Portuguese PowerAim locale from the source English locale.

Requires: pip install deep-translator
Usage: python tools/translate_ptbr.py
The existing manual translations are preserved; missing entries are translated.
Never changes source keys or interpolated .NET placeholders.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "PowerAim/Localizations/Locale_en-US.json"
OUT = ROOT / "PowerAim/Localizations/Locale_pt-BR.json"
PH_RE = re.compile(r"\{\d+(?::[^{}]+)?\}")
URL_RE = re.compile(r"https?://[^\s\"']+")
PLACEHOLDER_RE = re.compile(r"\{\d+(?::[^{}]+)?\}")
# Exact English/technical labels which should be retained, not translated.
KEEP_AS_IS = {
    "FOV", "CUDA", "DirectML", "ONNX", "FPS", "OCR", "GPU", "CPU",
    "AutoPlay", "TensorRT", "Ollama", "ViGEm", "vJoy", "XInput",
    "DXGI", "EMA", "A", "B", "X", "Y", "x", "—", "-",
}


def signature(text: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(text))


def mask(text: str) -> tuple[str, dict[str, str]]:
    mapping = {}
    # Protect text-format tokens and URLs. Sentinels are intentionally uppercase.
    pat = re.compile(r"\{\d+(?::[^{}]+)?\}|https?://[^\s\"']+")
    def sub(m):
        token = f"ZZZPROTECT{len(mapping):03d}ZZZ"
        mapping[token] = m.group(0)
        return token
    return pat.sub(sub, text), mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    for token, orig in mapping.items():
        # Google sometimes inserts spaces in the sentinel.
        pieces = r"\s*".join(map(re.escape, list(token)))
        text = re.sub(pieces, lambda _m, v=orig: v, text, flags=re.I)
    if "ZZZPROTECT" in text.upper():
        raise ValueError("A protected token was not restored")
    return text


def run_translate(value: str, translator) -> str:
    protected, mapping = mask(value)
    result = translator.translate(protected)
    if not result:
        raise ValueError("Translator produced an empty answer")
    result = restore(result, mapping)
    if signature(value) != signature(result):
        # Try translating segments independently to guarantee .NET format strings.
        pieces = PH_RE.split(value)
        tokens = PH_RE.findall(value)
        translated = []
        for i, piece in enumerate(pieces):
            translated.append(translator.translate(piece) if piece.strip() else piece)
            if i < len(tokens):
                translated.append(tokens[i])
        result = "".join(translated)
    if signature(value) != signature(result):
        raise ValueError("Placeholder mismatch")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--attempts", type=int, default=5)
    p.add_argument("--minimum-success", type=float, default=0.95)
    args = p.parse_args()
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("Install first: pip install deep-translator", file=sys.stderr)
        return 2

    source = json.loads(SRC.read_text(encoding="utf-8-sig"))
    current = json.loads(OUT.read_text(encoding="utf-8-sig")) if OUT.exists() else {}
    if not isinstance(source, dict) or not isinstance(current, dict):
        raise ValueError("Unexpected locale JSON format")
    result = {k: v for k, v in current.items() if k in source and isinstance(v, str) and v.strip()}
    pending = [(k, v) for k, v in source.items() if k not in result and isinstance(v, str)]
    print(f"English entries: {len(source)} / manual entries: {len(result)} / to translate: {len(pending)}", flush=True)

    def worker(item):
        key, english = item
        if not english.strip() or english.strip() in KEEP_AS_IS:
            return key, english, None
        last_err = None
        for attempt in range(args.attempts):
            try:
                tr = GoogleTranslator(source="en", target="pt")
                candidate = run_translate(english, tr)
                if not candidate or signature(candidate) != signature(english):
                    raise ValueError("Invalid translated value")
                return key, candidate, None
            except Exception as exc:
                last_err = str(exc)
                time.sleep(min(25, 2 ** attempt + random.random()))
        return key, None, last_err

    errors = {}
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 5))) as pool:
        future_map = {pool.submit(worker, item): item[0] for item in pending}
        for i, fut in enumerate(as_completed(future_map), 1):
            key, translated, err = fut.result()
            if err is not None:
                errors[key] = err
            else:
                result[key] = translated
            if i % 50 == 0:
                print(f"Processed {i}/{len(pending)}; errors={len(errors)}", flush=True)
                # Checkpoint, so a partial locale is not lost on an interrupted run.
                ordered = {k: result[k] for k in source if k in result}
                OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ordered = {k: result[k] for k in source if k in result}
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    coverage = len(ordered) / len(source)
    print(f"Finished. pt-BR coverage: {len(ordered)}/{len(source)} = {coverage:.1%}; failures: {len(errors)}")
    if errors:
        for k, v in list(errors.items())[:30]:
            print(f"  {k}: {v}")
    if coverage < args.minimum_success:
        print("Translation coverage threshold not met; rerun the script to retry missing keys.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
