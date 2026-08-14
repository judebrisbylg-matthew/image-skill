---
name: fashion-lovart-nano-batch
description: "Use when the user wants to batch-process a dated first-level fashion folder for Lovart using Nano Banana Pro inside one monthly Lovart project: scan all SPU subfolders containing 产品图/, optional 搭配图/, and 对标图; first use the fashion-nano-tryon workflow in Codex to generate each SPU's black-and-white line-art prompt and save the resulting line-art image as 黑白线稿图 in the SPU root; then upload up to 8 separate full-detail product/styling references plus 1 line-art reference to Lovart right-side conversation panel in strict order; generate 10 separate single-person 3:4 4K white-background images per SPU; arrange references and results into date sections and clean SPU blocks; do not auto-download final results; and skip/log blocked SPUs instead of stopping the batch."
---

# Fashion Lovart Nano Batch

## Purpose

Run the user's Codex + Lovart + Nano Banana Pro batch workflow for fashion ecommerce try-on images. The user provides only a dated first-level folder path or a screenshot. Codex processes every valid SPU subfolder in two strict phases: first prepare and quality-check each SPU's black-and-white pose line art from `对标图.jpg`; only after an approved `黑白线稿图` exists in the SPU root may Codex enter the final Lovart Nano Banana Pro generation phase. Final generation keeps all same-month dated batches in one monthly Lovart project, uploads separate full-detail references to the right-side conversation panel in strict order, generates 10 separate single-person white-background images per SPU, arranges references/results into date sections and clean SPU blocks, records failures, skips blocked SPUs, and continues the batch.

Use the prompt logic from `fashion-nano-tryon` for both the upstream line-art workflow and the final Lovart Nano Banana Pro prompt. Do not use `fashion-line-tryon` for this skill.

Default conversation language is Chinese.

## Supporting Contracts

Read these files when the relevant stage is active:

- Read [references/batch-run-contract.md](references/batch-run-contract.md) before scanning a date folder or reporting a per-SPU status.
- Read [references/lovart-handoff-contract.md](references/lovart-handoff-contract.md) before creating the upload package or using the Lovart right-side panel.
- Read [references/quality-and-recovery.md](references/quality-and-recovery.md) before accepting a line art, candidate, queued state, or blocked SPU.
- Read [examples/sample-batch.md](examples/sample-batch.md) when the user needs a first-run example.

## User Input

Accept either:

- a first-level folder path, for example `/Users/chenyiming/Desktop/5 月 27 日`
- a screenshot showing the first-level folder and SPU folders

If the path cannot be determined from the screenshot, ask for the exact path.

## Automation-Friendly Path Rule

Before scanning or generating any files, check whether the provided first-level folder is inside a Codex-writable workspace.

Preferred daily-folder location:

```text
/Users/chenyiming/Desktop/Ai生图测试/<date_folder>
```

If the user provides a folder outside the writable workspace, such as:

```text
/Users/chenyiming/Desktop/5月24日
```

do not start the batch immediately. Explain that Codex will repeatedly ask for permission when writing `黑白线稿图.<ext>`, `_codex_outputs/`, logs, and temporary upload files. Recommend moving or copying the whole date folder into:

```text
/Users/chenyiming/Desktop/Ai生图测试/
```

Then ask the user to rerun the skill with the new path, for example:

```text
[$fashion-lovart-nano-batch] /Users/chenyiming/Desktop/Ai生图测试/5月24日
```

If the user explicitly chooses to continue with the external folder anyway, proceed, but warn once that Codex permission confirmations may appear during local file writes. Do not keep repeating the warning.

## Folder Contract

Expected structure:

```text
当天一级文件夹/
├── spu_code/
│   ├── 产品图/
│   │   ├── 1.jpg
│   │   ├── 2.jpg
│   │   └── ...
│   ├── 搭配图/
│   │   ├── 1.jpg
│   │   ├── 2.jpg
│   │   └── ...
│   ├── 对标图.jpg
│   └── 黑白线稿图.jpg
```

Rules:

- `产品图/` is required and contains all product/garment sources.
- `搭配图/` is optional and may contain accessories, bottoms, shoes, bags, jewelry, or other styling references.
- `对标图.jpg` is the benchmark pose source used to create the SPU's line-art pose reference. It is required when `黑白线稿图` does not already exist.
- Every SPU must pass through the Codex-side `fashion-nano-tryon` line-art stage in the current run: generate/update the line-art prompt, create or refresh the black-and-white line-art image, save it in the SPU root, and name it `黑白线稿图.<ext>`.
- Final generation must use the SPU-root `黑白线稿图.<ext>` as the single approved black-and-white line-art pose image.
- Never use local edge detection, thresholding, contour extraction, posterization, halftone, dotted-mask, or other non-AI image-processing shortcuts as a substitute for the required line-art image. A low-quality algorithmic edge map is worse than a skipped SPU because it breaks Lovart pose control.
- Do not upload `对标图.jpg` for final Nano Banana Pro generation. The benchmark photo may only be used before Lovart final generation to produce the local `黑白线稿图`.
- The final Lovart reference set is capped at 9 images total: up to 8 product/styling images plus exactly 1 line-art image.
- The final Lovart upload order is mandatory: upload all product images first, then all styling images, and upload the single black-and-white line-art image last.
- Supported image extensions: `.jpg`, `.jpeg`, `.png`, `.webp`.
- Do not assume `搭配图/1.jpg` has a fixed meaning. Identify each styling image visually.

