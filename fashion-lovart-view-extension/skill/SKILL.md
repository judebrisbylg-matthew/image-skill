---
name: fashion-lovart-view-extension
description: Use when processing one SKC or a batch of SKCs containing 正面、侧面、背面、全身 reference folders for multi-view fashion extension prompts and Lovart Nano Banana Pro generation in Chrome.
---

# Fashion Lovart View Extension

## Overview

Process every SKC as four isolated view jobs. Classify references visually, fill the matching Feishu-derived template, generate five independent prompts per view, operate Lovart in Chrome, and count completion only after five candidates pass Codex visual review.

## Required Skills

- **REQUIRED:** Use `chrome:control-chrome` for Lovart UI work.
- Use `computer-use:computer-use` only for a native file picker or UI element Chrome control cannot operate.

## Inputs and Outputs

Accept either a single SKC folder or a batch root. A single SKC contains one or more direct children named `正面`, `侧面`, `背面`, `全身`.

Write into each SKC without renaming or moving source images:

```text
<skc>/_codex/
├── manifest.json
├── role-assignments.json
├── run-state.json
├── run-log.md
└── prompts/
    ├── front.json
    ├── side.json
    ├── back.json
    └── full.json
```

Use `/tmp/lovart_view_extension/<first-12-sha256-of-skc-path>/<view>/` for ASCII-only upload packages. Never download Lovart results automatically.

## Workflow

### 1. Discover and inventory

Run:

```bash
python3 scripts/scan_skc.py <input-path> --output <temporary-batch-inventory.json>
```

The scanner records files, lowercase SHA-256 hashes, and duplicate groups. It deliberately leaves every semantic role `unclassified`. It also derives one authoritative `batch_contract` with strict schema version `1`, deterministic ordered `member_skc_ids`, and a lowercase SHA-256 `digest`; the wrapper and every member inventory carry the same exact contract. The canonical `正面/1.jpg` path/hash must resolve to exactly one real record in `views.front.files`; never copy a detached or user-supplied hash into the contract. It is also the highest whole-outfit styling authority.

### 2. Classify references visually

Open every unique image with image-view tooling. Assign each path exactly one role in `role-assignments.json`:

- `model_source`
- `product_source`
- `scene_source`
- `composition_source`
- `accessory_source`
- `unused`

Each assignment contains `role`, numeric `confidence` from 0 to 1, and a concrete visual `reason`; the scanner record retains that role, confidence, reason, path, and hash as the authoritative evidence. Follow the schema in `references/folder-contract.md`. Do not infer ordinary roles from filenames. The only filename-based exception is `正面/1.jpg`: treat it as the canonical **IDENTITY MODEL SOURCE** for identity only, then inspect it visually before deriving any identity evidence.

正面/1.jpg is the sole filename-based exception. A generic model_source or local pose/composition source must never supply canonical identity or body_profile.

Apply these rules:

- Each ready view has exactly one scanner-backed model, product, scene, and composition source. A path has one primary role; the sole legal overlap is an explicit `model_source` -> `composition_source` fallback recorded with `composition_fallback: model_source`.
- Attach the schema-2 `identity_profile` from visible evidence in `正面/1.jpg`, including head visibility, skin tone and visible ancestry cues, visible face features, hair evidence, age impression, and body profile. Never let a `侧面`, `背面`, or `全身` pose model override these canonical identity characteristics. Noncanonical local pose/composition sources must not control or override `body_profile`; they control only pose, crop, body direction, camera, and composition.
- Before every prompt, create a styling contract from `正面/1.jpg`: exact lower-body garment, exposed-or-covered waist relationship, shoes, bag, accessories, and carry method. Preserve it exactly; product evidence controls target-product construction only and must not turn confirmed trousers into a skirt/dress, conceal a confirmed exposed waist, or substitute accessories.
- Create a scene contract from the active scene source: setting type, weather/daylight, color temperature, key-light direction, shadow softness, and core environment. Never mix indoor/outdoor, sunny/overcast, warm/cool, or unrelated locations in one view.
- Inspect the product evidence and attach `garment_profile`. Set `requires_full_garment_frame: true` only when the garment is visually confirmed as a below-knee dress.
- If composition is absent and the model source clearly controls crop, reuse the model source as composition fallback.
- Accessories are optional. A non-empty `accessory_source` alone never proves footwear: bags, jewelry, and other styling remain footwear-inactive. Add the view's optional `footwear_contract` only after visually confirming required shoes. It must contain exactly `kind: footwear`, non-empty unique `source_paths`, numeric `confidence` from 0.7 to 1, and a canonical nonblank `reason`; every source path must belong to that view's `accessory_source`. Omit the contract when footwear is absent or unconfirmed.
- Each path has one primary role. The only multi-role rule is the explicit unique-model-to-composition fallback. Images with identical hashes upload only once.
- Every classified file with confidence below 0.7—including optional `accessory_source` and `unused` files—triggers `blocked:role-ambiguous`; unclassified images and multiple candidates for a required role also block that view. The canonical identity file may legitimately expose less than a complete head: `partial` or `absent` head_visibility is not itself a confidence penalty. Therefore head_visibility of `partial` or `absent` alone never lowers a view's ready status and never triggers `blocked:role-ambiguous`.

