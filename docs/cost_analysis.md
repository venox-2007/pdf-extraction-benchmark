# Cost Analysis: AWS Textract vs Self-Hosted Alternatives

Quantitative comparison of AWS Textract against the five evaluated open-source
tools at four production volumes. All pricing is from public sources; all
throughput figures are derived from benchmark measurements in this project.

---

## Pricing Sources and Assumptions

### AWS Textract pricing (public, as of 2025)

Source: https://aws.amazon.com/textract/pricing/

| API | Price per 1,000 pages | Price per page |
| --- | ---: | ---: |
| Detect Document Text (OCR only) | $1.50 | $0.0015 |
| Analyze Document (tables + forms) | $15.00 | $0.0150 |
| Analyze Document with Queries | $50.00 | $0.0500 |
| Free tier | 1,000 pages/month | Detect Text only; first 3 months |

**Baseline used in this analysis:** Analyze Document at **$0.015/page** — the
relevant API for workflows that require table and form extraction from invoices
and contracts. Where noted, Detect Text ($0.0015/page) is used as an
alternative baseline for text-only workflows.

### AWS EC2 pricing (on-demand, us-east-1, 2025)

Source: https://aws.amazon.com/ec2/pricing/on-demand/

| Instance | vCPUs | RAM | $/hr (on-demand) | $/month (24×7) |
| --- | ---: | ---: | ---: | ---: |
| t3.medium | 2 | 4 GB | $0.0416 | $29.95 |
| t3.large | 2 | 8 GB | $0.0832 | $59.90 |
| c5.xlarge | 4 | 8 GB | $0.1700 | $122.40 |
| c5.2xlarge | 8 | 16 GB | $0.3400 | $244.80 |
| g4dn.xlarge | 4 CPU + 1× T4 GPU | 16 GB | $0.5260 | $378.72 |

**Savings opportunity:** EC2 Reserved Instances (1-year, no upfront) reduce
on-demand prices by approximately 30–40%. These are not used in the analysis
below to keep comparisons conservative.

### Throughput assumptions (from benchmark data)

All latency figures are measured on CPU hardware (no GPU) from the benchmark
runs in this project. Per-vCPU throughput assumes one worker per vCPU and
linear scaling; actual scaling depends on tool and document complexity.

| Tool | Measured latency/doc | Per-vCPU throughput | Source |
| --- | ---: | ---: | --- |
| PyMuPDF | 6 ms | ~10,000 docs/hr | RVL-CDIP benchmark, n=48 |
| OpenDataLoader | 830 ms | ~1,205 docs/hr | RVL-CDIP benchmark, n=48 |
| Tesseract | 1,265 ms | ~2,844 docs/hr | RVL-CDIP benchmark, n=32 |
| PaddleOCR | 3,420 ms | ~1,053 docs/hr | RVL-CDIP benchmark, n=48 |
| Docling | 15,543 ms | ~232 docs/hr | RVL-CDIP benchmark, n=48 |

> **Note on PaddleOCR latency:** An earlier 2-doc/category run showed 8,735 ms
> mean (dominated by outlier documents). The 3-doc/category run (48 docs) shows
> 3,420 ms mean, which averages more document types and is used here. Expect
> 3–9s/doc depending on document complexity.

> **Note on Docling latency:** Measured mean is 15,543 ms; worst-case on a
> complex specification document was 207 seconds. A per-document timeout guard
> is mandatory in production.

---

## Per-Tool Cost Derivation

### Recommended instance and worker configuration per tool

| Tool | Recommended instance | Workers | Instance throughput | $/hr | $/page (compute) |
| --- | --- | ---: | ---: | ---: | ---: |
| PyMuPDF | t3.medium | 2 | 20,000 docs/hr | $0.0416 | **$0.0000021** |
| OpenDataLoader | t3.large | 2 | 2,410 docs/hr | $0.0832 | **$0.0000345** |
| Tesseract | t3.medium | 2 | 5,688 docs/hr | $0.0416 | **$0.0000073** |
| PaddleOCR (CPU) | c5.xlarge | 4 | 4,212 docs/hr | $0.1700 | **$0.0000404** |
| PaddleOCR (GPU) | g4dn.xlarge | 1 | ~2,400 docs/hr *(est.)* | $0.5260 | **$0.0002192** *(est.)* |
| Docling (CPU) | c5.2xlarge | 4 | 928 docs/hr | $0.3400 | **$0.0003664** |
| Docling (GPU) | g4dn.xlarge | 1 | ~900 docs/hr *(est.)* | $0.5260 | **$0.0005844** *(est.)* |

