# Batch Run Contract

## 输入

用户提供日期一级文件夹。每个有效 SPU 必须包含 `产品图/`，并包含可用的 `对标图.<ext>` 或已批准的 `黑白线稿图.<ext>`。

## 两阶段状态

| 阶段 | 输入 | 合格输出 | 不合格处理 |
| --- | --- | --- | --- |
| `LINE_ART_PREP` | `对标图.<ext>` | `黑白线稿图.<ext>`、线稿 Prompt | 记录 `line-art blocked`，跳过该 SPU |
| `FINAL_TRYON` | 最多 8 张产品/搭配图 + 1 张线稿 | 10 张独立合格候选图留在 Lovart 画布 | 记录 `queued-partial` 或 `blocked` |

## 单 SPU 本地记录

```text
spu_code/
├── 黑白线稿图.<ext>
├── _codex_outputs/
│   ├── _run_log.md
│   ├── 01-素材角色与执行记录.md
│   ├── 02-黑白线稿Prompt.md
│   └── 03-NanoBananaPro最终白底Prompt.md
└── _lovart_outputs/
```

## 完成规则

`generated_count >= 10` 不代表完成。只有 Codex 逐张复核后 `qualified_count >= 10` 才是 `completed`。所有 Lovart 候选图保留在画布中，等待人工下载。