## Batch Behavior

- Process SPUs one by one.
- One invalid or failed SPU must not stop the batch.
- Stop only if the first-level folder is invalid, no valid SPUs exist, Lovart is unavailable/not logged in, or the user explicitly asks to stop.
- Default confirmations are automatic in batch mode: source mapping, line-art strategy, model appearance lock, line-art result, product extraction, styling classification, and final strategy are all treated as confirmed unless the user asks for manual review.
- Never mix line-art generation and final try-on generation in the same SPU request. The batch has a hard gate between the two phases.
- If any SPU is missing a usable `黑白线稿图.<ext>`, run the line-art preprocessing phase first and do not start final Nano Banana Pro generation for that SPU.
- If the user is testing or if line-art quality has recently failed, prefer a one-SPU line-art validation run before processing the full dated folder.
- Lovart must not be used to generate `黑白线稿图` under any circumstance. Lovart is reserved for the final white-background model image generation phase only.

## Two-Phase Execution Gate

Phase 1 is `LINE_ART_PREP`.

- Input: `对标图.jpg` only.
- Output: one approved `黑白线稿图.<ext>` saved in the SPU root, plus `_codex_outputs/02-黑白线稿Prompt.md`.
- Allowed AI source: Codex-side `fashion-nano-tryon` workflow only. Use the line-art prompt and Codex-side image-generation/editing capability available to the assistant. Do not open Lovart for this phase.
- Forbidden in this phase: product images, styling images, final try-on prompt, 10-candidate batch instruction, downloads of final try-on images, and any paid/points acceleration.
- If Codex-side line-art generation is unavailable, fails, or cannot save the image locally, mark the SPU `line-art blocked` and do not proceed to Lovart final generation.
- If the produced line art fails the quality gate, regenerate once with stricter line-art wording. If it still fails, mark that SPU `line-art blocked` and skip final generation.

Phase 2 is `FINAL_TRYON`.

- Entry condition: the SPU root already contains an approved `黑白线稿图.<ext>`.
- Input: product images first, styling images second, approved line-art image last.
- Output: 10 separate single-person `3:4 · 4K · pure white background` Lovart/Nano Banana Pro candidates, left in the Lovart canvas for manual review/download.
- If the approved line-art file is missing, stale, or visually poor, return to `LINE_ART_PREP`; do not improvise with `对标图.jpg` or a low-quality edge map.

## Output Folders

For each SPU, create if needed:

```text
spu_code/
├── _codex_outputs/
│   ├── _run_log.md
│   ├── 01-素材角色与执行记录.md
│   ├── 02-黑白线稿Prompt.md
│   └── 03-NanoBananaPro最终白底Prompt.md
├── 黑白线稿图.<ext>
└── _lovart_outputs/
```

The final response must list completed, skipped, and failed SPUs with log/result paths.

Important: batch mode does not download generated Lovart images automatically. After all SPUs are generated, the user manually reviews the complete Lovart canvas and downloads only approved images.

## Preflight

Before opening Lovart:

1. Scan direct children of the first-level folder.
2. Treat a child as an SPU candidate if it is a directory and not an output/temp/system folder.
3. For each SPU, check:
   - `产品图/` exists and contains at least one supported image
   - `对标图.jpg` exists if the SPU does not already have a usable `黑白线稿图.<ext>`
   - a black-and-white line-art prompt can be generated from `对标图.jpg` through `fashion-nano-tryon`
   - a usable `黑白线稿图.<ext>` can be created or refreshed in the SPU root before Lovart final upload
   - `搭配图/` status and image count
   - final product/styling image count can be controlled to 8 or fewer
4. Build a manifest with counts, filenames, and skip reasons.
5. Skip invalid SPUs and continue.

## Mandatory Codex-Side Line-Art Stage

This stage runs before any Lovart final-generation work for each SPU.

Rules:

