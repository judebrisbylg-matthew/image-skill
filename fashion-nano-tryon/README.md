# fashion-nano-tryon

`fashion-nano-tryon` 是一个私有 Codex skill，用于电商服装「线稿辅助试穿」提示词工作流。

它和 `fashion-line-tryon` 保持相同的前置流程，但最后一步专门输出适配 **Nano Banana Pro** 的白底电商穿搭展示图 prompt。

它把参考图拆成两个阶段处理：

1. 先把模特对标图转换成黑白铅笔线稿姿态参考，并提取模特外观锁定描述。
2. 再把商品多视图参考、已确认线稿、模特外观锁定、配饰参考和下装参考组合成 Nano Banana Pro 可执行提示词，用于生成高保真白底穿搭展示图。

这个 skill 的职责是编写提示词和把控确认门槛，不直接生成最终图片。

## 核心能力

- 保留 `fashion-line-tryon` 的线稿辅助流程，避免直接多图混合导致动作、肤色、构图和商品款式漂移。
- 将商品款式、姿态构图、模特外观、配饰、下装分成不同控制源。
- 让商品多角度图成为最终上衣/主商品的唯一款式来源。
- 保留对标图中的姿势、构图、拍摄距离、身体比例、手位、腿位、穿着关系和必要空间关系。
- 从对标图提取肤色、发色、发型和可见外观锁定，避免线稿阶段丢失颜色信息。
- 支持配饰图和下装图迁移到最终展示图提示词，但不允许它们改写主商品。
- 最终输出 Nano Banana Pro 友好的结构化英文 prompt，默认用于 `3:4`、`4K`、纯白背景电商图。

## 适用场景

- 跨境电商服装白底试穿图提示词生产。
- 需要用一张模特对标图控制姿势、裁切和穿着效果，同时严格保留多张商品图款式。
- 需要把复杂参考图拆成「线稿姿态参考」与「模特外观锁定」两个控制面。
- 使用 Nano Banana Pro 时，需要降低动作不可控、搭配不可控、构图不可控、肤色不可控的问题。
- 需要 `3:4`、`4K`、纯白背景、清晰商品细节的时尚电商展示图。

## 默认输入约定

| 输入 | 默认角色 | 用途 |
| --- | --- | --- |
| Images 1-4 | 商品多角度参考图 | 最终主商品款式、颜色、结构、材质和细节的最高优先级来源 |
| Images 5+ | 配饰或下装参考 | 迁移到最终展示图提示词；裤子、裙子等应归入下装来源 |
| 最后一张对标图 | 模特对标图 | 先转线稿，再提供姿态、构图、身体比例和外观锁定 |

如果用户显式指定了别的图像顺序，以用户标签为准。图片角色不清楚时，skill 会先要求澄清。

## 输出约定

- Stage 0 输出：参考图角色映射和默认输出规格。
- Stage 1 输出：黑白线稿策略、人物外观锁定、中文线稿 prompt、英文线稿 prompt。
- Stage 2 输出：商品特征拆解、最终合成策略、中文最终说明、英文 Nano Banana Pro 最终 prompt。
- 最终展示图默认规格：`3:4`、`4K`、纯白背景 `#FFFFFF`。
- 质量目标：高端电商商品质感、清晰商品细节、干净棚拍光线、自然接地阴影、精致目录图完成度。

## 工作流

### Stage 0: 参考图角色映射

1. 根据用户说明确认哪些图是商品图、配饰图、下装图和对标图。
2. 明确主商品、配饰、下装、对标图各自的控制边界。
3. 输出角色映射，等待用户确认或在用户已明确说明时继续。

### Stage 1: 对标图转线稿

1. 分析对标图的姿势、拍摄距离、裁切、身体比例、手脚关系和穿着空间关系。
2. 输出线稿生成策略和人物外观锁定，等待用户确认。
3. 用户确认后，生成黑白铅笔线稿 prompt。
4. 用户用该 prompt 生成线稿，并确认线稿可用。

### Stage 2: Nano Banana Pro 最终展示图提示词

1. 只从商品图拆解主商品颜色、版型、结构、面料和前后侧细节。
2. 从配饰图和下装图拆解明确提供的造型元素。
3. 等待用户确认商品拆解和最终合成策略。
4. 结合已确认线稿、外观锁定、商品图、配饰图和下装图，输出 Nano Banana Pro 结构化英文 prompt。

## 质量门槛

skill 内置三个确认门槛：

1. 未确认线稿策略，不进入 Stage 1 prompt。
2. 未确认线稿结果和人物外观锁定，不进入最终展示图 prompt。
3. 未确认商品拆解和最终合成策略，不输出最终 Nano Banana Pro prompt。

这些门槛用于降低以下风险：

- 对标图原服装覆盖商品图款式。
- 线稿丢失肤色、发色和发型信息。
- 姿态参考误控制商品结构。
- 配饰参考干扰主体服装。
- Nano Banana Pro 随机改变构图、肤色、动作或输出比例。

## 仓库结构

