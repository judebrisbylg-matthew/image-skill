import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "scripts" / "update_run_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("update_run_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._SUBMISSION_COORDINATOR = module._InMemorySubmissionCoordinator()
    return module


def batch_contract(*skc_ids):
    digest_payload = {
        "schema_version": 1,
        "member_skc_ids": list(skc_ids),
    }
    digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {**digest_payload, "digest": digest}


def ready_state(module):
    state = module.initialize_state(
        {
            "skc_id": "ds-test",
            "batch_contract": batch_contract("ds-test"),
            "views": {"front": {"status": "ready"}},
        },
        verified_execution_context(),
    )
    module.record_layout_reservation(
        state,
        date_region="8月14日",
        skc_label="ds-test · V2测试",
        verified=True,
    )
    return state


def task_label(view, action_id, attempt=1):
    return f"SKC ds-test | VIEW {view} | ACTION {action_id} | ATTEMPT {attempt}"


def batch_context(*states):
    return {
        "schema_version": 1,
        "skc_ids": [state["skc_id"] for state in states],
        "states": list(states),
    }


def submit_action(module, state, view, action_id, *batch_states):
    attempt = state["views"][view]["actions"][action_id]["attempts"] + 1
    return module.transition_action(
        state,
        view,
        action_id,
        "submitted",
        task_label=task_label(view, action_id, attempt),
        batch_context=batch_context(*(batch_states or (state,))),
    )


def review_ready_state(module):
    state = gated_state(module, views=("front", "side", "back", "full"))
    for view, prefix in module.PREFIXES.items():
        view_state = state["views"][view]
        view_state["generated_count"] = 5
        for index in range(1, 6):
            action_id = f"{prefix}{index:02d}"
            label = task_label(view, action_id)
            action = view_state["actions"][action_id]
            action.update(
                status="generated",
                attempts=1,
                lovart_task_label=label,
                attempt_history=[
                    {
                        "attempt": 1,
                        "submitted_at": module.now_iso(),
                        "task_label": label,
                        "artifact_id": f"review-base-{view}-{index}",
                        "rejection_reason": None,
                        "rejection_reason_code": None,
                        "result_recorded_at": module.now_iso(),
                        "result_status": "generated",
                    }
                ],
            )
            action["canvas"]["current_attempt"] = 1
            action["canvas"]["placements"] = [
                {
                    "attempt": 1,
                    "area": "primary",
                    "slot": index,
                    "row_slot": index,
                    "verified": True,
                    "placement_status": "verified",
                }
            ]
    assert module.evaluate_review_gate(state)["review_allowed"]
    return state


def generate_action(module, state, view, action_id, artifact_id=None):
    attempt = state["views"][view]["actions"][action_id]["attempts"]
    label = task_label(view, action_id, attempt)
    return module.transition_action(
        state,
        view,
        action_id,
        "generated",
        task_label=label,
        artifact_id=artifact_id or f"artifact-{view}-{action_id.lower()}-{attempt}",
    )


def verified_execution_context():
    return {
        "source_path": "/Users/chenyiming/Desktop/8月/8月14日",
        "expected_month_project": "8月",
        "date_region": "8月14日",
        "verified_month_project": "8月",
        "project_verification_status": "verified",
        "blocker": None,
        "feedback_required": False,
        "feedback_message": None,
        "feedback_sent_at": None,
    }


def gated_state(module, views=("front",)):
    state = module.initialize_state(
        {
            "skc_id": "ds-test",
            "batch_contract": batch_contract("ds-test"),
            "views": {view: {"status": "ready"} for view in views},
        },
        verified_execution_context(),
    )
    module.record_layout_reservation(
        state,
        date_region="8月14日",
        skc_label="ds-test · V2测试",
        verified=True,
    )
    return state


def ready_generated_state(module):
    state = ready_state(module)
    submit_action(module, state, "front", "FR01")
    generate_action(module, state, "front", "FR01")
    return state


