# 示例工作流

## 输入

```text
[$fashion-nano-tryon] 图1-图4是产品图；图5-图8是配饰图；图9是对标图。执行流程
```

## 期望流程

### 1. 黑白线稿生成策略

Codex 应先输出：

```markdown
**黑白线稿生成策略**
- BENCHMARK SOURCE 用途：
- 保留的姿势信息：
- 保留的人体比例：
- 保留的拍摄距离/裁切：
- 保留的手部信息：
- 保留的腿部/重心信息：
- 保留的服装与身体空间关系：
- 保留的穿着效果：
- 可保留的原配饰位置关系：
- 需要弱化的信息：
- 不能强化的信息：
- 人物外观锁定：
- 肤色锁定：
- 发色/发型锁定：
- 可见皮肤区域一致性：
- 线稿风格：
- 输出要求：
- 负向约束：
```

用户确认后才能继续。

### 2. 黑白线稿 Prompt

Codex 输出中英文线稿 Prompt，并提醒用户生成或上传可用线稿。

### 3. 产品特征拆解

线稿确认后，Codex 只分析产品图，输出产品细节：

- 产品类型
- 主色
- 版型/廓形
- 领口/领型
- 袖型/肩部
- 面料纹理
- 必须保留的产品细节
- 容易与线稿原服饰混淆的风险点

### 4. 最终白底展示图策略

Codex 确认：

- 产品图控制什么
- 线稿控制什么
- 线稿不控制什么
- 人物外观锁控制什么
- 配饰/下装如何迁移
- Nano Banana Pro 防混图规则
- 输出规格：`3:4 ratio, 4K output`

### 5. 最终 Nano Banana Pro Prompt

最终英文 Prompt 必须使用短块结构：

```text
FINAL OUTPUT
...

REFERENCE ROLE CONTRACT
...

REFERENCE PRIORITY
...

GARMENT HARD LOCK
...

POSE AND BODY HARD LOCK
...

MODEL APPEARANCE HARD LOCK
...

ACCESSORIES AND BOTTOMS
...

LIGHTING AND FINISH
...

DO NOT INCLUDE
...
```

## 验收标准

- 没有跳过线稿流程
- 没有直接输出最终 Prompt
- 最终规格是 `3:4 ratio, 4K output`
- 最终背景是 `pure white #FFFFFF`
- 产品来源、线稿来源、人物外观锁、配饰和下装职责分开
- 明确禁止 benchmark outfit、line-art outfit、mannequin proportions、random skin tone、unlisted accessories

