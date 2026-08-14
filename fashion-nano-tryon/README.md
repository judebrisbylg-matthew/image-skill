# Fashion Nano Tryon

这是一套由 Codex 驱动的时装白底试穿提示词工作流。它先把对标图转换成黑白线稿来锁定动作、构图、人体比例和手位，再把产品图、搭配图、人物外观锁组合成适配 **Nano Banana Pro** 的最终英文 prompt。

它的重点不是“让模型自由参考多张图”，而是把每张参考图拆成固定角色，降低 Nano Banana Pro 在动作、构图、搭配和肤色上的漂移。

> 🌐 **新手推荐：** [点击在线打开完整可视化工作手册](https://judebrisbylg-matthew.github.io/image-skill/fashion-nano-tryon/)

![可视化工作手册预览](docs/handbook-preview.png)

## 它由什么组成

```text
Codex                         运行主体：视觉分析、流程门槛、提示词编排
  ↓
skill/                        正式能力包：SKILL.md、agents、examples、references
  ↓
Nano Banana Pro               外部生图模型：执行最终白底电商试穿图 prompt

docs/handbook.html            人类说明书：新人阅读流程、查看全部 Markdown
tools/build_handbook.mjs      文档构建器：从 skill/ 重新生成 HTML
```

`docs/handbook.html` 不是 Skill 本身。正式规则的唯一真源是 [`skill/`](skill/) 目录；HTML 中的编辑只会保存在浏览器本地草稿中。

## 核心能力

- 保留线稿辅助流程，避免直接多图混合导致动作、肤色、构图和商品款式漂移。
- 将参考图拆成 `PRODUCT SOURCE`、`BENCHMARK SOURCE`、`LINE_ART SOURCE`、`MODEL APPEARANCE LOCK`、`ACCESSORY SOURCES`、`BOTTOMS SOURCE` 和 `DENIED SOURCES`。
- 让产品多角度图成为最终主商品的唯一款式来源。
- 用黑白线稿锁定对标图中的姿势、拍摄距离、裁切、身体比例、手位、腿位和穿着空间关系。
- 从对标图提取肤色、发色、发型和基础可见外观，避免线稿阶段丢失颜色信息。
- 支持配饰图和下装图迁移到最终展示图，但不允许它们改写主商品。
- 最终输出 Nano Banana Pro 友好的结构化英文 prompt，默认用于 `3:4`、`4K`、纯白背景 `#FFFFFF`。

## 目录结构

```text
fashion-nano-tryon/
├── README.md
├── INSTALL.md
├── skill/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── examples/
│   └── references/
├── docs/
│   ├── handbook.html
│   ├── handbook-preview.png
│   └── quick-demo.html
└── tools/
    └── build_handbook.mjs
```

| 文件或目录 | 作用 |
| --- | --- |
| `skill/SKILL.md` | Codex 运行时读取的正式规则、流程门槛和输出模板 |
| `skill/agents/openai.yaml` | Codex 中展示名称、短说明和默认触发 prompt |
| `skill/references/` | 图片角色合同、确认门槛、最终 prompt 结构和质检清单 |
| `skill/examples/` | 示例输入、阶段输出和验收标准 |
| `docs/handbook.html` | 新人可视化工作手册，包含流程图、规则索引和 Markdown 预览 |
| `docs/handbook-preview.png` | GitHub README 顶部预览图 |
| `docs/quick-demo.html` | 旧版快速演示页，保留作轻量说明 |
| `tools/build_handbook.mjs` | 从 `skill/` 读取正式 Markdown 并重新生成 HTML 手册 |

## 安装

先克隆仓库，然后只把 `skill/` 目录同步到 Codex 的个人 Skills 目录。目标目录名必须保持为 `fashion-nano-tryon`。

```bash
git clone https://github.com/judebrisbylg-matthew/image-skill.git
mkdir -p ~/.codex/skills/fashion-nano-tryon
rsync -a --delete \
  image-skill/fashion-nano-tryon/skill/ \
  ~/.codex/skills/fashion-nano-tryon/
```

随后重启或刷新 Codex，使新 Skill 被发现。

## 使用

典型输入：

```text
[$fashion-nano-tryon] 图1-图4是产品图；图5-图8是搭配图；图9是对标图。执行流程
```

如果图片编号不同，直接说明角色：

```text
用 fashion-nano-tryon 执行流程。
产品图在 /path/to/产品图，搭配图在 /path/to/搭配图，对标图是 /path/to/对标图.png。
```

## 标准流程

1. 参考图角色映射。
2. 黑白线稿生成策略和人物外观锁定。
3. 黑白线稿 prompt。
4. 等待用户生成或上传批准线稿。
5. 产品特征拆解。
6. 最终白底展示图策略。
7. Nano Banana Pro 最终英文 prompt。

## 默认输出规格

```text
3:4 ratio, 4K output, pure white #FFFFFF background
```

不要使用旧的 `2048x3072` 或 `2:3`，除非用户明确要求。

## 查看可视化手册

本地打开：

```bash
open fashion-nano-tryon/docs/handbook.html
```

或启动本地服务：

```bash
cd fashion-nano-tryon
python3 -m http.server 8766
```

然后访问：

```text
http://localhost:8766/docs/handbook.html
```

手册包含：

- 仓库、Skill、线稿、Nano Banana Pro 和 HTML 的关系图。
- 图片角色合同和来源优先级。
- 六阶段流程和三个确认门槛。
- Nano Banana Pro 最终 prompt 结构。
- 常见错误和验收标准。
- `skill/` 当前 Markdown 原文和实时预览编辑器。

## 修改规则并重建 HTML

先修改 `skill/` 下的正式 Markdown，再运行：

```bash
node fashion-nano-tryon/tools/build_handbook.mjs
```

脚本会读取正式 Skill 文件并重新生成 `docs/handbook.html`。不要把 HTML 本地草稿当成正式规则。

## 完成标准

一次合格的执行必须同时满足：

- 没有跳过黑白线稿流程。
- 没有在批准线稿前进入最终 prompt。
- 主商品只来自 `PRODUCT SOURCE`。
- 线稿只控制姿势、构图、裁切、人体比例、手位、腿位和穿着空间关系。
- 肤色、发色和发型只来自 `MODEL APPEARANCE LOCK`。
- 配饰和下装只来自明确提供的来源。
- 最终 prompt 使用 Nano Banana Pro 短块结构。
- 最终输出规格是 `3:4 ratio, 4K output` 和 `pure white #FFFFFF background`。

## 隐私与权限

不要在仓库中提交客户商品图、模特图、配饰图、生成成品、账号凭据、GitHub token、SSH 私钥或任何本地配置密钥。