**Derivation notes:**

- *PyMuPDF:* t3.medium, 2 workers × 10,000 = 20,000 docs/hr.
  `$0.0416 / 20,000 = $0.0000021/page`

- *OpenDataLoader:* t3.large (8 GB RAM required for JVM heap + Docling backend
  in hybrid mode), 2 workers × 1,205 = 2,410 docs/hr.
  `$0.0832 / 2,410 = $0.0000345/page`

- *Tesseract:* t3.medium, 2 workers × 2,844 = 5,688 docs/hr.
  `$0.0416 / 5,688 = $0.0000073/page`

- *PaddleOCR CPU:* c5.xlarge (4 vCPU, 8 GB RAM needed for model), 4 workers ×
  1,053 = 4,212 docs/hr.
  `$0.1700 / 4,212 = $0.0000404/page`

- *PaddleOCR GPU:* g4dn.xlarge, 1 GPU worker. Estimated 1.5 s/doc on T4 →
  ~2,400 docs/hr. **Not directly measured; projected from GPU inference
  benchmarks in PaddleOCR literature.**
  `$0.5260 / 2,400 = $0.0002192/page`

- *Docling CPU:* c5.2xlarge (16 GB RAM needed for ONNX models), 4 workers ×
  232 = 928 docs/hr.
  `$0.3400 / 928 = $0.0003664/page`

- *Docling GPU:* g4dn.xlarge, 1 GPU worker. Estimated 4 s/doc on T4 → ~900
  docs/hr. **Not directly measured; conservative projection.**
  `$0.5260 / 900 = $0.0005844/page`

---

## Monthly Cost at Four Volumes

The tables below show **total compute cost** (instance cost × hours needed to
process the monthly volume), not fixed 24/7 instance cost. This models
on-demand or auto-scaled deployment where the instance runs only when needed.

For a **dedicated 24/7 instance** (fixed cost), see the Break-Even section.

### Formula

```
hours_needed = monthly_pages / instance_throughput
monthly_cost = hours_needed × $/hr
```

### Table 1 — Text-only workloads (native PDFs or OCR text extraction)

Textract baseline: **Detect Text, $0.0015/page**

| Tool | Instance | 10K pages/mo | 100K pages/mo | 1M pages/mo | 10M pages/mo |
| --- | --- | ---: | ---: | ---: | ---: |
| **Textract (Detect Text)** | — | $15.00 | $150.00 | $1,500.00 | $15,000.00 |
| PyMuPDF | t3.medium | **$0.02** | **$0.21** | **$2.08** | **$20.80** |
| Tesseract | t3.medium | $0.07 | $0.73 | $7.31 | $73.10 |
| PaddleOCR (CPU) | c5.xlarge | $0.40 | $4.04 | $40.40 | $404.00 |
| Docling (CPU) | c5.2xlarge | $3.66 | $36.60 | $366.00 | $3,660.00 |

Saving vs Textract (Detect Text) at 1M pages: PyMuPDF 99.9%, Tesseract 99.5%,
PaddleOCR 97.3%, Docling 75.6%.

---

### Table 2 — Table extraction workloads (invoices, contracts, forms)

Textract baseline: **Analyze Document, $0.015/page**

| Tool | Instance | 10K pages/mo | 100K pages/mo | 1M pages/mo | 10M pages/mo |
| --- | --- | ---: | ---: | ---: | ---: |
| **Textract (Analyze Doc)** | — | $150.00 | $1,500.00 | $15,000.00 | $150,000.00 |
| OpenDataLoader | t3.large | $0.35 | $3.45 | $34.50 | $345.00 |
| Docling (CPU) | c5.2xlarge | $3.66 | $36.60 | $366.00 | $3,660.00 |
| Docling (GPU) *(est.)* | g4dn.xlarge | $5.84 | $58.40 | $584.00 | $5,840.00 |

