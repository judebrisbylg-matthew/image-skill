# 安装方式

本文档说明如何从私有 GitHub 仓库安装 `fashion-nano-tryon` skill 到本机 Codex。

## 前提

- 你已经有该私有仓库的访问权限
- 本机已经安装 Codex
- 本机能访问 GitHub 私有仓库

Codex skills 默认目录：

```bash
~/.codex/skills
```

## 方式一：克隆私有仓库后复制 skill

适合最稳定的私享安装方式。

```bash
git clone git@github.com:<owner>/<repo>.git
mkdir -p ~/.codex/skills
cp -R <repo>/fashion-nano-tryon ~/.codex/skills/fashion-nano-tryon
```

如果仓库内采用 `skills/fashion-nano-tryon` 目录：

```bash
git clone git@github.com:<owner>/<repo>.git
mkdir -p ~/.codex/skills
cp -R <repo>/skills/fashion-nano-tryon ~/.codex/skills/fashion-nano-tryon
```

## 方式二：更新已安装 skill

```bash
cd <repo>
git pull
rm -rf ~/.codex/skills/fashion-nano-tryon
cp -R fashion-nano-tryon ~/.codex/skills/fashion-nano-tryon
```

如果仓库内采用 `skills/fashion-nano-tryon` 目录：

```bash
cd <repo>
git pull
rm -rf ~/.codex/skills/fashion-nano-tryon
cp -R skills/fashion-nano-tryon ~/.codex/skills/fashion-nano-tryon
```

## 验证安装

确认文件存在：

```bash
ls ~/.codex/skills/fashion-nano-tryon
```

应至少看到：

```text
SKILL.md
agents/openai.yaml
demo.html
README.md
INSTALL.md
examples/
```

在 Codex 中测试调用：

```text
[$fashion-nano-tryon] 图1-图4是产品图；图5-图8是配饰图；图9是对标图。执行流程
```

正确行为：

1. 先输出黑白线稿生成策略
2. 等你确认
3. 再输出黑白线稿 Prompt
4. 等你生成/确认线稿
5. 再进入产品拆解
6. 最后才输出 Nano Banana Pro 最终 Prompt

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

确保 `SKILL.md` 在 `fashion-nano-tryon` 目录第一层，不要多嵌套一级。

### 私有仓库 clone 失败

确认你对仓库有访问权限，并配置了 SSH key 或 GitHub credential。

SSH 测试：

```bash
ssh -T git@github.com
```

### 更新后仍是旧流程

删除旧目录后重新复制：

```bash
rm -rf ~/.codex/skills/fashion-nano-tryon
cp -R <repo>/fashion-nano-tryon ~/.codex/skills/fashion-nano-tryon
```

