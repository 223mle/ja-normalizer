"""PipelineService — high-level orchestration layer for normalization.

This class belongs to the **domain layer** and only depends on:
    • Pydantic-based domain models
    • Abstract ports (Detector, Normalizer)

It exposes a single public method `normalize()` that takes a
:class:`NormalizationRequest` and returns a :class:`CorrectionResult`.
Optionally it can render the result into JSON / TEXT using helper
methods on the model, but all I/O (API, CLI, DB) is outside this layer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..models import (
    CorrectionResult,
    NormalizationRequest,
    OutputFormat,
)

if TYPE_CHECKING:
    from ..ports import Detector, Normalizer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, *, detector: Detector, normalizer: Normalizer) -> None:
        self._detector = detector
        self._normalizer = normalizer

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def normalize(
        self, request: NormalizationRequest, *, render: bool = False
    ) -> CorrectionResult | str | dict[str, Any]:
        """Run detection → correction and return results.

        Parameters
        ----------
        request : NormalizationRequest
            Input payload containing the target text and desired output format.
        render : bool, default=False
            If *True*, returns a **formatted** representation (str or dict)
            according to `request.output_format`. When *False*, returns the
            raw :class:`CorrectionResult` domain object.

        """
        # 1. Validation is already handled by Pydantic, but we guard anyway.
        if not isinstance(request, NormalizationRequest):
            raise TypeError('`request` must be a NormalizationRequest instance')

        logger.debug('Starting normalization pipeline (len=%d)', len(request.text))

        # 2. Detect direct-translation spans
        detection = self._detector.detect(request.text)
        logger.debug(
            'Detection completed: %d spans, score=%.3f', len(detection.detection_spans), detection.signature_score
        )

        # 3. Generate corrected text
        correction = self._normalizer.normalize(request.text, detection)
        logger.debug('Correction completed: %d replacements', len(correction.diffs))

        if not render:
            return correction

        # 4. Render according to desired output format
        if request.output_format is OutputFormat.TEXT:
            return correction.to_text()
        if request.output_format is OutputFormat.JSON:
            return correction.to_json()

        # Future-proof: if new formats are added but not yet handled.
        logger.warning('Unhandled output format %s — returning raw model', request.output_format)
        return correction