Supply both visual profiles as Python dictionaries created from direct image inspection. `identity_profile` must contain nonblank `head_visibility`, `skin_tone_and_visible_ancestry_cues`, `visible_face_features`, `hair_evidence`, `age_impression`, `body_profile`, `reason`, and numeric `confidence` from 0 to 1. `garment_profile` must contain nonblank `garment_type`, valid `hem_position`, boolean `requires_full_garment_frame`, and nonblank `reason`. A `below_knee` hem is valid only for a `dress`, and that combination must set the frame lock to `true`.

Invoke the schema migration in this order after visual classification:

```python
import json
from pathlib import Path

from scripts.scan_skc import apply_role_assignments, attach_visual_contracts

batch_payload = json.loads(Path(batch_inventory_path).read_text(encoding="utf-8"))
for inventory in batch_payload["skcs"]:
    manifest = apply_role_assignments(
        inventory, assignments_by_skc[inventory["skc_id"]]
    )
    manifest = attach_visual_contracts(
        manifest,
        identity_profile=identity_profiles[inventory["skc_id"]],
        garment_profile=garment_profiles[inventory["skc_id"]],
    )
```

- **Batch wrapper:** `scan_skc.py` always emits one wrapper whose `skcs` member contains the single-SKC inventories. Treat `batch_payload["batch_contract"]` as immutable scanner authority. Its `member_skc_ids` and deterministic `digest` must match every member's copied `batch_contract`. Iterate `batch_payload["skcs"]` as shown; never pass the wrapper itself to `apply_role_assignments()`. For a single-SKC run, first require `len(batch_payload["skcs"]) == 1`, then select exactly `batch_payload["skcs"][0]`.
- **New run migration:** Build each identity profile only from that inventory's `正面/1.jpg`, build its garment profile from the active product evidence, index assignments and profiles by `inventory["skc_id"]`, call `apply_role_assignments(...)`, then call `attach_visual_contracts(...)` to produce schema-2 before saving that SKC's `_codex/manifest.json`. Attachment trims every required identity and garment string before persistence.
- **Resume migration:** Load the existing manifest before reusing prompts or browser state. If it is schema-1, or schema-2 with missing/invalid identity or garment evidence, reopen the canonical identity and product sources, rebuild both visual-profile dictionaries, rerun the two calls above, save schema-2, and regenerate prompts. If it is already schema-2, validate it and keep its exact canonical hash/profile contracts. New state initialization requires the manifest's scanner-derived `batch_contract` and persists a deep copy as run-state schema `6`; legacy states without that contract fail closed and must be recreated from the original authoritative scanner batch. A legacy/status-only layout reservation never clears submission; run `reserve-layout` again to record the complete v3 reservation.

Save the resulting single-SKC schema-2 object as `_codex/manifest.json`, then validate:

```bash
python3 scripts/validate_manifest.py manifest <skc>/_codex/manifest.json
```

### 3. Build five prompts per ready view

Read `references/prompt-output-schema.md` and the matching template:

| View | Folder | Template |
|---|---|---|
| `front` | 正面 | `references/templates/front.md` |
| `side` | 侧面 | `references/templates/side.md` |
| `back` | 背面 | `references/templates/back.md` |
| `full` | 全身 | `references/templates/full.md` |

