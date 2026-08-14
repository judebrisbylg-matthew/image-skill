# Lovart Handoff Contract

## 上传包

为每个有效 SPU 建立 ASCII 临时上传目录。总计不超过 9 张：最多 8 张产品/搭配参考图，最后一张必须是 `pose_lock_reference`。

```text
/tmp/lovart_batch/<date>/<spu>/
├── product_01.<ext>
├── accessory_01.<ext>
├── bottoms_01.<ext>
└── pose_lock_reference.<ext>
```

## 固定顺序

1. 所有 `product_##`。
2. 所有 `styling_##`、`accessory_##`、`bottoms_##`。
3. 最后一张 `pose_lock_reference`，它只能控制姿势、构图、裁切与人体比例。

不得上传 `对标图.jpg`，不得使用拼图或参考板作为默认上传方式。

## Lovart 设置

- 使用当月项目与当天日期分区。
- 只使用右侧对话面板的 Agent 生图模式。
- 模型必须显示 `Nano Banana Pro`；若显示 `Nano Banana 2` 或其他模型，标记 `blocked:model-mismatch`。
- 输出为 `3:4`、`4K`、纯白 `#FFFFFF`。
- 一次请求 10 张独立单人图；若少于 10 张或输出拼图，切换为候选编号的单张补图。

## 交接记录

记录月项目、日期区、入口、实际模型标签、上传包、生成数量、合格数量、拒绝原因、替换数量、队列状态和画布整理状态。
