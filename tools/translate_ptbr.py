#!/usr/bin/env python3
"""Complete PowerAim's pt-BR locale with the offline Argos English->Brazilian model.

Install: pip install argostranslate
Run:     python tools/translate_ptbr.py
A model is downloaded automatically on first run. Existing manual translations
are preserved. No original English locale entries or source keys are changed.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "PowerAim/Localizations/Locale_en-US.json"
TARGET_PATH = ROOT / "PowerAim/Localizations/Locale_pt-BR.json"
PROTECTED = re.compile(r"(\{\d+(?::[^{}]+)?\}|https?://[^\s\"']+)")
PLACEHOLDERS = re.compile(r"\{\d+(?::[^{}]+)?\}")
EXACT_TECHNICAL = {
    "FOV", "CUDA", "DirectML", "ONNX", "FPS", "OCR", "GPU", "CPU",
    "AutoPlay", "TensorRT", "Ollama", "ViGEm", "vJoy", "XInput",
    "DXGI", "EMA", "A", "B", "X", "Y", "x", "—", "-", "T", "F",
}


def get_brazilian_translator():
    import argostranslate.package
    import argostranslate.translate
    packages = argostranslate.package
    engine = argostranslate.translate

    def installed():
        langs = engine.get_installed_languages()
        en = next((x for x in langs if x.code == "en"), None)
        pb = next((x for x in langs if x.code == "pb"), None)
        if en is None or pb is None:
            return None
        return en.get_translation(pb)

    tr = installed()
    if tr is None:
        print("Downloading offline English -> Portuguese (Brazil) model...", flush=True)
        packages.update_package_index()
        model = next((x for x in packages.get_available_packages()
                      if x.from_code == "en" and x.to_code == "pb"), None)
        if model is None:
            raise RuntimeError("The Argos package index has no en -> pb model")
        packages.install_from_path(model.download())
        tr = installed()
    if tr is None:
        raise RuntimeError("Unable to load the Argos en -> pb translation")
    return tr


def translate_safe(text: str, translator):
    """Translate only unprotected segments; preserve .NET placeholders and URLs exactly."""
    if not text.strip() or text.strip() in EXACT_TECHNICAL:
        return text
    sections = PROTECTED.split(text)
    result = []
    for segment in sections:
        if not segment or PROTECTED.fullmatch(segment) or not segment.strip():
            result.append(segment)
        else:
            translated = translator.translate(segment)
            if not isinstance(translated, str) or not translated.strip():
                raise ValueError("Empty translated segment")
            result.append(translated)
    output = "".join(result)
    if sorted(PLACEHOLDERS.findall(text)) != sorted(PLACEHOLDERS.findall(output)):
        raise ValueError("Placeholder mismatch")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite-machine", action="store_true",
                        help="Do not use until after a human review of existing translations")
    args = parser.parse_args()

    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8-sig"))
    existing = json.loads(TARGET_PATH.read_text(encoding="utf-8-sig")) if TARGET_PATH.exists() else {}
    if not isinstance(source, dict) or not isinstance(existing, dict):
        raise ValueError("Unexpected JSON structure")
    translator = get_brazilian_translator()

    # Preserve hand-edited translations and restore exact original key order.
    pt = {}
    failed = {}
    for idx, (key, english) in enumerate(source.items(), 1):
        if not isinstance(english, str):
            raise TypeError(f"Expected string: {key}")
        if key in existing and isinstance(existing[key], str) and existing[key].strip():
            translated = existing[key]
        else:
            try:
                translated = translate_safe(english, translator)
            except Exception as exc:
                failed[key] = str(exc)
                continue
        if sorted(PLACEHOLDERS.findall(english)) != sorted(PLACEHOLDERS.findall(translated)):
            failed[key] = "Existing translation has mismatched placeholders"
            continue
        pt[key] = translated
        if idx % 100 == 0:
            print(f"{idx}/{len(source)} entries processed", flush=True)
            TARGET_PATH.write_text(json.dumps(pt, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")

    TARGET_PATH.write_text(json.dumps(pt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Complete: {len(pt)}/{len(source)}; missing: {len(failed)}")
    if failed:
        for k, why in failed.items():
            print(f"  {k}: {why}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
