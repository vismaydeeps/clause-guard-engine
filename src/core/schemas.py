"""Gates for inputand output data.
Input protects db against invalid data while parsing the pdf; Output protects users from LLM halllucinations."""


import uuid
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


def normalize_legal_text(text:str) -> str:
    """Normalizes whitespace and smart quotes for deterministic substring matching."""
    replacements = {
    "\u201c": '"',  # Left double quote (“)
    "\u201d": '"',  # Right double quote (”)
    "\u2018": "'",  # Left single quote (‘)
    "\u2019": "'",  # Right single quote (’)
    "\u2014": "-",  # Em dash (—)
    "\u2013": "-",  # En dash (–)
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split()).lower() # normalize whitespace and lowercase



class RiskSeverity(str, Enum):
    """Risk severity levels for legal text."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IngestedChunkCreate(BaseModel):
    """Input Gate: Validates chunks before they touch postgreSQL"""
    document_id: uuid.UUID
    tenant_id: str = Field(min_length=2, max_length=100)
    parent_section_id : str | None =None
    section_heading: str = Field(min_length=1, max_length=250)
    page_number : int = Field(ge=1)
    chunk_index : int = Field(ge=0)
    text_content: str = Field(min_length=10)

    @field_validator("tenant_id", "section_heading", "text_content")
    @classmethod
    def reject_blank_whitespaces(cls, v:str) -> str:
        """Rejects blank or whitespace only strings."""
        if not v.strip():
            raise ValueError("Field cannot be blank or whitespace only.")
        return v.strip()

class CitationSpan(BaseModel):
    """Output Gate Part 1: Forces every LLM claim to prove its quote exists in the source chunk."""
    document_id: uuid.UUID
    tenant_id: str = Field(min_length=2, max_length=100)
    page_number: int = Field(ge=1)
    section_heading: str
    verbatim_quote: str = Field(min_length=20)
    source_chunk_text: str = Field(exclude=True)  # Used for verification, hidden from final API JSON

    @model_validator(mode="after")
    def verify_verbatim_substring(self) -> "CitationSpan":
        norm_quote = normalize_legal_text(self.verbatim_quote)
        norm_source = normalize_legal_text(self.source_chunk_text)
        if norm_quote not in norm_source:
            raise ValueError(
                f"Hallucinated citation on page {self.page_number}: "
                f"Quote '{self.verbatim_quote[:50]}    ' not found verbatim in source chunk."
            )
        return self


class ClauseRiskFinding(BaseModel):
    """Output Gate Part 2: Complete structured risk assessment returned to the client."""
    clause_category: str = Field(min_length=3)
    severity: RiskSeverity
    contradicts_baseline_policy: bool
    risk_explanation: str = Field(min_length=15)
    recommended_redline: str = Field(min_length=15)
    citation: CitationSpan