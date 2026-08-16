# Task 1 Report: Deterministic Negative-Prompt Contract

## Status

DONE

## Commit

- `fe6e7da97ec9459688b36d252ecab96705b910c0` — `feat: enforce deterministic negative prompt contract`

## Files changed

Committed implementation files:

- `docs/index.html`
- `fashion-lovart-view-extension/docs/handbook.html`
- `fashion-lovart-view-extension/skill/SKILL.md`
- `fashion-lovart-view-extension/skill/references/prompt-output-schema.md`
- `fashion-lovart-view-extension/skill/references/templates/back.md`
- `fashion-lovart-view-extension/skill/references/templates/front.md`
- `fashion-lovart-view-extension/skill/references/templates/full.md`
- `fashion-lovart-view-extension/skill/references/templates/side.md`
- `fashion-lovart-view-extension/skill/scripts/negative_prompt.py`
- `fashion-lovart-view-extension/skill/scripts/validate_manifest.py`
- `fashion-lovart-view-extension/tests/test_documentation_contract.py`
- `fashion-lovart-view-extension/tests/test_validate_manifest.py`
- `fashion-lovart-view-extension/tools/handbook-template.html`

Task report artifact:

- `.superpowers/sdd/2026-08-16-deterministic-negative-prompt-contract/task-1-report.md` (the SDD report directory is intentionally gitignored)

## TDD RED

Tests were added before any production edit. After correcting a test-harness-only `str.name` mistake, the clean RED command was:

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests \
  test_documentation_contract.DocumentationContractTests.test_skill_schema_templates_and_handbook_publish_the_immutable_renderer_contract \
  test_documentation_contract.DocumentationContractTests.test_full_literal_actions_place_generation_settings_before_terminal_suffix
```

Exit summary: exit `1`; `Ran 9 tests`; `FAILED (failures=22)`; no test errors.

Expected failures observed:

- `render_negative_prompt` did not exist.
- Legacy free-form, plausible paraphrase, whitespace-padded, reordered, appended, removed, and another-view negative prompts were accepted.
- Long-dress and footwear variants were not bound to the active manifest/view contract.
- Skill/schema/templates/handbook still described editable free-form negative prose.

## GREEN verification

### Focused contract tests

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests \
  test_documentation_contract.DocumentationContractTests.test_skill_schema_templates_and_handbook_publish_the_immutable_renderer_contract \
  test_documentation_contract.DocumentationContractTests.test_full_literal_actions_place_generation_settings_before_terminal_suffix
```

Exit summary: exit `0`; `Ran 9 tests in 0.013s`; `OK`.

### Full repository unittest suite

```bash
python3 -m unittest discover -s fashion-lovart-view-extension/tests -p 'test_*.py'
```

Exit summary: exit `0`; `Ran 110 tests in 0.631s`; `OK`.

### Python compilation

```bash
PYTHONPYCACHEPREFIX=/private/tmp/deterministic-negative-pycache \
python3 -m py_compile \
  fashion-lovart-view-extension/skill/scripts/negative_prompt.py \
  fashion-lovart-view-extension/skill/scripts/validate_manifest.py
```

Exit summary: exit `0`; no stdout/stderr.

The first invocation without `PYTHONPYCACHEPREFIX` reached Python compilation but exited `1` because the macOS sandbox denied writing the default bytecode cache under `/Users/chenyiming/Library/Caches/com.apple.python/`. Redirecting only the cache to `/private/tmp` produced the required clean compile.

### Skill Creator quick validation

```bash
python3 /Users/chenyiming/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  fashion-lovart-view-extension/skill
```

Exit summary: exit `0`; `Skill is valid!`.

### Handbook build and byte comparison

Snapshot the checked-in handbook before rebuilding:

```bash
cp fashion-lovart-view-extension/docs/handbook.html \
  /private/tmp/deterministic-negative-task1-handbook.html
```

Exit summary: exit `0`; no output.

Rebuild both checked-in handbook artifacts:

```bash
node fashion-lovart-view-extension/tools/build_handbook.mjs
```

Exit summary: exit `0`; emitted:

```text
/private/tmp/image-skill-identity-worktree/fashion-lovart-view-extension/docs/handbook.html
/private/tmp/image-skill-identity-worktree/docs/index.html
```

Byte-compare the newly generated handbook with the pre-build checked-in artifact and with the site mirror:

```bash
cmp -s /private/tmp/deterministic-negative-task1-handbook.html \
  fashion-lovart-view-extension/docs/handbook.html && \
cmp -s fashion-lovart-view-extension/docs/handbook.html docs/index.html
```

Exit summary: exit `0`; no output. The rebuild was byte-identical and both published HTML files match.

### Whitespace and patch integrity

```bash
git diff --check
```

Exit summary: exit `0`; no diff-check diagnostics. The staged form also passed `git diff --cached --check` before commit.

## Self-review

- `render_negative_prompt(view, identity_contract, garment_contract)` is a pure renderer. It validates supported view names and the complete identity/garment input shapes before assembling output.
- The canonical output uses the required prefix verbatim, stable ordered phrases, and stable deduplication without reordering.
- Local versus full crop phrases are view-specific, so another view's canonical output cannot pass.
- Long-dress phrases derive only from the active `requires_full_garment_frame` contract.
- The current manifest schema represents an active accessory/footwear contract through a non-empty active-view `accessory_source`; the validator turns that into the typed `footwear_required` view flag.
- Prompt validation computes from the active manifest/view and performs direct string equality. The former finite regex/substring semantic gate was removed.
- Tests cover legacy prose, paraphrase, leading/trailing whitespace, reordering, additions, omissions, wrong view, long-dress on/off mismatch, footwear on/off mismatch, unsupported views, and malformed contracts.
- Existing positive prompt ordering and terminal suffix validation were not changed. Nano Banana Pro, 4K, 2:3 and action/camera/scene/correction prose remain before the immutable final suffix, with no appended prose accepted afterward.
- All four templates now call the renderer rather than providing editable negative prose. The schema's remaining literal negative example matches production output for its shown front/long-dress/no-footwear contract.
- The handbook source visibly labels Negative Prompt as script-generated and immutable; regenerated checked-in HTML is byte-stable.
- Scope review found only the 13 intended committed files. The pre-existing untracked `docs/superpowers/plans/` directory was preserved and excluded from the commit.

## Concerns

No unresolved functional concerns. The only environmental issue was the sandboxed default Python bytecode-cache path, resolved by redirecting the cache to `/private/tmp`. The pre-existing untracked `docs/superpowers/plans/` directory remains untouched.

---

# Fix Round 1: Explicit Footwear Evidence

## Status

DONE

## Commit

- `636e29b9b3bb4713112632e5eefb6d4305ec46db` — `fix: require explicit footwear evidence`

## Files changed

- `docs/index.html`
- `fashion-lovart-view-extension/docs/handbook.html`
- `fashion-lovart-view-extension/skill/SKILL.md`
- `fashion-lovart-view-extension/skill/references/folder-contract.md`
- `fashion-lovart-view-extension/skill/references/prompt-output-schema.md`
- `fashion-lovart-view-extension/skill/references/templates/back.md`
- `fashion-lovart-view-extension/skill/references/templates/front.md`
- `fashion-lovart-view-extension/skill/references/templates/full.md`
- `fashion-lovart-view-extension/skill/references/templates/side.md`
- `fashion-lovart-view-extension/skill/scripts/negative_prompt.py`
- `fashion-lovart-view-extension/skill/scripts/validate_manifest.py`
- `fashion-lovart-view-extension/tests/test_documentation_contract.py`
- `fashion-lovart-view-extension/tests/test_validate_manifest.py`
- `fashion-lovart-view-extension/tools/handbook-template.html`

## TDD RED

The review cases were added before production edits, covering footwear absent, full-view bag-only, full-view jewelry-only, explicit footwear present, valid front/side/back generic accessories, malformed evidence, and producer documentation:

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_view_contract_derivation_requires_explicit_footwear_evidence \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_generic_accessories_never_activate_required_footwear_defects \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_explicit_footwear_evidence_activates_the_required_footwear_defect \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_malformed_explicit_footwear_evidence_fails_closed \
  test_documentation_contract.DocumentationContractTests.test_footwear_docs_require_explicit_evidence_not_generic_accessories
