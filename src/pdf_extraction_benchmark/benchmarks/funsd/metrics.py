"""Shared FUNSD evaluation metrics."""

from __future__ import annotations

import re
from collections import Counter


def normalize_text(text: str) -> str:
    """Normalize line endings and collapse whitespace."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """Split normalized text into whitespace-delimited tokens."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [token for token in normalized.split(" ") if token]


def levenshtein_distance(reference: list[str], hypothesis: list[str]) -> int:
    """Compute standard Levenshtein edit distance."""
    if not reference:
        return len(hypothesis)
    if not hypothesis:
        return len(reference)

    previous = list(range(len(hypothesis) + 1))
    for reference_index, reference_item in enumerate(reference, start=1):
        current = [reference_index]
        for hypothesis_index, hypothesis_item in enumerate(hypothesis, start=1):
            substitution_cost = 0 if reference_item == hypothesis_item else 1
            current.append(
                min(
                    previous[hypothesis_index] + 1,
                    current[hypothesis_index - 1] + 1,
                    previous[hypothesis_index - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Compute normalized character error rate."""
    if not reference and not hypothesis:
        return 0.0
    if not reference:
        return 1.0
    distance = levenshtein_distance(list(reference), list(hypothesis))
    return distance / len(reference)


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute normalized word error rate."""
    reference_tokens = tokenize(reference)
    hypothesis_tokens = tokenize(hypothesis)
    if not reference_tokens and not hypothesis_tokens:
        return 0.0
    if not reference_tokens:
        return 1.0
    distance = levenshtein_distance(reference_tokens, hypothesis_tokens)
    return distance / len(reference_tokens)


def token_overlap_counts(reference: list[str], hypothesis: list[str]) -> tuple[int, int, int]:
    """Return matched, reference, and hypothesis token counts using multiset overlap."""
    reference_counts = Counter(reference)
    hypothesis_counts = Counter(hypothesis)
    overlap = reference_counts & hypothesis_counts
    matched = sum(overlap.values())
    return matched, sum(reference_counts.values()), sum(hypothesis_counts.values())


def token_precision(reference: list[str], hypothesis: list[str]) -> float:
    """Compute multiset token precision."""
    matched, _, hypothesis_count = token_overlap_counts(reference, hypothesis)
    if not hypothesis_count:
        return 0.0
    return matched / hypothesis_count


def token_recall(reference: list[str], hypothesis: list[str]) -> float:
    """Compute multiset token recall."""
    matched, reference_count, _ = token_overlap_counts(reference, hypothesis)
    if not reference_count:
        return 0.0
    return matched / reference_count


def token_f1(reference: list[str], hypothesis: list[str]) -> float:
    """Compute token F1 from multiset precision and recall."""
    precision = token_precision(reference, hypothesis)
    recall = token_recall(reference, hypothesis)
    if not precision and not recall:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def token_overlap_accuracy(reference: list[str], hypothesis: list[str]) -> float:
    """Compute order-insensitive token Jaccard overlap."""
    matched, reference_count, hypothesis_count = token_overlap_counts(reference, hypothesis)
    denominator = reference_count + hypothesis_count - matched
    if not denominator:
        return 0.0
    return matched / denominator
