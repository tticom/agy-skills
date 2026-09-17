#!/usr/bin/env python3
import copy
import unittest

from review_evidence_gate import EvidenceError, validate

HEAD = "a" * 40
PRIOR = "b" * 40


def packet(head=HEAD):
    probes = []
    for number in (1, 2):
        probes.append({
            "name": f"probe-{number}", "reviewer_created": True,
            "artifact_origin": "reviewer-created", "artifact_path": f"reviewer://probe-{number}",
            "oracle_authority": "product contract section 4", "author_test_only": False,
            "result": "killed", "command": f"python /tmp/probe-{number}.py",
            "input": "controlled input", "false_success_mutation": f"mutation-{number}",
            "observed_output": "rejected", "invariant": "invalid input is rejected",
            "execution_receipt": f"receipt-{head[:4]}-{number}", "executed_head": head,
            "fresh_execution": True, "targets_delta_claims": ["D1"],
            "production_path": number == 1,
        })
    return {
        "schema_version": 2, "verdict": "APPROVE", "review_head": head,
        "prior_review_head": None, "changed_test_paths": ["tests/test_changed.py"],
        "remediation_deltas": [],
        "head_delta_claims": [{"id": "D1", "changed_path": "src/x.py", "changed_hunk": "f", "risk": "false accept"}],
        "claims": [{"claim": "works", "production_path": "src/x.py", "evidence_path": "probe", "false_success_mutation": "remove guard", "status": "verified"}],
        "probes": probes,
        "counterexample_registry": [{"id": "C1", "origin_head": head, "invariant": "invalid input rejected", "current_probe": "probe-1"}],
        "test_evidence": [{
            "test_node": "test", "input_control": "direct", "production_boundary": "f",
            "assertion": "reject", "claim": "guard", "inspected_head": head,
            "data_class": "REAL_SOURCE_END_TO_END", "source_artifact": "fixture.pdf",
            "provenance_receipt": "sha256:source", "oracle": "reference score semantic diff",
            "oracle_independent": True,
        }],
        "real_artifacts_exercised": ["fixture.pdf@sha256:source"],
        "fixture_coupling": {
            "scanner_result": "PASS", "manual_review": True,
            "production_paths": ["src/x.py"], "fixture_identifiers_found": [],
        },
        "residual_risks": ["unseen parser variants"],
        "integrity_attestation": "I personally ran every listed probe against the pinned review head and recorded observed output without inference.",
    }


