# Lovart Execution and Review

## Preflight

1. Use Chrome through `chrome:control-chrome` and name the browser session.
2. Confirm Lovart is visible and signed in.
3. Resolve the expected month project and date region from the input path with `resolve_lovart_context.py`. `/Users/chenyiming/Desktop/8月/8月15日` resolves to project `8月` and date region `8月15日`.
4. Read the current visible Lovart project name and compare it exactly with the expected month project. Do not use a recent-project thumbnail, URL project ID, current date, or assumption as evidence.
5. If the name mismatches or cannot be read, do not upload references and do not submit tasks. Record `blocked:month-project-mismatch` and immediately send the generated feedback containing source path, expected project, current project, and correction instruction.
6. After the user replies `已修正`, re-read the visible project name and verify it again. Do not resume from the user's statement alone.
7. When verification passes, locate/create the correct date region, then the SKC area inside it, then the active view row. Dates run left-to-right; SKCs within the same date run top-to-bottom.
8. Before upload, reserve the entire destination using layout contract `date-skc-four-row-v3`: visible date/SKC labels, four view rows, and 10 cells per row. Record the verified reservation. Do not submit into an improvised or partially measured area.
9. Start a fresh conversation for the action. Keep all actions in one Chrome tab, but never reuse a conversation for another unfinished action.
10. Confirm the visible model is Nano Banana Pro, output is 4K, ratio is 2:3, and no points acceleration is enabled.

Project verification is a hard gate. No reference upload, prompt submission, or concurrency-slot reservation may occur while it is pending or blocked.

## Upload and submit

- Upload the action's view ASCII package in manifest order with canonical `identity_model_01` (`正面/1.jpg`) first. If a local view pose reference is byte-identical, upload no duplicate but preserve its pose/composition role logically. Repeat the same view package in each action conversation. For full-body actions, include the footwear accessory source and append the hard requirement that the complete head-to-toe model, full face, both shoes, toes, and soles stay inside the frame with safety margin.
- Verify the visible reference count and thumbnails before submitting.
- Submit `01`–`05` as separate action conversations in the same browser tab. After each submission, wait until `submitted` or `queued` is visible, then click New Conversation before preparing the next action. Never submit a second prompt into a conversation that already has an unfinished free-queue task because Lovart cancels the earlier task. Lovart accepts a maximum wave of 10 unfinished image tasks across the workflow. Count `submitted`, `queued`, and visibly generating actions as occupied slots. A free-queue wait estimate on an accepted task does not prevent filling the remaining slots. For a fresh SKC, fill wave one with front `FR01`–`FR05` plus side `SI01`–`SI05`; never submit an 11th. As each task completes, use the released slot for the next pending back/full action.
- Never request five variants in one combined image. Never use a collage, contact sheet, grid, or multiple people.
- If a button offers `立即生成` or points acceleration, do not click it. Record queue state and mark the accepted task `queued`.
- Record every visible free-queue estimate but continue submitting until 10 unfinished tasks are accepted. Fill a released slot immediately with the next pending back/full action. For each SKC, finish all 20 base generations before visual review or retry submissions. Finalize Chrome as a handoff only when the 10-task window is full or Lovart explicitly refuses an additional free submission. Do not block one tool call indefinitely.
- A completed result creates a placement backlog. Resolve its exact task label and artifact identity, move it to the correct slot, verify persistence, and update state before using the released concurrency slot. The placement backlog must remain zero before every new submission. Unknown identity is `blocked:result-identity`; an unverified move is `blocked:canvas-placement`.

## Base-count review gate

- Unified review and correction generation are forbidden until every view has five identified and verified base results in action slots `01`–`05`.
- Run the deterministic review gate after base generation. A missing result produces `blocked:base-count-incomplete` with the missing count for front, side, back, and full.
- “Submitted”, “queued”, a Lovart text response, or an unidentified canvas image is not a base result. Only a returned image with matching task label, artifact identity, and verified primary placement counts.
- When the gate reports fewer than five for any view, finish those missing base actions first. Do not start quality review and do not generate corrections.

## Ordered visual review

After the base-count gate passes, inspect every candidate in this fixed priority order before ordinary styling quality:

1. **Identity:** compare the candidate with the schema-2 `identity_profile` derived only from `正面/1.jpg`. A local pose model never overrides identity. Reject drift with `identity-drift`.
2. **Crop/head:** front, side, and back retain at least half the head; a complete head and complete face are allowed. Full-body results retain the complete reconstructed head and hair crown. Reject violations with `head-crop-below-minimum` or `full-head-incomplete`.
3. **Conditional dress frame:** only when the product is a visually confirmed below-knee dress and `requires_full_garment_frame` is true, require the complete neckline-to-hem garment in frame. Reject a cropped hem with `long-dress-hem-cropped`.
4. **Ordinary quality:** then inspect garment construction, action, hands, accessories, scene, lighting, anatomy, and artifacts.

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

## Per-view generation cap

- Treat 10 generated candidates as the absolute lifetime cap for each view: five base candidates plus no more than five correction candidates.
- Count an image when Lovart visibly returns it. Rejected and replaced images count. Pending, submitted, queued, cancelled, or failed requests that return no image do not count.
- Before submitting, add the view's generated count to its currently submitted/queued/generating reservations. Do not submit when that projected total is already 10.
- After all five base candidates in the view have been reviewed, give each rejected action one correction opportunity before giving any action an additional correction.
- Stop immediately when the view reaches five qualified actions. Never generate unused correction capacity.
- If the view reaches 10 generated candidates with fewer than five qualified actions, mark unresolved actions `blocked:quality-cap`, preserve every result and placement, and continue other views or SKCs.

