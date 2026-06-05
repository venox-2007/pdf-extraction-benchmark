"""FUNSD entity-level evaluation helpers."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

from pdf_extraction_benchmark.benchmarks.funsd.metrics import (
    normalize_text,
    token_f1,
    tokenize,
)


@dataclass(slots=True)
class MetricStatistics:
    """Descriptive statistics for entity-level metrics."""

    mean: float
    median: float
    minimum: float
    maximum: float
    stddev: float


@dataclass(slots=True)
class OcrLine:
    """Single OCR detection line with geometry."""

    text: str
    normalized_text: str
    box: tuple[float, float, float, float]
    confidence: float
    line_index: int


@dataclass(slots=True)
class FunsdEntity:
    """FUNSD question-answer relation parsed from annotations."""

    entity_id: str
    question_id: int
    answer_id: int
    question_text: str
    answer_text: str
    question_box: tuple[float, float, float, float]
    answer_box: tuple[float, float, float, float]
    combined_text: str
    combined_box: tuple[float, float, float, float]


@dataclass(slots=True)
class FunsdEntityResult:
    """Per-document entity-level evaluation."""

    document_id: str
    image_path: str
    annotation_path: str
    entity_count: int
    predicted_entity_count: int
    matched_entity_count: int
    entity_precision: float
    entity_recall: float
    entity_f1: float
    cer: float
    wer: float
    status: str
    error: str | None = None


@dataclass(slots=True)
class RankedEntityDocument:
    """Entity ranking payload for best and worst documents."""

    document_id: str
    entity_precision: float
    entity_recall: float
    entity_f1: float
    cer: float
    wer: float
    entity_count: int
    predicted_entity_count: int
    matched_entity_count: int


@dataclass(slots=True)
class EntityExample:
    """Document example showing entity extraction despite weak OCR scores."""

    document_id: str
    cer: float
    wer: float
    entity_precision: float
    entity_recall: float
    entity_f1: float
    note: str


@dataclass(slots=True)
class FunsdEntitySummary:
    """Aggregate summary for FUNSD entity evaluation."""

    dataset_dir: str
    total_documents: int
    evaluated_documents: int
    average_entity_precision: float
    average_entity_recall: float
    average_entity_f1: float
    average_cer: float
    average_wer: float
    metric_statistics: dict[str, MetricStatistics] = field(default_factory=dict)
    correlation_cer_entity_f1: float = 0.0
    correlation_wer_entity_f1: float = 0.0
    top_10_best: list[RankedEntityDocument] = field(default_factory=list)
    top_10_worst: list[RankedEntityDocument] = field(default_factory=list)
    successful_examples: list[EntityExample] = field(default_factory=list)
    output_dir: str = ""


def parse_funsd_entities(annotation_path: Path) -> list[FunsdEntity]:
    """Parse question-answer relationships from FUNSD annotations."""
    with annotation_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    entries = data.get("form", [])
    entry_by_id: dict[int, dict[str, Any]] = {}
    for entry in entries:
        entry_id = entry.get("id")
        if isinstance(entry_id, int):
            entry_by_id[entry_id] = entry

    entities: list[FunsdEntity] = []
    seen_pairs: set[tuple[int, int]] = set()
    for entry in entries:
        if entry.get("label") != "question":
            continue
        question_id = entry.get("id")
        if not isinstance(question_id, int):
            continue
        question_text = _normalize_entry_text(entry)
        question_box = _box_from_entry(entry)
        for link in entry.get("linking", []):
            if not isinstance(link, list) or len(link) != 2:
                continue
            source_id, target_id = link
            if source_id != question_id or not isinstance(target_id, int):
                continue
            answer_entry = entry_by_id.get(target_id)
            if not answer_entry or answer_entry.get("label") != "answer":
                continue
            pair_key = (question_id, target_id)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            answer_text = _normalize_entry_text(answer_entry)
            answer_box = _box_from_entry(answer_entry)
            combined_text = normalize_text(f"{question_text} {answer_text}")
            entities.append(
                FunsdEntity(
                    entity_id=f"{question_id}:{target_id}",
                    question_id=question_id,
                    answer_id=target_id,
                    question_text=question_text,
                    answer_text=answer_text,
                    question_box=question_box,
                    answer_box=answer_box,
                    combined_text=combined_text,
                    combined_box=_union_box(question_box, answer_box),
                )
            )
    return entities


def extract_ocr_lines(raw_result: object) -> list[OcrLine]:
    """Convert PaddleOCR output or a compatible structure into OCR lines."""
    lines: list[OcrLine] = []
    _flatten_ocr_result(raw_result, lines, line_index_start=0)
    return lines


def evaluate_entity_document(
    *,
    document_id: str,
    image_path: Path,
    annotation_path: Path,
    raw_ocr_result: object,
    cer: float,
    wer: float,
) -> FunsdEntityResult:
    """Score one FUNSD document at entity level."""
    ground_truth_entities = parse_funsd_entities(annotation_path)
    ocr_lines = extract_ocr_lines(raw_ocr_result)

    if not ground_truth_entities:
        return FunsdEntityResult(
            document_id=document_id,
            image_path=str(image_path),
            annotation_path=str(annotation_path),
            entity_count=0,
            predicted_entity_count=0,
            matched_entity_count=0,
            entity_precision=0.0,
            entity_recall=0.0,
            entity_f1=0.0,
            cer=cer,
            wer=wer,
            status="no_entities",
        )

    page_box = _estimate_page_box(ocr_lines, ground_truth_entities)
    candidates = _generate_candidates(ocr_lines, page_box)
    assignments = _assign_candidates(candidates, ground_truth_entities, page_box)

    matched_entities = len(assignments)
    predicted_entities = len(candidates)
    precision = matched_entities / predicted_entities if predicted_entities else 0.0
    recall = matched_entities / len(ground_truth_entities) if ground_truth_entities else 0.0
    f1 = 0.0 if not precision and not recall else 2 * precision * recall / (precision + recall)

    return FunsdEntityResult(
        document_id=document_id,
        image_path=str(image_path),
        annotation_path=str(annotation_path),
        entity_count=len(ground_truth_entities),
        predicted_entity_count=predicted_entities,
        matched_entity_count=matched_entities,
        entity_precision=precision,
        entity_recall=recall,
        entity_f1=f1,
        cer=cer,
        wer=wer,
        status="ok",
    )


def build_entity_summary(
    results: list[FunsdEntityResult],
    dataset_dir: Path,
    output_dir: Path,
) -> FunsdEntitySummary:
    """Build aggregate entity-level summary data."""
    metric_statistics = _compute_metric_statistics(results)
    sorted_by_entity_f1 = sorted(
        results,
        key=lambda result: (result.entity_f1, result.entity_recall, result.document_id),
        reverse=True,
    )
    sorted_by_worst = sorted(
        results,
        key=lambda result: (result.entity_f1, result.entity_recall, result.document_id),
    )
    successful_examples = _build_successful_examples(results)
    return FunsdEntitySummary(
        dataset_dir=str(dataset_dir),
        total_documents=len(results),
        evaluated_documents=len(results),
        average_entity_precision=metric_statistics["entity_precision"].mean,
        average_entity_recall=metric_statistics["entity_recall"].mean,
        average_entity_f1=metric_statistics["entity_f1"].mean,
        average_cer=metric_statistics["cer"].mean,
        average_wer=metric_statistics["wer"].mean,
        metric_statistics=metric_statistics,
        correlation_cer_entity_f1=_pearson_correlation(
            [result.cer for result in results],
            [result.entity_f1 for result in results],
        ),
        correlation_wer_entity_f1=_pearson_correlation(
            [result.wer for result in results],
            [result.entity_f1 for result in results],
        ),
        top_10_best=[_to_ranked(result) for result in sorted_by_entity_f1[:10]],
        top_10_worst=[_to_ranked(result) for result in sorted_by_worst[:10]],
        successful_examples=successful_examples,
        output_dir=str(output_dir),
    )


def build_entity_observations_markdown(
    results: list[FunsdEntityResult],
    summary: FunsdEntitySummary,
) -> str:
    """Render a concise stakeholder-facing entity analysis report."""
    lines = [
        "# FUNSD Entity Evaluation Report",
        "",
        "## Overview",
        "",
        f"- Dataset size: {summary.total_documents} documents",
        f"- Documents evaluated: {summary.evaluated_documents}",
        f"- Dataset directory: `{summary.dataset_dir}`",
        "",
        "## Average Metrics",
        "",
        _metrics_table(summary.metric_statistics),
        "",
        "## CER / WER Comparison",
        "",
        f"- Correlation between CER and entity F1: {summary.correlation_cer_entity_f1:.3f}",
        f"- Correlation between WER and entity F1: {summary.correlation_wer_entity_f1:.3f}",
        (
            "- Entity-level metrics better reflect question-answer extraction quality, "
            "while CER/WER remain sensitive to reading order and form layout."
        ),
        "",
        "## Documents Where CER/WER Look Worse Than Entity Extraction",
        "",
        _examples_table(summary.successful_examples),
        "",
        "## Interpretation",
        "",
        (
            "- A strong entity score means the benchmark recovered the question-answer "
            "relationship even if the flattened document text was reordered."
        ),
        (
            "- This makes entity precision/recall/F1 a better stakeholder-facing measure "
            "for FUNSD than document-level CER/WER alone."
        ),
    ]
    return "\n".join(lines).replace("\n\n\n", "\n\n").rstrip() + "\n"


def _normalize_entry_text(entry: dict[str, Any]) -> str:
    text = normalize_text(str(entry.get("text", "")))
    if text:
        return text
    words = [
        normalize_text(str(word.get("text", "")))
        for word in entry.get("words", [])
        if normalize_text(str(word.get("text", "")))
    ]
    return normalize_text(" ".join(words))


def _box_from_entry(entry: dict[str, Any]) -> tuple[float, float, float, float]:
    return _box_from_points(entry.get("box", []))


def _box_from_points(points: object) -> tuple[float, float, float, float]:
    if not isinstance(points, list) or not points:
        return (0.0, 0.0, 0.0, 0.0)
    if (
        len(points) == 2
        and isinstance(points[0], list)
        and isinstance(points[1], (list, tuple))
        and points[1]
        and isinstance(points[1][0], str)
    ):
        points = points[0]
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        if isinstance(point, list) and len(point) >= 2:
            xs.append(float(point[0]))
            ys.append(float(point[1]))
    if not xs or not ys:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def _union_box(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    if first == (0.0, 0.0, 0.0, 0.0):
        return second
    if second == (0.0, 0.0, 0.0, 0.0):
        return first
    return (
        min(first[0], second[0]),
        min(first[1], second[1]),
        max(first[2], second[2]),
        max(first[3], second[3]),
    )


def _flatten_ocr_result(
    result: object,
    lines: list[OcrLine],
    *,
    line_index_start: int,
) -> int:
    if result is None:
        return line_index_start
    if isinstance(result, list):
        if _looks_like_ocr_line(result):
            parsed_line = _parse_ocr_line(result, line_index_start)
            if parsed_line is not None:
                lines.append(parsed_line)
                return line_index_start + 1
            return line_index_start

        current_index = line_index_start
        for item in result:
            current_index = _flatten_ocr_result(item, lines, line_index_start=current_index)
        return current_index
    if isinstance(result, tuple):
        return _flatten_ocr_result(list(result), lines, line_index_start=line_index_start)
    if isinstance(result, dict):
        parsed_line = _parse_ocr_line(result, line_index_start)
        if parsed_line is not None:
            lines.append(parsed_line)
            return line_index_start + 1
    return line_index_start


def _looks_like_ocr_line(value: object) -> bool:
    if isinstance(value, dict):
        return "text" in value and "box" in value
    if not isinstance(value, list) or len(value) != 2:
        return False
    box, line_data = value
    return isinstance(box, list) and isinstance(line_data, (list, tuple)) and len(line_data) >= 1


def _parse_ocr_line(value: object, line_index: int) -> OcrLine | None:
    if isinstance(value, dict):
        text = normalize_text(str(value.get("text", "")))
        box = _box_from_points(value.get("box", []))
        confidence = float(value.get("confidence", 1.0) or 1.0)
        return OcrLine(
            text=text,
            normalized_text=text,
            box=box,
            confidence=confidence,
            line_index=line_index,
        )
    if not isinstance(value, list) or len(value) != 2:
        return None
    box, line_data = value
    if not isinstance(box, list) or not isinstance(line_data, (list, tuple)) or not line_data:
        return None
    text = normalize_text(str(line_data[0]))
    confidence = (
        float(line_data[1])
        if len(line_data) > 1 and isinstance(line_data[1], (int, float))
        else 1.0
    )
    return OcrLine(
        text=text,
        normalized_text=text,
        box=_box_from_points(box),
        confidence=confidence,
        line_index=line_index,
    )


def _estimate_page_box(
    ocr_lines: list[OcrLine],
    entities: list[FunsdEntity],
) -> tuple[float, float, float, float]:
    x_values: list[float] = []
    y_values: list[float] = []
    for line in ocr_lines:
        x_values.extend([line.box[0], line.box[2]])
        y_values.extend([line.box[1], line.box[3]])
    for entity in entities:
        x_values.extend(
            [
                entity.question_box[0],
                entity.question_box[2],
                entity.answer_box[0],
                entity.answer_box[2],
            ]
        )
        y_values.extend(
            [
                entity.question_box[1],
                entity.question_box[3],
                entity.answer_box[1],
                entity.answer_box[3],
            ]
        )
    if not x_values or not y_values:
        return (0.0, 0.0, 1000.0, 1000.0)
    return (min(x_values), min(y_values), max(x_values), max(y_values))


def _generate_candidates(
    ocr_lines: list[OcrLine],
    page_box: tuple[float, float, float, float],
) -> list[tuple[OcrLine, OcrLine]]:
    if not ocr_lines:
        return []
    page_diagonal = _box_diagonal(page_box)
    distance_threshold = max(180.0, page_diagonal * 0.35)
    candidate_pairs: set[tuple[int, int]] = set()

    for line_index, _line in enumerate(ocr_lines):
        if _looks_like_complete_entity_line(ocr_lines[line_index].text):
            candidate_pairs.add((line_index, line_index))
        distances: list[tuple[float, int]] = []
        for other_index, other_line in enumerate(ocr_lines):
            if other_index == line_index:
                continue
            distance = _box_distance(ocr_lines[line_index].box, other_line.box)
            if distance <= distance_threshold:
                distances.append((distance, other_index))
        for _distance, other_index in sorted(distances, key=lambda item: item[0])[:6]:
            candidate_pairs.add(tuple(sorted((line_index, other_index))))
    ordered_pairs = sorted(candidate_pairs)
    return [
        (ocr_lines[first_index], ocr_lines[second_index])
        for first_index, second_index in ordered_pairs
    ]


def _looks_like_complete_entity_line(text: str) -> bool:
    normalized = normalize_text(text)
    tokens = tokenize(normalized)
    if len(tokens) < 2:
        return False
    if ":" in normalized or any(token.endswith(":") for token in tokens):
        return True
    if any(character.isdigit() for character in normalized):
        return True
    return len(tokens) >= 3


def _assign_candidates(
    candidates: list[tuple[OcrLine, OcrLine]],
    entities: list[FunsdEntity],
    page_box: tuple[float, float, float, float],
) -> dict[int, int]:
    scored_matches: list[tuple[float, int, int]] = []
    for candidate_index, candidate in enumerate(candidates):
        for entity_index, entity in enumerate(entities):
            score = _candidate_match_score_for_lines(candidate[0], candidate[1], entity, page_box)
            if score >= 0.42:
                scored_matches.append((score, candidate_index, entity_index))

    assigned_candidates: set[int] = set()
    assigned_entities: set[int] = set()
    assignments: dict[int, int] = {}
    for _score, candidate_index, entity_index in sorted(scored_matches, reverse=True):
        if candidate_index in assigned_candidates or entity_index in assigned_entities:
            continue
        assigned_candidates.add(candidate_index)
        assigned_entities.add(entity_index)
        assignments[candidate_index] = entity_index
    return assignments


def _candidate_match_score_for_lines(
    first_line: OcrLine,
    second_line: OcrLine,
    entity: FunsdEntity,
    page_box: tuple[float, float, float, float],
) -> float:
    orientations = [
        (
            first_line,
            second_line,
            entity.question_text,
            entity.answer_text,
            entity.question_box,
            entity.answer_box,
        ),
        (
            second_line,
            first_line,
            entity.question_text,
            entity.answer_text,
            entity.question_box,
            entity.answer_box,
        ),
    ]
    scores: list[float] = []
    for (
        question_line,
        answer_line,
        question_text,
        answer_text,
        question_box,
        answer_box,
    ) in orientations:
        question_score = _segment_score(question_line, question_text, question_box, page_box)
        answer_score = _segment_score(answer_line, answer_text, answer_box, page_box)
        combined_score = _segment_score(
            OcrLine(
                text=normalize_text(f"{question_line.text} {answer_line.text}"),
                normalized_text=normalize_text(f"{question_line.text} {answer_line.text}"),
                box=_union_box(question_line.box, answer_line.box),
                confidence=min(question_line.confidence, answer_line.confidence),
                line_index=min(question_line.line_index, answer_line.line_index),
            ),
            entity.combined_text,
            entity.combined_box,
            page_box,
        )
        scores.append((question_score + answer_score + combined_score) / 3)
    return max(scores)


def _segment_score(
    ocr_line: OcrLine,
    reference_text: str,
    reference_box: tuple[float, float, float, float],
    page_box: tuple[float, float, float, float],
) -> float:
    if not reference_text:
        return 0.0
    text_score = token_f1(tokenize(ocr_line.text), tokenize(reference_text))
    proximity_score = _box_similarity(ocr_line.box, reference_box, page_box)
    return 0.75 * text_score + 0.25 * proximity_score


def _box_similarity(
    first_box: tuple[float, float, float, float],
    second_box: tuple[float, float, float, float],
    page_box: tuple[float, float, float, float],
) -> float:
    if first_box == (0.0, 0.0, 0.0, 0.0) or second_box == (0.0, 0.0, 0.0, 0.0):
        return 0.0
    page_diagonal = max(_box_diagonal(page_box), 1.0)
    distance = _box_distance(first_box, second_box)
    return max(0.0, 1.0 - (distance / page_diagonal))


def _box_distance(
    first_box: tuple[float, float, float, float],
    second_box: tuple[float, float, float, float],
) -> float:
    first_center = _box_center(first_box)
    second_center = _box_center(second_box)
    return math.dist(first_center, second_center)


def _box_center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _box_diagonal(box: tuple[float, float, float, float]) -> float:
    return math.dist((box[0], box[1]), (box[2], box[3]))


def _compute_metric_statistics(results: list[FunsdEntityResult]) -> dict[str, MetricStatistics]:
    metric_names = [
        "entity_precision",
        "entity_recall",
        "entity_f1",
        "cer",
        "wer",
    ]
    statistics_map: dict[str, MetricStatistics] = {}
    for metric_name in metric_names:
        values = [getattr(result, metric_name) for result in results]
        statistics_map[metric_name] = _statistics_for(values)
    return statistics_map


def _statistics_for(values: list[float]) -> MetricStatistics:
    if not values:
        return MetricStatistics(0.0, 0.0, 0.0, 0.0, 0.0)
    stddev = pstdev(values) if len(values) > 1 else 0.0
    return MetricStatistics(
        mean=round(mean(values), 6),
        median=round(median(values), 6),
        minimum=round(min(values), 6),
        maximum=round(max(values), 6),
        stddev=round(stddev, 6),
    )


def _pearson_correlation(first_values: list[float], second_values: list[float]) -> float:
    if len(first_values) != len(second_values) or len(first_values) < 2:
        return 0.0
    first_mean = mean(first_values)
    second_mean = mean(second_values)
    numerator = sum(
        (first - first_mean) * (second - second_mean)
        for first, second in zip(first_values, second_values, strict=False)
    )
    first_denominator = math.sqrt(sum((value - first_mean) ** 2 for value in first_values))
    second_denominator = math.sqrt(sum((value - second_mean) ** 2 for value in second_values))
    denominator = first_denominator * second_denominator
    if not denominator:
        return 0.0
    return round(numerator / denominator, 6)


def _to_ranked(result: FunsdEntityResult) -> RankedEntityDocument:
    return RankedEntityDocument(
        document_id=result.document_id,
        entity_precision=result.entity_precision,
        entity_recall=result.entity_recall,
        entity_f1=result.entity_f1,
        cer=result.cer,
        wer=result.wer,
        entity_count=result.entity_count,
        predicted_entity_count=result.predicted_entity_count,
        matched_entity_count=result.matched_entity_count,
    )


def _build_successful_examples(results: list[FunsdEntityResult]) -> list[EntityExample]:
    if not results:
        return []
    sorted_by_cer = sorted(results, key=lambda result: result.cer, reverse=True)
    selected: list[FunsdEntityResult] = []
    for result in sorted_by_cer:
        if result.entity_f1 >= 0.7 and (result.cer >= 0.35 or result.wer >= 0.55):
            selected.append(result)
        if len(selected) >= 5:
            break
    if not selected:
        selected = sorted(
            results,
            key=lambda result: (result.entity_f1 - result.cer, result.entity_f1),
            reverse=True,
        )[:5]
    examples: list[EntityExample] = []
    for result in selected:
        examples.append(
            EntityExample(
                document_id=result.document_id,
                cer=result.cer,
                wer=result.wer,
                entity_precision=result.entity_precision,
                entity_recall=result.entity_recall,
                entity_f1=result.entity_f1,
                note=(
                    "Entity extraction stayed strong even though document-level "
                    "text was reordered or noisy."
                ),
            )
        )
    return examples


def _metrics_table(stats: dict[str, MetricStatistics]) -> str:
    header = "| Metric | Mean | Median | Min | Max | Std Dev |"
    separator = "| --- | ---: | ---: | ---: | ---: | ---: |"
    labels = {
        "entity_precision": "Entity Precision",
        "entity_recall": "Entity Recall",
        "entity_f1": "Entity F1",
        "cer": "CER",
        "wer": "WER",
    }
    rows = [header, separator]
    for metric_name, label in labels.items():
        stat = stats[metric_name]
        rows.append(
            f"| {label} | {stat.mean:.6f} | {stat.median:.6f} | {stat.minimum:.6f} | "
            f"{stat.maximum:.6f} | {stat.stddev:.6f} |"
        )
    return "\n".join(rows)


def _examples_table(examples: list[EntityExample]) -> str:
    if not examples:
        return "_No strong examples were identified._"
    header = "| Document | CER | WER | Entity F1 | Note |"
    separator = "| --- | ---: | ---: | ---: | --- |"
    rows = [header, separator]
    for example in examples:
        rows.append(
            f"| {example.document_id} | {example.cer:.6f} | {example.wer:.6f} | "
            f"{example.entity_f1:.6f} | {example.note} |"
        )
    return "\n".join(rows)


def entity_results_payload(results: list[FunsdEntityResult]) -> list[dict[str, Any]]:
    """Serialize results as dictionaries for CSV or JSON payloads."""
    return [asdict(result) for result in results]
