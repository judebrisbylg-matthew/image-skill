import copy
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = ROOT / "skill" / "scripts" / "scan_skc.py"
STATE_PATH = ROOT / "skill" / "scripts" / "update_run_state.py"
FIXTURES = runpy.run_path(str(Path(__file__).with_name("test_final_review_contract.py")))

STATE_CLI_WRAPPER = """
import importlib.util
import sys
from pathlib import Path

state_path = Path(sys.argv[1]).resolve()
coordination_root = Path(sys.argv[2]).resolve()
arguments = sys.argv[3:]
spec = importlib.util.spec_from_file_location("update_run_state_cli", state_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module._SUBMISSION_COORDINATION_ROOT = coordination_root
sys.argv = [str(state_path), *arguments]
raise SystemExit(module.main())
"""

load_module = FIXTURES["load_module"]
state_with_views = FIXTURES["state_with_views"]
task_label = FIXTURES["task_label"]
valid_manifest = FIXTURES["valid_manifest"]
valid_prompt = FIXTURES["valid_prompt"]
validate_manifest = FIXTURES["validate_manifest"]


def configure_submission_coordination(module, temp_root):
    coordination_root = (Path(temp_root).resolve() / "submission-coordination").resolve()
    module._SUBMISSION_COORDINATION_ROOT = coordination_root
    return coordination_root


def state_cli_command(coordination_root, *arguments):
    return [
        "python3",
        "-c",
        STATE_CLI_WRAPPER,
        str(STATE_PATH),
        str(Path(coordination_root).resolve()),
        *(str(argument) for argument in arguments),
    ]


