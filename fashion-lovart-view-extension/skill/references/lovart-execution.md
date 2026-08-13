# Lovart Execution and Review

## Preflight

1. Use Chrome through `chrome:control-chrome` and name the browser session.
2. Confirm Lovart is visible and signed in.
3. Open or create the monthly project `YYYY年M月`; never hard-code a project ID.
4. Locate/create the SKC area and the active view subsection.
5. Start a fresh conversation for the action. Keep all actions in one Chrome tab, but never reuse a conversation for another unfinished action.
6. Confirm the visible model is Nano Banana Pro, output is 4K, ratio is 2:3, and no points acceleration is enabled.

## Upload and submit

- Upload the action's view ASCII package in manifest order. Repeat the same view package in each action conversation. For full-body actions, include the footwear accessory source and append the hard requirement that the complete head-to-toe model, full face, both shoes, toes, and soles stay inside the frame with safety margin.
- Verify the visible reference count and thumbnails before submitting.
- Submit `01`–`05` as separate action conversations in the same browser tab. After each submission, wait until `submitted` or `queued` is visible, then click New Conversation before preparing the next action. Never submit a second prompt into a conversation that already has an unfinished free-queue task because Lovart cancels the earlier task. Lovart accepts a maximum wave of 10 unfinished image tasks across the workflow. Count `submitted`, `queued`, and visibly generating actions as occupied slots. A free-queue wait estimate on an accepted task does not prevent filling the remaining slots. For a fresh SKC, fill wave one with front `FR01`–`FR05` plus side `SI01`–`SI05`; never submit an 11th. As each task completes, use the released slot for the next pending back/full action.
- Never request five variants in one combined image. Never use a collage, contact sheet, grid, or multiple people.
- If a button offers `立即生成` or points acceleration, do not click it. Record queue state and mark the accepted task `queued`.
- Record every visible free-queue estimate but continue submitting until 10 unfinished tasks are accepted. Fill a released slot immediately with the next pending back/full action. For each SKC, finish all 20 base generations before visual review or retry submissions. Finalize Chrome as a handoff only when the 10-task window is full or Lovart explicitly refuses an additional free submission. Do not block one tool call indefinitely.

## Immediate canvas placement

Create the four row lanes before the first submission and keep them stable for the entire SKC:

1. `front` / `正面`
2. `side` / `侧面`
3. `back` / `背面`
4. `full` / `全身`

Each row has two horizontal zones:

- **Primary strip:** five equal cells for action `01`–`05`.
- **Supplemental strip:** starts after one clearly visible gap to the right of the primary strip; contains replaced, rejected, and retry candidates for that same view only.

For every newly completed task, perform this sequence before submitting another task:

1. Identify the result from its exact `SKC | VIEW | ACTION | ATTEMPT` conversation label.
2. For attempt 1, move the result directly into the action's primary cell.
3. For attempt 2 or 3, move the candidate currently occupying that primary cell into the same row's supplemental strip, ordered by action then attempt; then move the new result into the vacated primary cell.
4. Match the existing row image size and snap to the shared row baseline and column spacing.
5. Deselect the object, navigate away and back or refocus the canvas, and visually confirm the position persisted and no neighboring object moved.
6. Record the verified placement:

```bash
python3 scripts/update_run_state.py place <state> <view> <action-id> <attempt> \
  --area primary --slot <01-05> --verified
```

When moving a displaced candidate to the supplemental strip, update its earlier placement with the same command using `--area supplemental --slot <stable-row-local-index> --verified`.

Do not use `Cmd+A`, whole-canvas Auto Layout, or a final bulk drag. Do not leave any generated candidate in Lovart's default vertical stack. If a move cannot be verified, stop new submissions and log `blocked:canvas-placement` rather than risking the established rows.

## State labels

Use the prompt prefix as the search label. Record the visible task label when Lovart exposes one.

- `submitted`: request accepted.
- `queued`: accepted but waiting in the free queue.
- `qualified`: Codex individually inspected and accepted the image.
- `rejected`: Codex inspected and recorded a concrete defect.
- `blocked`: third quality failure or an unrecoverable execution blocker.

## Correction format

Keep the original prompt and append only evidence-based corrections:

```text
CORRECTION FOR ATTEMPT <n>: Preserve all original reference roles and constraints. Fix only: <specific observed defects>. Do not change: <already-correct product, pose, crop, and scene elements>.
```

Append the exact submitted correction and Lovart task label to `run-log.md`. Do not overwrite the base prompt JSON.

## Canvas organization

Within the monthly project, group by SKC and preserve the four continuously maintained row lanes. The five current candidates remain in the aligned primary strip; all replaced or rejected candidates remain in the supplemental strip of their own row. Normalize image size and spacing at placement time, not at the end. Do not download any result.

## Acceptable micro-variation

Allow small differences in loose hair strands, natural fabric wrinkles, micro-expression, and non-structural background texture. Reject any difference that changes garment construction, core action, hand/object placement, crop, requested view, shoes, scene identity, or lighting coherence.
