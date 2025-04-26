"""Domain-level data models for the Japanese direct-translation normalizer.

These models are **framework-agnostic** and reside in the domain layer.
Only standard library types and Pydantic v2 are used so that the domain
remains independent of external infrastructure.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class OutputFormat(str, enum.Enum):
    """Allowed output rendering formats."""

    JSON = 'json'
    TEXT = 'text'


class NormalizationRequest(BaseModel):
    text: str = Field(..., max_length=4_000, description='Target Japanese string to normalize.')
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON,
        description='Desired format of the returned result.',
    )

    # Extra guard against empty strings
    @field_validator('text')
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('text may not be empty or whitespace only')
        return v


class DetectionSpan(BaseModel):
    """A contiguous span in the input text flagged as a direct-translation candidate."""

    start_position: int = Field(..., ge=0, description='Start index (inclusive, UTF-8 code-point offset).')
    end_position: int = Field(..., gt=0, description='End index (exclusive). Must be > start.')
    detected_text: str = Field(..., description='The substring that triggered detection.')
    confidence_score: float = Field(..., ge=0.0, le=1.0, description='Confidence score (0-1).')

    @field_validator('end_position')
    @classmethod
    def _check_end_after_start(cls, v: int, info: ValidationInfo) -> int:
        if v <= info.data.get('start_position', 0):
            raise ValueError('`end_position` must be greater than `start_position`.')
        return v


class DetectionResult(BaseModel):
    """Aggregated output from the detection phase."""

    detection_spans: list[DetectionSpan] = Field(default_factory=list)
    signature_score: float = Field(..., ge=0.0, le=1.0, description='Overall direct-translation likelihood (0-1).')


class CorrectionSpan(BaseModel):
    """A single replacement suggestion produced by the correction engine."""

    original_text: str = Field(..., description='Original detected token.')
    suggestion: str = Field(..., description='Proposed natural Japanese alternative.')
    start_position: int = Field(..., ge=0, description='Start index in original text (inclusive).')
    end_position: int = Field(..., gt=0, description='End index (exclusive). Must be > start.')

    @field_validator('end')
    @classmethod
    def _check_end_after_start(cls, v: int, info: ValidationInfo) -> int:
        if v <= info.data.get('start', 0):
            raise ValueError('`end` must be greater than `start`.')
        return v


class CorrectionResult(BaseModel):
    """Final output returned to callers after correction."""

    corrected_text: str = Field(..., description='The fully normalized text.')
    diffs: list[CorrectionSpan] = Field(default_factory=list, description='List of applied replacements.')

    def to_text(self) -> str:
        """Return plain corrected text (helper for CLI)."""
        return self.corrected_text

    def to_json(self) -> dict[str, object]:
        """Return a JSON-serializable dict."""
        return self.model_dump(mode='json')