class EvidenceGateTest(unittest.TestCase):
    def test_valid_initial_packet(self):
        self.assertEqual(validate(packet(), prior_overturns=0, high_risk=False, expected_head=HEAD), (2, 4))

    def test_changed_author_test_cannot_be_probe(self):
        value = packet()
        value["probes"][0]["artifact_path"] = "tests/test_changed.py"
        value["probes"][0]["command"] = "pytest tests/test_changed.py"
        with self.assertRaisesRegex(EvidenceError, "author-changed test"):
            validate(value, prior_overturns=0, high_risk=False, expected_head=HEAD)

    def test_hard_review_rejects_synthetic_acceptance_evidence(self):
        value = packet()
        value["probes"].append(copy.deepcopy(value["probes"][0]))
        value["probes"][2].update({
            "name": "probe-3", "artifact_path": "reviewer://probe-3",
            "command": "python /tmp/probe-3.py", "false_success_mutation": "mutation-3",
            "execution_receipt": "receipt-hard-3",
        })
        value["test_evidence"][0]["data_class"] = "SYNTHETIC_OR_MOCKED"
        with self.assertRaisesRegex(EvidenceError, "real-source acceptance"):
            validate(value, prior_overturns=0, high_risk=True, expected_head=HEAD)

    def test_devils_advocate_requires_four_probes(self):
        value = packet()
        value["probes"].append(copy.deepcopy(value["probes"][0]))
        value["probes"][2].update({
            "name": "probe-3", "artifact_path": "reviewer://probe-3",
            "command": "python /tmp/probe-3.py", "false_success_mutation": "mutation-3",
            "execution_receipt": "receipt-devil-3",
        })
        with self.assertRaisesRegex(EvidenceError, "at least 4"):
            validate(
                value, prior_overturns=0, high_risk=True, expected_head=HEAD,
                devils_advocate=True,
            )

    def test_valid_devils_advocate_packet(self):
        value = packet()
        for number in (3, 4):
            probe = copy.deepcopy(value["probes"][0])
            probe.update({
                "name": f"probe-{number}",
                "artifact_path": f"reviewer://probe-{number}",
                "command": f"python /tmp/probe-{number}.py",
                "false_success_mutation": f"mutation-{number}",
                "execution_receipt": f"receipt-devil-{number}",
            })
            value["probes"].append(probe)
        self.assertEqual(
            validate(
                value, prior_overturns=0, high_risk=True, expected_head=HEAD,
                devils_advocate=True,
            ),
            (4, 8),
        )

    def test_governance_control_plane_packet_can_omit_real_source_evidence(self):
        value = packet()
        value["evidence_scope"] = "governance_control_plane"
        value["inapplicability_rationale"] = (
            "The reviewed behavior is a Git/GitHub control-plane state transition; "
            "no domain source artifact enters the production path."
        )
        value["control_plane_oracle"] = (
            "Exact state, identity, cleanliness, and exit-code assertions against "
            "the dispatcher contract."
        )
        value["real_artifacts_exercised"] = []
        value["fixture_coupling"] = {
            "scanner_result": "NOT_APPLICABLE",
            "manual_review": True,
            "production_paths": ["scripts/score2gp_dispatch.py"],
            "fixture_identifiers_found": [],
        }
        value["test_evidence"][0].update({
            "data_class": "CONTROL_PLANE",
            "oracle": "independent dispatcher state contract",
            "oracle_independent": True,
        })
        for number in (3, 4):
            probe = copy.deepcopy(value["probes"][0])
            probe.update({
                "name": f"probe-{number}",
                "artifact_path": f"reviewer://probe-{number}",
                "command": f"python /tmp/probe-{number}.py",
                "false_success_mutation": f"mutation-{number}",
                "execution_receipt": f"receipt-governance-{number}",
            })
            value["probes"].append(probe)
        self.assertEqual(
            validate(
                value, prior_overturns=0, high_risk=True, expected_head=HEAD,
                devils_advocate=True,
            ),
            (4, 8),
        )

    def test_governance_scope_requires_inapplicability_rationale(self):
        value = packet()
        value["evidence_scope"] = "governance_control_plane"
        with self.assertRaisesRegex(EvidenceError, "inapplicability_rationale"):
            validate(value, prior_overturns=0, high_risk=True, expected_head=HEAD)

    def test_rereview_requires_remediation_threat_model(self):
        prior = packet(PRIOR)
        value = packet()
        value["prior_review_head"] = PRIOR
        with self.assertRaisesRegex(EvidenceError, "remediation delta threat model"):
            validate(value, prior_overturns=0, high_risk=False, expected_head=HEAD, prior_packet=prior)

    def test_rereview_cannot_drop_prior_counterexample(self):
        prior = packet(PRIOR)
        prior["counterexample_registry"].append({"id": "C2", "origin_head": PRIOR, "invariant": "boundary", "current_probe": "probe-2"})
        value = packet()
        value["prior_review_head"] = PRIOR
        value["remediation_deltas"] = [{"finding_id": "F1", "changed_symbols": "f", "fix_assumption": "strict bound", "new_branches": "one reject branch", "adjacent_risks": "off by one", "authority_citation": "spec section 4", "oracle_changed": False}]
        with self.assertRaisesRegex(EvidenceError, "dropped prior counterexamples"):
            validate(value, prior_overturns=0, high_risk=False, expected_head=HEAD, prior_packet=prior)


if __name__ == "__main__":
    unittest.main()
