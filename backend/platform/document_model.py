"""Normalized document structure with explicit provenance and reading order."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DocumentItemKind = Literal["title", "heading", "paragraph", "table", "picture", "key_value", "unknown"]


class BoundingBox(BaseModel):
    left: float
    top: float
    right: float
    bottom: float


class DocumentProvenance(BaseModel):
    source_name: str
    extraction_method: str
    page: int | None = Field(default=None, ge=1)
    bounding_box: BoundingBox | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class DocumentItem(BaseModel):
    item_id: str
    kind: DocumentItemKind
    text: str = ""
    parent_id: str | None = None
    provenance: DocumentProvenance


class NormalizedDocument(BaseModel):
    document_id: str
    source_name: str
    items: list[DocumentItem]
    warnings: list[str] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(item.text for item in self.items if item.text)


def from_extraction(document_id: str, source_name: str, extraction: dict[str, object]) -> NormalizedDocument:
    """Adapt the current text/OCR result without inventing unavailable layout."""
    text = str(extraction.get("text") or "")
    method = str(extraction.get("method") or "none")
    warning = extraction.get("warning")
    items = []
    if text:
        items.append(
            DocumentItem(
                item_id="item-0001",
                kind="paragraph",
                text=text,
                provenance=DocumentProvenance(source_name=source_name, extraction_method=method),
            )
        )
    return NormalizedDocument(
        document_id=document_id,
        source_name=source_name,
        items=items,
        warnings=[str(warning)] if warning else [],
    )