Fill the template from visual evidence. Save the completed Chinese analysis in `analysis_markdown` and exactly five complete English prompts in `actions`. `schema_version` is the strict JSON integer `2`, never `2.0`, `true`, or `"2"`. Every action contains strict positive-integer `attempt`, scanner-backed `source_bindings`, and `action_directives` whose `action`, `camera`, `composition`, and `scene` are supported controlled code values. The exact action sequence is `catalogue-neutral`, `weight-shift`, `controlled-step`, `detail-gesture`, `soft-turn`; camera, composition, and scene codes come only from the render maps in `validate_manifest.py`. `correction` is `null` on attempt 1; retries use an exact rejection code as `fix` and `accepted-contracts` as `preserve`. One-letter values and arbitrary prose are invalid.

Build `prompt_en` only with `render_positive_prompt(skc_id, view, action, manifest)` and require exact output equality during validation. The deterministic renderer emits canonical identity, product, scene, and pose/composition path/hash bindings; fixed action/camera/pose-composition/scene-extension blocks from controlled maps; optional mapped correction; generation settings; then the exact terminal contract. These fields accept no free authority prose. Every free identity evidence string, scanner-derived SKC ID, and noncanonical scanner path is emitted only as reversible `utf8hex` inert evidence data; only controlled sentences may carry execution authority. A positive `FOOTWEAR SOURCE` block and `EXPLICIT FOOTWEAR FRAME` appear only from an explicit validated `footwear_contract`; without it, no other evidence field or source path has a structural route to emit positive footwear authority.

The renderer prefixes every executable prompt:

```text
SKC utf8hex:<UTF-8 hex of skc_id> | VIEW <view> | ACTION <action_id> | ATTEMPT <n>
```

Every standalone action must end with one immutable, manifest-derived final contract suffix. Put all action, camera, composition, scene, lighting, and Nano Banana Pro / 4K / 2:3 prose before this suffix. Start the suffix with this exact sentence:

```text
FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.
```

Follow it with exactly one actionable `IDENTITY LOCK:` section. Use this fixed semicolon-delimited order. `head_visibility` is a controlled enum; every free evidence value is the reversible `utf8hex` encoding of the type- and value-equal active manifest string. Prefix matches, duplicate assignments, reordered fields, coercion, decoded prose, and conflicting extra assignments are invalid:

```text
IDENTITY LOCK: canonical_source=正面/1.jpg; head_visibility=<exact controlled value>; skin_tone_and_visible_ancestry_cues=utf8hex:<UTF-8 hex of exact active value>; visible_face_features=utf8hex:<UTF-8 hex of exact active value>; hair_evidence=utf8hex:<UTF-8 hex of exact active value>; age_impression=utf8hex:<UTF-8 hex of exact active value>; body_profile=utf8hex:<UTF-8 hex of exact active value>; Noncanonical local pose/composition sources must not control or override body_profile.
```

A generic instruction such as “preserve identity,” an empty marker, or values placed elsewhere in the prompt is invalid. Use the following positive lock clauses verbatim; negated, paraphrased, partial, or duplicated clauses fail validation:

```text
HEAD CROP FLOOR: The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary.

FULL-BODY HEAD COMPLETION: Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics.

FULL-BODY FRAME: Keep the complete model continuously visible from the highest point of the hair and top of the head through the entire body to the lowest point of both feet. Keep the complete hair crown, full head, full face, chin, neck, entire body, garment hem, ankles, both feet, and toes fully inside the frame. Leave clear visible safety margin above the hair and below both feet. No body part may touch, cross, or be cropped by an image edge. Move the camera farther away whenever the pose or camera distance would violate this frame.

EXPLICIT FOOTWEAR FRAME: Because an explicit scanner-validated footwear_contract is active, keep both validated shoes and their shoe soles fully visible inside the lower safety margin.

GARMENT FRAME LOCK: Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
```

