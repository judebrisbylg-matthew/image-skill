# Image Skills

面向 Codex 的生图工作流 Skill 仓库。每个目录是一套独立能力包；先阅读对应说明，再将其中的正式 Skill 安装到本机。

> 🌐 **新手入口：** [点击打开《SKC 四视角 Lovart 延展·可视化工作手册》](https://judebrisbylg-matthew.github.io/image-skill/)
> 👗 **Nano 试穿入口：** [点击打开《Fashion Nano Tryon·可视化工作手册》](https://judebrisbylg-matthew.github.io/image-skill/fashion-nano-tryon/)

## Skill 目录

| Skill | 作用 | 文档 |
|---|---|---|
| [`fashion-nano-tryon`](fashion-nano-tryon/) | 用 Nano Banana Pro 完成线稿辅助的白底时装试穿 | [使用说明](fashion-nano-tryon/README.md) · [在线可视化手册](https://judebrisbylg-matthew.github.io/image-skill/fashion-nano-tryon/) · [HTML 源文件](fashion-nano-tryon/docs/handbook.html) |
| [`fashion-lovart-view-extension`](fashion-lovart-view-extension/) | 批量处理 SKC 的正面、侧面、背面、全身延展图，并在 Lovart 中生成、质检和排版 | [使用说明](fashion-lovart-view-extension/README.md) · [在线可视化手册](https://judebrisbylg-matthew.github.io/image-skill/) · [HTML 源文件](fashion-lovart-view-extension/docs/handbook.html) |

## 仓库、智能体与 Skill 的关系

```text
image-skill 仓库
├── fashion-nano-tryon 线稿辅助 Nano 试穿工作流
│   ├── skill/        Codex 可安装的核心能力包
│   ├── docs/         给人阅读的可视化 HTML 手册
│   └── tools/        从正式 Markdown 重新生成手册的工具
└── fashion-lovart-view-extension 智能体工作流
    ├── skill/        Codex 可安装的核心能力包
    ├── docs/         给人阅读的可视化 HTML 手册
    └── tools/        从正式 Markdown 重新生成手册的工具
```

HTML 是说明书，不是可执行 Skill。正式行为始终以各目录中 `skill/` 下的 `SKILL.md`、`references/` 和 `scripts/` 为准。

## 使用提醒

- 仓库不包含 Lovart 账号、浏览器登录状态或付费额度。
- 浏览器自动化需要使用者自行安装并启用 Codex 的 Chrome 控制能力。
- 运行前请阅读每个 Skill 的前置条件和输入目录规范。
