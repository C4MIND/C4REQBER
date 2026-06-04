"""Reproducibility Validator for C4REQBER.

Checklist validation, provenance tracking, and result hash verification
based on reproducibility standards (FAIR, Turing Way).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

from src.compat import UTC


class CheckStatus(Enum):
    """CheckStatus."""
    PASS = auto()
    FAIL = auto()
    WARN = auto()
    SKIP = auto()


@dataclass(frozen=True)
class CheckItem:
    """CheckItem."""
    id: str
    category: str
    description: str
    required: bool = True


@dataclass
class CheckResult:
    """CheckResult."""
    item: CheckItem
    status: CheckStatus
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.item.id,
            "category": self.item.category,
            "description": self.item.description,
            "required": self.item.required,
            "status": self.status.name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


STANDARD_CHECKLIST: list[CheckItem] = [
    CheckItem("data_avail", "Data", "Raw data is available and documented", True),
    CheckItem("code_avail", "Code", "Source code is version-controlled and accessible", True),
    CheckItem(
        "env_spec", "Environment",
        "Software dependencies are specified (requirements, lock files)", True,
    ),
    CheckItem("random_seed", "Methodology", "Random seeds are set and reported", True),
    CheckItem(
        "params_doc", "Methodology",
        "All hyperparameters and configuration are documented", True,
    ),
    CheckItem("stats_report", "Analysis", "Statistical methods are fully described", True),
    CheckItem("pre_reg", "Analysis", "Analysis plan was pre-registered (optional)", False),
    CheckItem(
        "replication", "Validation",
        "Independent replication was attempted (optional)", False,
    ),
    CheckItem("license", "Legal", "Code and data have appropriate licenses", True),
    CheckItem("citation", "Documentation", "All external resources are cited", True),
]


@dataclass
class ProvenanceRecord:
    """ProvenanceRecord."""
    step_name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source_file: str | None = None
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_name": self.step_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "source_file": self.source_file,
            "line_number": self.line_number,
        }


@dataclass
class ProvenanceLog:
    """ProvenanceLog."""
    experiment_id: str
    records: list[ProvenanceRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_record(self, record: ProvenanceRecord) -> None:
        self.records.append(record)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "created_at": self.created_at.isoformat(),
            "n_records": len(self.records),
            "records": [r.to_dict() for r in self.records],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_result_hash(data: Any, algorithm: str = "sha256") -> str:
    """Compute result hash."""
    canonical = _canonical_json(data)
    hasher = hashlib.new(algorithm)
    hasher.update(canonical.encode("utf-8"))
    return hasher.hexdigest()


def compute_file_hash(path: Path | str, algorithm: str = "sha256") -> str:
    """Compute file hash."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    hasher = hashlib.new(algorithm)
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass
class ReproducibilityReport:
    """ReproducibilityReport."""
    experiment_id: str
    check_results: list[CheckResult]
    provenance: ProvenanceLog
    result_hashes: dict[str, str] = field(default_factory=dict)
    overall_score: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score,
            "result_hashes": self.result_hashes,
            "check_results": [c.to_dict() for c in self.check_results],
            "provenance": self.provenance.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


class ReproducibilityValidator:
    """ReproducibilityValidator."""
    def __init__(
        self,
        experiment_id: str,
        checklist: list[CheckItem] | None = None,
    ) -> None:
        self.experiment_id = experiment_id
        self.checklist = checklist or STANDARD_CHECKLIST.copy()
        self.provenance = ProvenanceLog(experiment_id=experiment_id)
        self.result_hashes: dict[str, str] = {}

    def validate_checklist(
        self,
        checks: dict[str, tuple[CheckStatus, str]],
    ) -> list[CheckResult]:
        """Validate checklist."""
        results: list[CheckResult] = []
        for item in self.checklist:
            status, message = checks.get(item.id, (CheckStatus.SKIP, "Not evaluated"))
            results.append(CheckResult(item=item, status=status, message=message))
        return results

    def quick_validate(
        self,
        data_available: bool = False,
        code_available: bool = False,
        env_specified: bool = False,
        seeds_set: bool = False,
        params_documented: bool = False,
        stats_described: bool = False,
        pre_registered: bool | None = None,
        replication_attempted: bool | None = None,
        licensed: bool = False,
        cited: bool = False,
    ) -> list[CheckResult]:
        """Quick validate."""
        checks: dict[str, tuple[CheckStatus, str]] = {
            "data_avail": (CheckStatus.PASS if data_available else CheckStatus.FAIL, ""),
            "code_avail": (CheckStatus.PASS if code_available else CheckStatus.FAIL, ""),
            "env_spec": (CheckStatus.PASS if env_specified else CheckStatus.FAIL, ""),
            "random_seed": (CheckStatus.PASS if seeds_set else CheckStatus.FAIL, ""),
            "params_doc": (CheckStatus.PASS if params_documented else CheckStatus.FAIL, ""),
            "stats_report": (CheckStatus.PASS if stats_described else CheckStatus.FAIL, ""),
            "license": (CheckStatus.PASS if licensed else CheckStatus.FAIL, ""),
            "citation": (CheckStatus.PASS if cited else CheckStatus.FAIL, ""),
        }
        if pre_registered is not None:
            checks["pre_reg"] = (
                CheckStatus.PASS if pre_registered else CheckStatus.WARN,
                "Pre-registration optional but recommended",
            )
        if replication_attempted is not None:
            checks["replication"] = (
                CheckStatus.PASS if replication_attempted else CheckStatus.WARN,
                "Replication optional but recommended",
            )
        return self.validate_checklist(checks)

    def add_provenance(
        self,
        step_name: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        source_file: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Add provenance."""
        record = ProvenanceRecord(
            step_name=step_name,
            inputs=inputs or {},
            outputs=outputs or {},
            parameters=parameters or {},
            source_file=source_file,
            line_number=line_number,
        )
        self.provenance.add_record(record)

    def hash_result(self, name: str, data: Any) -> str:
        """Hash result."""
        h = compute_result_hash(data)
        self.result_hashes[name] = h
        return h

    def verify_result(self, name: str, data: Any) -> tuple[bool, str | None]:
        """Verify result."""
        expected = self.result_hashes.get(name)
        if expected is None:
            return False, None
        actual = compute_result_hash(data)
        return actual == expected, actual

    def compute_score(self, check_results: list[CheckResult]) -> float:
        """Compute score."""
        if not check_results:
            return 0.0
        required = [c for c in check_results if c.item.required]
        optional = [c for c in check_results if not c.item.required]
        req_score = (
            sum(1.0 for c in required if c.status == CheckStatus.PASS)
            / max(len(required), 1)
        )
        opt_score = (
            sum(0.5 for c in optional if c.status == CheckStatus.PASS)
            / max(len(optional), 1)
        )
        return float(req_score + opt_score * 0.2)

    def generate_report(
        self,
        check_results: list[CheckResult] | None = None,
    ) -> ReproducibilityReport:
        """Generate report."""
        if check_results is None:
            check_results = self.quick_validate()
        score = self.compute_score(check_results)
        return ReproducibilityReport(
            experiment_id=self.experiment_id,
            check_results=check_results,
            provenance=self.provenance,
            result_hashes=self.result_hashes.copy(),
            overall_score=score,
        )
