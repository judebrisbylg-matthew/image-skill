# 安装方式

本文档说明如何从 `image-skill` 仓库安装 `fashion-nano-tryon` 到本机 Codex。

## 前提

- 你已经有仓库访问权限。
- 本机已经安装 Codex。
- 本机能访问 GitHub。

Codex skills 默认目录：

```bash
~/.codex/skills
```

## 推荐方式：只同步正式 skill 包

```bash
git clone https://github.com/judebrisbylg-matthew/image-skill.git
mkdir -p ~/.codex/skills/fashion-nano-tryon
rsync -a --delete \
  image-skill/fashion-nano-tryon/skill/ \
  ~/.codex/skills/fashion-nano-tryon/
```

为什么只同步 `skill/`：

- `skill/` 是 Codex 真正需要读取的正式能力包。
- `docs/` 是给人看的手册，不需要安装进 Codex。
- `tools/` 是文档构建工具，不需要安装进 Codex。

## 更新已安装 skill

```bash
cd image-skill
git pull
rsync -a --delete \
  fashion-nano-tryon/skill/ \
  ~/.codex/skills/fashion-nano-tryon/
```

## 验证安装

确认文件存在：

```bash
ls ~/.codex/skills/fashion-nano-tryon
```

应至少看到：

```text
SKILL.md
agents
examples
references
```

检查正式规则：

```bash
sed -n '1,40p' ~/.codex/skills/fashion-nano-tryon/SKILL.md
```

在 Codex 中测试调用：

```text
[$fashion-nano-tryon] 图1-图4是产品图；图5-图8是搭配图；图9是对标图。执行流程
```

正确行为：

1. 先输出参考图角色映射或黑白线稿生成策略。
2. 等你确认。
3. 再输出黑白线稿 prompt。
4. 等你生成或确认线稿。
5. 再进入产品拆解。
6. 最后才输出 Nano Banana Pro 最终 prompt。

## 查看新人手册

无需安装到 Codex，也可以直接查看手册：

```bash
open image-skill/fashion-nano-tryon/docs/handbook.html
```

如果修改了 `skill/` 下的 Markdown，重新生成手册：

```bash
node image-skill/fashion-nano-tryon/tools/build_handbook.mjs
```

## 卸载

```bash
rm -rf ~/.codex/skills/fashion-nano-tryon
```

## 常见问题

### Codex 没有识别 skill

检查路径是否正确：

```bash
cat ~/.codex/skills/fashion-nano-tryon/SKILL.md
```

确保 `SKILL.md` 在 `~/.codex/skills/fashion-nano-tryon/` 第一层，不要多嵌套一级。

### 更新后仍是旧流程

重新同步正式 skill 包：

```bash
rsync -a --delete \
  image-skill/fashion-nano-tryon/skill/ \
  ~/.codex/skills/fashion-nano-tryon/
```

然后开启一个新的 Codex 会话再触发。