## Monthly canvas coordinate contract

Treat the monthly Lovart project as deterministic layout contract `date-skc-four-row-v3`. The confirmed screenshot maps to `date -> SKC -> front/side/back/full -> primary/supplemental`:

- **Horizontal axis = date.** Date regions such as `8月13日`, `8月14日`, and `8月15日` advance from left to right.
- **Vertical axis inside a date = SKC.** Different SKCs from the same date must stack from top to bottom and must never be placed side by side.
- **Rows inside an SKC = view.** The fixed order is front, side, back, full.
- **Columns inside a view = action/attempt.** Five primary cells are followed by five supplemental cells.
- **Horizontal gap inside a row = approximately 8% of displayed image width.**
- **Vertical gap between view rows = approximately 8% of displayed image height.**
- **Vertical gap between SKC blocks = approximately 25% of displayed image height.**

Before the first submission for a date or SKC:

1. Derive the date from the dated input folder or batch label and locate or create a visible date label.
2. If the date already exists, reuse its horizontal region. Find the actual bottom edge of every object belonging to the last SKC in that date and place the new SKC below it with a gap approximately 25% of one displayed image height.
3. If the date is new, find the actual rightmost edge of the previous date region, including labels, all SKCs, every five-cell primary strip, and every five-cell supplemental strip. Start the new date only after that boundary plus a visible safety gap.
4. Create a visible SKC label and reserve a four-row block whose full width covers all 10 cells in every row.
5. Verify that the reserved date and SKC regions do not overlap any existing image, label, supplemental strip, or future correction area.

Do not infer a region boundary from the current viewport, the first five base images, or an incomplete SKC. The placement key is always `date -> SKC -> front/side/back/full -> primary/supplemental`, with action and attempt recorded inside the selected row zone.

## Immediate canvas placement

Inside the assigned date/SKC region, create the four row lanes before the first submission and keep them stable for the entire SKC:

1. `front` / `正面`
2. `side` / `侧面`
3. `back` / `背面`
4. `full` / `全身`

Each row has two horizontal zones:

- **Primary strip:** five equal cells for action `01`–`05`.
- **Supplemental strip:** five fixed cells after one clearly visible gap to the right of the primary strip; contains replaced, rejected, and retry candidates for that same view only. A row therefore contains at most 10 generated images.

Normalize at placement time: every image in the SKC uses the same displayed width while retaining its original aspect ratio; images within a row share a top edge; all four rows share a left edge. Use a horizontal gap approximately 8% of image width and a vertical gap approximately 8% of image height. Small operational tolerance is acceptable, but inconsistent spacing, large holes, overlap, stretching, and crop changes are not.

For every newly completed task, perform this sequence before submitting another task:

1. Identify the result from its exact `SKC | VIEW | ACTION | ATTEMPT` conversation label.
2. For attempt 1, move the result directly into the action's primary cell.
3. For every correction attempt, move the candidate currently occupying that primary cell into the next available cell of the same row's five-cell supplemental strip, ordered by action then attempt; then move the new result into the vacated primary cell.
4. Match the existing row image size and snap to the shared row baseline and column spacing.
5. Deselect the object, navigate away and back or refocus the canvas, and visually confirm the position persisted and no neighboring object moved.
6. Record the verified placement:

```bash
python3 scripts/update_run_state.py place <state> <view> <action-id> <attempt> \
  --area primary --slot <01-05> --verified
```

When moving a displaced candidate to the supplemental strip, update its earlier placement with the same command using `--area supplemental --slot <stable-row-local-index> --verified`.

Do not use `Cmd+A`, whole-canvas Auto Layout, or a final bulk drag. Do not leave any generated candidate in Lovart's default vertical stack. Do not move a correction into another SKC or date region. If a move cannot be verified, stop new submissions and log `blocked:canvas-placement` rather than risking the established rows.

## State labels

Use the prompt prefix as the search label. Record the visible task label when Lovart exposes one.

- `submitted`: request accepted.
- `queued`: accepted but waiting in the free queue.
- `qualified`: Codex individually inspected and accepted the image.
- `rejected`: Codex inspected and recorded a concrete defect.
- `blocked`: the view reached its 10-image quality cap or encountered an unrecoverable execution blocker.

## Correction format

Keep the original prompt and append only evidence-based corrections:

```text
CORRECTION FOR ATTEMPT <n>: Preserve all original reference roles and constraints. Fix only: <specific observed defects>. Do not change: <already-correct product, pose, crop, and scene elements>.
```

Append the exact submitted correction and Lovart task label to `run-log.md`. Do not overwrite the base prompt JSON.

## Canvas organization

Within the monthly project, place date regions left-to-right. Within each date, stack SKCs top-to-bottom. Within each SKC, preserve the four continuously maintained row lanes. The five current candidates remain in the aligned primary strip; up to five replaced or rejected candidates remain in the fixed supplemental strip of their own row. Normalize image size and spacing at placement time, not at the end. Do not download any result.

## Acceptable micro-variation

Allow small differences in loose hair strands, natural fabric wrinkles, micro-expression, and non-structural background texture. Reject any difference that changes garment construction, core action, hand/object placement, crop, requested view, shoes, scene identity, or lighting coherence.