```

Exit summary: exit `1`; `Ran 5 tests`; `FAILED (failures=27)`; no test errors.

Expected failures observed:

- `view_contract_from_manifest` did not exist.
- Bag-only, jewelry-only, and valid non-full generic accessories were incorrectly rendered as footwear-active.
- Malformed explicit footwear state was ignored rather than rejected.
- Producer documentation still derived footwear from `bool(accessory_source)`.

An additional malformed-source micro-cycle first reproduced an unhandled non-string evidence path:

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_malformed_explicit_footwear_evidence_fails_closed
```

Exit summary: exit `1`; `Ran 1 test`; `FAILED (errors=1)` with expected `TypeError: unhashable type: 'dict'`. Production validation was then reordered to reject non-string evidence before uniqueness checking.

Independent self-review identified one backward-compatibility edge case. The regression test was added before its production correction:

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_omitted_optional_accessory_bucket_remains_footwear_inactive
```

Exit summary: exit `1`; `Ran 1 test in 0.001s`; `FAILED (errors=1)` with expected `ValueError: manifest view accessory_source must be a list`.

## GREEN verification

### Review-case tests

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_view_contract_derivation_requires_explicit_footwear_evidence \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_generic_accessories_never_activate_required_footwear_defects \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_explicit_footwear_evidence_activates_the_required_footwear_defect \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_malformed_explicit_footwear_evidence_fails_closed \
  test_documentation_contract.DocumentationContractTests.test_footwear_docs_require_explicit_evidence_not_generic_accessories
```

Exit summary: exit `0`; `Ran 5 tests in 0.006s`; `OK`.

The omitted-optional-bucket regression was then GREEN after treating an absent bucket as empty only when no explicit evidence needs backing:

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests.test_omitted_optional_accessory_bucket_remains_footwear_inactive
```

Exit summary: exit `0`; `Ran 1 test in 0.001s`; `OK`.

### Final focused contract suite

```bash
cd fashion-lovart-view-extension/tests
python3 -m unittest \
  test_validate_manifest.DeterministicNegativePromptContractTests \
  test_documentation_contract.DocumentationContractTests.test_skill_schema_templates_and_handbook_publish_the_immutable_renderer_contract \
  test_documentation_contract.DocumentationContractTests.test_footwear_docs_require_explicit_evidence_not_generic_accessories \
  test_documentation_contract.DocumentationContractTests.test_full_literal_actions_place_generation_settings_before_terminal_suffix
```

Exit summary: exit `0`; `Ran 15 tests in 0.015s`; `OK`.

### Full repository unittest suite

```bash
python3 -m unittest discover -s fashion-lovart-view-extension/tests -p 'test_*.py'
```

Exit summary: exit `0`; `Ran 116 tests in 0.559s`; `OK`.

### Python compilation

```bash
PYTHONPYCACHEPREFIX=/private/tmp/deterministic-negative-pycache \
python3 -m py_compile \
  fashion-lovart-view-extension/skill/scripts/negative_prompt.py \
  fashion-lovart-view-extension/skill/scripts/validate_manifest.py
```

Exit summary: exit `0`; no stdout/stderr.

### Skill Creator quick validation

```bash
python3 /Users/chenyiming/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  fashion-lovart-view-extension/skill
```

Exit summary: exit `0`; `Skill is valid!`.

### Handbook build and byte comparison

```bash
cp fashion-lovart-view-extension/docs/handbook.html \
  /private/tmp/deterministic-negative-task1-fix1-handbook-final.html
node fashion-lovart-view-extension/tools/build_handbook.mjs
cmp -s /private/tmp/deterministic-negative-task1-fix1-handbook-final.html \
  fashion-lovart-view-extension/docs/handbook.html && \
