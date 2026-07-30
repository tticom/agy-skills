#!/usr/bin/env python3
"""Fail closed when an approval lacks reviewer-created falsification evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class EvidenceError(ValueError):
    pass


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{field} must be non-empty text")
    return value.strip()


def validate(packet: dict[str, Any], *, prior_overturns: int, high_risk: bool) -> tuple[int, int]:
    if packet.get("verdict") != "APPROVE":
        raise EvidenceError("gate is only valid for verdict APPROVE")

    claims = packet.get("claims")
    if not isinstance(claims, list) or not claims:
        raise EvidenceError("claims must be a non-empty list")
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise EvidenceError(f"claims[{index}] must be an object")
        for field in ("claim", "production_path", "evidence_path", "false_success_mutation"):
            text(claim.get(field), f"claims[{index}].{field}")
        if claim.get("status") != "verified":
            raise EvidenceError(f"claims[{index}].status must be verified")

    probes = packet.get("probes")
    if not isinstance(probes, list):
        raise EvidenceError("probes must be a list")
    required = max(3 if high_risk else 2, 2) + min(max(prior_overturns, 0), 2)
    if len(probes) < required:
        raise EvidenceError(f"need at least {required} reviewer-created probes; found {len(probes)}")

    commands: set[str] = set()
    mutations: set[str] = set()
    production_count = 0
    score = 0
    for index, probe in enumerate(probes):
        if not isinstance(probe, dict):
            raise EvidenceError(f"probes[{index}] must be an object")
        if probe.get("reviewer_created") is not True:
            raise EvidenceError(f"probes[{index}] is not reviewer-created")
        if probe.get("author_test_only") is not False:
            raise EvidenceError(f"probes[{index}] must not be author-test-only")
        if probe.get("result") not in {"killed", "exposed"}:
            raise EvidenceError(f"probes[{index}].result must be killed or exposed")
        for field in ("name", "command", "input", "false_success_mutation", "observed_output", "invariant"):
            text(probe.get(field), f"probes[{index}].{field}")
        command = probe["command"].strip()
        mutation = probe["false_success_mutation"].strip()
        if command in commands:
            raise EvidenceError(f"duplicate probe command: {command}")
        if mutation in mutations:
            raise EvidenceError(f"duplicate false-success mutation: {mutation}")
        commands.add(command)
        mutations.add(mutation)
        if probe.get("production_path") is True:
            production_count += 1
        score += 2

    required_production = 2 if high_risk else 1
    if production_count < required_production:
        raise EvidenceError(
            f"need {required_production} production-path probes; found {production_count}"
        )

    risks = packet.get("residual_risks")
    if not isinstance(risks, list) or not risks:
        raise EvidenceError("residual_risks must be a non-empty list")
    banned = {"none", "no risk", "no risks", "zero", "n/a"}
    for index, risk in enumerate(risks):
        normalized = text(risk, f"residual_risks[{index}]").lower().rstrip(".")
        if normalized in banned:
            raise EvidenceError("zero-risk claims are forbidden")

    expected = (
        "I personally ran every listed probe against the pinned review head "
        "and recorded observed output without inference."
    )
    if packet.get("integrity_attestation") != expected:
        raise EvidenceError("integrity_attestation is missing or not exact")
    return required, score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--prior-overturns", type=int, default=0)
    parser.add_argument("--high-risk", action="store_true")
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        if not isinstance(packet, dict):
            raise EvidenceError("packet root must be an object")
        required, score = validate(
            packet,
            prior_overturns=args.prior_overturns,
            high_risk=args.high_risk,
        )
    except (OSError, json.JSONDecodeError, EvidenceError) as error:
        raise SystemExit(f"APPROVAL_EVIDENCE_GATE=FAIL: {error}") from error
    print(f"APPROVAL_EVIDENCE_GATE=PASS required_probes={required} score={score}")


if __name__ == "__main__":
    main()
