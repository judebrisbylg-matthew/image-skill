# 安装方式

将正式 Skill 同步到 Codex：

```bash
git clone https://github.com/judebrisbylg-matthew/image-skill.git
mkdir -p ~/.codex/skills/fashion-lovart-nano-batch
rsync -a --delete \
  image-skill/fashion-lovart-nano-batch/skill/ \
  ~/.codex/skills/fashion-lovart-nano-batch/
```

更新时：

```bash
cd image-skill
git pull
rsync -a --delete \
  fashion-lovart-nano-batch/skill/ \
  ~/.codex/skills/fashion-lovart-nano-batch/
```

验证：

```bash
sed -n '1,20p' ~/.codex/skills/fashion-lovart-nano-batch/SKILL.md
```

在 Codex 中调用：

```text
[$fashion-lovart-nano-batch] /Users/chenyiming/Desktop/Ai生图测试/6月17日
```

HTML 手册不需要安装。查看或重建手册：

```bash
open image-skill/fashion-lovart-nano-batch/docs/handbook.html
node image-skill/fashion-lovart-nano-batch/tools/build_handbook.mjs
```
