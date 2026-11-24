"""
Unforgeable Pydantic v2 Execution Provenance Schemas.

Guarantees scientific transparency between empirical live NVIDIA NIM API calls,
partial/fallback hybrid runs, and deterministic in-silico heuristic simulations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


class ExecutionMode(StrEnum):
    """Aggregate execution mode computed strictly from verified stage statuses."""

    LIVE_NVIDIA_NIM = "LIVE_NVIDIA_NIM"
    HYBRID_FALLBACK = "HYBRID_FALLBACK"
    HEURISTIC_SIMULATION = "HEURISTIC_SIMULATION"


class StageStatus(StrEnum):
    """Observed per-stage execution source."""

    LIVE = "LIVE"
    FALLBACK = "FALLBACK"
    MOCK = "MOCK"


class StageProvenance(BaseModel):
    """Immutable cryptographic/telemetry record for a single pipeline stage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage_name: str = Field(..., min_length=1, max_length=80)
    status: StageStatus
    model_id: str | None = None
    endpoint_url: str | None = None
    http_status: int | None = None
    nim_request_id: str | None = None
    latency_ms: float = Field(default=0.0, ge=0.0)
    fallback_reason: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _enforce_epistemic_invariants(self) -> StageProvenance:
        if self.status == StageStatus.LIVE:
            if self.http_status != 200:
                raise ValueError(
                    f"Stage '{self.stage_name}' marked LIVE requires http_status == 200 (got {self.http_status})."
                )
            if not self.endpoint_url or not self.endpoint_url.strip():
                raise ValueError(
                    f"Stage '{self.stage_name}' marked LIVE requires non-empty endpoint_url."
                )
            if not self.nim_request_id or not self.nim_request_id.strip():
                raise ValueError(
                    f"Stage '{self.stage_name}' marked LIVE requires non-empty nim_request_id."
                )
            if self.fallback_reason is not None:
                raise ValueError(
                    f"Stage '{self.stage_name}' marked LIVE cannot carry fallback_reason."
                )
        elif self.status == StageStatus.FALLBACK:
            if not self.fallback_reason or not self.fallback_reason.strip():
                raise ValueError(
                    f"Stage '{self.stage_name}' marked FALLBACK requires a non-empty fallback_reason."
                )
        elif self.status == StageStatus.MOCK:
            if self.nim_request_id is not None or self.http_status is not None:
                raise ValueError(
                    f"Stage '{self.stage_name}' marked MOCK cannot carry live nim_request_id or http_status."
                )
        return self


class CampaignProvenance(BaseModel):
    """Unforgeable campaign-level provenance envelope computed exclusively from stages."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stages: tuple[StageProvenance, ...] = Field(..., min_length=1)
    backend_host: str = Field(..., min_length=1)
    rdkit_version: str = Field(..., min_length=1)
    elapsed_ms: float = Field(default=0.0, ge=0.0)
    seed: int = 42
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def overall_mode(self) -> ExecutionMode:
        statuses = {stage.status for stage in self.stages}
        if statuses == {StageStatus.LIVE}:
            return ExecutionMode.LIVE_NVIDIA_NIM
        if StageStatus.LIVE in statuses:
            return ExecutionMode.HYBRID_FALLBACK
        return ExecutionMode.HEURISTIC_SIMULATION

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mode(self) -> ExecutionMode:
        return self.overall_mode

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_simulated(self) -> bool:
        return self.overall_mode != ExecutionMode.LIVE_NVIDIA_NIM

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nim_endpoints_called(self) -> list[str]:
        return [
            stage.endpoint_url
            for stage in self.stages
            if stage.status == StageStatus.LIVE and stage.endpoint_url
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def request_ids(self) -> list[str]:
        return [
            stage.nim_request_id
            for stage in self.stages
            if stage.status == StageStatus.LIVE and stage.nim_request_id
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def simulated_stages(self) -> list[str]:
        return [
            stage.stage_name
            for stage in self.stages
            if stage.status != StageStatus.LIVE
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pdf_watermark(self) -> str:
        if self.overall_mode == ExecutionMode.LIVE_NVIDIA_NIM:
            return "VERIFIED NVIDIA NIM EXECUTION"
        if self.overall_mode == ExecutionMode.HYBRID_FALLBACK:
            return "HYBRID NIM + HEURISTIC FALLBACK"
        return "HEURISTIC SIMULATION — NOT FOR CLINICAL USE"