Saving vs Textract (Analyze Doc) at 1M pages: OpenDataLoader 99.8%, Docling
CPU 97.6%, Docling GPU (est.) 96.1%.

---

### Table 3 — Scanned document workloads (OCR required, accuracy priority)

Textract baseline: **Analyze Document, $0.015/page**

| Tool | Instance | 10K pages/mo | 100K pages/mo | 1M pages/mo | 10M pages/mo |
| --- | --- | ---: | ---: | ---: | ---: |
| **Textract (Analyze Doc)** | — | $150.00 | $1,500.00 | $15,000.00 | $150,000.00 |
| Tesseract | t3.medium | $0.07 | $0.73 | $7.31 | $73.10 |
| PaddleOCR (CPU) | c5.xlarge | $0.40 | $4.04 | $40.40 | $404.00 |
| PaddleOCR (GPU) *(est.)* | g4dn.xlarge | $2.19 | $21.90 | $219.00 | $2,190.00 |
| Docling (CPU) | c5.2xlarge | $3.66 | $36.60 | $366.00 | $3,660.00 |

Saving vs Textract (Analyze Doc) at 1M pages: Tesseract 99.95%, PaddleOCR CPU
99.7%, PaddleOCR GPU (est.) 98.5%, Docling CPU 97.6%.

---

### Table 4 — Recommended mixed pipeline

Realistic document split: **60% native, 35% scanned, 5% table-heavy scanned**.
Routing: native → PyMuPDF, scanned → PaddleOCR CPU, table-heavy → Docling CPU.

```
Blended $/page = 0.60 × $0.0000021
               + 0.35 × $0.0000404
               + 0.05 × $0.0003664
               = $0.0000013 + $0.0000141 + $0.0000183
               = $0.0000337 / page
```

| | 10K pages/mo | 100K pages/mo | 1M pages/mo | 10M pages/mo |
| --- | ---: | ---: | ---: | ---: |
| **Textract (Analyze Doc)** | $150.00 | $1,500.00 | $15,000.00 | $150,000.00 |
| Mixed self-hosted pipeline | $0.34 | $3.37 | $33.70 | $337.00 |
| **Saving** | **$149.66 (99.8%)** | **$1,496.63 (99.8%)** | **$14,966.30 (99.8%)** | **$149,663.00 (99.8%)** |
| **Annual saving** | **$1,796** | **$17,960** | **$179,596** | **$1,795,956** |

---

## Break-Even Analysis

Break-even: the monthly volume at which self-hosting a **dedicated 24/7
instance** becomes cheaper than Textract on a variable (pay-per-page) basis.

### Against Textract Analyze Document ($0.015/page)

```
break_even_pages = instance_monthly_cost / textract_price_per_page
```

| Tool | Instance | Monthly cost (24/7) | Break-even vs Analyze Doc |
| --- | --- | ---: | ---: |
| PyMuPDF | t3.medium | $29.95 | **2,000 pages/month** |
| Tesseract | t3.medium | $29.95 | **2,000 pages/month** |
| OpenDataLoader | t3.large | $59.90 | **3,993 pages/month** |
| PaddleOCR (CPU) | c5.xlarge | $122.40 | **8,160 pages/month** |
| Docling (CPU) | c5.2xlarge | $244.80 | **16,320 pages/month** |
| PaddleOCR (GPU) *(est.)* | g4dn.xlarge | $378.72 | **25,248 pages/month** |
| Docling (GPU) *(est.)* | g4dn.xlarge | $378.72 | **25,248 pages/month** |
| Mixed pipeline (PyMuPDF + PaddleOCR) | t3.medium + c5.xlarge | $152.35 | **10,157 pages/month** |

### Against Textract Detect Text ($0.0015/page)

| Tool | Instance | Monthly cost (24/7) | Break-even vs Detect Text |
| --- | --- | ---: | ---: |
| PyMuPDF | t3.medium | $29.95 | **19,967 pages/month** |
| Tesseract | t3.medium | $29.95 | **19,967 pages/month** |
| OpenDataLoader | t3.large | $59.90 | **39,933 pages/month** |
| PaddleOCR (CPU) | c5.xlarge | $122.40 | **81,600 pages/month** |
| Docling (CPU) | c5.2xlarge | $244.80 | **163,200 pages/month** |

