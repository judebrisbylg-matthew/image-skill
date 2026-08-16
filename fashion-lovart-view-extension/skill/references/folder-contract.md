# Folder Contract

## Accepted input

A single SKC is a directory with at least one direct child named `正面`, `侧面`, `背面`, or `全身`. A batch root contains multiple such SKC directories as direct children.

Supported images: `.jpg`, `.jpeg`, `.png`, `.webp`.

Ignore `.DS_Store`, hidden metadata, existing `_codex`, and unsupported files.

## Scanner batch contract

Every scanner invocation creates one authoritative `batch_contract` and copies it unchanged into the batch wrapper and every member inventory:

```json
{
  "schema_version": 1,
  "member_skc_ids": ["SKC-A", "SKC-B"],
  "digest": "<lowercase SHA-256>"
}
```

`member_skc_ids` is the scanner's deterministic ordered, non-empty, unique list. Compute `digest` from canonical compact JSON containing only schema version and those IDs, with sorted object keys. Classification and visual-contract attachment preserve this object exactly. State initialization copies it into run-state schema `6`; submission requires the original inventory and every authoritative member state, all with the same digest. A reduced inventory, omitted member, reordered IDs/states, changed digest, or legacy state without `batch_contract` fails closed before unfinished work is counted.

Batch membership is not the global-concurrency authority. The state transition runtime and CLI derive one registry scope from the verified month-project evidence and local OS user, then store it under the fixed passwd-derived persistent authority `~/Library/Application Support/fashion-lovart-view-extension/submission-registries`. Source roots and date ancestors never select or partition that location, so independent scanner batches, different source trees, and concurrent singleton runs cannot create separate 10-slot windows. Registry access uses a stable OS lock plus no-follow, crash-durable atomic writes. One persistent state lock covers every state-file CLI command's complete read-mutate-atomic-write transaction, including durable comparison and registry release. Finished work releases its reservation only after the updated state is atomically persisted and `fsync`ed; direct file-coordinator callers use `release_submission_slot` after their own durable write, and that API acquires the same state lock before comparing and releasing.

## Role contract

Assign roles from visual content, with one filename-based exception: `正面/1.jpg` is always the canonical **IDENTITY MODEL SOURCE** for identity only. Inspect this file visually before continuing; the filename selects the source but does not replace evidence-based analysis.

- `model_source`: per-view human pose, body direction, and crop evidence. Only canonical `正面/1.jpg` contributes identity or `body_profile`; a noncanonical model source never does.
- `product_source`: garment construction for the requested view.
- `scene_source`: environmental identity and light evidence.
- `composition_source`: crop, subject scale, head visibility, and framing.
- `accessory_source`: shoes, bags, jewelry, or other separately supplied styling.
- `unused`: irrelevant or conflicting image.

Model, product, scene, and composition must each resolve to exactly one scanner record in a ready view. Composition may fall back to the unique model source. Accessories are optional and may contain multiple files.

Every persisted `files[]` scanner record is the authoritative evidence object: it carries canonical `relative_path`, lowercase 64-character `sha256`, exact `role`, finite numeric `confidence`, and canonical nonblank visual `reason`. Ready records require confidence at least 0.7. An unclassified record instead keeps `role: unclassified`, `confidence: null`, and `reason: ""`, and cannot appear in a ready view or role list. Role lists must exactly reflect scanner-record roles; the only overlap is the ordered `[model_source, composition_source]` membership under explicit `composition_fallback: model_source`. Legacy path-only files, role-only lists, duplicated paths, missing metadata, or any other overlap fail closed.

`canonical_identity_source` and `identity_profile.canonical_source` must both be the strict scanner path/hash for exactly one `views.front.files` record at `正面/1.jpg`. A detached, stale, differently cased, non-front, missing, or duplicate record is invalid.

An optional per-view `footwear_contract` is the only evidence that activates required-footwear defects:

```json
"footwear_contract": {
  "kind": "footwear",
  "source_paths": ["全身/4.png"],
  "confidence": 0.99,
  "reason": "Visually confirmed required shoes"
}
```

It must contain exactly those four fields. `source_paths` must be non-empty, unique, canonical relative paths already present in the same view's `accessory_source`; `confidence` must be a number from 0.7 to 1; and `reason` must be a canonical nonblank string. Omit `footwear_contract` when shoes are absent or unconfirmed, including bag-only, jewelry-only, and other generic accessory cases. Derive prompt state with `view_contract_from_manifest`; never infer footwear from a non-empty `accessory_source`. A malformed explicit contract is invalid rather than footwear-inactive.

Each file path has exactly one primary role. The only supported multi-role behavior is `composition_fallback: model_source` when no separate composition source exists.

Attach `canonical_identity_source`, `identity_profile`, and `garment_profile` to the schema-2 manifest. Derive `head_visibility`, `skin_tone_and_visible_ancestry_cues`, `visible_face_features`, `hair_evidence`, `age_impression`, and `body_profile` only from visible evidence in `正面/1.jpg`; require numeric `confidence` from 0 to 1 and a nonblank visual `reason`. Noncanonical local pose/composition sources must not control or override `body_profile`; they may control only pose, crop, body direction, camera, and composition.

Require all garment fields: nonblank `garment_type`, valid `hem_position`, boolean `requires_full_garment_frame`, and nonblank visual `reason`. `hem_position: below_knee` is valid only with `garment_type: dress`, and that combination always requires `requires_full_garment_frame: true`.

## Role assignment JSON

```json
{
  "正面/1.jpg": {
    "role": "model_source",
    "confidence": 0.98,
    "reason": "Adult human pose on a plain background; body direction and crop are clearly visible."
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
