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

The scanner records files, hashes, and duplicate groups. It deliberately leaves every semantic role `unclassified`.

### 2. Classify references visually

Open every unique image with image-view tooling. Assign each path exactly one role in `role-assignments.json`:

- `model_source`
- `product_source`
- `scene_source`
- `composition_source`
- `accessory_source`
- `unused`

Each assignment contains `role`, numeric `confidence` from 0 to 1, and a concrete visual `reason`. Follow the schema in `references/folder-contract.md`. Do not infer ordinary roles from filenames. The only filename-based exception is `正面/1.jpg`: treat it as the canonical **IDENTITY MODEL SOURCE** for identity only, then inspect it visually before deriving any identity evidence.

正面/1.jpg is the sole filename-based exception. A generic model_source or local pose/composition source must never supply canonical identity or body_profile.

Apply these rules:

- Each ready view has exactly one model, product, and scene source.
- Attach the schema-2 `identity_profile` from visible evidence in `正面/1.jpg`, including head visibility, skin tone and visible ancestry cues, visible face features, hair evidence, age impression, and body profile. Never let a `侧面`, `背面`, or `全身` pose model override these canonical identity characteristics. Noncanonical local pose/composition sources must not control or override `body_profile`; they control only pose, crop, body direction, camera, and composition.
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

- **Batch wrapper:** `scan_skc.py` always emits one wrapper whose `skcs` member contains the single-SKC inventories. Iterate `batch_payload["skcs"]` as shown; never pass the wrapper itself to `apply_role_assignments()`. For a single-SKC run, first require `len(batch_payload["skcs"]) == 1`, then select exactly `batch_payload["skcs"][0]`.
- **New run migration:** Build each identity profile only from that inventory's `正面/1.jpg`, build its garment profile from the active product evidence, index assignments and profiles by `inventory["skc_id"]`, call `apply_role_assignments(...)`, then call `attach_visual_contracts(...)` to produce schema-2 before saving that SKC's `_codex/manifest.json`. Attachment trims every required identity and garment string before persistence.
- **Resume migration:** Load the existing manifest before reusing prompts or browser state. If it is schema-1, or schema-2 with missing/invalid identity or garment evidence, reopen the canonical identity and product sources, rebuild both visual-profile dictionaries, rerun the two calls above, save schema-2, and regenerate prompts. If it is already schema-2, validate it and keep its exact canonical hash/profile contracts. A legacy/status-only layout reservation never clears submission; run `reserve-layout` again to record the complete v3 reservation.

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

Fill the template from visual evidence. Save the completed Chinese analysis in `analysis_markdown` and exactly five complete English prompts in `actions`. Prefix every executable prompt:

```text
SKC <skc_id> | VIEW <view> | ACTION <action_id> | ATTEMPT <n>
```

Every standalone action must end with one immutable, manifest-derived final contract suffix. Put all action, camera, composition, scene, lighting, and Nano Banana Pro / 4K / 2:3 prose before this suffix. Start the suffix with this exact sentence:

```text
FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.
```

Follow it with exactly one actionable `IDENTITY LOCK:` section. Use this fixed semicolon-delimited order and replace each placeholder with the type- and value-equal active manifest string; prefix matches, duplicate assignments, reordered fields, coercion, and conflicting extra assignments are invalid:

```text
IDENTITY LOCK: canonical_source=正面/1.jpg; head_visibility=<exact active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile.
```

A generic instruction such as “preserve identity,” an empty marker, or values placed elsewhere in the prompt is invalid. Use the following positive lock clauses verbatim; negated, paraphrased, partial, or duplicated clauses fail validation:

```text
HEAD CROP FLOOR: The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary.

FULL-BODY HEAD COMPLETION: Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics.

GARMENT FRAME LOCK: Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
```

Every front, side, and back action must contain one actionable `HEAD CROP FLOOR:` section and retain at least half the head; a complete head is allowed. Every full action must contain one actionable `FULL-BODY HEAD COMPLETION:` section and reconstruct a natural complete head from the canonical visible evidence when the source head is partial or absent. When `garment_contract.requires_full_garment_frame` is true, every action must contain one actionable `GARMENT FRAME LOCK:` section: keep the below-knee dress continuously visible from the shoulder/neckline through the lowest hem point, leave visible safety margin below the hem, the hem must not touch or cross an image edge, keep the major hem silhouette unobscured, and keep the apparent garment length unchanged. Do not add that lock for any active garment contract that is not a visually confirmed below-knee dress.