- Do not treat a missing line-art image as a reason to go directly into Lovart final generation.
- Do not create the required line-art image inside Lovart. Do not use Lovart Agent, the Lovart right-side conversation panel, the Lovart bottom image generator, or any Lovart canvas workflow for `LINE_ART_PREP`.
- Use the `fashion-nano-tryon` workflow to analyze `对标图.jpg`, generate the black-and-white line-art strategy, extract the model appearance lock, and write `02-黑白线稿Prompt.md`.
- Generate or refresh the actual black-and-white line-art image from `对标图.jpg` and `02-黑白线稿Prompt.md` before Lovart final upload.
- Save the actual line-art image in the SPU root as `黑白线稿图.<ext>`; prefer `.png` when the generation tool returns PNG.
- The line-art image must be generated by the AI workflow from `fashion-nano-tryon` or by an equivalent AI image-generation/editing step that follows `02-黑白线稿Prompt.md`. Do not generate it with PIL/OpenCV/ImageMagick/sips edge filters or any local deterministic image-processing fallback.
- A line-art image generated in Lovart is not valid for this workflow even if it visually passes the quality gate. Quarantine it outside the SPU root and regenerate through Codex-side `fashion-nano-tryon`.
- In batch mode, the line-art result is automatically treated as confirmed only if it passes the line-art quality gate below.
- If the line-art image cannot be generated or does not pass the quality gate, mark only that SPU as blocked with the reason `line-art quality failed before Lovart`, log the issue, do not build/upload a Lovart final package for that SPU, and continue with the next SPU.
- Only after `黑白线稿图.<ext>` exists in the SPU root may Codex build the Lovart upload package for that SPU.

### Line-Art Preprocessing Prompt Requirements

When generating line art, use a concise prompt that focuses only on pose extraction:

```text
Generate exactly 1 high-quality clean black-and-white pencil line-art pose reference from the uploaded benchmark image.
Preserve the benchmark pose, crop, body scale, camera angle, torso angle, shoulder slope, arms, elbows, hands, waist/hip position, leg stance if visible, bag/phone/hand relationship if present, and composition as closely as possible.
Use a pure white or near-white background.
Keep only simplified body outline, hair/head outline, neck, shoulders, torso, arms, hands, waist/hip, visible leg/crop boundary, and essential object-position cues needed for pose locking.
Remove all color, garment print, fabric texture, material rendering, lighting, background, logo, watermark, text, and decorative details.
This must be a clean pose-control line drawing, not edge detection, not dotted or halftone, not noisy contours, not a black blob, not posterized silhouette, and not a fashion design sketch.
Do not generate final try-on.
Do not use paid or points acceleration.
```

If the benchmark is cropped, preserve the same crop. Do not expand a half-body benchmark into a full-body sketch unless the user explicitly asks.

### Line-Art Quality Gate

Before Lovart upload, inspect `黑白线稿图.<ext>` visually or through available image-view tooling. The line art is acceptable only when all of these are true:

- Clean white or near-white background.
- Clear continuous human silhouette.
- Head, hair outline, neck, shoulders, torso, arms, elbows, hands, waist/hip, visible legs, and crop boundary are readable.
- Pose, camera angle, crop/framing, body angle, hand positions, elbow positions, bag/phone position if present, leg stance, and body proportions match `对标图.jpg` closely enough to act as a pose lock.
- Clothing-body overlap cues are simplified but spatially useful.
- Product colors, patterns, fabric texture, material rendering, lighting, room/outdoor background, brand marks, and accessory details are removed or reduced.

Reject the line art if any of these are true:

- It is a dotted/halftone mask, noisy contour map, edge-detection output, broken skeleton, black blob, posterized silhouette, or texture-heavy extraction.
- It preserves garment pattern/texture so strongly that Lovart may treat it as product design instead of pose.
- It loses important pose-control details such as hand height, elbow bend, bag/phone placement, leg stance, head crop, or torso angle.
- It changes the benchmark pose, crop, body scale, body angle, or camera angle.
- It looks like a fashion design sketch of a new garment rather than a pose/spatial reference.

If rejected, do not upload it to Lovart. Regenerate once through `fashion-nano-tryon` if possible. If regeneration still fails, skip that SPU and log the rejected line-art path and reason.

Required local artifacts per SPU:

```text
spu_code/
├── 黑白线稿图.<ext>
└── _codex_outputs/
    ├── 02-黑白线稿Prompt.md
    └── 03-NanoBananaPro最终白底Prompt.md
```

## Desktop Window Preflight

Before operating Lovart in Chrome:

- Confirm Chrome/Lovart is the actual foreground window, not Feishu, WeCom/Enterprise WeChat, Finder, Preview, or a full-screen image preview overlay.
- If a chat app, image viewer, screen-share overlay, or another modal layer is covering Chrome, stop Lovart actions and tell the user exactly what to bring to the front.
- Do not continue clicking if the visible foreground app is not Lovart; otherwise file uploads and prompts may be sent to the wrong app.
- Once Lovart is foregrounded, re-check the current canvas/project name before uploading any SPU assets.

## Temporary Upload Package

For every valid SPU, create an ASCII-only upload package:

```text
/tmp/lovart_batch/<date_folder_name>/<spu_code>/
├── product_01.<ext>
├── product_02.<ext>
├── styling_01.<ext>
├── styling_02.<ext>
├── bottoms_01.<ext>
├── pose_lock_reference.<ext>
└── ...
```

Use this package for Lovart uploads. Build it only after the SPU-root `黑白线稿图.<ext>` exists. Do not upload directly from Chinese folder names or rely on original numeric filenames.

The package and Lovart upload order are mandatory:

