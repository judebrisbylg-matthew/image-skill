# Fashion Nano Tryon Complete-Agent Design

## Goal

Upgrade `fashion-nano-tryon` from a prompt-only workflow into the reusable single-SPU execution unit for Nano Banana Pro fashion try-on. It must remain useful in a manual conversation and provide a stable hand-off package for `fashion-lovart-nano-batch`.

## Responsibility Boundary

`fashion-nano-tryon` owns one SPU:

1. Map source images and classify styling references.
2. Extract the model appearance lock before the benchmark becomes line art.
3. Produce, inspect, approve, and record the line-art pose reference.
4. Extract product details, write the final Nano Banana Pro prompt, and run final quality checks.
5. Save a standard local evidence package when the user supplies an SPU folder.

`fashion-lovart-nano-batch` owns a dated folder:

1. Discover SPUs and schedule one run per SPU.
2. Call this single-SPU contract in automatic-confirmation mode.
3. Upload the approved package to Lovart in its prescribed order and record Lovart results.

Neither skill duplicates the other skill's responsibility.

## Single-SPU Input and Output Contract

When an SPU folder is available, use:

```text
spu_code/
├── 产品图/                 required
├── 搭配图/                 optional
├── 对标图.<ext>            required when no approved line art exists
├── 黑白线稿图.<ext>        generated/approved line-art reference
└── _codex_outputs/
    ├── 00-状态与素材清单.md
    ├── 01-线稿策略与人物外观锁.md
    ├── 02-黑白线稿Prompt.md
    ├── 03-产品拆解与搭配分类.md
    ├── 04-最终白底策略.md
    ├── 05-NanoBananaPro最终Prompt.md
    └── 06-质检与交接记录.md
```

For image-only chats without a folder, retain the current conversational outputs. State that no local evidence package was requested; never invent file paths.

## State Model

Use one visible state record with these statuses:

`MAPPED` → `LINE_ART_PLANNED` → `LINE_ART_READY` → `PRODUCT_LOCKED` → `PROMPT_READY` → `QA_PASSED` → `HANDOFF_READY`.

Use `BLOCKED` for a missing source, rejected line art, ambiguous styling role, or failed quality gate. Include the exact failed gate, reason, next action, and affected artifact. A batch caller may skip a blocked SPU without stopping the remaining SPUs.

## Stage Changes

Keep the existing six stages and three manual gates. Add these requirements:

- Stage 0 classifies every styling image as accessory, bottoms, or excluded; cap the final Nano reference package at eight product/styling images plus one approved line-art image when handing off to Lovart.
- Stage 2 includes a line-art visual acceptance checklist and records its result before Stage 3.
- Stage 3 records the source-of-truth garment details and the styling classification.
- Stage 5 produces the final structured prompt plus a compact upload manifest: product images first, styling images second, line art last.
- Final QA checks source roles, pose/appearance locks, product accuracy, output specification, prohibited content, and hand-off readiness.

## Documentation and GitHub Presentation

The handbook will add a complete-agent overview: input contract, output package, status progression, manual versus batch execution, Lovart hand-off, and blocked-SPU behavior. README will expose the same architecture and link to the handbook. The generated GitHub Pages copy remains derived from the same handbook builder.

## Validation

Add a deterministic contract validator for a generated `_codex_outputs/` package. Test it with one valid fixture and failure cases for: missing line art, invalid state order, and a final prompt that appears before product lock. Validate the skill frontmatter and regenerate the handbook after edits.

## Non-goals

- Do not make the single-SPU skill operate Chrome or Lovart itself.
- Do not silently auto-generate images when the selected image generator is unavailable.
- Do not remove the existing manual confirmation gates.
- Do not store user product images, credentials, or generated production assets in the Git repository.
