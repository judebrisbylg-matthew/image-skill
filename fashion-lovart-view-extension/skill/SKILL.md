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

Each assignment contains `role`, numeric `confidence` from 0 to 1, and a concrete visual `reason`. Follow the schema in `references/folder-contract.md`. Do not infer role from filename alone.

Apply these rules:

- Each ready view has exactly one model, product, and scene source.
- If composition is absent and the model source clearly controls crop, reuse the model source as composition fallback.
- Accessories are optional. In the full-body workflow, shoes are normally an accessory source.
- Each path has one primary role. The only multi-role rule is the explicit unique-model-to-composition fallback. Images with identical hashes upload only once.
- Confidence below 0.7, unclassified images, or multiple candidates for a required role produce `blocked:role-ambiguous` for that view only.

Apply assignments using `apply_role_assignments()` from `scripts/scan_skc.py`, save the resulting single-SKC object as `_codex/manifest.json`, then validate:

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

Validate each prompt JSON before browser work:

```bash
python3 scripts/validate_manifest.py prompt <skc>/_codex/prompts/<view>.json
```

### 4. Initialize or resume state

If `_codex/run-state.json` does not exist:

```bash
python3 scripts/update_run_state.py init <manifest.json> <run-state.json>
```

Resume rules:

- Skip `qualified` actions.
- Search the monthly Lovart project for `submitted` or `queued` task labels before resubmitting.
- Resume `rejected` actions only while that view has produced fewer than 10 candidate images.
- Never restart completed views.

### 5. Prepare references

Create one ASCII-only package per view. Use only the fixed ASCII root and a SHA-derived SKC slug; never place a Chinese or user-provided name directly in the temporary path. Copy unique files in this order:

1. `model_01`
2. `product_01`
3. `scene_01`
4. `composition_01` when its hash is not already present
5. `accessory_01...`

Keep a mapping from temporary name to manifest path in the run log. Prompts refer to semantic labels such as `MODEL SOURCE`, `PRODUCT SOURCE`, `SCENE SOURCE`, and `SHOES ACCESSORY SOURCE`, never Lovart's numeric image index. Upload all references once per isolated view conversation.

### 6. Operate Lovart in Chrome

Read `references/lovart-execution.md` completely before browser work. Use the existing signed-in Chrome session. Work in project `YYYY年M月`, then find or create an SKC section with four view subsections.

Use one Chrome tab and a separate Lovart conversation for every action. Upload that action's view package, submit exactly one task, wait until Lovart visibly accepts or queues it, then switch to a new conversation without opening another browser tab. Do not submit a second task in the same conversation while the first is unfinished: Lovart cancels the earlier free-queue task. Select Nano Banana Pro, 4K, 2:3. Treat 10 accepted unfinished tasks as Lovart's hard global concurrency window: count `submitted`, `queued`, and visibly generating actions across all views and SKCs, fill the window up to 10 even when early tasks show a free-queue estimate, never submit an 11th, and fill every released slot immediately with the next pending action. For a fresh four-view SKC, submit front `FR01`–`FR05` and side `SI01`–`SI05` as the first 10-task wave unless existing unfinished tasks already occupy slots. As soon as any slot is released, continue with back and then full-body actions; do not wait for a whole wave to finish.

Use a two-phase quality order for each SKC: first submit and wait for all 20 base actions (four views times five actions) to finish; only then begin the unified visual review. Do not interrupt base generation with quality retries. After all 20 base results exist, review them one by one, then use released slots for evidence-based retries.

Apply a hard generation cap independently to every view. Front, side, back, and full may each produce at most 10 candidate images total: five base candidates plus no more than five correction candidates. Count a candidate only after Lovart visibly returns an image; count rejected images and replacement images, but do not count pending, submitted, queued, cancelled, or failed requests that return no image. Before submitting, reserve capacity for all unfinished requests in that view so accepted work cannot exceed the 10-image cap. Give every rejected action one correction opportunity before assigning another correction to an action that has already received one. Stop the view immediately after it has five qualified actions or reaches 10 generated candidates. At the cap, mark every unresolved action `blocked:quality-cap` and continue other views or SKCs.