1. Upload all selected `product_##` images first, preserving the numeric product order.
2. Upload all selected `styling_##`, `accessory_##`, and `bottoms_##` images second, preserving the chosen styling order.
3. Upload `pose_lock_reference` last as the 9th-or-fewer final reference image.

Do not upload the line-art image before the product/styling references. Do not interleave product images, styling images, and line art.

Role names:

- `product_01`, `product_02`, ...
- `accessory_01`, `accessory_02`, ...
- `bottoms_01`, `bottoms_02`, ...
- `pose_lock_reference` copied from the SPU-root `黑白线稿图.<ext>`

Final upload package rules:

- Keep product/styling references as separate full-resolution images by default.
- Do not merge product/styling references into contact sheets or grids by default.
- Upload no more than 8 product/styling images for final generation.
- Upload exactly 1 approved black-and-white line-art pose image for final generation, copied from the SPU-root `黑白线稿图.<ext>`.
- The final upload sequence must be: product references first, styling references second, black-and-white line-art reference last.
- Do not include `benchmark_pose` in the final Nano Banana Pro upload package.

Do not rely on Lovart global image numbers. Lovart may count previous images in the same canvas.

## Final Reference Upload Policy

Default Lovart upload mode must be separate full-detail references, not compact boards.

Reason:

- Product and styling details are easier for Nano Banana Pro to preserve when each source remains a full-size image.
- Contact sheets and grids can cause Lovart/Nano Banana Pro to copy the board structure into the final output.
- The user's workflow controls product/styling images to 8 or fewer, so the final reference count stays within the expected 9-image limit after adding the line-art reference.

Final upload package:

```text
/tmp/lovart_batch/<date_folder_name>/<spu_code>/
├── product_01.<ext>
├── product_02.<ext>
├── ...
├── styling_01.<ext>
├── ...
└── pose_lock_reference.<ext>
```

Rules:

- Upload all product/styling references as separate images when their combined count is 8 or fewer.
- Upload `pose_lock_reference` copied from `黑白线稿图.<ext>` as the only pose/composition reference for final generation.
- Upload order is strict: first all `product_##`, then all `styling/accessory/bottoms_##`, and finally `pose_lock_reference` as the last image.
- Do not upload `对标图.jpg` or `benchmark_pose` during final generation. If the line-art file is missing, stop that SPU's Lovart final stage, create `黑白线稿图.<ext>` locally first, then rebuild the upload package.
- If Lovart keeps the submit button disabled with 9 images, reduce only the lowest-value styling image first; keep core product images and line art.
- Use a contact sheet only as an emergency fallback after logging the blocker. When a fallback board is used, the prompt must state that board layout must never be copied.

## Styling Classification

Analyze every image in `搭配图/` before final prompting and classify it as one of:

- `ACCESSORY SOURCES`: jewelry, handbag, belt, hat, scarf, glasses, shoes, or other non-bottom styling item
- `BOTTOMS SOURCE`: jeans, trousers, skirt, shorts, leggings, or other lower-body garment
- `UNUSED / BLOCKED`: unclear item, incompatible item, or item outside locked crop

For each styling source, record:

- category
- color/material/texture
- likely wearing or carrying position
- whether it fits within the locked line-art crop

If an accessory or bottom conflicts with the locked pose/crop, preserve the line-art pose and crop first. Include only the visible compatible part, or omit and log why.

## Lovart Monthly Project Policy

Use one Lovart canvas/project for the whole month, not one project per dated first-level folder.

Recommended:

- Derive the month from the provided first-level folder name or path.
  - `5月23日`, `5 月 23 日`, and `2026年5月23日` all map to the May Lovart project.
  - Prefer a concise project name such as `5月`.
  - If the year is needed to avoid ambiguity, use `2026年5月`.
- If a matching monthly Lovart project is already open or available, use it.
- If not, create/open a new monthly project and label/name it with the month when possible.
- Never hard-code Lovart `projectId`; find or create the current monthly project dynamically.
- Do not create a new Lovart project just because the date folder changed from `5月23日` to `5月24日`.

Within the same monthly canvas:

- Create or preserve a visible date section for each dated first-level folder, for example `5月23日` and `5月24日`.
- Place all SPU blocks for the same date under that date section.
- Start a new date section when processing a different first-level folder in the same monthly project.
- Isolate each SPU operationally with a fresh prompt sequence and visually separate block.
- Prefix prompts with `SPU <spu_code> - Nano Banana Pro controlled try-on`.
- Keep per-SPU logs and output folders separate on disk.
- Use temporary role names, not Lovart image numbers.
- If the monthly canvas becomes too crowded or Lovart performance noticeably degrades, continue in a second monthly project named with a part suffix, for example `5月-Part2`, and log the project split.

## Lovart Entry Point Policy

For final image generation, use the Lovart right-side conversation panel (`对话`) in Agent image-generation mode as the fixed default path. Do not use the canvas bottom image generator for normal batch execution.

Reason:

- The bottom image generator reference upload works, but configured-generator duplication is not reliable enough for batch work.
- In observed Lovart UI states, `Cmd+C` / `Cmd+V` did not duplicate a configured generator; it pasted clipboard text as a canvas text object.
- The user has verified that Lovart's right-side Agent mode can generate 10 images from one request. This is now the preferred throughput path for batch production.
- The right-side conversation panel is more stable for attaching references, pasting long prompts, selecting Agent/image mode/model, and asking for 10 separate outputs in one instruction.
- Do not use the Lovart right-side conversation panel to create the required `黑白线稿图`; line art must already exist locally before Lovart final generation.
- Before committing to a batch, verify that the right-side panel is in Agent image-generation mode, supports local/reference upload, uses **Nano Banana Pro only**, and displays or accepts the required `3:4 · 4K` settings.
- Do not submit final Lovart generation if the visible model label is `Nano Banana 2`, `Nano Banana`, or anything other than `Nano Banana Pro`.
- If the right-side panel defaults to `Nano Banana 2`, switch it to `Nano Banana Pro` before uploading/submitting. If Codex cannot find or select `Nano Banana Pro`, stop that SPU, mark it `blocked:model-mismatch`, and ask for user confirmation. Never silently downgrade to `Nano Banana 2`.
- Upload final references to the right-side panel in strict sequence: all product images first, all styling images second, and the single `pose_lock_reference` image last.
- The last uploaded image must be treated as `pose_lock_reference`, the mandatory fixed pose skeleton, not as a styling/product image.
- Do not use the global bottom toolbar upload icon for final references unless the user explicitly wants standalone canvas reference objects; it creates canvas images rather than right-panel generation references.

Fallback:

- If the right-side panel cannot upload references, cannot use Agent image mode, cannot use Nano Banana Pro, or cannot accept the prompt, mark that SPU as blocked/partial and log the blocker. Do not silently switch to `Nano Banana 2` or the bottom canvas image generator.
- Use the bottom canvas image generator only when the user explicitly asks to test or use it.
- Log which entry point was used for each SPU.
- Do not keep retrying a blocked entry point once the blocker is confirmed in a run.
- If the right-side Agent mode accepts the request but returns fewer than 10 standalone outputs, fall back to candidate-indexed one-image submissions in the same right-side panel and log the throughput blocker.
- If Lovart accepts the job only into a long free queue, do not click `立即生成` or spend credits unless the user explicitly approves. Log the queue estimate and mark the SPU as queued/partial until the user asks to wait or continue.
- If one SPU is still queued or partially generated, do not claim the dated folder batch is complete. Report that SPU as `queued-partial` with accepted/visible image count and queue status, then continue only when it is operationally safe to do so. If the Lovart UI is blocked by the active queue and cannot accept the next SPU, stop and report the queue blocker instead of silently leaving later SPUs unprocessed.

## Canvas Layout Policy

The final Lovart canvas must be organized for manual review, not just generation.

Date section layout:

- Each dated first-level folder gets one visible date section inside the monthly project.
- The date section label should match the local folder name, for example `5月23日`.
- Keep date sections separated with clear vertical spacing.
- Do not mix SPU blocks from different dates in the same visual row unless the user explicitly asks for a compact layout.

SPU block layout:

- Each SPU gets one visible block.
- Top row of the block: reference materials in this order when available:
  `product_01...product_##`, `styling_01...styling_##`, `accessory_01...accessory_##`, `bottoms_01...bottoms_##`, `pose_lock_reference`.
- Bottom row of the block: exactly 10 generated result images, each a separate single-person image.
- Keep image sizes visually consistent inside the same row.
- Leave clear horizontal/vertical spacing between reference row and result row.
- Add or preserve the SPU code as the block label when Lovart supports text labels.

Batch grid layout:

- Place SPU blocks left to right.
- One canvas row may contain up to 10 SPU blocks.
- The 11th SPU starts a second row, left-aligned with the first row.
- Keep second and later rows aligned to the same block width and spacing as the first row.
- Do not leave generated images scattered in the canvas. After each SPU completes, arrange its references and 10 results before moving to the next SPU when possible.

## Generation Workflow Per SPU

1. Read and classify local files.
2. Run the mandatory Codex-side `fashion-nano-tryon` line-art stage before Lovart final generation.
3. Analyze `benchmark_pose`/`对标图.jpg` for:
   - pose, crop, body scale, body angle
   - body proportions
   - hand and leg positions
   - model appearance lock: skin tone consistency, hair color, hairstyle, basic visible appearance