The final suffix order is `FINAL CONTRACT OVERRIDE` -> `IDENTITY LOCK` -> the view's `HEAD CROP FLOOR` or `FULL-BODY HEAD COMPLETION` -> conditional `GARMENT FRAME LOCK`. Earlier prompt prose may describe the requested action freely because this final block overrides any conflict. Nothing except trailing whitespace may follow the applicable final lock; appended prose invalidates the prompt.

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

If a local view pose reference is byte-identical to `正面/1.jpg`, upload only `identity_model_01` but retain the local pose/composition role logically in the manifest and prompt. Keep a mapping from temporary name to manifest path in the run log. Prompts refer to semantic labels such as `IDENTITY MODEL SOURCE`, `POSE/COMPOSITION SOURCE`, `PRODUCT SOURCE`, `SCENE SOURCE`, and `SHOES ACCESSORY SOURCE`, never Lovart's numeric image index. Upload all references once per isolated view conversation.

### 7. Operate Lovart in Chrome

Read `references/lovart-execution.md` completely before browser work. Use the existing signed-in Chrome session. Work in project `YYYY年M月`, then resolve the canvas hierarchy before submitting anything. The confirmed screenshot maps to `date -> SKC -> front/side/back/full -> primary/supplemental`; enforce layout contract version `date-skc-four-row-v3`. Dates are horizontal canvas regions from left to right; SKCs belonging to the same date are stacked vertically from top to bottom; every SKC contains four view rows; every row contains five primary cells followed by five supplemental cells.

Create or locate the date label and SKC label before generation. A date region must be wide enough for the full 10-cell row plus labels and safety padding. Place a new date strictly to the right of the previous date region's actual rightmost object plus a visible safety gap. Place a new SKC for an existing date strictly below that date region's previous SKC actual bottom edge plus a gap approximately 25% of one displayed image height. Never place two different SKCs from the same date side by side, and never estimate the next region from only the first five base images.

Before the first submission, reserve and visually verify the complete destination block: one date label, one SKC label, four labeled rows, and 10 cells per row. Record it with `update_run_state.py reserve-layout`. Submission is forbidden until the month project and layout reservation are both verified. Keep the placement backlog at zero: whenever a result appears, identify it from its exact task label and artifact, record `generated`, place and verify it, then submit the next task. If the task label or artifact cannot be matched, record `blocked:result-identity`; if any generated result remains unplaced, stop new submissions with `blocked:canvas-placement`.

Use one Chrome tab and a separate Lovart conversation for every action. Upload that action's view package, submit exactly one task, wait until Lovart visibly accepts or queues it, then switch to a new conversation without opening another browser tab. Do not submit a second task in the same conversation while the first is unfinished: Lovart cancels the earlier free-queue task. Select Nano Banana Pro, 4K, 2:3. Treat 10 accepted unfinished tasks as Lovart's hard global concurrency window: count `submitted`, `queued`, and visibly generating actions across all views and SKCs, fill the window up to 10 even when early tasks show a free-queue estimate, never submit an 11th, and fill every released slot immediately with the next pending action. For a fresh four-view SKC, submit front `FR01`–`FR05` and side `SI01`–`SI05` as the first 10-task wave unless existing unfinished tasks already occupy slots. As soon as any slot is released, continue with back and then full-body actions; do not wait for a whole wave to finish.

Use a two-phase quality order for each SKC: first submit and wait for all 20 base actions (four views times five actions) to finish; only then begin the unified visual review. Do not interrupt base generation with quality retries. Run `update_run_state.py review-gate` before review. Every view must contain five identified and verified base results in action slots `01`–`05`. If any view has fewer than five, record `blocked:base-count-incomplete`; do not review or submit corrections until the missing base actions finish and are placed. After the gate passes, review the 20 base results one by one, then use released slots for evidence-based retries.