**Interpretation:** If the platform uses Analyze Document (tables + forms), any
tool on a dedicated instance breaks even below 30K pages/month. If the platform
uses Detect Text only, the heavier tools (Docling, PaddleOCR) require ~100K+
pages/month to justify dedicated infrastructure.

---

## Cost at Scale: 10M Pages/Month Detail

At 10M pages/month, on-demand compute is not practical — dedicated instances
running continuously are required. The table below shows the **number of
instances** needed and **total monthly infrastructure cost**.

| Tool | Instance | Throughput | Instances needed | Monthly cost | $/page |
| --- | --- | ---: | ---: | ---: | ---: |
| Textract (Analyze Doc) | — | unlimited | — | $150,000.00 | $0.0150 |
| PyMuPDF | t3.medium | 20,000/hr | 1 | $29.95 | $0.0000030 |
| Tesseract | t3.medium | 5,688/hr | 1 | $29.95 | $0.0000030 |
| OpenDataLoader | t3.large | 2,410/hr | 2 | $119.80 | $0.0000120 |
| PaddleOCR (CPU) | c5.xlarge | 4,212/hr | 2 | $244.80 | $0.0000245 |
| PaddleOCR (GPU) *(est.)* | g4dn.xlarge | 2,400/hr | 3 | $1,136.16 | $0.0001136 |
| Docling (CPU) | c5.2xlarge | 928/hr | 12 | $2,937.60 | $0.0002938 |
| Docling (GPU) *(est.)* | g4dn.xlarge | 900/hr | 12 | $4,534.56 | $0.0004535 |
| Mixed pipeline | mixed | — | 3 | $422.15 | $0.0000422 |

> **Instance count formula:** `ceil(10M pages / (720 hr/month × throughput))`
> where 720 = 24 hr × 30 days, assuming 100% utilisation. In practice,
> over-provision by 20–30% for burst headroom.

**At 10M pages/month, even Docling GPU (est.) at $4,535 saves $145,465/month
vs Textract Analyze Document.**

---

## Factors Not Captured in Compute Cost

### Costs that increase self-hosting total cost of ownership

| Factor | Estimate | Notes |
| --- | --- | --- |
| Engineering ops (patching, monitoring) | 4–8 hrs/month | Amortised across tools |
| Model updates / dependency upgrades | 1–2 hrs/quarter | Docling, PaddleOCR models update frequently |
| Storage (model weights) | $0.023/GB/month (S3) | PaddleOCR ~200 MB, Docling ~1.5 GB: <$0.05/month |
| Data transfer (if Lambda/API pattern) | ~$0.09/GB out | Negligible for text extraction payloads |
| Monitoring (CloudWatch or equivalent) | $3–$10/month | |

**Total additional overhead estimate: $50–$200/month** for a production
deployment. Immaterial at 100K+ pages/month but represents a large fraction of
compute cost at 10K pages/month.

### Factors that favour self-hosting (non-cost)

- **Data residency:** Documents never leave your infrastructure — no S3
  upload, no Textract API call, no data traversing AWS network boundaries.
- **Latency:** PyMuPDF at 6ms/doc vs Textract at 0.5–5s/page for synchronous
  workflows. For real-time pipelines, latency reduction is often more valuable
  than cost reduction.
- **No vendor lock-in:** Tool can be swapped without changing billing model,
  infrastructure, or downstream code (shared `BaseExtractor` interface).
- **Accuracy tuning:** Open-source tools can be fine-tuned on domain-specific
  documents. Textract cannot be fine-tuned.

### Remaining Textract advantages

- **No infrastructure management:** No EC2 provisioning, OS patching, or
  model version management.
- **Automatic scaling:** Textract handles burst traffic without
  over-provisioning or queue design.
- **Textract-specific features:** Queries API, Identity Documents, Expense
  analysis — no direct open-source equivalent.
- **Handwriting:** Textract significantly outperforms all five evaluated tools
  on handwritten content. No open-source alternative is viable.
- **SLA:** Textract carries AWS enterprise SLA; self-hosted has none.

---

## Summary: Executive Cost Table