4. Generate and save the black-and-white line-art prompt as `_codex_outputs/02-黑白线稿Prompt.md`.
5. Generate or refresh the actual black-and-white line-art image from `对标图.jpg` before Lovart work starts.
6. Save the generated line-art image in the SPU root as `黑白线稿图.<ext>`.
7. Run the line-art quality gate. Treat line art as confirmed by default only when it is a high-quality AI line drawing. Reject noisy local edge maps, dotted/halftone masks, texture-heavy contours, broken silhouettes, or any line art that changes the benchmark pose/crop.
8. Analyze all `product_##` sources for garment identity and construction.
9. Classify all `搭配图/` images into `styling_##`, `accessory_##`, `bottoms_##`, or unused.
10. Generate and save the final Nano Banana Pro structured prompt.
11. Create the temporary upload package.
12. Create the final separate-reference Lovart upload package: up to 8 product/styling images plus 1 `pose_lock_reference` copied from the SPU-root `黑白线稿图.<ext>`.
13. Open or switch to the monthly Lovart project for the folder's month, then create/find the visible date section for the current first-level folder.
14. Open the Lovart right-side conversation panel (`对话`) and set it to Agent image-generation mode.
15. Upload the separate reference images to the right-side panel in strict order: all product images first, all styling images second, and the single black-and-white line-art image last. Do not upload contact sheets or grids.
16. Select/use Lovart Nano Banana Pro with 3:4 ratio and 4K output. This is a hard requirement: do not continue if the visible model selector or generated task label shows `Nano Banana 2` or any non-Pro model.
17. Paste the final Nano Banana Pro prompt plus the right-side Agent batch instruction requesting exactly 10 separate standalone outputs.
18. Submit once in right-side Agent mode and ask Lovart to generate 10 separate single-image outputs, not one grid/contact sheet.
19. After submission, immediately verify the generated task label. If Lovart starts the job under `Nano Banana 2` or any non-Pro label, stop treating that SPU as valid, log `blocked:model-mismatch`, and do not count those outputs as accepted.
20. If the right-side panel produces fewer than 10 standalone outputs, continue with candidate-indexed one-image submissions in the same panel until 10 accepted candidates are visible or a blocker is logged.
21. Do not use the bottom image generator or bottom-generator duplication unless the user explicitly asks to test it again.
22. After candidates complete, verify that each visible result is one standalone image, one model, one outfit, not a collage/grid/contact sheet, and was generated with `Nano Banana Pro`.
23. Number and review every generated image individually against the active SPU's own `pose_lock_reference`. Codex itself must open or enlarge each candidate and perform the visual comparison; never delegate this decision to Lovart Agent, Lovart image analysis, or Lovart's written self-check. Check head/neck direction, shoulder line, exposed shoulder/waist/navel requirements, body angle and scale, left/right hand height and placement, phone/bag/cup relationship, waist/hip alignment, visible shorts/legs, camera angle, crop boundary, product identity, white background, and 4K size.
24. If any result is a collage, grid, multi-person image, multi-panel image, wrong product, wrong background, non-Pro output, or has any material pose/composition drift, mark that candidate `rejected` and do not count it toward completion. Generate a single replacement candidate in the same Agent conversation with stricter pose-lock wording, then review the replacement again. Repeat as many times as needed; do not stop after one retry.
25. Completion is based on `qualified_count >= 10`, not `generated_count >= 10`. The total number generated may exceed 10. Do not start the next SPU while the current SPU has fewer than 10 individually reviewed qualified images.
26. Arrange the SPU block under the current date section: keep the 10 base images on their horizontal row when possible; keep replacement images in the same SPU's continuous canvas area. Rejected images may remain visible but must not be counted as qualified.
27. Do not download generated results during batch execution.
28. Log the Lovart monthly project, date section, entry point used, actual model label, right-panel multi-output status, generated count, individually reviewed qualified count, rejected candidate numbers/reasons, replacement count, queued candidate count, queued/partial status, and visible arrangement status as `pending manual review/download`. For every qualified candidate, record explicit Codex visual-review evidence such as candidate number plus the checked pose/crop/hand/object criteria. A Lovart-written pass list is not valid evidence.

## Line-Art Prompt Rules

The line-art prompt must be produced through `fashion-nano-tryon` and must instruct the line-art generation tool to:

- convert `benchmark_pose` into a clean black-and-white pencil line-art pose reference
- preserve shooting distance, crop, body scale, body angle, hand positions, leg pose, and composition
- preserve body proportions: shoulder width, neck-to-shoulder relationship, torso length, chest/waist/hip relationship, waist position, hip/waistband height, arm length, elbow position, hand size, visible leg proportion
- keep simplified clothing-body overlap and wearing-behavior cues only as spatial guidance
- reduce color, material, lighting, background, brand text, logos, patterns, fabric texture, jewelry detail, and accessory detail
- forbid detailed fashion design sketch, photorealistic rendering, random text, watermark, or logo-like marks

## Final Nano Banana Pro Prompt Rules

Use the `fashion-nano-tryon` final prompt structure. The final executable prompt must be English and structured with these blocks:

```text
FINAL OUTPUT
REFERENCE ROLE CONTRACT
REFERENCE PRIORITY
GARMENT HARD LOCK
POSE AND BODY HARD LOCK
MODEL APPEARANCE HARD LOCK
ACCESSORIES AND BOTTOMS
LIGHTING AND FINISH
DO NOT INCLUDE
```

Required output defaults:

- 10 accepted standalone studio ecommerce candidate photos per SPU
- `3:4 ratio, 4K output`
- pure white `#FFFFFF` background
- Nano Banana Pro model in Lovart

