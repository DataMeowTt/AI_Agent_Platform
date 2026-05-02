import re
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
QUERY_AGENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = QUERY_AGENT_DIR.parents[1]

SCAN_FILES = [
    QUERY_AGENT_DIR / "configs/question_templates.v1.json",
    QUERY_AGENT_DIR / "configs/indicator_catalog.v1.json",
    QUERY_AGENT_DIR / "configs/country_catalog.v1.json",
    QUERY_AGENT_DIR / "configs/alias_generation_rules.v1.json",
    REPO_ROOT / "services/ai-agent-service/app/catalog/indicator_catalog.py",
    REPO_ROOT / "services/ai-agent-service/app/resolver/country_resolver.py",
    REPO_ROOT / "services/ai-agent-service/app/composer/template_composer.py",
    REPO_ROOT / "services/ai-agent-service/app/composer/gemini_composer.py",
    REPO_ROOT / "server/src/indicators/indicators.service.ts",
]

MOJIBAKE_LITERALS = [
    "d? li?u",
    "ch? s?",
    "qu?c",
    "k?t",
    "d??i",
    "d?ng",
    "hi?n",
    "n? công",
    "l?m phát",
    "th?t nghi?p",
    "t?ng tr",
    "kh?ng ho?ng",
    "c?nh báo",
    "r?i ro",
    "phân t?ch",
    "xu h??ng",
]
MOJIBAKE_MARKERS = [
    "Ã",
    "Â²",
    "Ä",
    "á»",
    "áº",
    "Æ",
    "�",
]
MOJIBAKE_REGEXES = [
    re.compile(r"[A-Za-zÀ-ỹ]\?[A-Za-zÀ-ỹ]"),
    re.compile(r"\?\?"),
    re.compile(r"(?:^|\s)\?[A-Za-zÀ-ỹ]"),
    re.compile(r"\b(?:d|ch|k|n|l|t|h|qu)\?", re.IGNORECASE),
    re.compile(r"tr\?\?", re.IGNORECASE),
]


def has_mojibake(text):
    lowered = text.lower()
    if any(literal.lower() in lowered for literal in MOJIBAKE_LITERALS):
        return True
    if any(marker in text for marker in MOJIBAKE_MARKERS):
        return True
    return any(pattern.search(text) for pattern in MOJIBAKE_REGEXES)


def printable(text):
    return text.encode("ascii", errors="backslashreplace").decode("ascii")


def main():
    findings = []
    for path in SCAN_FILES:
        if not path.exists():
            findings.append((path, 0, "missing file"))
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if has_mojibake(line):
                findings.append((path, line_number, line.strip()))

    print(f"scanned files: {len(SCAN_FILES)}")
    print(f"mojibake findings count: {len(findings)}")
    if findings:
        print("mojibake examples:")
        for path, line_number, line in findings[:30]:
            relative = path.relative_to(REPO_ROOT)
            print(f"  {relative}:{line_number}: {printable(line)}")
        raise SystemExit(f"Text quality check failed: {len(findings)} mojibake findings")

    print("PASS")


if __name__ == "__main__":
    main()
