# Folder Contract

## Accepted input

A single SKC is a directory with at least one direct child named `正面`, `侧面`, `背面`, or `全身`. A batch root contains multiple such SKC directories as direct children.

Supported images: `.jpg`, `.jpeg`, `.png`, `.webp`.

Ignore `.DS_Store`, hidden metadata, existing `_codex`, and unsupported files.

## Role contract

Roles are assigned from visual content, never numeric names:

- `model_source`: model identity, body, styling base, pose/crop when applicable.
- `product_source`: garment construction for the requested view.
- `scene_source`: environmental identity and light evidence.
- `composition_source`: crop, subject scale, head visibility, and framing.
- `accessory_source`: shoes, bags, jewelry, or other separately supplied styling.
- `unused`: irrelevant or conflicting image.

Model, product, and scene must each resolve to exactly one source. Composition may fall back to the unique model source. Accessories are optional and may contain multiple files.

Each file path has exactly one primary role. The only supported multi-role behavior is `composition_fallback: model_source` when no separate composition source exists.

## Role assignment JSON

```json
{
  "正面/1.jpg": {
    "role": "model_source",
    "confidence": 0.98,
    "reason": "Adult model on a plain background; crop and styling are clearly visible."
  },
  "全身/4.png": {
    "role": "accessory_source",
    "confidence": 0.99,
    "reason": "Product-only image containing a pair of sandals."
  }
}
```

Every supported visible image must appear. Confidence below `0.7` blocks that view for manual resolution.

## Duplicate policy

SHA-256 groups byte-identical files. Upload one physical copy per hash. Preserve logical role records in the manifest; do not delete originals.

## ASCII upload names

Use `/tmp/lovart_view_extension/<first-12-sha256-of-skc-path>/<view>/`. Preserve the original extension and name files `model_01`, `product_01`, `scene_01`, `composition_01`, `accessory_01...`. Resolve collisions by increasing the two-digit suffix.
