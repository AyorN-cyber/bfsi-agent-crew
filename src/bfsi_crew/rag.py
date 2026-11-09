"""A small, dependency-free retrieval layer over the policy library.

TF-IDF with cosine similarity is enough for a few dozen policy passages and
keeps the project runnable without an embedding API. The ``PolicyIndex``
interface is deliberately narrow so it can be swapped for a vector store.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

from .models import Citation

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an and are as at be by for from has have in is it its of on or that the to was were will with".split()
)


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


class Chunk:
    """One retrievable passage: a ``##`` section of a policy file."""

    __slots__ = ("source", "heading", "text")

    def __init__(self, source: str, heading: str, text: str) -> None:
        self.source = source
        self.heading = heading
        self.text = text


def load_chunks(directory: Path | str) -> List[Chunk]:
    """Split every ``*.md`` file in ``directory`` into chunks at ``##`` headings."""
    chunks: List[Chunk] = []
    for path in sorted(Path(directory).glob("*.md")):
        heading = path.stem
        body: List[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                text = "\n".join(body).strip()
                if text:
                    chunks.append(Chunk(path.name, heading, text))
                heading, body = line[3:].strip(), []
            elif line.startswith("# "):
                continue
            else:
                body.append(line)
        text = "\n".join(body).strip()
        if text:
            chunks.append(Chunk(path.name, heading, text))
    return chunks


class PolicyIndex:
    def __init__(self, chunks: Iterable[Chunk]) -> None:
        self.chunks = list(chunks)
        counts = [Counter(tokenize(f"{c.heading} {c.text}")) for c in self.chunks]
        doc_freq: Counter = Counter()
        for c in counts:
            doc_freq.update(c.keys())
        n = len(self.chunks)
        self._idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in doc_freq.items()}
        self._vectors = [self._vectorise(c) for c in counts]

    @classmethod
    def from_directory(cls, directory: Path | str) -> "PolicyIndex":
        return cls(load_chunks(directory))

    def _vectorise(self, counts: Counter) -> dict:
        vec = {t: c * self._idf[t] for t, c in counts.items() if t in self._idf}
        norm = math.sqrt(sum(v * v for v in vec.values()))
        return {t: v / norm for t, v in vec.items()} if norm else {}

    def search(self, query: str, k: int = 3) -> List[Citation]:
        """Return up to ``k`` passages ranked by cosine similarity to ``query``."""
        q = self._vectorise(Counter(tokenize(query)))
        scored: List[Tuple[float, Chunk]] = []
        for chunk, vec in zip(self.chunks, self._vectors):
            score = sum(w * vec.get(t, 0.0) for t, w in q.items())
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [Citation(c.source, c.heading, c.text, round(s, 4)) for s, c in scored[:k]]