Canvas placement is **not** deferred to either phase. The moment any task finishes, pause submission long enough to place its result in the deterministic row/slot described in `references/lovart-execution.md`. Verify the placement visually, record it with `update_run_state.py place`, and only then fill the released concurrency slot. Never allow completed results to accumulate in Lovart's automatic vertical output stack.

Never click `立即生成`, use points, pay for acceleration, silently select Nano Banana 2, combine actions into a grid request, or upload references to the wrong view conversation.

Update state after every observable task change:

```bash
python3 scripts/update_run_state.py transition <state> <view> <action-id> <status> [--reason ...] [--task-label ...]
```

### 7. Review candidates

Codex must open or enlarge every candidate and compare it against the active manifest sources and action prompt. Lovart-written self-checks and thumbnail rows are not evidence.

A candidate qualifies only when all are true:

- One standalone image with exactly one adult model; no grid, collage, or multiple panels.
- Garment color, silhouette, neckline, sleeves, length, material, and requested view match product evidence.
- Action, hands, bag, shoes, camera, and crop match the action contract.
- Scene identity is preserved while perspective changes only as the template permits.
- Model, background lighting direction, ground shadow, reflections, and color temperature agree.
- No cutout edge, halo, severe anatomy error, text, watermark, or random logo.
- Front, side, back, and full-body purposes are not confused.
- For every full-body action, the frame contains the complete model continuously from the very top of the hair/head to the bottom of both feet, including the complete face, both shoes, toes, and soles. Leave visible safety margin above the hair and below the footwear; no part of the head, chin, ankles, feet, or shoes may touch or cross the image edge.

On failure, record a specific reason and resubmit the same action with a concise correction only when the view still has generation capacity. Append each exact correction prompt and visible Lovart label to `run-log.md`; `run-state.json` retains structured attempt and rejection history plus the view-level generated count. There is no per-action three-attempt rule. The view stops at five qualified actions or 10 generated candidates; unresolved actions then become `blocked:quality-cap`.

Maintain the canvas continuously as four horizontal lanes: row 1 `正面`, row 2 `侧面`, row 3 `背面`, row 4 `全身`. The left side of every row is a fixed five-cell primary strip ordered action `01` through `05`. The right side is a fixed five-cell supplemental strip, so each row can contain at most 10 generated images. Place every base result immediately in its action's primary cell. When a retry finishes, first move the displaced/rejected candidate into the same row's next supplemental cell, then put the new candidate into the original primary cell. Keep supplemental candidates grouped by action and attempt number. Never move supplemental images to another row or a detached vertical pile.

After every placement, verify all of the following before continuing: the result is in the correct view row, the action cell or supplemental position is correct, image size matches the row, spacing is even, no other image moved unexpectedly, and Lovart has visibly retained the position. Record the placement in `run-state.json`. If placement cannot be verified, stop new submissions, record `blocked:canvas-placement`, and preserve the existing layout; do not attempt a final bulk rearrangement.

An SKC is `completed` only when all four views contain five `qualified` actions, every generated attempt has a verified canvas placement, and the five current qualified candidates in each row occupy the official primary strip: 20 qualified images total.

## Stop Conditions

Stop the affected view and log the blocker when Lovart is signed out, Nano Banana Pro is unavailable, reference upload fails repeatedly, a required role remains ambiguous, or Lovart refuses to accept another task before the 10-task window is full. Continue other safe views or SKCs when the UI permits.

A visible multi-minute free-queue estimate is not itself a stop condition. Mark each accepted job `queued`, record the estimate, and continue filling available slots until 10 unfinished tasks have been accepted. Stop the browser turn only after the 10-task window is full or the UI explicitly rejects further free submissions. Never click points acceleration and never wait indefinitely inside one tool call.

## Common Mistakes

- Treating `1/2/3/4` as global roles. Roles vary by view; full-body image 4 may be shoes.
- Counting submitted or generated images as qualified. Only individual visual review changes status to `qualified`.
- Exceeding 10 generated candidates in a view. Five base images plus five correction images is the absolute row limit.
- Reusing one Lovart conversation for multiple unfinished actions. Lovart cancels the earlier free-queue task; use one conversation per action while keeping one browser tab.
- Deferring layout until all results finish. Place and verify every completed result immediately; late bulk layout is fragile and can exceed the browser-control window.
- Spending points to clear a queue. This workflow is free-queue only.
- Downloading results. Leave them organized on the Lovart canvas.
