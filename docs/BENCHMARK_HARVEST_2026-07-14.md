# Benchmark harvest: document and evaluation systems

Reviewed 2026-07-14. This record captures ideas, licenses, and explicit adopt/reject decisions; no source was copied.

| System | Verified license | Pattern reviewed | Decision | Pramaan implementation |
|---|---|---|---|---|
| Docling | MIT | A unified document representation with typed content, reading hierarchy, layout, and provenance | Adopt the model boundary; defer the full parser dependency | `backend/platform/document_model.py` normalizes items and provenance without inventing missing pages, boxes, or confidence |
| Unstructured | Apache-2.0 | Type detection followed by a format-specific partition strategy, with fast/high-resolution/OCR choices | Adopt explicit routing and metadata; reject the large dependency surface for the bounded demo | Existing upload magic checks and PDF/image/text extractors remain format-specific and now adapt into the normalized document model |
| Langfuse | MIT outside its enterprise directories; repository-specific license for enterprise paths | Trace/evaluation separation, datasets, and correlated generation telemetry | Adopt vendor-neutral OpenTelemetry correlation and frozen eval artifacts; reject embedding or copying its application | Optional OTLP tracing, request IDs, benchmark manifests, calibration reports, and provider timing remain local interfaces |

## Rationale

Docling’s model usefully separates content items from document structure and retains provenance. Pramaan needs that contract even before it needs a richer parser, because citation correctness cannot be audited if extraction loses its source.

Unstructured’s routing demonstrates why one generic text extractor is insufficient. Pramaan already rejects disguised uploads and chooses PDF, image, or text extraction explicitly. The next parser can implement the normalized contract without changing analysis or API code.

Langfuse demonstrates a strong operational separation between traces and evaluation datasets. Pramaan keeps the same separation with OpenTelemetry for runtime evidence and immutable benchmark/calibration artifacts for quality evidence. No Langfuse enterprise code or schema is used.

## Primary sources

- Docling document representation: https://docling-project.github.io/docling/concepts/docling_document/
- Docling license: https://github.com/docling-project/docling/blob/main/LICENSE
- Unstructured partitioning: https://docs.unstructured.io/open-source/core-functionality/partitioning
- Unstructured license: https://github.com/Unstructured-IO/unstructured/blob/main/LICENSE.md
- Langfuse repository and license: https://github.com/langfuse/langfuse