Apply a hard generation cap independently to every view. Front, side, back, and full may each produce at most 10 candidate images total: five base candidates plus no more than five correction candidates. Count a candidate only after Lovart visibly returns an image; count rejected images and replacement images, but do not count pending, submitted, queued, cancelled, or failed requests that return no image. Before submitting, reserve capacity for all unfinished requests in that view so accepted work cannot exceed the 10-image cap. Give every rejected action one correction opportunity before assigning another correction to an action that has already received one. Stop the view immediately after it has five qualified actions or reaches 10 generated candidates. At the cap, mark every unresolved action `blocked:quality-cap` and continue other views or SKCs.

Canvas placement is **not** deferred to either phase. The moment any task finishes, pause submission long enough to place its result in the deterministic row/slot described in `references/lovart-execution.md`. Verify the placement visually, record it with `update_run_state.py place`, and only then fill the released concurrency slot. Never allow completed results to accumulate in Lovart's automatic vertical output stack.

Never click `立即生成`, use points, pay for acceleration, silently select Nano Banana 2, combine actions into a grid request, or upload references to the wrong view conversation.

Update state after every observable task change. Use `generated` only after the exact Lovart task label and artifact identity are confirmed:

```bash
python3 scripts/update_run_state.py transition <state> <view> <action-id> <status> [--reason ...] [--task-label ...] [--artifact-id ...]
```

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
- Scene identity is preserved while perspective changes only as the template permits.
- Model, background lighting direction, ground shadow, reflections, and color temperature agree.
- No cutout edge, halo, severe anatomy error, text, watermark, or random logo.
- Front, side, back, and full-body purposes are not confused.
- Identity matches `正面/1.jpg`; reject drift with `identity-drift`.
- Front, side, and back retain at least half the model's head; reject a lower crop with `head-crop-below-minimum`. A complete head or complete face is acceptable.
- When the manifest visually confirms a below-knee dress and requires a full garment frame, keep it continuously visible from the shoulder/neckline through the lowest hem point, leave visible safety margin below the hem, require that the hem must not touch or cross an image edge, keep the major hem silhouette unobscured, and keep the apparent garment length unchanged. Reject any violation with `long-dress-hem-cropped`.
- For every full-body action, the frame contains the complete model continuously from the very top of the hair/head to the bottom of both feet, including the complete face, both shoes, toes, and soles. Leave visible safety margin above the hair and below the footwear; no part of the head, chin, ankles, feet, or shoes may touch or cross the image edge. Reject an incomplete reconstructed head with `full-head-incomplete`.

On failure, record a specific reason and resubmit the same action with a concise correction only when the view still has generation capacity. Rebuild every retry prompt in this exact order:

1. Remove the existing terminal block from FINAL CONTRACT OVERRIDE through the end of the prompt.
2. Insert the evidence-based correction into the action prose before the terminal block.
3. Rebuild and append the entire manifest-derived terminal block from the active manifest.
4. Validate the rebuilt prompt; never append correction text after the terminal block.

Append each exact correction prompt and visible Lovart label to `run-log.md`; `run-state.json` retains structured attempt and rejection history plus the view-level generated count. There is no per-action three-attempt rule. The view stops at five qualified actions or 10 generated candidates; unresolved actions then become `blocked:quality-cap`.

Maintain the canvas continuously inside the assigned date/SKC region as four horizontal lanes: row 1 `正面`, row 2 `侧面`, row 3 `背面`, row 4 `全身`. Give every image the same displayed width while preserving its original aspect ratio. Align the tops of images within a row and the left edges of all four rows. Use a horizontal gap approximately 8% of the displayed image width and a vertical row gap approximately 8% of the displayed image height. These ratios are visual targets with small operational tolerance; visible uneven gaps, large empty spaces, or overlap fail placement verification. The left side of every row is a fixed five-cell primary strip ordered action `01` through `05`. The next five continuous positions are supplemental cells, so each row can contain at most 10 generated images. Place every base result immediately in its action's primary cell. When a retry finishes, first move the displaced/rejected candidate into the same row's next supplemental cell, then put the new candidate into the original primary cell. Keep supplemental candidates grouped by action and attempt number. Never move supplemental images to another row, another SKC/date region, or a detached vertical pile.

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