Monthly cost including compute only (no overhead). Based on Textract Analyze
Document ($0.015/page) as the relevant baseline.

| Tool | 10K pages/mo | 100K pages/mo | 1M pages/mo | 10M pages/mo | Saving at 1M |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Textract (Analyze Doc)** | **$150** | **$1,500** | **$15,000** | **$150,000** | baseline |
| PyMuPDF (native only) | $0.02 | $0.21 | $2.08 | $29.95 | **99.99%** |
| Tesseract | $0.07 | $0.73 | $7.31 | $73.10 | **99.95%** |
| OpenDataLoader | $0.35 | $3.45 | $34.50 | $345.00 | **99.8%** |
| PaddleOCR (CPU) | $0.40 | $4.04 | $40.40 | $404.00 | **99.7%** |
| PaddleOCR (GPU) *(est.)* | $2.19 | $21.90 | $219.00 | $2,190.00 | **98.5%** |
| Docling (CPU) | $3.66 | $36.60 | $366.00 | $3,660.00 | **97.6%** |
| Docling (GPU) *(est.)* | $5.84 | $58.40 | $584.00 | $5,840.00 | **96.1%** |
| **Mixed pipeline** | **$0.34** | **$3.37** | **$33.70** | **$337.00** | **99.8%** |

---

## Recommendation

| Workload | Recommended tool | Infrastructure | Break-even |
| --- | --- | --- | ---: |
| Native PDFs (text layer) | PyMuPDF | t3.medium ($30/mo) | 2,000 pages/mo |
| Native PDFs (tables required) | OpenDataLoader | t3.large ($60/mo) | 4,000 pages/mo |
| Scanned PDFs, speed priority | Tesseract | t3.medium ($30/mo) | 2,000 pages/mo |
| Scanned PDFs, accuracy priority | PaddleOCR CPU | c5.xlarge ($122/mo) | 8,200 pages/mo |
| Table-heavy scanned documents | Docling CPU | c5.2xlarge ($245/mo) | 16,300 pages/mo |
| Handwritten content | **Retain Textract** | n/a | n/a |
| Mixed production pipeline | PyMuPDF + PaddleOCR | t3.medium + c5.xlarge ($152/mo) | 10,200 pages/mo |

**Minimum viable migration** (text-only, no tables): Deploy PyMuPDF for native
PDFs and Tesseract for scanned PDFs on a single t3.medium ($30/month). Break-
even occurs at ~2,000 pages/month against Analyze Document pricing.

**Full pipeline migration** (native + scanned + table extraction): PyMuPDF +
PaddleOCR + Docling on two instances. Total infrastructure cost ~$152–$375/month.
Break-even at ~10,000–25,000 pages/month. At 1M pages/month the annual saving
exceeds **$179,000**.

GPU instances improve Docling and PaddleOCR throughput (not yet directly
measured) but raise break-even points due to higher instance cost. GPU
acceleration is recommended only above ~25,000 pages/month or where latency
SLAs require sub-second response times.

---

## Appendix: Assumptions and Limitations

1. **All compute costs are on-demand EC2 pricing.** Reserved Instances
   (1-year) reduce costs by 30–40% and would lower all break-even thresholds
   proportionally.

2. **GPU latency figures are projected, not measured.** PaddleOCR and Docling
   GPU latency are estimated from PaddleOCR documentation and Docling issue
   tracker reports. They should be validated with a direct benchmark before
   committing to GPU infrastructure.

3. **Throughput assumes 100% CPU utilisation.** Real deployments should
   provision for 70–80% peak utilisation to handle burst; instance counts and
   costs at 10M pages/month should be multiplied by ~1.25–1.4.

4. **Single-page document throughput.** All latency figures are from single-
   page RVL-CDIP documents. Multi-page documents scale approximately linearly
   for most tools; Docling may be sublinear due to model initialization
   amortised across pages.

5. **Network and storage costs are excluded.** At typical text extraction
   payload sizes (<100 KB/page), transfer and storage costs are under $1/month
   at 1M pages and are omitted from the main analysis.

6. **Textract pricing may change.** AWS adjusts Textract pricing periodically.
   Verify current pricing at https://aws.amazon.com/textract/pricing/ before
   production planning.
