# ---------------------------------------------------------------------------
# Domain > Ports (Abstract Interfaces)
# ---------------------------------------------------------------------------

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .models import CorrectionResult, DetectionResult


# ---------------------------------------------------------------------------
# Shared DTOs (light-weight; kept here to avoid circular imports)
# ---------------------------------------------------------------------------


class Token(BaseModel):
    """A minimal token emitted by a TextAnalyzer."""

    surface: str = Field(..., description='Original surface form')
    pos: str = Field(..., description='Part-of-speech tag (名詞, 動詞, etc.)')
    start_position: int = Field(..., ge=0, description='Offset (inclusive)')
    end_position: int = Field(..., gt=0, description='Offset (exclusive)')

    model_config = {
        'frozen': True,  # make instances hashable / immutable
    }


# ---------------------------------------------------------------------------
# Inbound / Outbound Port Definitions
# ---------------------------------------------------------------------------


@runtime_checkable
class TextAnalyzer(Protocol):
    """Outbound port for morphological or semantic tokenization."""

    def tokenize(self, text: str) -> Iterable[Token]:
        """Return an iterator of :class:`Token` objects for *text*."""


class Detector(abc.ABC):
    """Outbound port that detects direct-translation spans in Japanese text."""

    @abc.abstractmethod
    def detect(self, text: str) -> DetectionResult:
        """Analyze *text* and return :class:`DetectionResult`."""


class Normalizer(abc.ABC):
    """Outbound port that generates natural Japanese corrections."""

    @abc.abstractmethod
    def normalize(self, text: str, detection: DetectionResult) -> CorrectionResult:
        """Return a :class:`CorrectionResult` based on *detection*."""
