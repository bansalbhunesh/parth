from backend.platform.document_model import BoundingBox, DocumentProvenance, from_extraction


def test_normalized_document_preserves_text_method_and_warning() -> None:
    document = from_extraction(
        "doc-1",
        "submittal.pdf",
        {"text": "Heading\nRequirement", "method": "ocr_pdf", "warning": "OCR was used"},
    )
    assert document.text == "Heading\nRequirement"
    assert document.items[0].provenance.extraction_method == "ocr_pdf"
    assert document.warnings == ["OCR was used"]


def test_normalized_document_does_not_invent_layout() -> None:
    document = from_extraction("doc-2", "plain.txt", {"text": "value", "method": "plain_text"})
    assert document.items[0].provenance.page is None
    assert document.items[0].provenance.bounding_box is None


def test_bounding_box_and_confidence_are_validated() -> None:
    provenance = DocumentProvenance(
        source_name="scan.png",
        extraction_method="ocr_image",
        page=1,
        bounding_box=BoundingBox(left=1, top=2, right=3, bottom=4),
        confidence=0.98,
    )
    assert provenance.bounding_box is not None
    assert provenance.confidence == 0.98
