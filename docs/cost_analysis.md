# Cost Analysis: AWS Textract vs Self-Hosted Alternatives

This document compares the per-page cost of the current AWS Textract setup
against the open-source tools evaluated in this project, at three scale points:
10K, 100K, and 1M pages per month.

---

## AWS Textract Pricing (Public, as of 2025)

Source: https://aws.amazon.com/textract/pricing/

| API | Price | Notes |
| --- | ---: | --- |
| Detect Document Text (OCR only) | $1.50 / 1,000 pages | $0.0015 / page |
| Analyze Document (tables + forms) | $15.00 / 1,000 pages | $0.015 / page |
| Analyze Document with Queries | $50.00 / 1,000 pages | $0.050 / page |
| Free tier | 1,000 pages / month | Detect Text only; first 3 months |

Our platform currently uses Analyze Document (tables + forms) because invoices
and contracts require table extraction. This means **$0.015 per page** is the
relevant baseline.

---

## Self-Hosted Cost Model

Self-hosted tools have no per-page charge. The only cost is compute time.

### Throughput assumptions (from benchmark data)

| Tool | Mean latency / doc | Est. throughput (1 vCPU) |
| --- | ---: | ---: |
| PyMuPDF | 6 ms | ~10,000 docs/hr |
| OpenDataLoader | 730 ms | ~4,900 docs/hr |
| Tesseract | 1,265 ms | ~2,844 docs/hr |
| PaddleOCR (CPU) | 8,735 ms | ~411 docs/hr |
| Docling (CPU) | 32,295 ms | ~111 docs/hr |

*Latency source: RVL-CDIP benchmark, 32 mixed native/scanned documents.
RVL-CDIP documents are single-page. Multi-page documents scale roughly linearly.*

### AWS EC2 reference pricing (on-demand, us-east-1, 2025)

| Instance | vCPUs | RAM | On-demand / hr |
| --- | ---: | ---: | ---: |
| t3.medium | 2 | 4 GB | $0.0416 |
| t3.large | 2 | 8 GB | $0.0832 |
| c5.xlarge | 4 | 8 GB | $0.1700 |
| c5.2xlarge | 8 | 16 GB | $0.3400 |

For PaddleOCR and Docling, a GPU instance reduces latency significantly:

| Instance | GPU | On-demand / hr | Est. PaddleOCR latency |
| --- | --- | ---: | ---: |
| g4dn.xlarge | 1× T4 16GB | $0.5260 | ~1–2 s/doc (est.) |
| g4dn.2xlarge | 1× T4 16GB | $0.7520 | ~1–2 s/doc (est.) |

*GPU latency estimates are projected; not directly measured in this benchmark.*

---

## Cost per Page: Self-Hosted vs Textract

### Scenario A — Native PDFs only (PyMuPDF)

PyMuPDF on a t3.medium:

```
Throughput: ~10,000 docs/hr × 2 vCPU = 10,000 docs/hr
Cost/hr: $0.0416
Cost/page: $0.0416 / 10,000 = $0.0000042
```

| Volume | Textract (Detect Text, $0.0015/page) | PyMuPDF self-hosted |
| ---: | ---: | ---: |
| 10,000 pages/month | $15.00 | $0.04 |
| 100,000 pages/month | $150.00 | $0.42 |
| 1,000,000 pages/month | $1,500.00 | $4.20 |

**Saving: ~99.7% cost reduction at all scales.**

---

### Scenario B — Scanned PDFs, accuracy priority (PaddleOCR, CPU)

PaddleOCR on a c5.xlarge (4 vCPU, run 4 workers in parallel):

```
Throughput: 411 docs/hr × 4 workers = 1,644 docs/hr
Cost/hr: $0.17
Cost/page: $0.17 / 1,644 = $0.0001034
```

Textract baseline is Analyze Document at $0.015/page (table extraction needed
for invoices/contracts).

| Volume | Textract (Analyze Doc, $0.015/page) | PaddleOCR CPU (c5.xlarge) |
| ---: | ---: | ---: |
| 10,000 pages/month | $150.00 | $1.03 |
| 100,000 pages/month | $1,500.00 | $10.34 |
| 1,000,000 pages/month | $15,000.00 | $103.40 |

**Saving: ~99.3% cost reduction at all scales.**

---