cmp -s fashion-lovart-view-extension/docs/handbook.html docs/index.html
```

Exit summaries: snapshot exit `0`; build exit `0`, emitting both generated HTML paths; byte comparison exit `0` with no output. The rebuild was byte-identical and the handbook/site artifacts match.

### Whitespace and staged patch integrity

```bash
git diff --check
git diff --cached --check
```

Exit summary: both exit `0`; no diagnostics.

## Self-review

- `view_contract_from_manifest` now defaults to footwear-inactive when no explicit `footwear_contract` exists, regardless of bags, jewelry, other styling, or view name.
- Footwear activation requires an exact four-field evidence object: `kind: footwear`, non-empty unique canonical `source_paths`, finite non-boolean confidence from 0.7 to 1, and a canonical nonblank reason.
- Every footwear evidence path must be backed by the same view's existing `accessory_source`; malformed or unbacked explicit state invalidates the manifest and therefore prompt validation.
- Existing manifests remain compatible: `footwear_contract` is optional, and an omitted optional `accessory_source` bucket remains valid and inactive. If explicit footwear evidence is present without an accessory-backed path, validation still fails closed.
- Prompt exact-equality validation derives the same typed view contract; direct `bool(accessory_source)` derivation was removed from production and producer documentation.
- Focused tests exercise footwear present/absent, bag-only, jewelry-only, all valid non-full generic-accessory views, malformed evidence fields/types/ranges, and the omitted optional-role bucket.
- Skill, folder/schema references, all four templates, handbook source, and both generated HTML artifacts publish the explicit-evidence rule.
- An independent task-scoped re-review returned `CLEAN` after the compatibility correction.
- The staged diff contained only the 14 intended Fix Round 1 files. The pre-existing untracked `docs/superpowers/plans/` directory was preserved and excluded.

## Concerns

No unresolved task-scoped concerns. The pre-existing untracked `docs/superpowers/plans/` directory remains untouched.

# Final Review Fix Wave

## Scope and interface decisions

- Addressed the complete final-branch-review finding set in one implementation wave: all four Critical findings, all four Important findings, and the strict `schema_version` Minor.
- Manifest/prompt schema version remains `2`, but it is now accepted only as a strict JSON integer. Prompt actions now carry typed `attempt`, scanner-backed `source_bindings`, four-field `action_directives`, and retry-only `correction`; `render_positive_prompt` is the deterministic executable positive renderer.
- Run-state schema remains `5`. Legacy or malformed action histories, placement records, review-gate evidence, and batch states fail closed instead of being upgraded during an invalid transition.
- Submission now requires an explicit batch context (`schema_version: 1`) assembled by the CLI from `--batch-inventory` plus the current state and repeatable `--batch-state` paths. It covers every inventory SKC exactly once, validates every participating run-state/project context, and counts unfinished candidates across the full batch.
- Returned results use exact canonical task labels plus unique canonical artifact IDs before placement. Primary row slots are strict integers `1–5`; supplemental row slots are strict integers `6–10` and are available only to a formerly verified primary result displaced by a later canonically identified returned attempt.
- A ready review gate persists the exact twenty base result records, artifact IDs, canonical labels, verified primary slots, and verification timestamp. Quality transitions and SKC completion depend on that evidence.
- Positive footwear authority and the full-view footwear source sentence are emitted only when an explicit, validated `footwear_contract` exists. Generic accessory evidence remains non-authoritative.

## RED evidence

Baseline before the wave:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-baseline-pycache \
python3 -m unittest discover -s fashion-lovart-view-extension/tests -p 'test_*.py' -v
```

Exit summary: exit `0`; `Ran 116 tests`; `OK`.

Initial finding probes:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-red-pycache \
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -v
```

Exit summary: nonzero; `Ran 20 tests`; `FAILED (failures=29)` including scanner provenance, typed positive actions, retry state, artifact/placement/review gating, cross-SKC capacity, canonical labels/project evidence, transition mutation, footwear authority, and strict schema type.

Scanner/documentation probes:

```bash
python3 -m unittest \
  fashion-lovart-view-extension/tests/test_final_review_contract.py \
  fashion-lovart-view-extension/tests/test_documentation_contract.py -v
```

Focused exit summary at the first scanner/docs checkpoint: nonzero; `Ran 5 tests`; `FAILED (failures=15)`. A subsequent missing-role-record probe ran one test and errored with `TypeError`, proving malformed evidence did not yet fail closed.

Legacy-suite compatibility after the first production pass:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-legacy-red-pycache \
python3 -m unittest discover -s fashion-lovart-view-extension/tests -p 'test_*.py' -v
```