Every front, side, and back action must contain one actionable `HEAD CROP FLOOR:` section and retain at least half the head; a complete head is allowed. Every full action must contain one actionable `FULL-BODY HEAD COMPLETION:` section and the exact `FULL-BODY FRAME:` block. The generic full-body block always keeps the complete model through both feet and toes with top/bottom safety margins, but never invents shoes authority. Append `EXPLICIT FOOTWEAR FRAME:` only when the active full view has an explicit validated `footwear_contract`; only that conditional block may require validated shoes and shoe soles. When `garment_contract.requires_full_garment_frame` is true, every action must contain one actionable `GARMENT FRAME LOCK:` section: keep the below-knee dress continuously visible from the shoulder/neckline through the lowest hem point, leave visible safety margin below the hem, the hem must not touch or cross an image edge, keep the major hem silhouette unobscured, and keep the apparent garment length unchanged. Do not add that lock for any active garment contract that is not a visually confirmed below-knee dress.

The final suffix order is `FINAL CONTRACT OVERRIDE` -> `IDENTITY LOCK` -> the view's `HEAD CROP FLOOR`, or `FULL-BODY HEAD COMPLETION` -> `FULL-BODY FRAME` -> conditional `EXPLICIT FOOTWEAR FRAME`, then conditional `GARMENT FRAME LOCK`. All preceding executable prose comes from controlled renderer maps; evidence remains inert data. Nothing except trailing whitespace may follow the applicable final lock; appended prose invalidates the prompt.

Negative Prompt is script-generated and immutable. Do not write, paraphrase, reorder, trim, extend, or otherwise compose `negative_prompt` as Markdown prose. Derive the active view contract with `view_contract_from_manifest`, call `render_negative_prompt`, and copy its return value without modification into all five actions. Only an explicit validated `footwear_contract` activates required-footwear defects; a generic bag, jewelry, or other `accessory_source` never does, and a malformed explicit contract invalidates the manifest:

```python
from scripts.negative_prompt import render_negative_prompt, view_contract_from_manifest

view_contract = view_contract_from_manifest(view, manifest["views"][view])
negative_prompt = render_negative_prompt(
    view_contract,
    manifest["identity_profile"],
    manifest["garment_profile"],
)
for action in actions:
    action["negative_prompt"] = negative_prompt
```

The canonical renderer activates view-specific crop defects, below-knee-dress defects only when `requires_full_garment_frame` is `true`, and required-footwear defects only when the active view's explicit validated `footwear_contract` is present. Action-specific composition restrictions remain in `prompt_en` before the immutable final suffix; they never become ad hoc negative-prompt text.

Validate each prompt JSON against its active schema-2 manifest before browser work. The prompt `skc_id`, complete canonical identity path/hash/profile, and garment contract must match that manifest exactly:

```bash
python3 scripts/validate_manifest.py prompt <skc>/_codex/prompts/<view>.json <skc>/_codex/manifest.json
```

For retries, also pass the active run-state so typed `attempt`, `ATTEMPT n`, and the immediately preceding rejected attempt remain consistent:

```bash
python3 scripts/validate_manifest.py prompt <skc>/_codex/prompts/<view>.json \
  <skc>/_codex/manifest.json <skc>/_codex/run-state.json
```

### 4. Resolve and verify the dated Lovart context

Before preparing uploads, resolve the expected month project and date region from the user-provided path:

```bash
python3 scripts/resolve_lovart_context.py resolve <input-path> --output <batch-context.json>
```

For a path such as `/Users/chenyiming/Desktop/8月/8月15日`, the exact expected Lovart project is `8月` and the date region is `8月15日`. The dated folder's direct parent is the only source of the project name; never infer it from today's date, recent projects, the active canvas, or a project ID.

After Chrome exposes the current visible project name, verify it:

```bash
python3 scripts/resolve_lovart_context.py verify <batch-context.json> \
  --visible-project <exact-visible-project-name> --output <batch-context.json>
```

`project_verification_status` must be `verified` before browser execution continues. If verification returns `blocked:month-project-mismatch`: Do not upload references or submit any generation task. Stop the current batch and immediately report the script-produced message to the user, including input path, expected project, current project, and the instruction to enter or create the correct project and reply `已修正`. Record that feedback with `update_run_state.py feedback-sent`. After the user replies, re-read the visible Lovart project name and run verification again; a user confirmation alone never clears the gate.

### 5. Initialize or resume state

If `_codex/run-state.json` does not exist:

```bash
python3 scripts/update_run_state.py init <manifest.json> <run-state.json> \
  --execution-context <batch-context.json>
```

Resume rules:

- Skip `qualified` actions.
- Search the monthly Lovart project for `submitted` or `queued` task labels before resubmitting.
- Resume `rejected` actions only while that view has produced fewer than 10 candidate images.
- Never restart completed views.

### 6. Prepare references

Create one ASCII-only package per view. Use only the fixed ASCII root and a SHA-derived SKC slug; never place a Chinese or user-provided name directly in the temporary path. Copy unique files in this order:

1. `identity_model_01`: canonical `正面/1.jpg`, always first
2. `pose_model_01`: separate local view pose/composition model when its hash differs
3. `product_01`
4. `scene_01`
5. `composition_01` when its hash is not already present
6. `accessory_01...`

If a local view pose reference is byte-identical to `正面/1.jpg`, upload only `identity_model_01` but retain the local pose/composition role logically in the manifest and prompt. Keep a mapping from temporary name to manifest path in the run log. Prompts refer to semantic labels such as `IDENTITY MODEL SOURCE`, `POSE/COMPOSITION SOURCE`, `PRODUCT SOURCE`, `SCENE SOURCE`, and conditional `FOOTWEAR SOURCE`, never Lovart's numeric image index. Upload all references once per isolated view conversation.

### 7. Operate Lovart in Chrome

Read `references/lovart-execution.md` completely before browser work. Use the existing signed-in Chrome session. Work in project `YYYY年M月`, then resolve the canvas hierarchy before submitting anything. The confirmed screenshot maps to `date -> SKC -> front/side/back/full -> primary/supplemental`; enforce layout contract version `date-skc-four-row-v3`. Dates are horizontal canvas regions from left to right; SKCs belonging to the same date are stacked vertically from top to bottom; every SKC contains four view rows; every row contains five primary cells followed by five supplemental cells.

Create or locate the date label and SKC label before generation. A date region must be wide enough for the full 10-cell row plus labels and safety padding. Place a new date strictly to the right of the previous date region's actual rightmost object plus a visible safety gap. Place a new SKC for an existing date strictly below that date region's previous SKC actual bottom edge plus a gap approximately 25% of one displayed image height. Never place two different SKCs from the same date side by side, and never estimate the next region from only the first five base images.

Before the first submission, reserve and visually verify the complete destination block: one date label, one SKC label, four labeled rows, and 10 cells per row. Record it with `update_run_state.py reserve-layout`. Submission is forbidden until the month project and layout reservation are both verified and internally consistent (`expected_month_project == verified_month_project`, matching date region, no blocker, no pending feedback). Keep the placement backlog at zero: whenever a result appears, resolve its exact canonical task label and unique artifact, record `generated`, place and verify it, then submit the next task. If the task label or artifact cannot be matched, record `blocked:result-identity`; if any generated result remains unplaced, stop new submissions with `blocked:canvas-placement`.

Every submission must supply an explicit deterministic batch context: the original scanner batch inventory plus the current run-state of every SKC in its authoritative `batch_contract.member_skc_ids`. The wrapper, current state, and every other member state must carry the same valid `digest`; the supplied SKC/state order must exactly equal the contract. Pass the current state as the positional state; repeat `--batch-state` once for every other authoritative member. Even a single-SKC run passes `--batch-inventory`. Reduced, missing, legacy, duplicated, differently ordered, re-digested, or cross-month/date context fails closed. Only after complete membership validation does the runtime count unfinished work across all authoritative states and enforce the global 10-unfinished cap:

The state API and CLI derive one shared registry from the verified month project and local OS user under a fixed local-user coordination root: the passwd-derived persistent per-user state directory `~/Library/Application Support/fashion-lovart-view-extension/submission-registries`, never `/tmp`. Source roots never select or partition this authority, and no batch/caller path can override it. Each scope uses a stable sibling lock file opened through directory descriptors with `O_NOFOLLOW` at every component; the walk must fsync every parent directory entry so newly created authority directories survive a crash or restart. Under that lock, a missing registry alone permits first creation; an existing zero-byte, malformed, scope-mismatched, symlinked, or otherwise unsafe registry fails closed. Updates write a same-directory exclusive temporary regular file, file-`fsync`, atomic replace, and directory fsync without ever truncating the live registry. They reserve each canonical task label before state mutation. The CLI serializes every state-file CLI command for the same state under one persistent lock for its entire read-mutate-atomic-write transaction; durable state comparison and release remain inside that lock. It atomically replaces and `fsync`s that state before releasing a finished slot, so a write failure or crash keeps the reservation conservatively occupied. A direct caller of `transition_action` with the production file coordinator must likewise persist the returned state before calling `release_submission_slot(state, view, action_id, persisted_state_path)`, which acquires the same state lock and verifies strict equality with that durable file. Therefore independent scanner batches and source trees, including independently scanned singleton batches and concurrent processes, contribute to the same atomic 10-slot ceiling for that local-user/month-project scope. A corrupt registry, duplicate reservation, missing release record, or eleventh reservation fails closed.

The scope invariant is literal: source roots never select or partition the authority.

Registry JSON with duplicate JSON object keys is malformed and fails closed before any reservation mutation.

```bash
python3 scripts/update_run_state.py transition <state> <view> <action-id> submitted \
  --task-label "SKC <skc-id> | VIEW <view> | ACTION <action-id> | ATTEMPT <n>" \
  --batch-inventory <temporary-batch-inventory.json> \
  --batch-state <other-skc-1-run-state.json> --batch-state <other-skc-2-run-state.json>
```

Use one Chrome tab and a separate Lovart conversation for every action. Upload that action's view package, submit exactly one task, wait until Lovart visibly accepts or queues it, then switch to a new conversation without opening another browser tab. Do not submit a second task in the same conversation while the first is unfinished: Lovart cancels the earlier free-queue task. Select Nano Banana Pro, 4K, 2:3. Lovart's 10-task limit remains a hard ceiling, but do not mix views merely to fill it.

Use a **per-view closed loop**: submit the five base actions for the active view, place every returned image immediately, inspect that view, and correct failures until five qualify or the view reaches its 10-image cap. Only then begin the next view in front → side → back → full order. If the active view has fewer than five identified and verified base results, record `blocked:base-count-incomplete`; do not review or correct it until its base slots are resolved.

Apply a hard generation cap independently to every view. Front, side, back, and full may each produce at most 10 candidate images total: five base candidates plus no more than five correction candidates. Count a candidate only after Lovart visibly returns an image; count rejected images and replacement images, but do not count pending, submitted, queued, cancelled, or failed requests that return no image. Before submitting, reserve capacity for all unfinished requests in that view so accepted work cannot exceed the 10-image cap. Give every rejected action one correction opportunity before assigning another correction to an action that has already received one. Stop the view immediately after it has five qualified actions or reaches 10 generated candidates. At the cap, mark every unresolved action `blocked:quality-cap` and continue other views or SKCs.

Canvas placement is **not** deferred to either phase. The moment any task finishes, pause submission long enough to place its result in the deterministic row/slot described in `references/lovart-execution.md`. Verify the placement visually, record it with `update_run_state.py place`, and only then fill the released concurrency slot. Never allow completed results to accumulate in Lovart's automatic vertical output stack.

Never click `立即生成`, use points, pay for acceleration, silently select Nano Banana 2, combine actions into a grid request, or upload references to the wrong view conversation.

Update state after every observable task change. Use `generated` only after the exact Lovart task label and a canonical nonblank unique artifact identity are confirmed. A result record must exist before any placement or quality transition; pre-placement and duplicate artifacts fail closed:

```bash
python3 scripts/update_run_state.py transition <state> <view> <action-id> generated \
  --task-label "SKC <skc-id> | VIEW <view> | ACTION <action-id> | ATTEMPT <n>" \
  --artifact-id "<unique-visible-artifact-id>"

python3 scripts/update_run_state.py place <state> <view> <action-id> <attempt> \
  --area primary --slot <1-5> --verified
```

`attempt` and `slot` are strict JSON integers, never booleans, floats, or numeric strings. Primary slots `1`–`5` must equal the action number. Only a verified primary result displaced after a later attempt has returned may move into supplemental slots `6`–`10`; each physical row slot has at most one placement.

Use `--reason-code` only for these four hard-rule failures and always pair it with an evidence-based `--reason`:

```bash
python3 scripts/update_run_state.py transition <state> <view> <action-id> rejected \
  --reason "<observed defect>" --reason-code <code>
```

- `identity-drift` — canonical identity mismatch
- `head-crop-below-minimum` — front/side/back crop below the half-head floor
- `full-head-incomplete` — full-body head or hair crown incomplete
- `long-dress-hem-cropped` — confirmed below-knee dress hem cropped

Ordinary garment, hands, scene, light, or anatomy rejection uses free-form `--reason` only:

```bash
python3 scripts/update_run_state.py transition <state> <view> <action-id> rejected \
  --reason "<ordinary quality defect>"
```

### 8. Review candidates

Codex must open or enlarge every candidate and compare it against the active manifest sources and action prompt. Lovart-written self-checks and thumbnail rows are not evidence. Review in this order: identity against the canonical `identity_profile`; crop/head framing; conditional full-garment framing; then ordinary product, pose, scene, lighting, and styling quality.

A candidate qualifies only when all are true:

- One standalone image with exactly one adult model; no grid, collage, or multiple panels.
- Garment color, silhouette, neckline, sleeves, length, material, and requested view match product evidence.
- Action, hands, bag, shoes, camera, and crop match the action contract.
- The whole outfit exactly preserves the styling contract from `正面/1.jpg`: lower-body garment, exposed/covered waist relationship, shoes, bag, accessories, and carry method all match.
- Scene identity exactly preserves the active scene contract: setting type, weather/daylight, color temperature, key-light direction, shadows, and core environment agree.
- For side view, body rotation is 15–45 degrees. A pure 90-degree profile, above-45-degree side profile, and below-15-degree near-front image fail.
- No cutout edge, halo, severe anatomy error, text, watermark, or random logo.
- Front, side, back, and full-body purposes are not confused.
- Identity matches `正面/1.jpg`; reject drift with `identity-drift`.
- Front, side, and back retain at least half the model's head; reject a lower crop with `head-crop-below-minimum`. A complete head or complete face is acceptable.
- When the manifest visually confirms a below-knee dress and requires a full garment frame, keep it continuously visible from the shoulder/neckline through the lowest hem point, leave visible safety margin below the hem, require that the hem must not touch or cross an image edge, keep the major hem silhouette unobscured, and keep the apparent garment length unchanged. Reject any violation with `long-dress-hem-cropped`.
- For every full-body action, the frame contains the complete model continuously from the highest point of the hair/head to the lowest point of both feet, including the complete face, ankles, both feet, and toes. Leave visible safety margin above the hair and below both feet; no body part may touch or cross an image edge. Only an explicit validated `footwear_contract` additionally requires both validated shoes and shoe soles. Reject an incomplete reconstructed head with `full-head-incomplete`.

On failure, record a specific reason and resubmit the same action with a concise correction only when the view still has generation capacity. Rebuild every retry prompt in this exact order:

1. Remove the existing terminal block from FINAL CONTRACT OVERRIDE through the end of the prompt.
2. Insert the evidence-based correction into the action prose before the terminal block.
3. Rebuild and append the entire manifest-derived terminal block from the active manifest.
4. Validate the rebuilt prompt; never append correction text after the terminal block.

Implement that order through typed data: increment `attempt` to the exact next run-state attempt and set `correction` to `{"fix": "<exact rejection_reason_code>", "preserve": "accepted-contracts"}`. A retry requires its canonical immediately preceding attempt record: exact attempt number and task label, timezone-aware returned-result evidence, a nonblank unique artifact, verified primary placement, rejected action/result status, one of the four exact `rejection_reason_code` values, and nonblank rejection evidence. The complete history is the strict integer sequence `1..n-1` before submission and `1..n` afterward—no gaps, duplicates, booleans, future attempts, or extra records. In the already-recorded form, action status is exactly `submitted` or `queued`, `lovart_task_label` is the exact current label, and history ends with an exact eight-field current attempt record (`attempt`, `submitted_at`, `task_label`, `artifact_id`, `rejection_reason`, `rejection_reason_code`, `result_recorded_at`, `result_status`): the timestamp is timezone-aware, action-level `submitted_at` exactly equals that current-record value, it is strictly later than the predecessor `result_recorded_at`, and all five result fields are `null`. Prompt validation enforces both that current record and the canonical rejected predecessor; state submission checks the predecessor before mutation. Call `render_positive_prompt`; the fixed renderer places the mapped correction before settings and the exact terminal suffix. No free authority prose may be spliced into rendered output.