Lovart executable prompt rule:

- Prefer a concise Lovart-submittable prompt using separate reference role names.
- Keep the critical constraints: 10 separate standalone image outputs, role-based source mapping, product identity lock, pose/crop/body lock from line art, model appearance lock if available, styling lock, pure white background, `4K · 3:4`, and negative rules.
- If the full structured prompt causes Lovart's submit button to remain disabled, replace it with a compressed prompt under roughly 2,000 characters and log that fallback.
- For Lovart right-panel use, append the right-panel batch instruction from this skill after the main prompt.

Right-panel batch instruction:

```text
LOVART EXECUTION INSTRUCTION
Use the right-side conversation panel in Agent image-generation mode with Nano Banana Pro.
Do not use Nano Banana 2 or any non-Pro model. If Nano Banana Pro is unavailable, stop and report that the model is unavailable instead of generating.
Output size: 3:4 ratio, 4K resolution.
Generate exactly 10 separate standalone image outputs for this SPU in this one request.
Start 10 independent image-generation tasks immediately. Do not wait for one candidate to finish before starting the next candidate. If the system limits free concurrency, start the maximum free parallel batch first, then continue the remaining candidates until 10 outputs exist.
Do not use paid/points acceleration. Do not click or require `立即生成`.
Each output must be a single image containing exactly one adult female model, exactly one outfit, and no multi-image layout.
Do not create a collage, grid, contact sheet, 2x5 layout, 3x3 layout, side-by-side comparison, thumbnail board, product board, or one image containing multiple variants.
Do not return one combined image containing 10 variants. Return 10 individual images.

REFERENCE ORDER LOCK
The uploaded references are ordered as product images first, styling images second, and the final uploaded image is pose_lock_reference.
POSE LOCK IS MANDATORY: the final uploaded image `pose_lock_reference` is the fixed pose skeleton and the highest-priority composition reference.
Reproduce the pose 1:1, including the same torso angle, shoulder tilt, neck/head crop, arm bend, elbow position, hand height, phone-hand position, bag-hand position, leg stance, hip/waist alignment, body proportions, shooting distance, crop boundary, and camera angle.
All 10 outputs must use the same locked pose and same camera composition. Variation is allowed only in micro rendering details such as fabric realism, hair strand placement, facial naturalness, lighting softness, and accessory visibility within the locked crop.
Do not invent a new pose. Do not change the gesture. Do not change the camera angle. Do not change crop/framing. Do not change hand placement, bag placement, leg placement, or body angle.
Do not treat the final uploaded line-art image as a garment design, color source, background source, or styling source.

BACKGROUND HARD LOCK
All 10 outputs must be pure white #FFFFFF studio ecommerce background only.
No outdoor scene, no street, no garden, no cafe, no patio, no window, no furniture, no plants, no room, no lifestyle background, no environmental props, no shadows suggesting a real location.
Only subtle studio contact shadows are allowed.

BATCH REVIEW RULE
If any output violates the standalone-image rule, pure-white-background rule, single-model rule, product identity, or mandatory pose lock, treat only that output as failed and regenerate that candidate with stricter negative wording. Do not restart the whole SPU unless all outputs fail.
Pose drift means any clear change to hand height, phone-hand position, bag-hand position, leg stance, body angle, camera angle, crop boundary, or head/face crop compared with `pose_lock_reference`.
```

Candidate count rules:

- Lovart's own completion text, image-analysis result, self-check conclusion, `Specifications Met` checklist, task labels, or a full-row thumbnail overview are not pose-review evidence and must never be copied into `qualified_count`. Codex must open or zoom every candidate and visually compare it against the active SPU's `pose_lock_reference` before marking it qualified.
- Maintain explicit counters: `generated_count`, `qualified_count`, `rejected_count`, and `replacement_count`. `generated_count >= 10` never implies completion; only `qualified_count >= 10` does.
- In the right-side Agent panel, ask for 10 outputs in one request when the instruction explicitly says `exactly 10 separate standalone image outputs` and forbids collage/grid/contact-sheet layouts.
- Prefer parallel throughput wording: ask Lovart to start 10 independent image-generation tasks immediately. If Lovart limits concurrency, ask it to run the maximum free parallel batch first, then continue the remaining candidates. Never use paid/points acceleration.
- If the first right-panel request produces a collage, grid, contact sheet, multi-panel image, or fewer than 10 standalone outputs, do not repeat the same 10-output request. Switch to candidate-indexed one-image submissions.
- Use candidate-index wording for fallback one-image submissions, for example: `Generate candidate 03 of 10: exactly one standalone single-person ecommerce try-on image for SPU <spu_code>. Use the same uploaded references and the same locks.`
- Continue single-candidate replacement generation and candidate-level visual review until at least 10 qualified standalone images exist for the SPU or until a genuine blocker is logged and the SPU is marked partial. A rejected replacement does not consume the retry loop; generate another replacement.
- If Lovart queues candidate generation for several minutes and the user has not approved waiting indefinitely, mark the SPU as `queued-partial` with the current accepted count and queue estimate. Do not click `立即生成`, do not spend credits, and do not report the SPU as completed.
- Do not download intermediate or final candidates during batch execution.
- Every candidate must preserve the same locked product identity, `pose_lock_reference` pose/crop/body proportions/camera angle, model appearance lock, accessory rules, bottoms rules, and white ecommerce background.
- Candidate variation is allowed only in subtle natural rendering details such as fabric drape, micro-expression, hair strand placement, lighting nuance, and accessory visibility within the locked crop.
- Do not create different outfits, different poses, different models, different crops, different backgrounds, different hand placements, different bag placements, different leg stances, different body angles, or random styling across the 10 candidates.