Exit summary: nonzero; `Ran 142 tests`; `FAILED (failures=42, errors=144)`. The failures were legacy fixtures/docs still emitting pre-contract scanner, prompt, and run-state records; production was not weakened, and fixtures were migrated to the binding schema.

Adversarial hardening RED checkpoints:

```bash
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -v
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k action_distinctness -v
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k every_batch_state -v
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k malformed_legacy -v
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k nonprimary -v
```

Exit summaries, in order: the hardening aggregate ran 24 tests and failed four; normalized action distinctness failed one; inconsistent batch evidence failed one; malformed legacy histories errored twice; malformed non-primary quality placement failed one.

Final placement/state hardening RED checkpoints:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-supp-label-red-pycache \
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k supplemental_slots -v

PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-gate-history-red-pycache \
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k malformed_legacy_attempt_records -v

PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-batch-state-red-pycache \
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -k every_batch_state -v
```

Exit summaries: each was nonzero. The supplemental-label probe failed one (`ValueError not raised`); the null review-history probe errored one (`TypeError: 'NoneType' object is not iterable`); the incomplete batch run-state probe failed one (`ValueError not raised`).

## GREEN evidence

Every RED checkpoint was rerun after its minimal production or contract change. Intermediate focused aggregates reached `Ran 21 tests; OK`, then `Ran 45 tests; OK`; the documentation contract suite reached `Ran 36 tests; OK`.

Final focused finding suite:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-focused-final-pycache \
python3 -m unittest fashion-lovart-view-extension/tests/test_final_review_contract.py -v
```

Exit summary: exit `0`; `Ran 29 tests in 0.064s`; `OK`.

Final repository suite:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-final2-pycache \
python3 -m unittest discover -s fashion-lovart-view-extension/tests -p 'test_*.py' -v
```

Exit summary: exit `0`; `Ran 150 tests in 0.589s`; `OK`.

Python compilation:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-compile2-pycache \
python3 -m py_compile \
  fashion-lovart-view-extension/skill/scripts/scan_skc.py \
  fashion-lovart-view-extension/skill/scripts/negative_prompt.py \
  fashion-lovart-view-extension/skill/scripts/resolve_lovart_context.py \
  fashion-lovart-view-extension/skill/scripts/update_run_state.py \
  fashion-lovart-view-extension/skill/scripts/validate_manifest.py
```

Exit summary: exit `0`; no stdout/stderr.

Skill validation:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/final-fix-wave-quick2-pycache \
python3 /Users/chenyiming/.codex/skills/skill-creator/scripts/quick_validate.py \
  fashion-lovart-view-extension/skill
