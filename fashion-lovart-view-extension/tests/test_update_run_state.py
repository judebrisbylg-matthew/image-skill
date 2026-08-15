import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "scripts" / "update_run_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("update_run_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ready_state(module):
    return module.initialize_state(
        {"skc_id": "ds-test", "views": {"front": {"status": "ready"}}}
    )


def ready_submitted_state(module):
    state = ready_state(module)
    module.transition_action(state, "front", "FR01", "submitted")
    return state


class RunStateTests(unittest.TestCase):
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
            {"skc_id": "ds-test", "views": {"front": {"status": "ready"}}},
            context,
        )

        self.assertEqual(state["schema_version"], 4)
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
        state = ready_submitted_state(module)

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
        state = ready_submitted_state(module)
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
        state = ready_state(module)
        for index in range(10):
            action_id = f"FR{index % 5 + 1:02d}"
            module.transition_action(state, "front", action_id, "submitted")
            module.transition_action(
                state,
                "front",
                action_id,
                "rejected",
                reason=f"quality drift {index + 1}",
            )

        view = state["views"]["front"]
        self.assertEqual(view["generated_count"], 10)
        self.assertEqual(
            {item["blocker"] for item in view["actions"].values()},
            {"blocked:quality-cap"},
        )


if __name__ == "__main__":
    unittest.main()
