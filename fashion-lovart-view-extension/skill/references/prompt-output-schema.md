# Prompt Output Schema

Write UTF-8 JSON for each view:

```json
{
  "schema_version": 2,
  "skc_id": "ds726301071",
  "view": "front",
  "generation": {
    "model": "nano banana pro",
    "resolution": "4K",
    "aspect_ratio": "2:3"
  },
  "identity_contract": {
    "canonical_source": {
      "relative_path": "正面/1.jpg",
      "sha256": "<64-character SHA-256 from manifest>"
    },
    "head_visibility": "partial",
    "skin_tone_and_visible_ancestry_cues": "<visible evidence>",
    "visible_face_features": "<visible evidence>",
    "hair_evidence": "<visible evidence>",
    "age_impression": "<visible evidence>",
    "body_profile": "<visible evidence>",
    "confidence": 0.86,
    "reason": "<nonblank visible-evidence reason>"
  },
  "garment_contract": {
    "garment_type": "dress",
    "hem_position": "below_knee",
    "requires_full_garment_frame": true,
    "reason": "<nonblank product-evidence reason>"
  },
  "analysis_markdown": "# Completed Chinese analysis...",
  "actions": [
    {
      "action_id": "FR01",
      "title": "正面标准角度",
      "prompt_en": "SKC ... one complete executable English prompt",
      "negative_prompt": "one complete shared negative prompt"
    }
  ]
}
```

## View action IDs

- Front: `FR01`–`FR05`
- Side: `SI01`–`SI05`
- Back: `BA01`–`BA05`
- Full: `FU01`–`FU05`

## Contract

- Validate every prompt against its active schema-2 manifest:

  ```bash
  python3 scripts/validate_manifest.py prompt <prompt.json> <manifest.json>
  ```

- `skc_id` must match the active manifest. `identity_contract` must match `identity_profile` exactly, including canonical relative path, hash, and every profile value. `garment_contract` must match `garment_profile` exactly. A prompt cannot weaken a below-knee dress by self-declaring a shirt or a false frame lock.
- Exactly five unique action objects.
- `prompt_en` is a complete standalone English prompt, not notes or a placeholder.
- Every action must include exactly one actionable `IDENTITY LOCK:` section. Use the fixed semicolon-delimited order below and substitute exact active values. Prefix matches, reordered fields, duplicates, conflicts, empty/generic marker text, and concrete values outside the lock section fail validation.

  ```text
  IDENTITY LOCK: canonical_source=正面/1.jpg; head_visibility=<exact active value>; skin_tone_and_visible_ancestry_cues=<exact active value>; visible_face_features=<exact active value>; hair_evidence=<exact active value>; age_impression=<exact active value>; body_profile=<exact active value>; Noncanonical local pose/composition sources must not control or override body_profile.
  ```

  In contract terms, Noncanonical local pose/composition sources must not control or override `body_profile`; the raw prompt sentence above intentionally omits Markdown backticks.

- Use each applicable positive marker body verbatim. Negated, paraphrased, partial, or duplicated clauses fail validation:

  ```text
  HEAD CROP FLOOR: The final image must retain at least half of the model's head. A complete head is allowed. Never crop below the half-head boundary.

  FULL-BODY HEAD COMPLETION: Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural complete head using only the visible skin tone, ancestry cues, partial facial evidence, hair evidence, age impression, neck/shoulder evidence, and body profile. Do not change the model's visible identity characteristics.

  GARMENT FRAME LOCK: Activate only for a visually confirmed below-knee dress; when active, keep the dress continuously visible from the shoulder/neckline through the lowest hem point; leave visible safety margin below the hem; the hem must not touch or cross an image edge; keep the major hem silhouette unobscured; keep the apparent garment length unchanged.
  ```

- Front, side, and back actions use `HEAD CROP FLOOR:`; full actions use `FULL-BODY HEAD COMPLETION:`. Add `GARMENT FRAME LOCK:` only when the active manifest's `garment_profile.requires_full_garment_frame` is `true`.
- `正面/1.jpg` remains the canonical identity source even when a local view model image supplies pose or crop evidence.
- Preserve the template's action order, bag rules, view limits, crop/head rules, and scene-extension rules.
- Append Nano Banana Pro, 4K, and 2:3 inside every English prompt even though these settings also exist in `generation`.
- Keep the same negative prompt in all five actions unless a stricter action-specific prohibition is required.
