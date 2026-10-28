import uuid

import pytest
from pydantic import ValidationError

from src.core.schemas import CitationSpan, IngestedChunkCreate

SOURCE_CHUNK = (
    "Section 12.2 Limitation of Liability. Notwithstanding anything to the contrary, "
    "Vendor’s aggregate liability under this Agreement shall not\n   exceed “$50,000” "
    "for any claims arising in a twelve (12) month period."
)


def test_exact_verbatim_quote_passes() -> None:
    span = CitationSpan(
        document_id=uuid.uuid4(),
        tenant_id="tenant_alpha",
        page_number=4,
        section_heading="12.2 Limitation of Liability",
        verbatim_quote='Vendor’s aggregate liability under this Agreement shall not\n   exceed “$50,000”',
        source_chunk_text=SOURCE_CHUNK,
    )
    assert span.page_number == 4
    # Verify source_chunk_text is excluded when serialized to JSON/dict for the API response
    assert "source_chunk_text" not in span.model_dump()


def test_dirty_pdf_whitespace_and_smart_quotes_pass() -> None:
    # LLM outputs clean straight quotes and single spaces, while PDF has newlines and curly quotes
    span = CitationSpan(
        document_id=uuid.uuid4(),
        tenant_id="tenant_alpha",
        page_number=4,
        section_heading="12.2 Limitation of Liability",
        verbatim_quote='Vendor\'s aggregate liability under this Agreement shall not exceed "$50,000"',
        source_chunk_text=SOURCE_CHUNK,
    )
    assert "50,000" in span.verbatim_quote


def test_paraphrased_or_hallucinated_quote_fails() -> None:
    # LLM paraphrases "aggregate liability" as "total liability" -> MUST RAISE ValidationError
    with pytest.raises(ValidationError, match="Hallucinated citation"):
        CitationSpan(
            document_id=uuid.uuid4(),
            tenant_id="tenant_alpha",
            page_number=4,
            section_heading="12.2 Limitation of Liability",
            verbatim_quote='Vendor total liability under this Agreement shall not exceed "$50,000"',
            source_chunk_text=SOURCE_CHUNK,
        )


def test_ingested_chunk_rejects_whitespace_tenant() -> None:
    with pytest.raises(ValidationError):
        IngestedChunkCreate(
            document_id=uuid.uuid4(),
            tenant_id="   ",
            section_heading="1. Definitions",
            page_number=1,
            chunk_index=0,
            text_content="Valid contract text content here.",
        )