```text
fashion-nano-tryon/
├── SKILL.md
├── README.md
├── INSTALL.md
├── demo.html
├── agents/
│   └── openai.yaml
└── examples/
    └── sample-workflow.md
```

| 文件 | 作用 |
| --- | --- |
| `SKILL.md` | skill 的触发描述、工作流、约束和输出模板 |
| `agents/openai.yaml` | Codex 中展示名称、短说明和默认触发 prompt |
| `README.md` | 私有仓库分发、安装、使用和维护说明 |
| `INSTALL.md` | 更详细的安装说明 |
| `demo.html` | HTML 演示页，用于快速理解这个 skill 做什么、怎么做 |
| `examples/sample-workflow.md` | 示例流程 |

## 私有安装

### 前提

- 已获得该私有 GitHub 仓库的读取权限。
- 本机 Git 已可访问该仓库。
- Codex 使用默认 skill 目录 `~/.codex/skills`，或你已设置自己的 `CODEX_HOME`。

私有仓库建议优先使用 SSH。HTTPS 也可以，但需要浏览器登录、Git Credential Manager、GitHub CLI 登录态，或有仓库读取权限的 GitHub token。

### 方式 A: 安装到默认 Codex 目录

```bash
mkdir -p ~/.codex/skills
git clone git@github.com:judebrisbylg-matthew/fashion-nano-tryon.git ~/.codex/skills/fashion-nano-tryon
```

### 方式 B: 使用 HTTPS

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/judebrisbylg-matthew/fashion-nano-tryon.git ~/.codex/skills/fashion-nano-tryon
```

### 方式 C: 安装到自定义 `CODEX_HOME`

```bash
mkdir -p "$CODEX_HOME/skills"
git clone git@github.com:judebrisbylg-matthew/fashion-nano-tryon.git "$CODEX_HOME/skills/fashion-nano-tryon"
```

## 安装后验证

检查目录是否齐全：

```bash
ls ~/.codex/skills/fashion-nano-tryon
```

至少应看到：

```text
SKILL.md
README.md
agents
```

然后在 Codex 中用以下任一表达触发：

- `fashion-nano-tryon`
- `用 fashion-nano-tryon 帮我做 Nano Banana Pro 服装线稿试穿 prompt`
- `图1-图4是产品图，图5-图8是配饰图，图9是对标图，用 fashion-nano-tryon 执行流程`

如果你刚安装完 skill 但当前会话没有识别到它，开启一个新会话后再触发一次。

## 更新

默认目录安装：

```bash
cd ~/.codex/skills/fashion-nano-tryon
git pull
```

自定义 `CODEX_HOME` 安装：

```bash
cd "$CODEX_HOME/skills/fashion-nano-tryon"
git pull
```

## 卸载

默认目录安装：

```bash
rm -rf ~/.codex/skills/fashion-nano-tryon
```

自定义 `CODEX_HOME` 安装：

```bash
rm -rf "$CODEX_HOME/skills/fashion-nano-tryon"
```

## 使用示例

### 示例 1: 先做线稿

```text
用 fashion-nano-tryon 处理这些图。
图1-图4是商品图，图5-图8是配饰或下装图，图9是对标图。先进入黑白线稿策略。
```

### 示例 2: 进入最终展示图

```text
这是商品图、配饰图、下装图、已确认线稿和人物外观锁定。
用 fashion-nano-tryon 先拆商品特征，再准备 Nano Banana Pro 的 3:4 4K 白底穿搭展示图 prompt。
```

### 示例 3: 指定 Nano Banana Pro 输出规格

```text
最终输出给 Nano Banana Pro 使用。
尺寸选择 3:4，像素选择 4K，背景必须是纯白 #FFFFFF。
```

## HTML 演示页

本仓库包含 `demo.html`，用于用图文结构快速查看这个 skill 是做什么的、每一步怎么做、最终 prompt 应该如何组织。

本地打开：

```bash
cd ~/.codex/skills/fashion-nano-tryon
open demo.html
```

或启动本地服务：

```bash
cd ~/.codex/skills/fashion-nano-tryon
python3 -m http.server 8766
```

然后访问：

```text
http://localhost:8766/demo.html
```

## 维护建议

- 运行时规则放在 `SKILL.md`，不要把私有业务图片或成品客户素材提交进仓库。
- 调整触发说明或默认 prompt 后，同步检查 `agents/openai.yaml`。
- 修改工作流后，至少用一组 Stage 1 请求和一组 Stage 2 请求做人工验证。
- 调整最终输出规格时，同时检查 `SKILL.md`、`README.md`、`INSTALL.md` 和 `demo.html`。
- 分发给其他账号前，先确认仓库可见性仍为 `private`，并只授予必要的仓库读取权限。

## 隐私与权限

该仓库应保持 `private`。

不要在仓库中公开提交：

- 客户商品图、模特图、配饰图和生成成品。
- 商业账号凭据、GitHub token、SSH 私钥或任何本地配置密钥。
- 只应保留在内部使用的客户命名、渠道信息和生产记录。

私有仓库仍会向被授权协作者完整暴露 skill 规则。分发时应按 GitHub 仓库权限管理协作者。
