"""CS entity labels, name normalization, and a lazy GLiNER singleton."""

import re

from app import config

# Title-case labels work best with GLiNER. Keep the set small and CS-focused;
# more labels means slower, noisier extraction.
ENTITY_LABELS: list[str] = [
    "Algorithm",
    "Data Structure",
    "Programming Language",
    "Software",
    "Protocol",
    "Concept",
    "Technology",
    "Hardware",
    "Mathematical Concept",
    "Organization",
    "Person",
    "File Format",
]

_MODEL = None


def get_ner_model(device: str | None = None):
    """Lazily load and cache the GLiNER model (CLAUDE.md lazy-load rule)."""
    global _MODEL
    if _MODEL is None:
        from gliner import GLiNER

        _MODEL = GLiNER.from_pretrained(config.GRAPH_NER_MODEL)
        _MODEL = _MODEL.to(device or config.GRAPH_NER_DEVICE)
    return _MODEL


def normalize_entity(text: str) -> str:
    """Canonical key so 'Quick Sort', 'quicksort ', 'QuickSort' converge."""
    return re.sub(r"\s+", " ", text.strip().lower())


def keep_entity(name: str) -> bool:
    """Filter junk: too short/long, purely numeric, or punctuation-only."""
    if not (2 <= len(name) <= 60):
        return False
    if re.fullmatch(r"[\d\W_]+", name):
        return False
    return True