def batch_contract(*skc_ids):
    digest_payload = {
        "member_skc_ids": list(skc_ids),
        "schema_version": 1,
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


def batch_context(*states):
    return {
        "schema_version": 1,
        "skc_ids": [state["skc_id"] for state in states],
        "states": list(states),
    }


def canonical_rejected_state(module):
    contract = batch_contract("ds-final-review")
    state = state_with_views(module)
    self_contract = state["batch_contract"]
    if self_contract != contract:
        raise AssertionError("state fixture must preserve the scanner batch contract")
    action = state["views"]["front"]["actions"]["FR01"]
    action.update(
        status="rejected",
        attempts=1,
        lovart_task_label=task_label(state, "front", "FR01", 1),
        attempt_history=[
            {
                "attempt": 1,
                "submitted_at": "2026-08-16T00:00:00+00:00",
                "task_label": task_label(state, "front", "FR01", 1),
                "artifact_id": "artifact-fr01-attempt-1",
                "rejection_reason": "The canonical identity drifted.",
                "rejection_reason_code": "identity-drift",
                "result_recorded_at": "2026-08-16T00:01:00+00:00",
                "result_status": "rejected",
            }
        ],
    )
    action["canvas"]["current_attempt"] = 1
    action["canvas"]["placements"] = [
        {
            "attempt": 1,
            "area": "primary",
            "slot": 1,
            "row_slot": 1,
            "verified": True,
            "placement_status": "verified",
        }
    ]
    return state


def retry_prompt(manifest):
    prompt = valid_prompt(manifest=manifest)
    action = prompt["actions"][0]
    action["attempt"] = 2
    action["correction"] = {
        "fix": "identity-drift",
        "preserve": "accepted-contracts",
    }
    action["prompt_en"] = validate_manifest.render_positive_prompt(
        manifest["skc_id"], "front", action, manifest
    )
    return prompt


class ControlledPositiveRendererRegressionTests(unittest.TestCase):
    def test_vacuous_one_letter_directives_are_rejected(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        for index, action in enumerate(prompt["actions"]):
            with self.subTest(index=index):
                action["title"] = "x"
                action["action_directives"] = {
                    "action": chr(ord("a") + index),
                    "camera": "x",
                    "composition": "x",
                    "scene": "x",
                }
                with self.assertRaises(ValueError):
                    validate_manifest.render_positive_prompt(
                        manifest["skc_id"], "front", action, manifest
                    )

    def test_no_footwear_contract_rejects_free_text_footwear_authority(self):
        manifest = valid_manifest()
        prompt = valid_prompt("full", manifest)
        self.assertNotIn("footwear_contract", manifest["views"]["full"])
        for action in prompt["actions"]:
            action["action_directives"]["scene"] = (
                "Preserve the required red shoes from the accessory source"
            )
            with self.assertRaises(ValueError):
                validate_manifest.render_positive_prompt(
                    manifest["skc_id"], "full", action, manifest
                )


class ScannerBatchContractRegressionTests(unittest.TestCase):
    def test_scanner_binds_every_member_to_one_deterministic_batch_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            for skc_id, payload in (("alpha", b"alpha"), ("beta", b"beta")):
                view = root / skc_id / "正面"
                view.mkdir(parents=True)
                (view / "1.jpg").write_bytes(payload)
            output = root / "batch.json"

            subprocess.run(
                ["python3", str(SCANNER_PATH), str(root), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            expected = batch_contract("alpha", "beta")

            self.assertEqual(payload.get("batch_contract"), expected)
            self.assertEqual(
                [item.get("batch_contract") for item in payload["skcs"]],
                [expected, expected],
            )

    def test_reduced_context_cannot_omit_an_authoritative_live_member(self):
        module = load_module("second_remediation_batch_state", STATE_PATH)
        contract = batch_contract("ds-first", "ds-second")
        first = state_with_views(
            module,
            "ds-first",
            views=("front", "side"),
            batch_member_ids=("ds-first", "ds-second"),
        )
        second = state_with_views(
            module,
            "ds-second",
            views=("back",),
            batch_member_ids=("ds-first", "ds-second"),
        )
        self.assertEqual(first["batch_contract"], contract)
        self.assertEqual(second["batch_contract"], contract)
        full_context = batch_context(first, second)
        for view, prefix in (("front", "FR"), ("side", "SI")):
            for index in range(1, 6):
                action_id = f"{prefix}{index:02d}"
                module.transition_action(
                    first,
                    view,
                    action_id,
                    "submitted",
                    task_label=task_label(first, view, action_id, 1),
                    batch_context=full_context,
                )

        with self.assertRaisesRegex(ValueError, "batch|member|contract"):
            module.transition_action(
                second,
                "back",
                "BA01",
                "submitted",
                task_label=task_label(second, "back", "BA01", 1),
                batch_context=batch_context(second),
            )

    def test_legacy_state_without_batch_contract_fails_closed(self):
        module = load_module("second_remediation_legacy_state", STATE_PATH)
        state = state_with_views(module)
        del state["batch_contract"]

        with self.assertRaisesRegex(ValueError, "batch|contract|legacy"):
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label=task_label(state, "front", "FR01", 1),
                batch_context=batch_context(state),
            )

    def test_independent_singleton_batches_share_the_month_project_cap(self):
        module = load_module("second_remediation_global_registry", STATE_PATH)
        first = state_with_views(
            module,
            "singleton-first",
            views=("front", "side"),
        )
        second = state_with_views(module, "singleton-second", views=("back",))

        for view, prefix in (("front", "FR"), ("side", "SI")):
            for index in range(1, 6):
                action_id = f"{prefix}{index:02d}"
                module.transition_action(
                    first,
                    view,
                    action_id,
                    "submitted",
                    task_label=task_label(first, view, action_id, 1),
                    batch_context=batch_context(first),
                )

        with self.assertRaisesRegex(ValueError, "global unfinished limit"):
            module.transition_action(
                second,
                "back",
                "BA01",
                "submitted",
                task_label=task_label(second, "back", "BA01", 1),
                batch_context=batch_context(second),
            )

    def test_file_registry_reserves_at_most_ten_slots_under_concurrency(self):
        module = load_module("second_remediation_atomic_registry", STATE_PATH)
        state = state_with_views(module, "atomic-registry")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir).resolve()
            coordination_root = configure_submission_coordination(module, temp_root)
            scope = module._submission_scope(state)
            registry_path = coordination_root / f"{scope['digest']}.json"
            worker = """
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("registry_worker", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module._SUBMISSION_COORDINATION_ROOT = Path(sys.argv[2]).resolve()
scope = json.loads(sys.argv[3])
reservation = json.loads(sys.argv[4])
try:
    module._FileSubmissionCoordinator(
        module._SUBMISSION_COORDINATION_ROOT / f"{scope['digest']}.json"
    ).reserve(
        scope, reservation
    )
except ValueError as exc:
    print(exc)
else:
    print("reserved")
"""

            def reserve(index):
                label = (
                    "SKC atomic-registry | VIEW front | "
                    f"ACTION FR{index:02d} | ATTEMPT 1"
                )
                reservation = {
                    "task_label": label,
                    "skc_id": state["skc_id"],
                    "batch_digest": state["batch_contract"]["digest"],
                    "reserved_at": "2026-08-16T00:00:00+00:00",
                }
                completed = subprocess.run(
                    [
                        "python3",
                        "-c",
                        worker,
                        str(STATE_PATH),
                        str(coordination_root),
                        json.dumps(scope, ensure_ascii=False),
                        json.dumps(reservation, ensure_ascii=False),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                results = list(pool.map(reserve, range(1, 21)))

            self.assertEqual(results.count("reserved"), 10)
            self.assertEqual(
                sum("global unfinished limit" in result for result in results),
                10,
            )
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(len(registry["reservations"]), 10)
            one_label = next(iter(registry["reservations"]))
            with self.assertRaisesRegex(ValueError, "owner|batch|reservation"):
                module._FileSubmissionCoordinator(registry_path).release(
                    scope,
                    one_label,
                    state["skc_id"],
                    "0" * 64,
                )
            unchanged = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(len(unchanged["reservations"]), 10)

    def test_registry_scope_resolves_the_verified_date_ancestor(self):
        module = load_module("second_remediation_nested_scope", STATE_PATH)
        daily = state_with_views(module, "daily-scope")
        nested = state_with_views(module, "nested-scope")
        nested["execution_context"]["source_path"] = (
            "/Users/chenyiming/Desktop/8月/8月14日/nested-scope/正面"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            coordination_root = configure_submission_coordination(module, temp_dir)
            nested_scope = module._submission_scope(nested)
            self.assertEqual(nested_scope, module._submission_scope(daily))
            registry_path = module._submission_registry_path(nested)
            self.assertEqual(
                registry_path,
                coordination_root / f"{nested_scope['digest']}.json",
            )
            self.assertNotIn(
                "/Users/chenyiming/Desktop/8月",
                str(registry_path),
            )

    def test_imported_state_api_defaults_to_the_shared_file_registry(self):
        spec = importlib.util.spec_from_file_location(
            "second_remediation_production_default", STATE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        state = state_with_views(module, "production-default")

        with tempfile.TemporaryDirectory() as temp_dir:
            coordination_root = configure_submission_coordination(module, temp_dir)
            scope = module._submission_scope(state)
            coordinator = module._coordinator_for_state(state)

            self.assertIsInstance(coordinator, module._FileSubmissionCoordinator)
            self.assertEqual(
                coordinator.path,
                coordination_root / f"{scope['digest']}.json",
            )
            self.assertNotIn(
                "/Users/chenyiming/Desktop/8月",
                str(coordinator.path),
            )

    def test_file_registry_release_waits_for_durable_state_acknowledgement(self):
        spec = importlib.util.spec_from_file_location(
            "second_remediation_durable_release", STATE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir).resolve()
            configure_submission_coordination(module, temp_root)
            date_root = (temp_root / "8月" / "8月14日").resolve()
            date_root.mkdir(parents=True)
            state = state_with_views(module, "durable-release")
            state["execution_context"]["source_path"] = str(
                date_root / "durable-release"
            )
            context = batch_context(state)
            label = task_label(state, "front", "FR01", 1)
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label=label,
                batch_context=context,
            )
            registry_path = module._submission_registry_path(state)
            self.assertEqual(
                len(json.loads(registry_path.read_text())["reservations"]), 1
            )

            module.transition_action(
                state,
                "front",
                "FR01",
                "generated",
                task_label=label,
                artifact_id="durable-artifact",
            )

            self.assertEqual(
                len(json.loads(registry_path.read_text())["reservations"]), 1
            )
            state_path = date_root / "durable-release" / "_codex" / "run-state.json"
            with self.assertRaisesRegex(ValueError, "persist|durable|state"):
                module.release_submission_slot(
                    state,
                    "front",
                    "FR01",
                    state_path,
                )
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            module.release_submission_slot(
                state,
                "front",
                "FR01",
                state_path,
            )
            self.assertEqual(
                json.loads(registry_path.read_text())["reservations"], {}
            )

    def test_cli_write_failure_keeps_the_global_slot_reserved(self):
        spec = importlib.util.spec_from_file_location(
            "second_remediation_failed_write", STATE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir).resolve()
            coordination_root = configure_submission_coordination(module, temp_root)
            date_root = (temp_root / "8月" / "8月14日").resolve()
            state = state_with_views(module, "failed-write")
            state["execution_context"]["source_path"] = str(
                date_root / "failed-write"
            )
            label = task_label(state, "front", "FR01", 1)
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label=label,
                batch_context=batch_context(state),
            )
            state_path = date_root / "failed-write" / "_codex" / "run-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            state_path.with_name(f".{state_path.name}.lock").touch()
            registry_path = module._submission_registry_path(state)

            os.chmod(state_path.parent, 0o500)
            try:
                completed = subprocess.run(
                    state_cli_command(
                        coordination_root,
                        "transition",
                        state_path,
                        "front",
                        "FR01",
                        "generated",
                        "--task-label",
                        label,
                        "--artifact-id",
                        "failed-write-artifact",
                    ),
                    capture_output=True,
                    text=True,
                )
            finally:
                os.chmod(state_path.parent, 0o700)

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(
                json.loads(state_path.read_text())["views"]["front"]["actions"]
                ["FR01"]["status"],
                "submitted",
            )
            self.assertEqual(
                len(json.loads(registry_path.read_text())["reservations"]), 1
            )

    def test_concurrent_cli_transitions_serialize_one_state_and_registry(self):
        module = load_module("second_remediation_same_state_setup", STATE_PATH)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir).resolve()
            coordination_root = configure_submission_coordination(module, temp_root)
            date_root = (temp_root / "8月" / "8月14日").resolve()
            state = state_with_views(module, "same-state")
            state["execution_context"]["source_path"] = str(
                date_root / "same-state"
            )
            state_path = date_root / "same-state" / "_codex" / "run-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            contract = state["batch_contract"]
            inventory_path = (temp_root / "batch.json").resolve()
            inventory_path.write_text(
                json.dumps(
                    {
                        "batch_contract": contract,
                        "skcs": [
                            {
                                "skc_id": state["skc_id"],
                                "batch_contract": contract,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            def submit(action_id):
                return subprocess.run(
                    state_cli_command(
                        coordination_root,
                        "transition",
                        state_path,
                        "front",
                        action_id,
                        "submitted",
                        "--task-label",
                        task_label(state, "front", action_id, 1),
                        "--batch-inventory",
                        inventory_path,
                    ),
                    capture_output=True,
                    text=True,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                completed = list(pool.map(submit, ("FR01", "FR02")))

            self.assertEqual([item.returncode for item in completed], [0, 0])
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            actions = persisted["views"]["front"]["actions"]
            self.assertEqual(actions["FR01"]["status"], "submitted")
            self.assertEqual(actions["FR02"]["status"], "submitted")
            registry_path = module._submission_registry_path(state)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(len(registry["reservations"]), 2)

    def test_cross_command_cli_race_cannot_restore_unfinished_state(self):
        spec = importlib.util.spec_from_file_location(
            "second_remediation_cross_command_race", STATE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir).resolve()
            coordination_root = configure_submission_coordination(module, temp_root)
            date_root = (temp_root / "8月" / "8月14日").resolve()
            state = state_with_views(module, "cross-command")
            state["execution_context"]["source_path"] = str(
                date_root / "cross-command"
            )
            label = task_label(state, "front", "FR01", 1)
            module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label=label,
                batch_context=batch_context(state),
            )
            state_path = date_root / "cross-command" / "_codex" / "run-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps(state), encoding="utf-8")
            registry_path = module._submission_registry_path(state)
            context_pipe = (temp_root / "project-context.fifo").resolve()
            os.mkfifo(context_pipe)

            project_process = subprocess.Popen(
                state_cli_command(
                    coordination_root,
                    "project",
                    state_path,
                    context_pipe,
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            pipe_descriptor = os.open(context_pipe, os.O_WRONLY)
            transition_process = subprocess.Popen(
                state_cli_command(
                    coordination_root,
                    "transition",
                    state_path,
                    "front",
                    "FR01",
                    "generated",
                    "--task-label",
                    label,
                    "--artifact-id",
                    "cross-command-artifact",
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                try:
                    transition_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
                os.write(
                    pipe_descriptor,
                    json.dumps(state["execution_context"]).encode("utf-8"),
                )
            finally:
                os.close(pipe_descriptor)

            project_stdout, project_stderr = project_process.communicate(timeout=5)
            transition_stdout, transition_stderr = transition_process.communicate(
                timeout=5
            )
            self.assertEqual(
                project_process.returncode,
                0,
                project_stdout + project_stderr,
            )
            self.assertEqual(
                transition_process.returncode,
                0,
                transition_stdout + transition_stderr,
            )
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                persisted["views"]["front"]["actions"]["FR01"]["status"],
                "generated",
            )
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(registry["reservations"], {})


class CanonicalRetryPredecessorRegressionTests(unittest.TestCase):
    @staticmethod
    def _canonical_second_rejection(module):
        state = canonical_rejected_state(module)
        action = state["views"]["front"]["actions"]["FR01"]
        action.update(
            attempts=2,
            lovart_task_label=task_label(state, "front", "FR01", 2),
        )
        action["attempt_history"].append(
            {
                "attempt": 2,
                "submitted_at": "2026-08-16T00:02:00+00:00",
                "task_label": task_label(state, "front", "FR01", 2),
                "artifact_id": "artifact-fr01-attempt-2",
                "rejection_reason": "The canonical identity drifted again.",
                "rejection_reason_code": "identity-drift",
                "result_recorded_at": "2026-08-16T00:03:00+00:00",
                "result_status": "rejected",
            }
        )
        action["canvas"]["current_attempt"] = 2
        action["canvas"]["placements"].append(
            {
                "attempt": 2,
                "area": "primary",
                "slot": 1,
                "row_slot": 1,
                "verified": True,
                "placement_status": "verified",
            }
        )
        return state

    def test_retry_sequence_rejects_boolean_and_float_earlier_attempts(self):
        module = load_module("second_remediation_retry_sequence_types", STATE_PATH)
        manifest = valid_manifest()
        prompt = retry_prompt(manifest)
        prompt["actions"][0]["attempt"] = 3
        prompt["actions"][0]["prompt_en"] = validate_manifest.render_positive_prompt(
            manifest["skc_id"], "front", prompt["actions"][0], manifest
        )

        for malformed_attempt in (True, 1.0):
            with self.subTest(malformed_attempt=malformed_attempt):
                state = self._canonical_second_rejection(module)
                state["views"]["front"]["actions"]["FR01"]["attempt_history"][0][
                    "attempt"
                ] = malformed_attempt
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest, state)
                )
                before = copy.deepcopy(state)
                with self.assertRaisesRegex(ValueError, "history|sequence|retry"):
                    module.transition_action(
                        state,
                        "front",
                        "FR01",
                        "submitted",
                        task_label=task_label(state, "front", "FR01", 3),
                        batch_context=batch_context(state),
                    )
                self.assertEqual(state, before)

    def test_non_string_reason_codes_fail_cleanly_before_mutation(self):
        module = load_module("second_remediation_reason_code_types", STATE_PATH)
        baseline = state_with_views(module)
        baseline["views"]["front"]["actions"]["FR01"]["status"] = "generated"
        for malformed_code in ([], {}, True, 1, 1.0):
            with self.subTest(malformed_code=malformed_code):
                state = copy.deepcopy(baseline)
                before = copy.deepcopy(state)
                with self.assertRaisesRegex(ValueError, "reason code|reason_code"):
                    module.transition_action(
                        state,
                        "front",
                        "FR01",
                        "rejected",
                        reason="Concrete rejection evidence.",
                        reason_code=malformed_code,
                    )
                self.assertEqual(state, before)

    def test_prompt_retry_rejects_every_noncanonical_predecessor_record(self):
        module = load_module("second_remediation_prompt_state", STATE_PATH)
        manifest = valid_manifest()
        prompt = retry_prompt(manifest)
        baseline = canonical_rejected_state(module)

        mutations = {
            "missing predecessor": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ].update(attempt_history=[]),
            "wrong attempt": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ]["attempt_history"][0].update(attempt=0),
            "forged future attempt before predecessor": lambda state: state["views"]
            ["front"]["actions"]["FR01"]["attempt_history"].insert(
                0,
                {
                    "attempt": 2,
                    "task_label": task_label(state, "front", "FR01", 2),
                    "artifact_id": None,
                    "result_recorded_at": None,
                },
            ),
            "boolean predecessor attempt": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["attempt_history"][0].update(attempt=True),
            "wrong task label": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ]["attempt_history"][0].update(task_label="wrong"),
            "missing returned evidence": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["attempt_history"][0].update(result_recorded_at=None),
            "blank artifact": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ]["attempt_history"][0].update(artifact_id=""),
            "unverified placement": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["canvas"]["placements"][0].update(verified=False),
            "boolean placement coordinates": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["canvas"]["placements"][0].update(
                attempt=True,
                slot=True,
                row_slot=True,
            ),
            "wrong result status": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ]["attempt_history"][0].update(result_status="generated"),
            "unknown rejection code": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["attempt_history"][0].update(
                rejection_reason_code="unknown"
            ),
            "non-string rejection code": lambda state: state["views"]["front"]
            ["actions"]["FR01"]["attempt_history"][0].update(
                rejection_reason_code=[]
            ),
            "blank rejection evidence": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["attempt_history"][0].update(rejection_reason=" "),
        }
        for defect, mutate in mutations.items():
            with self.subTest(defect=defect):
                state = copy.deepcopy(baseline)
                mutate(state)
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest, state),
                    defect,
                )

        duplicate = copy.deepcopy(baseline)
        other = duplicate["views"]["front"]["actions"]["FR02"]
        other["attempt_history"] = [
            copy.deepcopy(
                duplicate["views"]["front"]["actions"]["FR01"][
                    "attempt_history"
                ][0]
            )
        ]
        self.assertTrue(
            validate_manifest.validate_prompt_data(prompt, manifest, duplicate)
        )

        malformed_correction = retry_prompt(manifest)
        malformed_correction["actions"][0]["correction"]["fix"] = []
        self.assertTrue(
            validate_manifest.validate_prompt_data(
                malformed_correction,
                manifest,
                baseline,
            )
        )

    def test_state_retry_rejects_noncanonical_predecessor_before_mutation(self):
        module = load_module("second_remediation_retry_state", STATE_PATH)
        baseline = canonical_rejected_state(module)
        mutations = {
            "missing predecessor": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ].update(attempt_history=[]),
            "forged future attempt before predecessor": lambda state: state["views"]
            ["front"]["actions"]["FR01"]["attempt_history"].insert(
                0,
                {
                    "attempt": 2,
                    "task_label": task_label(state, "front", "FR01", 2),
                    "artifact_id": None,
                    "result_recorded_at": None,
                },
            ),
            "wrong label": lambda state: state["views"]["front"]["actions"]["FR01"][
                "attempt_history"
            ][0].update(task_label="wrong"),
            "missing artifact": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ]["attempt_history"][0].update(artifact_id=None),
            "unverified placement": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["canvas"]["placements"][0].update(verified=False),
            "wrong result status": lambda state: state["views"]["front"]["actions"][
                "FR01"
            ]["attempt_history"][0].update(result_status="generated"),
            "unknown rejection code": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["attempt_history"][0].update(
                rejection_reason_code="unknown"
            ),
            "non-string rejection code": lambda state: state["views"]["front"]
            ["actions"]["FR01"]["attempt_history"][0].update(
                rejection_reason_code=[]
            ),
            "blank rejection evidence": lambda state: state["views"]["front"][
                "actions"
            ]["FR01"]["attempt_history"][0].update(rejection_reason=""),
        }
        for defect, mutate in mutations.items():
            with self.subTest(defect=defect):
                state = copy.deepcopy(baseline)
                mutate(state)
                before = copy.deepcopy(state)
                with self.assertRaisesRegex(
                    ValueError, "retry|preceding|predecessor|rejected"
                ):
                    module.transition_action(
                        state,
                        "front",
                        "FR01",
                        "submitted",
                        task_label=task_label(state, "front", "FR01", 2),
                        batch_context=batch_context(state),
                    )
                self.assertEqual(state, before)


if __name__ == "__main__":
    unittest.main()
