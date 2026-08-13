# Prompt Output Schema

Write UTF-8 JSON for each view:

```json
{
  "schema_version": 1,
  "skc_id": "ds726301071",
  "view": "front",
  "generation": {
    "model": "nano banana pro",
    "resolution": "4K",
    "aspect_ratio": "2:3"
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

- Exactly five unique action objects.
- `prompt_en` is a complete standalone English prompt, not notes or a placeholder.
- Preserve the template's action order, bag rules, view limits, crop/head rules, and scene-extension rules.
- Append Nano Banana Pro, 4K, and 2:3 inside every English prompt even though these settings also exist in `generation`.
- Keep the same negative prompt in all five actions unless a stricter action-specific prohibition is required.