```

Exit summary: exit `0`; `Skill is valid!`.

Handbook regeneration and deterministic byte comparison:

```bash
node fashion-lovart-view-extension/tools/build_handbook.mjs
cp fashion-lovart-view-extension/docs/handbook.html /private/tmp/final-fix-wave-handbook.html
cp docs/index.html /private/tmp/final-fix-wave-index.html
node fashion-lovart-view-extension/tools/build_handbook.mjs
cmp /private/tmp/final-fix-wave-handbook.html fashion-lovart-view-extension/docs/handbook.html
cmp /private/tmp/final-fix-wave-index.html docs/index.html
```

Exit summary: both builds exited `0` and emitted the two expected HTML paths; both byte comparisons exited `0` with no output.

Whitespace/staged integrity:

```bash
git diff --check
git diff --cached --check
```

Exit summary: both exit `0`; no diagnostics.

## Files

- Runtime/scanner: `skill/scripts/scan_skc.py`, `skill/scripts/validate_manifest.py`, `skill/scripts/update_run_state.py`.
- Skill contracts: `skill/SKILL.md`, `skill/references/folder-contract.md`, `skill/references/prompt-output-schema.md`, `skill/references/lovart-execution.md`.
- Prompt templates: `skill/references/templates/front.md`, `side.md`, `back.md`, `full.md`.
- Tests: `tests/test_final_review_contract.py`, `test_scan_skc.py`, `test_validate_manifest.py`, `test_update_run_state.py`, `test_documentation_contract.py`.
- Published documentation: `README.md`, `tools/handbook-template.html`, generated `docs/handbook.html`, and repository `docs/index.html`.

## Commit

- `28e9634 fix: close final review contract gaps`

## Self-review

- Canonical identity and every required role are now proven against real scanner file records with exact path/hash and strict role/confidence/reason semantics; only the explicit model-to-composition fallback may overlap.
- The validator no longer treats five copied lock blocks as executable actions. Five typed, normalized-distinct action directives and exact deterministic source/action/camera/composition/scene rendering are required.
- Retry prompts bind `ATTEMPT n` to active run-state evidence and place typed correction text before the unchanged exact terminal suffix.
- Result recording precedes placement; artifacts and labels are canonical and unique; slot zones/collisions are checked; review and completion depend on the verified twenty-base snapshot and current qualified primary placements.
- Submission validates layout/project/task/batch evidence before mutation and counts all valid current batch SKC states. Missing, stale, legacy, or structurally malformed batch state fails closed.
- Footwear positive authority is derived only from the same explicit validated evidence contract that controls negative-prompt footwear defects. The deterministic negative prompt implementation/order, head/identity/hem locks, ratios/order/caps, twenty-base gate, and rejection code set remain intact.
- Requirements are represented through typed metadata, equality against scanner/run-state records, and deterministic renderers rather than free-text blacklist matching.
- The staged implementation commit contained exactly the twenty intended runtime, test, Skill, template, and generated documentation files. The pre-existing untracked `docs/superpowers/plans/` directory was preserved and excluded.

## Concerns

No unresolved implementation concern. Existing persisted schema-2 prompt records that lack typed bindings/directives, schema-5 run-states that lack canonical artifact/placement/review evidence, or submissions without the explicit batch context now intentionally fail closed and must be regenerated or migrated. The pre-existing untracked `docs/superpowers/plans/` directory remains untouched.

# Second Remediation Cycle

## Scope and architecture decisions

- Closed only the scoped residuals C2, C4, I4, and N1 while retaining every previously passing identity, provenance, framing, negative-prompt, project/task-label, result/placement, slot, review-gate, quality-code, per-view-cap, and layout-v3 contract.
- C2 and I4 now use a closed deterministic positive renderer. Five exact action codes (`catalogue-neutral`, `weight-shift`, `controlled-step`, `detail-gesture`, `soft-turn`) map to distinct action semantics; camera, composition, and scene also use controlled maps. Scanner-backed source bindings and the active visual contracts produce fixed identity, product, scene, pose/composition, action, and camera blocks. Arbitrary action text is neither accepted as a code nor rendered as authority. A positive footwear block has exactly one structural source: a validated explicit `footwear_contract`; when that contract is absent, no positive footwear-authority sentence can be emitted.
- C4 now binds scanner output and every initialized schema-6 run-state to one immutable `batch_contract` containing strict schema version `1`, ordered authoritative `member_skc_ids`, and the SHA-256 digest of the canonical schema/member payload. Submission requires the exact full member inventory and one matching state per member; reduced, duplicated, missing, mismatched, and legacy contexts fail closed.
- Batch membership is not treated as the global concurrency authority. The runtime derives one registry at `<verified-month-source-root>/_codex/lovart-submissions.json`, atomically reserves canonical labels under `flock`, and rejects an eleventh unfinished reservation across independent scanner batches and processes. Every CLI command touching a state file now holds the same persistent state lock for the complete read-mutate/review-atomic-write transaction. Atomic replacement plus file/directory `fsync` precedes release, and durable equality is rechecked under that lock before registry deletion.
- N1 validates the whole retry history as strict positive JSON-integer records in the exact sequence `1..n-1` before submission or `1..n` after recording. The immediately preceding record must have the exact attempt and task label, timezone-aware returned-result evidence, a canonical nonblank globally unique artifact, verified primary placement, rejected action/result status, one exact rejection code, and canonical nonblank rejection evidence. Prompt binding and state submission enforce the same proof before mutation. Boolean, float, future, duplicate, missing, malformed, and extra attempts fail closed; non-string rejection codes return `ValueError` without mutation.

## RED evidence

Initial focused residual contract:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-red \
python3 -m unittest \
  fashion-lovart-view-extension/tests/test_second_remediation_contract.py -v
```

