# 示例批处理

## 调用

```text
[$fashion-lovart-nano-batch] /Users/chenyiming/Desktop/Ai生图测试/6月17日
```

## 正确行为

1. 扫描一级目录的直接 SPU 子文件夹，跳过输出目录和无效文件夹。
2. 对每个 SPU 先执行 `LINE_ART_PREP`，保存并质检 `黑白线稿图.<ext>`。
3. 只为通过线稿门禁的 SPU 生成 Lovart 上传包与 Nano Banana Pro Prompt。
4. 在同一个月度 Lovart 项目内，按日期区和 SPU 块整理参考图与结果。
5. 逐张复核候选图；达到 10 张合格独立图才记录完成。
6. 输出完成、阻塞、队列中的 SPU 清单及本地日志路径；不自动下载候选图。

## 不正确行为

- 缺少线稿时直接把 `对标图.jpg` 上传给 Lovart。
- 用 Nano Banana 2 代替 Nano Banana Pro。
- 把 10 个结果做成一张网格图。
- 以生成数量代替逐张合格数量。
