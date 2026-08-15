# Folder Contract

## Accepted input

A single SKC is a directory with at least one direct child named `正面`, `侧面`, `背面`, or `全身`. A batch root contains multiple such SKC directories as direct children.

Supported images: `.jpg`, `.jpeg`, `.png`, `.webp`.

Ignore `.DS_Store`, hidden metadata, existing `_codex`, and unsupported files.

## Role contract

Assign roles from visual content, with one filename-based exception: `正面/1.jpg` is always the canonical **IDENTITY MODEL SOURCE** for identity only. Inspect this file visually before continuing; the filename selects the source but does not replace evidence-based analysis.

- `model_source`: model identity, body, styling base, pose/crop when applicable.
- `product_source`: garment construction for the requested view.
- `scene_source`: environmental identity and light evidence.
- `composition_source`: crop, subject scale, head visibility, and framing.
- `accessory_source`: shoes, bags, jewelry, or other separately supplied styling.
- `unused`: irrelevant or conflicting image.

Model, product, and scene must each resolve to exactly one source. Composition may fall back to the unique model source. Accessories are optional and may contain multiple files.

Each file path has exactly one primary role. The only supported multi-role behavior is `composition_fallback: model_source` when no separate composition source exists.

Attach `canonical_identity_source`, `identity_profile`, and `garment_profile` to the schema-2 manifest. Derive `head_visibility`, `skin_tone_and_visible_ancestry_cues`, `visible_face_features`, `hair_evidence`, `age_impression`, and `body_profile` only from visible evidence in `正面/1.jpg`; require numeric `confidence` from 0 to 1 and a nonblank visual `reason`. Noncanonical local pose/composition sources must not control or override `body_profile`; they may control only pose, crop, body direction, camera, and composition.

Require all garment fields: nonblank `garment_type`, valid `hem_position`, boolean `requires_full_garment_frame`, and nonblank visual `reason`. `hem_position: below_knee` is valid only with `garment_type: dress`, and that combination always requires `requires_full_garment_frame: true`.

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

Every supported visible image must appear. Every classified file with confidence below 0.7—including optional `accessory_source` and `unused` files—triggers `blocked:role-ambiguous`. Unclassified images and multiple candidates for a required role also block that view for manual resolution. The canonical identity file may legitimately expose less than a complete head: `partial` or `absent` head_visibility is not itself a confidence penalty. Therefore head_visibility of `partial` or `absent` alone never lowers a view's ready status and never triggers `blocked:role-ambiguous`.

## Duplicate policy

SHA-256 groups byte-identical files. Upload one physical copy per hash. If a local view pose/composition reference is byte-identical to `正面/1.jpg`, deduplicate the upload while retaining its pose/composition role logically in the manifest and prompt. Preserve all original files.

## ASCII upload names

Use `/tmp/lovart_view_extension/<first-12-sha256-of-skc-path>/<view>/`. Preserve the original extension. Every view package must place the canonical `正面/1.jpg` first and name it `identity_model_01`. Name the remaining physical uploads `pose_model_01` when a separate local pose model exists, then `product_01`, `scene_01`, `composition_01`, and `accessory_01...`. Omit any later byte-identical physical copy without removing its logical role. Resolve collisions by increasing the two-digit suffix.