Append each exact correction prompt and visible Lovart label to `run-log.md`; `run-state.json` retains structured attempt and rejection history plus the view-level generated count. There is no per-action three-attempt rule. The view stops at five qualified actions or 10 generated candidates; unresolved actions then become `blocked:quality-cap`.

Maintain the canvas continuously inside the assigned date/SKC region as four horizontal lanes: row 1 `正面`, row 2 `侧面`, row 3 `背面`, row 4 `全身`. Reserve a separate **label rail** before the image grid: date, SKC and row labels stay entirely inside that rail, with visible clearance before the first image cell. Images may never overlap, cover, or begin beneath a label. Give every image the same displayed width while preserving its original aspect ratio. Align the tops of images within a row and the left edges of all four rows. Use a horizontal gap approximately 8% of the displayed image width and a vertical row gap approximately 8% of the displayed image height. These ratios are visual targets with small operational tolerance; visible uneven gaps, large empty spaces, label collisions, or overlap fail placement verification. The left side of every row is a fixed five-cell primary strip ordered action `01` through `05`. The next five continuous positions are supplemental slots `6`–`10`, so each row can contain at most 10 generated images. Place every base result immediately in its action's primary cell. When a retry finishes, first record its returned unique artifact, then move the displaced/rejected candidate into the same row's next supplemental slot, and finally put the new candidate into the original primary cell. Keep supplemental candidates grouped by action and attempt number. Never move supplemental images to another row, another SKC/date region, or a detached vertical pile.

After every placement, verify all of the following before continuing: the result is in the correct view row, the action cell or supplemental position is correct, image size matches the row, spacing is even, no other image moved unexpectedly, and Lovart has visibly retained the position. Record the placement in `run-state.json`. If placement cannot be verified, stop new submissions, record `blocked:canvas-placement`, and preserve the existing layout; do not attempt a final bulk rearrangement.

An SKC is `completed` only when all four views contain five `qualified` actions, every generated attempt has a verified canvas placement, the five current qualified candidates in each row occupy the official primary strip, and its entire four-row block remains inside the correct date region without overlap: 20 qualified images total.

## Stop Conditions

Stop the affected view and log the blocker when Lovart is signed out, Nano Banana Pro is unavailable, reference upload fails repeatedly, a required role remains ambiguous, or Lovart refuses to accept another task before the 10-task window is full. Continue other safe views or SKCs when the UI permits.

A visible multi-minute free-queue estimate is not itself a stop condition. Mark each accepted job `queued`, record the estimate, and continue filling available slots until 10 unfinished tasks have been accepted. Stop the browser turn only after the 10-task window is full or the UI explicitly rejects further free submissions. Never click points acceleration and never wait indefinitely inside one tool call.

## Common Mistakes

- Treating `1/2/3/4` as global roles. Roles vary by view; full-body image 4 may be shoes.
- Counting submitted or generated images as qualified. Only individual visual review changes status to `qualified`.
- Exceeding 10 generated candidates in a view. Five base images plus five correction images is the absolute row limit.
- Reusing one Lovart conversation for multiple unfinished actions. Lovart cancels the earlier free-queue task; use one conversation per action while keeping one browser tab.
- Deferring layout until all results finish. Place and verify every completed result immediately; late bulk layout is fragile and can exceed the browser-control window.
- Starting review when a view has fewer than five identified and verified base results. The 20-image base-count gate must pass first.
- Continuing submission with a non-zero placement backlog or guessing an action from completion order. Stop and resolve the exact task label and artifact identity.
- Arranging SKCs from the same date side by side. Dates advance horizontally; SKCs within one date advance vertically.
- Starting the next date after only the five-cell primary strip. Reserve the full 10-cell row width and a safety gap so later corrections cannot collide with the next date.
- Spending points to clear a queue. This workflow is free-queue only.
- Downloading results. Leave them organized on the Lovart canvas.
