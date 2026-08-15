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
      "negative_prompt": "NEGATIVE PROMPT CONTRACT — reject only these defects: collage/multiple panels; multiple people; text; watermark; logo-like marks; distorted anatomy/hands; pasted-on/cutout/halo/edge glow; mismatched lighting/color temperature/shadows; wrong scene; wrong product identity; wrong garment color/neckline/sleeves/length/material; identity drift; ethnicity/visible-ancestry drift; skin-tone drift; age drift; hair drift; body-profile drift; phone/selfie behavior; bag on ground; military stance; both hands hanging straight down; less than a visible half head; complete loss of the head; wrong requested front view; crop violations for the active front composition contract; cropped/obscured hem; hem touching/crossing an image edge; shortened apparent garment length; interrupted shoulder-to-lowest-hem continuity"
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

- `skc_id` in both files must be a nonblank string already equal to its stripped form, and the two strings must match without coercion. Every required identity and garment evidence string in the manifest must also already be stripped. `identity_contract` must match `identity_profile` exactly, including canonical relative path, hash, JSON types, and every profile value. `garment_contract` must match `garment_profile` exactly. A prompt cannot weaken a below-knee dress by self-declaring a shirt or a false frame lock.
- Exactly five unique action objects.
- `analysis_markdown`, every action `title`, and every `negative_prompt` must be real nonblank JSON strings; booleans and numeric coercions are invalid.
- Negative Prompt is script-generated and immutable. Derive `view_contract` from the active validated manifest with `view_contract_from_manifest(view, manifest["views"][view])`, then call `render_negative_prompt(view_contract, identity_contract, garment_contract)`. The exact prefix is `NEGATIVE PROMPT CONTRACT — reject only these defects: `. Copy the return value without trimming or any other modification into all five actions. Validation computes the same value from the active manifest/view and requires exact string equality; legacy prose, paraphrases, whitespace padding, phrase reordering, additions, omissions, another view's output, and incorrect long-dress or footwear variants fail.
- Required-footwear defects activate only when the view contains an explicit validated `footwear_contract`: exactly `kind: footwear`, non-empty unique accessory-backed `source_paths`, numeric `confidence` from 0.7 to 1, and a canonical nonblank `reason`. Omit it when footwear is absent or unconfirmed. A generic bag, jewelry, or other non-footwear `accessory_source` never activates footwear, while a malformed explicit contract fails validation. The renderer adds the view's crop contract and adds the four hem defects only for a visually confirmed below-knee dress. Never compose negative prompts in a template or add action-specific prose to them; put action, camera, composition, scene, correction, and generation prose in `prompt_en` before its immutable terminal suffix.
- `prompt_en` is a complete standalone English prompt, not notes or a placeholder.
- Put all action-specific, camera, composition, scene, lighting, and generation-setting prose first. Every action must then end with this exact manifest-derived suffix introduction; nothing except trailing whitespace may follow the applicable final lock:

  ```text
  FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, full-body, and garment contracts override every earlier sentence in this prompt.
  ```

- Immediately follow that introduction with exactly one actionable `IDENTITY LOCK:` section. Use the fixed semicolon-delimited order below and substitute type- and value-equal active manifest strings. Prefix matches, reordered fields, duplicates, conflicts, coercion, empty/generic marker text, and concrete values outside the lock section fail validation.

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

- The terminal suffix order is `FINAL CONTRACT OVERRIDE` -> `IDENTITY LOCK` -> the applicable framing lock -> the conditional garment lock. Front, side, and back actions use `HEAD CROP FLOOR:`; full actions use `FULL-BODY HEAD COMPLETION:`. Add `GARMENT FRAME LOCK:` only when the active manifest's `garment_profile.requires_full_garment_frame` is `true`. Earlier contradictory prose is superseded by this terminal block; prose appended after it fails validation.
- `正面/1.jpg` remains the canonical identity source even when a local view model image supplies pose or crop evidence.
- Preserve the template's action order, bag rules, view limits, crop/head rules, and scene-extension rules.
- Include Nano Banana Pro, 4K, and 2:3 before the final contract suffix in every English prompt even though these settings also exist in `generation`.
- Keep the exact same renderer output in all five actions. Action-specific prohibitions belong in `prompt_en` before the immutable final-contract suffix.