### Scenario C — Mixed pipeline (recommended architecture)

A realistic production pipeline for our use case would route documents:

- Native PDFs → PyMuPDF (fast, free)
- Scanned PDFs → PaddleOCR (accurate, $0.0001/page)
- Table-heavy documents → Docling (structured output, $0.0003/page)

Assuming a typical split of 60% native, 35% scanned, 5% complex/table-heavy:

```
Blended cost/page = 0.60×$0.000004 + 0.35×$0.000103 + 0.05×$0.000300
                  ≈ $0.0000524 / page
```

| Volume | Textract (Analyze Doc) | Mixed self-hosted pipeline |
| ---: | ---: | ---: |
| 10,000 pages/month | $150.00 | $0.52 |
| 100,000 pages/month | $1,500.00 | $5.24 |
| 1,000,000 pages/month | $15,000.00 | $52.40 |

**Saving: ~99.6% cost reduction.**

---

## Break-Even Analysis

At what page volume does self-hosting become cheaper than Textract, accounting
for a dedicated EC2 instance running 24/7?

A c5.xlarge running 24/7 costs: $0.17/hr × 24 × 30 = **$122.40/month** (fixed).

Break-even with Textract (Analyze Document at $0.015/page):

```
$122.40 / $0.015 = 8,160 pages/month
```

**If your monthly volume exceeds ~8,200 pages, self-hosting pays for itself.**
At 10,000 pages/month the monthly saving is already $27.60. At 1M pages/month
the annual saving exceeds **$176,000**.

---

## Additional Cost Factors

### Factors that favour self-hosting

- **No per-page API cost**: Volume growth does not increase marginal cost.
- **Latency control**: Avoids synchronous Textract call latency (0.5–5s/page
  depending on document complexity). Self-hosted PyMuPDF runs in 6ms/doc.
- **Data residency**: Documents never leave your infrastructure. Avoids
  Textract's requirement to upload to S3 and pass data through AWS systems.
- **No vendor lock-in**: Tool can be swapped (PaddleOCR → Tesseract or future
  model) without changing infrastructure or billing model.
- **Accuracy tuning**: Open-source tools can be fine-tuned or prompt-tuned on
  domain-specific documents; Textract cannot.

### Factors that favour Textract (remaining Textract advantages)

- **No infrastructure management**: No EC2 provisioning, OS patching, or model
  management.
- **Automatic scaling**: Textract handles burst traffic without over-provisioning.
- **Textract-specific features**: Queries API, Identity Document analysis,
  Expense analysis — these have no direct open-source equivalent.
- **Handwriting**: Textract handles handwriting significantly better than any
  evaluated open-source tool (none of the five tools evaluated are usable for
  handwritten content).
- **Support SLA**: Textract carries AWS enterprise SLA; self-hosted has no SLA.

---

## Recommendation

| Workload | Recommendation | Reason |
| --- | --- | --- |
| Native PDFs (text-layer) | **PyMuPDF self-hosted** | ~$0 marginal cost; 6ms/doc |
| Scanned PDFs, accuracy | **PaddleOCR self-hosted** | $0.0001/page vs $0.015/page; 99%+ saving |
| Table-heavy docs | **Docling self-hosted** | Structured output; cost similar to PaddleOCR |
| Handwritten content | **Retain Textract** | No viable open-source alternative found |
| Unknown document mix | **Classify first, route accordingly** | Avoids applying OCR to native PDFs (saves 10-100× latency) |

For a platform with minimal handwritten content, migrating to the self-hosted
pipeline produces **>99% cost reduction** at all tested volumes. The minimum
viable migration requires only PyMuPDF (native) + PaddleOCR (scanned), which
can be deployed on a single EC2 instance and break even at ~8,200 pages/month.

---

## Appendix: AWS Textract API used

Current platform uses:
- `analyze_document` with `FeatureTypes=["TABLES", "FORMS"]`
- Billed at $15.00 per 1,000 pages ($0.015/page)
- Does not use Textract Queries (billed at $0.05/page) or Identity Documents

If the platform is using only Detect Document Text (OCR only, no tables/forms):
- Cost is $0.0015/page
- Break-even with self-hosting still occurs at ~8,200 pages/month
- Saving at 1M pages/month: ~$1,500 → ~$52 (97% reduction vs Analyze Document)