Exit summary: nonzero; `Ran 7 tests`; `FAILED (failures=26)`. The assertions covered vacuous one-letter directives, free-text footwear authority, scanner batch binding/reduced membership/legacy states, and noncanonical retry predecessors.

Initial documentation contract:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-doc-red \
python3 -m unittest \
  fashion-lovart-view-extension.tests.test_documentation_contract.DocumentationContractTests.test_second_remediation_contracts_are_published_consistently -v
```

Exit summary: nonzero; `Ran 1 test`; `FAILED (failures=16)`.

Expanded global-coordinator probes:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-registry-red \
python3 -m unittest \
  fashion-lovart-view-extension/tests/test_second_remediation_contract.py -v
```

Exit summary: nonzero; `Ran 9 tests`; `FAILED (failures=1, errors=1)`. Independent singleton batches could still obtain separate windows and the shared coordinator was not yet implemented.

First independent-review N1/type probes:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-review-findings-red \
python3 -m unittest \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.CanonicalRetryPredecessorRegressionTests -v
```

Exit summary: nonzero; `Ran 2 tests`; `FAILED (failures=2, errors=3)`. A forged future record could precede an otherwise canonical rejection, and list-valued correction/rejection codes raised `TypeError`.

Final independent-review findings were reproduced together before their production fixes:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-review-red \
python3 -m unittest \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.ScannerBatchContractRegressionTests.test_cross_command_cli_race_cannot_restore_unfinished_state \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.CanonicalRetryPredecessorRegressionTests.test_retry_sequence_rejects_boolean_and_float_earlier_attempts \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.CanonicalRetryPredecessorRegressionTests.test_non_string_reason_codes_fail_cleanly_before_mutation -v
```

Exit summary: nonzero; `Ran 3 tests in 0.174s`; `FAILED (failures=3, errors=2)`. The deterministic FIFO race restored a stale unfinished state after slot release, earlier `True`/`1.0` attempts compared equal to integer `1`, and list/dict reason codes raised `TypeError`.

The strengthened transaction-lock documentation contract was also captured RED:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-lock-doc-red \
python3 -m unittest \
  fashion-lovart-view-extension.tests.test_documentation_contract.DocumentationContractTests.test_second_remediation_contracts_are_published_consistently -v
```

Exit summary: nonzero; `Ran 1 test in 0.007s`; `FAILED (failures=3)`.

## GREEN evidence

The three final independent-review regressions passed after the minimal lock/type changes:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-review-green \
python3 -m unittest \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.ScannerBatchContractRegressionTests.test_cross_command_cli_race_cannot_restore_unfinished_state \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.CanonicalRetryPredecessorRegressionTests.test_retry_sequence_rejects_boolean_and_float_earlier_attempts \
  fashion-lovart-view-extension.tests.test_second_remediation_contract.CanonicalRetryPredecessorRegressionTests.test_non_string_reason_codes_fail_cleanly_before_mutation -v
```

Exit summary: exit `0`; `Ran 3 tests in 1.102s`; `OK`.

The synchronized documentation contract passed:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-lock-doc-green \
python3 -m unittest \
  fashion-lovart-view-extension.tests.test_documentation_contract.DocumentationContractTests.test_second_remediation_contracts_are_published_consistently -v
```

Exit summary: exit `0`; `Ran 1 test in 0.006s`; `OK`.

Final focused remediation suite:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-focused-postreview \
python3 -m unittest \
  fashion-lovart-view-extension/tests/test_second_remediation_contract.py -v
```

Exit summary: exit `0`; `Ran 17 tests in 1.786s`; `OK`.

Final full repository suite:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-full-postreview \
python3 -m unittest discover \
  -s fashion-lovart-view-extension/tests -p 'test_*.py' -v
