# Fashion Lovart Nano Batch

这是完整的时装白底试穿批处理智能体。用户提供一个按日期组织的一级文件夹，智能体会扫描其中的 SPU，先在 Codex 侧为每款生成并验收黑白线稿，再在 Lovart 右侧 Agent 面板中使用 **Nano Banana Pro** 生成、逐张质检和整理白底电商候选图。

> 🌐 **新手推荐：** [点击在线打开完整可视化工作手册](https://judebrisbylg-matthew.github.io/image-skill/fashion-lovart-nano-batch/)

![可视化工作手册预览](docs/handbook-preview.png)

## 它解决什么

- 一次处理一个日期文件夹中的多个 SPU，不让单款失败阻断整批。
- 强制先生成并验收 `黑白线稿图`，禁止把对标图直接用于 Lovart 最终生图。
- 每款最多上传 8 张产品/搭配图，最后上传 1 张 `pose_lock_reference` 作为固定姿势线稿。
- 强制 Lovart 使用 `Nano Banana Pro`、`3:4`、`4K`、纯白 `#FFFFFF`，不能降级为 Nano Banana 2。
- 每个 SPU 以 `qualified_count >= 10` 为完成标准，而不是只看生成数量。
- 在一个月度 Lovart 项目中按日期区、SPU 块整理参考图和候选图；候选图保留在画布供人工审核下载。

## 架构

```text
日期文件夹
  ↓ 扫描每个 SPU
fashion-lovart-nano-batch
  ├── 调用 fashion-nano-tryon：外观锁、线稿、产品拆解、最终 Prompt
  ├── 检查黑白线稿质量与上传包
  ├── Lovart Agent + Nano Banana Pro：生成候选图
  ├── Codex：逐张复核、补图、记录状态
  └── Lovart 月度画布：日期分区 / SPU 参考图 / 合格候选图
```

## 目录结构

```text
fashion-lovart-nano-batch/
├── README.md
├── INSTALL.md
├── skill/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   └── examples/
├── docs/
│   ├── handbook.html
│   ├── handbook-preview.png
│   └── quick-demo.html
├── tools/
│   └── build_handbook.mjs
└── tests/
    └── handbook-contract.test.mjs
```

`skill/` 是 Codex 的正式能力包；`docs/` 是新人手册；`tools/` 用于由正式 Markdown 重新生成 HTML。不要在 HTML 本地草稿中修改正式规则。

## 输入目录

```text
日期一级文件夹/
└── spu_code/
    ├── 产品图/             必填
    ├── 搭配图/             可选
    ├── 对标图.<ext>        无线稿时必填
    └── 黑白线稿图.<ext>    Codex 侧生成并验收
```

推荐将日期文件夹放在 Codex 可写工作区，例如：

```text
/Users/chenyiming/Desktop/Ai生图测试/6月17日
```

## 调用

```text
[$fashion-lovart-nano-batch] /Users/chenyiming/Desktop/Ai生图测试/6月17日
```

完整输入、输出、质量门禁、队列处理和 Lovart 上传规则见在线手册。