Single-image negative rules:

- No collage.
- No grid.
- No contact sheet.
- No moodboard.
- No side-by-side comparison.
- No multiple panels.
- No multiple people.
- No repeated copies of the same model inside one image.
- No reference-board layout reproduction.
- No product catalog sheet.
- No thumbnails inside the final image.

Separate-reference handling:

- Keep all product/styling references separate by default.
- Do not create or upload contact sheets, grids, or reference boards unless Lovart blocks the normal 9-image package.
- The model must create one natural ecommerce photo, not a board, grid, or multi-image page.
- If an emergency fallback board is used and Lovart visually reproduces the board layout, reject that candidate and regenerate with stronger negative wording.

Role contract requirements:

- `PRODUCT SOURCE`: `product_##`; only source for final garment identity and details
- `STYLING SOURCES`: `styling_##`, `accessory_##`, `bottoms_##`; only source for compatible accessories and bottoms
- `LINE_ART SOURCE`: `pose_lock_reference`; the last uploaded image and mandatory pose skeleton/blueprint; only source for pose, body proportions, crop, shooting distance, camera angle, hand positions, arm bend, bag placement, leg pose, body angle, composition, spatial relationship, and compatible wearing behavior
- `MODEL APPEARANCE LOCK`: text lock from the upstream benchmark analysis when available; source for skin tone and hair, but do not upload the benchmark photo during final generation
- `ACCESSORY SOURCES`: `accessory_##`; only source for listed accessories
- `BOTTOMS SOURCE`: `bottoms_##`; only source for listed bottoms
- `DENIED SOURCES`: benchmark outfit design, line-art outfit design, mannequin body proportions, unlisted accessories, random styling, random skin tone, random model identity, text, logos, watermarks, background elements, outdoor scenes, lifestyle scenes, rooms, cafes, patios, gardens, furniture, windows, plants, street backgrounds, and environmental props

Control rules:

- Treat each source as a separate locked role, not a moodboard.
- Use direct wording: `copy`, `preserve exactly`, `must match`, `do not borrow`, `ignore`.
- Use direct Lovart wording for line-art control: `The last uploaded image is pose_lock_reference and is the mandatory fixed pose skeleton. Reproduce its pose, crop, camera angle, hand positions, bag position, leg stance, and body angle 1:1. Do not create pose variations across the 10 outputs.`
- Use direct Lovart wording for background control: `Pure white #FFFFFF ecommerce studio background only. No outdoor, lifestyle, room, plant, furniture, cafe, patio, street, or environmental background.`
- Do not infer skin tone from black-and-white line art.
- Do not alter body proportions to match mannequin, product flat-lay, or product-only references.
- No handbag unless a handbag is explicitly classified as `ACCESSORY SOURCES`.
- If a styling source is missing, omit that category instead of inventing it.
- Preserve line-art crop/pose first; do not change framing to fit accessories unless the user explicitly approves.

## Failure Handling

Log and skip the current SPU if:

- required local files are missing
- Lovart upload fails repeatedly
- line-art generation fails or is unusable
- line-art was produced by local edge/threshold/contour processing instead of the required AI line-art workflow
- line-art quality gate fails after one allowed AI regeneration attempt
- final Nano Banana Pro generation fails repeatedly
- browser or file-picker blocker cannot be resolved after reasonable retries

Do not fail or skip an SPU because generated images were not downloaded. Downloading is intentionally deferred to manual review after the whole dated folder batch finishes.

Continue with the next SPU.

Use `queued-partial`, not `completed`, when:

- Lovart has accepted the SPU but fewer than 10 accepted standalone images are visible.
- Lovart is still generating or queued in the free queue.
- The current accepted candidate count is known, but later candidates are pending.
- The browser/UI blocks moving to the next SPU while a queue is active.

For every queued/partial SPU, log:

- accepted visible candidate count
- queued candidate count if known
- current queue estimate if shown
- whether any `立即生成`/points button was shown
- confirmation that no points were spent

## Final Response

Keep the final response concise. Include:

- batch folder path
- Lovart monthly project used
- date section used inside the monthly project
- completed SPU count
- queued/partial SPUs with accepted image count and queue reason
- skipped/failed SPUs with reasons
- paths to logs and local output folders
- clear note that generated Lovart images were left in the canvas for manual review/download
