"""Semantic-aware text chunking with F1-specific metadata tagging."""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("chunker")

# F1-specific patterns for metadata extraction
SEASON_PATTERN = re.compile(r"\b(19[5-9]\d|20[0-9]\d)\b")
DRIVER_KEYWORDS = [
    "verstappen", "hamilton", "leclerc", "norris", "sainz", "piastri",
    "russell", "alonso", "stroll", "gasly", "ocon", "tsunoda", "ricciardo",
    "hulkenberg", "magnussen", "bottas", "zhou", "albon", "sargeant", "lawson",
    "bearman", "colapinto", "schumacher", "senna", "prost", "lauda", "vettel",
    "raikkonen", "hakkinen", "fangio", "clark", "hill", "mansell", "piquet",
    "antonelli",
]
TEAM_KEYWORDS = [
    "red bull", "mercedes", "ferrari", "mclaren", "aston martin",
    "alpine", "williams", "haas", "rb", "sauber", "kick sauber",
    "alfa romeo", "alphatauri", "renault", "racing point", "toro rosso",
    "cadillac",
]


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def _extract_f1_metadata(text: str) -> Dict[str, Any]:
    """Extract F1-specific metadata from text content."""
    text_lower = text.lower()
    meta: Dict[str, Any] = {}

    # Detect season years
    years = SEASON_PATTERN.findall(text)
    if years:
        meta["seasons"] = ",".join(sorted(set(years)))

    # Detect drivers
    found_drivers = [d for d in DRIVER_KEYWORDS if d in text_lower]
    if found_drivers:
        meta["drivers"] = ",".join(found_drivers[:5])  # top 5

    # Detect teams
    found_teams = [t for t in TEAM_KEYWORDS if t in text_lower]
    if found_teams:
        meta["teams"] = ",".join(found_teams[:5])

    return meta


def chunk_text(
    text: str,
    source_metadata: Optional[Dict[str, Any]] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Chunk]:
    """
    Split text into semantically meaningful chunks with metadata.

    1. Split on double-newlines (paragraph boundaries)
    2. If a paragraph is too big, split on single newlines then sentences
    3. Merge small chunks to reach target size
    4. Add overlap from previous chunk
    """
    settings = get_settings()
    max_size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP
    base_meta = source_metadata or {}

    # Step 1: Split into paragraphs
    paragraphs = re.split(r"\n{2,}", text.strip())
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    # Step 2: Further split oversized paragraphs
    segments: List[str] = []
    for para in paragraphs:
        if len(para) <= max_size:
            segments.append(para)
        else:
            # Split by sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) + 1 <= max_size:
                    current = f"{current} {sent}".strip()
                else:
                    if current:
                        segments.append(current)
                    current = sent
            if current:
                segments.append(current)

    # Step 3: Merge small segments
    merged: List[str] = []
    current = ""
    for seg in segments:
        if len(current) + len(seg) + 2 <= max_size:
            current = f"{current}\n\n{seg}".strip()
        else:
            if current:
                merged.append(current)
            current = seg
    if current:
        merged.append(current)

    # Step 4: Create chunks with overlap and metadata
    chunks: List[Chunk] = []
    prev_tail = ""

    for i, text_block in enumerate(merged):
        # Prepend overlap from previous chunk
        if prev_tail and i > 0:
            chunk_text_with_overlap = f"{prev_tail} {text_block}".strip()
        else:
            chunk_text_with_overlap = text_block

        # Extract F1-specific metadata
        f1_meta = _extract_f1_metadata(chunk_text_with_overlap)

        chunk_meta = {
            **base_meta,
            **f1_meta,
            "chunk_index": i,
            "total_chunks": len(merged),
            "char_count": len(chunk_text_with_overlap),
        }

        chunks.append(Chunk(text=chunk_text_with_overlap, metadata=chunk_meta))

        # Save tail for next chunk's overlap
        prev_tail = text_block[-overlap:] if len(text_block) > overlap else text_block

    logger.info(
        f"Chunked text into {len(chunks)} chunks "
        f"(avg size={sum(len(c.text) for c in chunks) // max(len(chunks), 1)} chars)"
    )
    return chunks