```

Exit summary: exit `0`; `Ran 168 tests in 3.258s`; `OK`.

Python compilation:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-pycompile-release \
python3 -m py_compile \
  fashion-lovart-view-extension/skill/scripts/scan_skc.py \
  fashion-lovart-view-extension/skill/scripts/negative_prompt.py \
  fashion-lovart-view-extension/skill/scripts/resolve_lovart_context.py \
  fashion-lovart-view-extension/skill/scripts/update_run_state.py \
  fashion-lovart-view-extension/skill/scripts/validate_manifest.py
```

Exit summary: exit `0`; no stdout/stderr.

Skill Creator quick validation:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/second-remediation-quick-release \
python3 /Users/chenyiming/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  fashion-lovart-view-extension/skill
```

Exit summary: exit `0`; `Skill is valid!`.

Handbook rebuild and deterministic byte comparison:

```bash
cp fashion-lovart-view-extension/docs/handbook.html \
  /private/tmp/second-remediation-release-handbook.before.html
cp docs/index.html \
  /private/tmp/second-remediation-release-index.before.html
node fashion-lovart-view-extension/tools/build_handbook.mjs
cmp /private/tmp/second-remediation-release-handbook.before.html \
  fashion-lovart-view-extension/docs/handbook.html
cmp /private/tmp/second-remediation-release-index.before.html docs/index.html
cmp fashion-lovart-view-extension/docs/handbook.html docs/index.html
```

Exit summary: all commands exited `0`; the builder emitted both expected paths, both rebuild comparisons were byte-identical, and the handbook/site artifacts match each other.

Whitespace and staged integrity:

```bash
git diff --check
git diff --cached --check
```

Exit summary: both exited `0`; no diagnostics.

## Files

- Runtime/scanner: `skill/scripts/scan_skc.py`, `skill/scripts/validate_manifest.py`, `skill/scripts/update_run_state.py`.
- Focused and migrated tests: `tests/test_second_remediation_contract.py`, `test_final_review_contract.py`, `test_validate_manifest.py`, `test_update_run_state.py`, `test_documentation_contract.py`.
- Skill/runtime contracts: `skill/SKILL.md`, `skill/references/folder-contract.md`, `prompt-output-schema.md`, `lovart-execution.md`, and all four prompt templates.
- Published documentation: `README.md`, `tools/handbook-template.html`, generated `docs/handbook.html`, and repository `docs/index.html`.

## Commit

- `e2cde7d fix: close second remediation contract gaps`

## Self-review

- C2/I4 are implemented with positive construction, exact controlled values, and scanner/manifest equality rather than a prohibited-word blacklist. Every rendered action is executable and structurally complete; no-footwear manifests have no positive footwear rendering branch.
- C4 has two mutually reinforcing authorities: immutable scanner membership prevents batch reduction, while the shared file registry prevents independent batches from resetting the global window. Atomic reservation, persistent state locking across every CLI command, durable write verification, owner-bound release, and fail-closed malformed/legacy handling prevent over-cap races.
- N1 validates both the complete typed sequence and the immediately preceding evidence record in prompt and state paths. Adversarial future records, boolean/float aliases, duplicate artifacts, malformed placements, mismatched correction codes, blank evidence, and unhashable JSON values are covered.
- Existing deterministic negative-prompt ordering, canonical `正面/1.jpg` identity, source role provenance, head/dress framing locks, strict project/task labels, result-before-placement, unique artifacts, physical slot rules, twenty-base review/completion, rejection-code set, per-view cap, and layout-v3 tests remain green.
- The independent reviewer first returned three release blockers (cross-command stale overwrite, non-predecessor boolean/float attempt aliases, and unhashable reason-code types). Each was reproduced RED, fixed without weakening gates, and rerun; the reviewer then returned `CLEAN` after static inspection plus `17/17` focused and `168/168` full verification.
- The implementation commit contains exactly the twenty intended runtime, tests, Skill, template, and generated-documentation files. The pre-existing untracked `docs/superpowers/plans/` directory was preserved and excluded.

## Concerns

A process crash after a reservation is created but before its state update is durably written, or after a finished state is persisted but before registry release completes, intentionally leaves a conservative stale reservation. This cannot free capacity early or exceed the global cap, but it requires audited reconciliation before that slot can be reused. Malformed/corrupted registry data likewise fails closed for availability. The pre-existing untracked `docs/superpowers/plans/` directory remains untouched.