class RunStateTests(unittest.TestCase):
    def test_cli_reserves_layout_and_blocks_review_before_base_twenty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            manifest = temp / "manifest.json"
            context = temp / "context.json"
            state = temp / "state.json"
            manifest.write_text(
                json.dumps({
                    "skc_id": "ds-test",
                    "batch_contract": batch_contract("ds-test"),
                    "views": {
                        view: {"status": "ready"}
                        for view in ("front", "side", "back", "full")
                    },
                }),
                encoding="utf-8",
            )
            context.write_text(json.dumps(verified_execution_context()), encoding="utf-8")
            subprocess.run(
                ["python3", str(SCRIPT), "init", str(manifest), str(state),
                 "--execution-context", str(context)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["python3", str(SCRIPT), "reserve-layout", str(state),
                 "--date-region", "8月14日", "--skc-label", "ds-test · V2测试",
                 "--verified"],
                check=True,
                capture_output=True,
                text=True,
            )
            reviewed = subprocess.run(
                ["python3", str(SCRIPT), "review-gate", str(state)],
                capture_output=True,
                text=True,
            )
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(reviewed.returncode, 4)
            self.assertEqual(payload["layout_reservation"]["status"], "verified")
            self.assertEqual(
                payload["review_gate"]["status"], "blocked:base-count-incomplete"
            )

    def test_submission_requires_verified_project_and_reserved_layout(self):
        module = load_module()
        state = module.initialize_state(
            {
                "skc_id": "ds-test",
                "batch_contract": batch_contract("ds-test"),
                "views": {"front": {"status": "ready"}},
            },
            verified_execution_context(),
        )

        with self.assertRaisesRegex(ValueError, "layout reservation is not verified"):
            submit_action(module, state, "front", "FR01")

        module.record_layout_reservation(
            state,
            date_region="8月14日",
            skc_label="ds-test · V2测试",
            verified=True,
        )
        module.transition_action(
            state,
            "front",
            "FR01",
            "submitted",
            task_label="SKC ds-test | VIEW front | ACTION FR01 | ATTEMPT 1",
            batch_context=batch_context(state),
        )
        self.assertEqual(state["views"]["front"]["actions"]["FR01"]["status"], "submitted")

    def test_submission_rejects_status_only_legacy_layout_until_rereserved(self):
        module = load_module()
        state = gated_state(module)
        state["layout_reservation"] = {"status": "verified"}

        with self.assertRaisesRegex(ValueError, "reserve-layout.*again"):
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label="SKC ds-test | VIEW front | ACTION FR01 | ATTEMPT 1",
            )

        self.assertEqual(state["views"]["front"]["actions"]["FR01"]["status"], "pending")

    def test_submission_rejects_any_incomplete_v3_layout_reservation(self):
        module = load_module()
        mutations = {
            "contract version": lambda reservation: reservation.update(
                contract_version="date-skc-four-row-v2"
            ),
            "date region": lambda reservation: reservation.update(date_region="   "),
            "active date": lambda reservation: reservation.update(date_region="8月15日"),
            "skc label": lambda reservation: reservation.update(skc_label=""),
            "active skc": lambda reservation: reservation.update(
                skc_label="another-skc"
            ),
            "verification time": lambda reservation: reservation.update(
                verified_at="not-a-timestamp"
            ),
            "view row order": lambda reservation: reservation["view_rows"].reverse(),
            "ten cells": lambda reservation: reservation["view_rows"][0].update(
                cells=list(range(1, 10))
            ),
            "horizontal ratio": lambda reservation: reservation.update(
                horizontal_gap_ratio=0.31
            ),
            "vertical ratio": lambda reservation: reservation.update(
                vertical_gap_ratio=0.31
            ),
            "skc ratio": lambda reservation: reservation.update(skc_gap_ratio=0.31),
        }
        for defect, mutate in mutations.items():
            with self.subTest(defect=defect):
                state = gated_state(module)
                mutate(state["layout_reservation"])

                with self.assertRaisesRegex(ValueError, "reserve-layout.*again"):
                    module.transition_action(
                        state,
                        "front",
                        "FR01",
                        "submitted",
                        task_label=(
                            "SKC ds-test | VIEW front | ACTION FR01 | ATTEMPT 1"
                        ),
                    )

                self.assertEqual(
                    state["views"]["front"]["actions"]["FR01"]["status"],
                    "pending",
                )

    def test_json_true_cannot_be_layout_cell_one(self):
        module = load_module()
        invalid_cells = {
            "boolean": [True, *range(2, 11)],
            "float": [1.0, *range(2, 11)],
            "numeric string": ["1", *range(2, 11)],
            "duplicate": [1, 1, *range(3, 11)],
            "tuple": tuple(range(1, 11)),
        }

        for defect, cells in invalid_cells.items():
            with self.subTest(defect=defect):
                state = gated_state(module)
                state["layout_reservation"]["view_rows"][0]["cells"] = cells

                self.assertTrue(module._layout_reservation_errors(state))

    def test_rejected_identity_drift_requires_structured_reason_code(self):
        module = load_module()
        state = review_ready_state(module)

        module.transition_action(
            state,
            "front",
            "FR01",
            "rejected",
            reason="Skin tone and visible face structure differ from 正面/1.jpg.",
            reason_code="identity-drift",
        )

        action = state["views"]["front"]["actions"]["FR01"]
        history = action["attempt_history"][-1]
        self.assertEqual(history["rejection_reason_code"], "identity-drift")
        self.assertEqual(action["rejection_reason_codes"], ["identity-drift"])

    def test_rejected_quality_failures_accept_only_known_structured_reason_codes(self):
        module = load_module()
        state = review_ready_state(module)
        cases = (
            ("FR01", "head-crop-below-minimum"),
            ("FR02", "full-head-incomplete"),
            ("FR03", "long-dress-hem-cropped"),
        )

        for action_id, reason_code in cases:
            module.transition_action(
                state,
                "front",
                action_id,
                "rejected",
                reason=f"Rejected for {reason_code}.",
                reason_code=reason_code,
            )
            history = state["views"]["front"]["actions"][action_id][
                "attempt_history"
            ][-1]
            self.assertEqual(history["rejection_reason_code"], reason_code)
        with self.assertRaisesRegex(ValueError, "unknown quality reason code"):
            module.transition_action(
                state,
                "front",
                "FR04",
                "rejected",
                reason="Rejected for an unrecognized reason.",
                reason_code="unknown-quality-failure",
            )

    def test_reason_code_is_validated_and_limited_to_rejected_transitions(self):
        module = load_module()
        state = ready_state(module)

        with self.assertRaisesRegex(ValueError, "unknown quality reason code"):
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                reason_code="unknown-quality-failure",
            )
        self.assertEqual(state["views"]["front"]["actions"]["FR01"]["status"], "pending")

        with self.assertRaisesRegex(
            ValueError, "reason_code is only allowed for rejected transitions"
        ):
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                reason_code="identity-drift",
            )

    def test_rejected_transition_requires_a_nonempty_string_reason(self):
        module = load_module()

        for reason in ("   ", 123):
            with self.subTest(reason=reason):
                state = review_ready_state(module)

                with self.assertRaisesRegex(
                    ValueError, "rejected transition requires a non-empty string reason"
                ):
                    module.transition_action(
                        state,
                        "front",
                        "FR01",
                        "rejected",
                        reason=reason,
                    )
                self.assertEqual(
                    state["views"]["front"]["actions"]["FR01"]["status"],
                    "generated",
                )

    def test_verified_layout_reservation_preserves_four_row_canvas_contract(self):
        module = load_module()
        state = module.initialize_state(
            {
                "skc_id": "ds-test",
                "batch_contract": batch_contract("ds-test"),
                "views": {
                    view: {"status": "ready"}
                    for view in ("front", "side", "back", "full")
                },
            }
        )

        module.record_layout_reservation(
            state,
            date_region="8月14日",
            skc_label="ds-test · V2测试",
            verified=True,
        )

        reservation = state["layout_reservation"]
        self.assertEqual(reservation["contract_version"], "date-skc-four-row-v3")
        self.assertEqual(
            [row["view"] for row in reservation["view_rows"]],
            ["front", "side", "back", "full"],
        )
        self.assertTrue(all(row["cells"] == list(range(1, 11)) for row in reservation["view_rows"]))
        self.assertEqual(reservation["horizontal_gap_ratio"], 0.08)
        self.assertEqual(reservation["vertical_gap_ratio"], 0.08)
        self.assertEqual(reservation["skc_gap_ratio"], 0.25)

    def test_generated_result_requires_identity_and_blocks_next_submission_until_placed(self):
        module = load_module()
        state = gated_state(module)
        label = "SKC ds-test | VIEW front | ACTION FR01 | ATTEMPT 1"
        module.transition_action(
            state,
            "front",
            "FR01",
            "submitted",
            task_label=label,
            batch_context=batch_context(state),
        )

        with self.assertRaisesRegex(ValueError, "artifact identity is required"):
            module.transition_action(state, "front", "FR01", "generated")

        module.transition_action(
            state,
            "front",
            "FR01",
            "generated",
            task_label=label,
            artifact_id="artifact-fr01",
        )
        with self.assertRaisesRegex(ValueError, "placement backlog must be zero"):
            module.transition_action(
                state,
                "front",
                "FR02",
                "submitted",
                task_label="SKC ds-test | VIEW front | ACTION FR02 | ATTEMPT 1",
                batch_context=batch_context(state),
            )

        module.place_attempt(
            state, "front", "FR01", 1, area="primary", slot=1, verified=True
        )
        module.transition_action(
            state,
            "front",
            "FR02",
            "submitted",
            task_label="SKC ds-test | VIEW front | ACTION FR02 | ATTEMPT 1",
            batch_context=batch_context(state),
        )
        self.assertEqual(state["views"]["front"]["actions"]["FR02"]["status"], "submitted")

    def test_review_gate_requires_five_identified_and_placed_base_results_per_view(self):
        module = load_module()
        state = gated_state(module, views=("front", "side", "back", "full"))

        initial = module.evaluate_review_gate(state)
        self.assertEqual(initial["status"], "blocked:base-count-incomplete")
        self.assertEqual(initial["missing_base_results"], {
            "front": 5,
            "side": 5,
            "back": 5,
            "full": 5,
        })

        for view, prefix in module.PREFIXES.items():
            for index in range(1, 6):
                action_id = f"{prefix}{index:02d}"
                label = (
                    f"SKC ds-test | VIEW {view} | ACTION {action_id} | ATTEMPT 1"
                )
                module.transition_action(
                    state,
                    view,
                    action_id,
                    "submitted",
                    task_label=label,
                    batch_context=batch_context(state),
                )
                module.transition_action(
                    state,
                    view,
                    action_id,
                    "generated",
                    task_label=label,
                    artifact_id=f"artifact-{action_id.lower()}",
                )
                module.place_attempt(
                    state,
                    view,
                    action_id,
                    1,
                    area="primary",
                    slot=index,
                    verified=True,
                )

        ready = module.evaluate_review_gate(state)
        self.assertEqual(ready["status"], "ready")
        self.assertTrue(ready["review_allowed"])

    def test_initialization_without_execution_context_cannot_bypass_submission_gates(self):
        module = load_module()
        state = module.initialize_state(
            {
                "skc_id": "ds-test",
                "batch_contract": batch_contract("ds-test"),
                "views": {"front": {"status": "ready"}},
            }
        )
        module.record_layout_reservation(
            state,
            date_region="8月14日",
            skc_label="ds-test · V2测试",
            verified=True,
        )

        with self.assertRaisesRegex(ValueError, "month project is not verified"):
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label=task_label("front", "FR01"),
            )

    def test_global_unfinished_limit_rejects_the_eleventh_submission_across_views(self):
        module = load_module()
        state = gated_state(module, views=("front", "side", "back", "full"))
        first_wave = [
            (view, f"{module.PREFIXES[view]}{index:02d}")
            for view in ("front", "side")
            for index in range(1, 6)
        ]
        for view, action_id in first_wave:
            submit_action(module, state, view, action_id)

        with self.assertRaisesRegex(ValueError, "global unfinished limit"):
            submit_action(module, state, "back", "BA01")

    def test_review_gate_requires_exact_base_identity_and_verified_primary_slots(self):
        module = load_module()
        state = gated_state(module, views=("front", "side", "back", "full"))
        for view, prefix in module.PREFIXES.items():
            for index in range(1, 6):
                action_id = f"{prefix}{index:02d}"
                label = task_label(view, action_id)
                module.transition_action(
                    state,
                    view,
                    action_id,
                    "submitted",
                    task_label=label,
                    batch_context=batch_context(state),
                )
                module.transition_action(
                    state,
                    view,
                    action_id,
                    "generated",
                    task_label=label,
                    artifact_id=f"artifact-{action_id.lower()}",
                )
                module.place_attempt(
                    state,
                    view,
                    action_id,
                    1,
                    area="primary",
                    slot=index,
                    verified=True,
                )
        self.assertTrue(module.evaluate_review_gate(state)["review_allowed"])

        def missing_view(candidate):
            candidate["views"].pop("full")

        def ghost_view(candidate):
            candidate["views"]["ghost"] = {"status": "pending", "actions": {}}

        def missing_action(candidate):
            candidate["views"]["front"]["actions"].pop("FR05")

        def wrong_label(candidate):
            candidate["views"]["front"]["actions"]["FR01"]["attempt_history"][0][
                "task_label"
            ] = "wrong label"

        def boolean_artifact(candidate):
            candidate["views"]["front"]["actions"]["FR01"]["attempt_history"][0][
                "artifact_id"
            ] = True

        def supplemental_only(candidate):
            placement = candidate["views"]["front"]["actions"]["FR01"]["canvas"][
                "placements"
            ][0]
            placement.update(area="supplemental", slot=6, row_slot=6)

        def wrong_primary_slot(candidate):
            placement = candidate["views"]["front"]["actions"]["FR01"]["canvas"][
                "placements"
            ][0]
            placement.update(slot=2, row_slot=2)

        def malformed_canvas(candidate):
            candidate["views"]["front"]["actions"]["FR01"]["canvas"] = "broken"

        for defect, mutate in {
            "missing view": missing_view,
            "ghost view": ghost_view,
            "missing action": missing_action,
            "wrong task label": wrong_label,
            "boolean artifact": boolean_artifact,
            "supplemental-only placement": supplemental_only,
            "wrong primary slot": wrong_primary_slot,
            "malformed canvas": malformed_canvas,
        }.items():
            with self.subTest(defect=defect):
                candidate = copy.deepcopy(state)
                mutate(candidate)
                self.assertFalse(
                    module.evaluate_review_gate(candidate)["review_allowed"], defect
                )

    def test_initializes_five_pending_actions_and_generation_cap(self):
        module = load_module()
        state = ready_state(module)

        self.assertEqual(len(state["views"]["front"]["actions"]), 5)
        self.assertEqual(state["views"]["front"]["generation_limit"], 10)
        self.assertEqual(state["views"]["front"]["supplemental_limit"], 5)

    def test_initialization_persists_month_and_date_context(self):
        module = load_module()
        context = {
            "source_path": "/Users/chenyiming/Desktop/8月/8月15日",
            "expected_month_project": "8月",
            "date_region": "8月15日",
            "verified_month_project": None,
            "project_verification_status": "pending",
            "blocker": None,
            "feedback_required": False,
            "feedback_message": None,
            "feedback_sent_at": None,
        }

        state = module.initialize_state(
            {
                "skc_id": "ds-test",
                "batch_contract": batch_contract("ds-test"),
                "views": {"front": {"status": "ready"}},
            },
            context,
        )

        self.assertEqual(state["schema_version"], 6)
        self.assertEqual(state["execution_context"]["expected_month_project"], "8月")
        self.assertEqual(state["execution_context"]["date_region"], "8月15日")

    def test_record_project_verification_blocks_and_then_recovers_state(self):
        module = load_module()
        state = ready_state(module)
        blocked_context = {
            "source_path": "/Users/chenyiming/Desktop/8月/8月15日",
            "expected_month_project": "8月",
            "date_region": "8月15日",
            "verified_month_project": "7月",
            "project_verification_status": "blocked",
            "blocker": "blocked:month-project-mismatch",
            "feedback_required": True,
            "feedback_message": "任务已暂停",
            "feedback_sent_at": None,
        }

        module.record_project_verification(state, blocked_context)
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(
            state["execution_context"]["blocker"],
            "blocked:month-project-mismatch",
        )
        module.mark_project_feedback_sent(state)
        self.assertFalse(state["execution_context"]["feedback_required"])
        self.assertIsNotNone(state["execution_context"]["feedback_sent_at"])

        recovered_context = dict(blocked_context)
        recovered_context.update(
            verified_month_project="8月",
            project_verification_status="verified",
            blocker=None,
            feedback_required=False,
            feedback_message=None,
        )
        module.record_project_verification(state, recovered_context)

        self.assertEqual(state["status"], "pending")
        self.assertEqual(
            state["execution_context"]["project_verification_status"], "verified"
        )

    def test_verified_placement_records_compact_grid_contract(self):
        module = load_module()
        state = ready_generated_state(module)

        module.place_attempt(
            state,
            "front",
            "FR01",
            1,
            area="primary",
            slot=1,
            verified=True,
        )

        placed = state["views"]["front"]["actions"]["FR01"]["canvas"][
            "placements"
        ][0]
        self.assertEqual(placed["row_slot"], 1)
        self.assertEqual(placed["placement_status"], "verified")
        self.assertEqual(placed["display_width_unit"], 1.0)
        self.assertEqual(placed["horizontal_gap_ratio"], 0.08)
        self.assertEqual(placed["vertical_gap_ratio"], 0.08)
        self.assertEqual(placed["skc_gap_ratio"], 0.25)

    def test_unverified_placement_cannot_complete_an_skc(self):
        module = load_module()
        state = ready_generated_state(module)
        module.place_attempt(
            state,
            "front",
            "FR01",
            1,
            area="primary",
            slot=1,
            verified=False,
        )

        placed = state["views"]["front"]["actions"]["FR01"]["canvas"][
            "placements"
        ][0]
        self.assertEqual(placed["placement_status"], "unverified")

    def test_generation_cap_blocks_unresolved_actions_after_ten_results(self):
        module = load_module()
        state = review_ready_state(module)
        for index in range(5):
            action_id = f"FR{index + 1:02d}"
            module.transition_action(
                state,
                "front",
                action_id,
                "rejected",
                reason=f"quality drift {index + 1}",
                reason_code="identity-drift",
            )

        for index in range(5):
            action_id = f"FR{index + 1:02d}"
            submit_action(module, state, "front", action_id)
            generate_action(module, state, "front", action_id)
            module.place_attempt(
                state,
                "front",
                action_id,
                1,
                area="supplemental",
                slot=index + 6,
                verified=True,
            )
            module.place_attempt(
                state,
                "front",
                action_id,
                2,
                area="primary",
                slot=index + 1,
                verified=True,
            )
            module.transition_action(
                state,
                "front",
                action_id,
                "rejected",
                reason=f"quality drift {index + 6}",
                reason_code="identity-drift",
            )

        view = state["views"]["front"]
        self.assertEqual(view["generated_count"], 10)
        self.assertEqual(
            {item["blocker"] for item in view["actions"].values()},
            {"blocked:quality-cap"},
        )


if __name__ == "__main__":
    unittest.main()
