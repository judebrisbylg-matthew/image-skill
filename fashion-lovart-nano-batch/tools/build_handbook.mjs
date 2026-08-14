import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const toolsRoot = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(toolsRoot, '..');
const skillRoot = path.join(packageRoot, 'skill');
const outputHtml = path.join(packageRoot, 'docs', 'handbook.html');
const siteOutputHtml = path.join(packageRoot, '..', 'docs', 'fashion-lovart-nano-batch', 'index.html');

const documents = [
  ['skill', '智能体主流程', 'SKILL.md', 'SKILL.md'],
  ['contract', '批处理运行合同', 'references/batch-run-contract.md', 'batch-run-contract.md'],
  ['handoff', 'Lovart 交接合同', 'references/lovart-handoff-contract.md', 'lovart-handoff-contract.md'],
  ['quality', '质检与恢复', 'references/quality-and-recovery.md', 'quality-and-recovery.md'],
  ['example', '示例批处理', 'examples/sample-batch.md', 'sample-batch.md'],
].map(([id, title, relativePath, fileName]) => ({
  id,
  title,
  relativePath,
  fileName,
  content: fs.readFileSync(path.join(skillRoot, relativePath), 'utf8'),
}));

const escapeHtml = value => value.replace(/[&<>"']/g, char => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
}[char]));

const docsJson = JSON.stringify(documents).replace(/<\/script/gi, '<\\/script');

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="fashion-lovart-nano-batch Skill 可视化工作手册" />
  <title>Fashion Lovart Nano Batch · 可视化工作手册</title>
  <style>
    :root {
      --ink: #111827;
      --muted: #5f6b7a;
      --faint: #8b95a5;
      --line: #dde3ea;
      --soft: #f6f8fb;
      --paper: #fff;
      --blue: #2563eb;
      --blue-dark: #1d4ed8;
      --blue-soft: #eff6ff;
      --green: #16875d;
      --green-soft: #e8f7ef;
      --amber: #b35b09;
      --amber-soft: #fff7e8;
      --red: #c33c54;
      --red-soft: #fff1f3;
      --shadow: 0 18px 55px rgba(15, 23, 42, .08);
      --sans: "Aptos", "SF Pro Text", "PingFang SC", "Noto Sans CJK SC", sans-serif;
      --mono: "SFMono-Regular", "Cascadia Mono", "Roboto Mono", monospace;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { margin: 0; color: var(--ink); background: var(--paper); font: 15px/1.62 var(--sans); -webkit-font-smoothing: antialiased; }
    a { color: inherit; text-decoration: none; }
    code, pre, textarea { font-family: var(--mono); }
    .topbar { position: sticky; top: 0; z-index: 20; display: flex; justify-content: space-between; align-items: center; min-height: 58px; padding: 0 24px; background: rgba(255,255,255,.94); border-bottom: 1px solid var(--line); backdrop-filter: blur(18px); }
    .brand { display: flex; align-items: center; gap: 12px; }
    .mark { width: 28px; height: 28px; display: grid; place-items: center; color: #fff; background: var(--blue); border-radius: 8px; font-weight: 850; }
    .brand strong { display: block; font-size: 14px; }
    .brand small { color: var(--faint); font-size: 12px; }
    .pill { display: inline-flex; align-items: center; gap: 7px; padding: 6px 10px; color: #0f6b49; background: var(--green-soft); border: 1px solid #cfeedd; border-radius: 999px; font-size: 12px; font-weight: 750; }
    .pill::before { content: ""; width: 7px; height: 7px; background: var(--green); border-radius: 50%; }
    .shell { display: grid; grid-template-columns: 240px minmax(0,1fr) 300px; min-height: calc(100vh - 58px); }
    .left, .right { position: sticky; top: 58px; height: calc(100vh - 58px); overflow: auto; padding: 28px 20px 44px; background: #fff; }
    .left { border-right: 1px solid var(--line); }
    .right { border-left: 1px solid var(--line); }
    .rail-label { margin: 0 8px 10px; color: var(--faint); font: 800 10px/1 var(--mono); letter-spacing: .12em; text-transform: uppercase; }
    .nav { display: grid; gap: 3px; }
    .nav a { display: flex; justify-content: space-between; align-items: center; min-height: 36px; padding: 8px 10px; color: var(--muted); border-radius: 8px; font-size: 13px; }
    .nav a:hover, .nav a.active { color: var(--blue-dark); background: var(--blue-soft); font-weight: 750; }
    .nav a span:last-child { color: var(--faint); font: 10px/1 var(--mono); }
    main { min-width: 0; padding: 48px clamp(24px, 5vw, 76px) 96px; }
    .content { max-width: 920px; margin: 0 auto; }
    section { scroll-margin-top: 82px; padding-top: 76px; }
    .kicker { color: var(--blue-dark); font: 800 11px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; }
    h1, h2, h3 { line-height: 1.13; letter-spacing: -.035em; text-wrap: balance; }
    h1 { margin: 10px 0 20px; font-size: clamp(42px, 7vw, 72px); letter-spacing: -.06em; }
    h1 span { color: var(--blue); }
    h2 { margin: 8px 0 14px; font-size: 34px; }
    h3 { margin: 0 0 8px; font-size: 17px; }
    p { color: var(--muted); }
    .lede { max-width: 730px; margin: 0 0 28px; font-size: 18px; line-height: 1.7; }
    .hero { display: grid; grid-template-columns: 1.05fr .95fr; gap: 16px; margin-top: 26px; }
    .hero-card { min-height: 250px; padding: 26px; color: #fff; background: #111827; border-radius: 18px; box-shadow: var(--shadow); }
    .hero-card b { display: block; margin-bottom: 12px; font-size: 68px; line-height: 1; letter-spacing: -.06em; }
    .hero-card p { max-width: 330px; color: #cbd5e1; }
    .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .metric { min-height: 120px; display: flex; flex-direction: column; justify-content: space-between; padding: 18px; background: var(--soft); border: 1px solid var(--line); border-radius: 13px; }
    .metric b { font-size: 30px; line-height: 1; }
    .metric span { color: var(--muted); font-size: 12px; }
    .metric.accent { color: var(--blue-dark); background: var(--blue-soft); }
    .map { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 9px; margin-top: 22px; }
    .node { position: relative; min-height: 128px; padding: 16px; background: #fff; border: 1px solid var(--line); border-radius: 12px; }
    .node:not(:last-child)::after { content: "→"; position: absolute; top: 50%; right: -10px; z-index: 1; color: var(--blue); background: #fff; font-weight: 900; transform: translateY(-50%); }
    .node.core { color: #fff; background: #111827; border-color: #111827; }
    .node.core p { color: #cbd5e1; }
    .node small { display: block; margin-bottom: 8px; color: var(--faint); font: 800 10px/1 var(--mono); }
    .cards { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; }
    .card { padding: 18px; background: #fff; border: 1px solid var(--line); border-radius: 12px; }
    .card.warn { background: var(--amber-soft); border-color: #f0d8ad; }
    .card.danger { background: var(--red-soft); border-color: #f3c6cf; }
    .card p, .card ul { margin: 0; color: var(--muted); font-size: 13px; }
    .card ul { padding-left: 18px; }
    .roles { overflow: hidden; border: 1px solid var(--line); border-radius: 13px; }
    .role { display: grid; grid-template-columns: 190px 1fr 1fr; border-bottom: 1px solid var(--line); }
    .role:last-child { border-bottom: 0; }
    .role > * { margin: 0; padding: 13px 15px; font-size: 13px; }
    .role code { color: var(--blue-dark); background: var(--blue-soft); }
    .role p { border-left: 1px solid var(--line); }
    .pipeline { display: grid; grid-template-columns: repeat(6, minmax(90px,1fr)); gap: 8px; margin: 24px 0 16px; padding: 7px; background: var(--soft); border: 1px solid var(--line); border-radius: 14px; }
    .stage { min-height: 96px; padding: 11px 10px; text-align: left; background: transparent; border: 0; border-radius: 10px; cursor: pointer; }
    .stage.active { color: #fff; background: var(--blue); }
    .stage small { display: block; margin-bottom: 9px; font: 800 10px/1 var(--mono); opacity: .72; }
    .stage strong { display: block; font-size: 12px; line-height: 1.35; }
    .stage-detail { display: grid; grid-template-columns: 62px 1fr auto; gap: 16px; align-items: center; min-height: 128px; padding: 22px; background: #fff; border: 1px solid var(--line); border-radius: 13px; box-shadow: var(--shadow); }
    .stage-no { color: var(--blue); font-size: 36px; font-weight: 850; }
    .stage-tag { padding: 6px 9px; color: var(--blue-dark); background: var(--blue-soft); border-radius: 999px; font-size: 11px; font-weight: 800; white-space: nowrap; }
    .split { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .codebox { position: relative; overflow: auto; padding: 18px 18px 18px; color: #e5e7eb; background: #111827; border-radius: 12px; font: 12px/1.7 var(--mono); white-space: pre; }
    .copy { position: absolute; top: 10px; right: 10px; padding: 5px 8px; color: #cbd5e1; background: #1f2937; border: 1px solid #374151; border-radius: 7px; cursor: pointer; font-size: 10px; }
    .done { display: grid; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    .done div { display: grid; grid-template-columns: 26px 1fr auto; gap: 10px; align-items: center; padding: 12px 14px; border-bottom: 1px solid var(--line); }
    .done div:last-child { border-bottom: 0; }
    .check { display: grid; place-items: center; width: 18px; height: 18px; color: #fff; background: var(--green); border-radius: 50%; font-size: 10px; }
    .done code { color: var(--faint); font-size: 10px; }
    .context { margin-bottom: 15px; padding: 16px; background: var(--soft); border: 1px solid var(--line); border-radius: 12px; }
    .context h3 { font-size: 13px; }
    .context p { margin: 0; font-size: 12px; }
    .spec { display: grid; gap: 9px; }
    .spec div { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 12px; }
    .spec strong { color: var(--ink); text-align: right; }
    .md-workbench { overflow: hidden; border: 1px solid var(--line); border-radius: 14px; background: #fff; box-shadow: var(--shadow); }
    .md-head { display: flex; justify-content: space-between; gap: 14px; padding: 14px 16px; background: var(--soft); border-bottom: 1px solid var(--line); }
    .md-path { display: block; color: var(--faint); font: 10px/1.5 var(--mono); }
    .md-actions { display: flex; gap: 6px; flex-wrap: wrap; }
    .md-btn { padding: 7px 10px; background: #fff; border: 1px solid var(--line); border-radius: 7px; cursor: pointer; font-size: 11px; font-weight: 750; }
    .md-btn.primary { color: #fff; background: var(--blue); border-color: var(--blue); }
    .md-layout { display: grid; grid-template-columns: 220px minmax(0,1fr); min-height: 700px; }
    .md-library { padding: 12px; background: #fafbfc; border-right: 1px solid var(--line); }
    .md-search { width: 100%; height: 36px; margin-bottom: 10px; padding: 0 11px; border: 1px solid var(--line); border-radius: 8px; outline: none; }
    .md-doc-list { display: grid; gap: 4px; }
    .md-doc { width: 100%; padding: 10px; text-align: left; color: var(--muted); background: transparent; border: 0; border-radius: 8px; cursor: pointer; }
    .md-doc.active, .md-doc:hover { color: var(--blue-dark); background: var(--blue-soft); }
    .md-doc strong { display: block; font-size: 12px; }
    .md-doc small { display: block; margin-top: 3px; font: 9px/1.35 var(--mono); }
    .md-editor { display: grid; grid-template-columns: 1fr 1fr; min-width: 0; }
    .md-pane + .md-pane { border-left: 1px solid var(--line); }
    .md-pane-title { display: flex; justify-content: space-between; align-items: center; height: 38px; padding: 0 12px; color: var(--faint); background: #fbfcfd; border-bottom: 1px solid var(--line); font: 10px/1 var(--mono); }
    #markdownInput { display: block; width: 100%; height: 662px; resize: none; padding: 18px; color: #e5e7eb; background: #111827; border: 0; outline: none; font: 12px/1.72 var(--mono); }
    .md-preview { height: 662px; overflow: auto; padding: 22px; font-size: 13px; }
    .md-preview h1 { margin: 0 0 24px; font-size: 30px; }
    .md-preview h2 { margin: 30px 0 12px; font-size: 21px; }
    .md-preview h3 { margin: 22px 0 10px; font-size: 16px; }
    .md-preview p, .md-preview li { color: var(--muted); }
    .md-preview code { padding: 2px 5px; color: var(--blue-dark); background: var(--blue-soft); border-radius: 4px; }
    .md-preview pre { overflow: auto; padding: 15px; color: #e5e7eb; background: #111827; border-radius: 9px; }
    .md-preview pre code { padding: 0; color: inherit; background: transparent; }
    .md-preview table { width: 100%; margin: 16px 0; border-collapse: collapse; font-size: 11px; }
    .md-preview th, .md-preview td { padding: 8px; text-align: left; border: 1px solid var(--line); }
    .md-preview th { background: var(--soft); }
    footer { margin-top: 74px; padding-top: 24px; border-top: 1px solid var(--line); color: var(--faint); font-size: 11px; }
    @media (max-width: 1180px) { .shell { grid-template-columns: 220px minmax(0,1fr); } .right { display: none; } }
    @media (max-width: 840px) { .shell { display: block; } .left { display: none; } main { padding: 36px 18px 70px; } .hero, .cards, .split { grid-template-columns: 1fr; } .map { grid-template-columns: 1fr; } .node:not(:last-child)::after { content: "↓"; top: auto; right: 50%; bottom: -14px; transform: translateX(50%); } .pipeline { grid-template-columns: repeat(2, 1fr); } .stage-detail { grid-template-columns: 48px 1fr; } .stage-tag { display: none; } .role { grid-template-columns: 1fr; } .role p { border-left: 0; border-top: 1px solid var(--line); } .md-layout, .md-editor { grid-template-columns: 1fr; } .md-library { border-right: 0; border-bottom: 1px solid var(--line); } .md-pane + .md-pane { border-left: 0; border-top: 1px solid var(--line); } }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand"><div class="mark">L</div><div><strong>Fashion Lovart Nano Batch</strong><small>Codex 编排 · Lovart 批量白底试穿</small></div></div>
    <span class="pill">仓库随附 Skill</span>
  </header>
  <div class="shell">
    <aside class="left">
      <p class="rail-label">指南</p>
      <nav class="nav" id="sideNav">
        <a href="#overview" class="active"><span>概览</span><span>01</span></a>
        <a href="#architecture"><span>整体框架</span><span>02</span></a>
        <a href="#roles"><span>输入与交接</span><span>03</span></a>
        <a href="#workflow"><span>完整执行流程</span><span>04</span></a>
        <a href="#gates"><span>质量门禁</span><span>05</span></a>
        <a href="#nano"><span>Lovart 执行合同</span><span>06</span></a>
        <a href="#usage"><span>安装与调用</span><span>07</span></a>
        <a href="#mistakes"><span>阻塞与恢复</span><span>08</span></a>
        <a href="#markdown"><span>Markdown 原文</span><span>09</span></a>
        <a href="#completion"><span>完成标准</span><span>10</span></a>
      </nav>
    </aside>
    <main>
      <div class="content">
        <section id="overview">
          <span class="kicker">01 / OVERVIEW</span>
          <h1>Codex 先做线稿，Lovart 再做<span>白底图</span></h1>
          <p class="lede">\`fashion-lovart-nano-batch\` 是完整的日期文件夹批处理智能体：逐个扫描 SPU、在 Codex 侧生成并验收黑白线稿、把合格素材按固定角色交给 Lovart Nano Banana Pro、逐张复核 10 个独立候选图，并整理到月度画布中。</p>
          <div class="hero">
            <div class="hero-card"><b>10</b><p>每个合格 SPU 要有 10 张逐张复核通过的独立候选图。生成数量不等于合格数量。</p></div>
            <div class="metrics">
              <div class="metric accent"><b>2</b><span>线稿准备与 Lovart 最终试穿两个硬阶段</span></div>
              <div class="metric"><b>9</b><span>最多 8 张产品/搭配图 + 1 张姿势线稿</span></div>
              <div class="metric"><b>1</b><span>每月一个 Lovart 项目，按日期分区</span></div>
              <div class="metric"><b>0</b><span>不使用 Nano Banana 2，不消耗加速点数</span></div>
            </div>
          </div>
        </section>

        <section id="architecture">
          <span class="kicker">02 / ARCHITECTURE</span>
          <h2>完整智能体的职责边界</h2>
          <p>正式规则放在 \`skill/\`，HTML 是给新人阅读和培训的手册。这个智能体调用 \`fashion-nano-tryon\` 处理单款的线稿与 Prompt；自己负责整批 SPU 的调度、Lovart、质检和画布整理。</p>
          <div class="map">
            <div class="node"><small>INPUT</small><h3>日期文件夹</h3><p>发现所有含产品图的 SPU，预检缺失素材与可写路径。</p></div>
            <div class="node"><small>PHASE 1</small><h3>Codex 线稿准备</h3><p>调用单款流程，生成并验收 \`黑白线稿图\`。</p></div>
            <div class="node core"><small>CORE</small><h3>Batch 编排</h3><p>按 SPU 记录状态，准备上传包，跳过阻塞项而不中断全批。</p></div>
            <div class="node"><small>PHASE 2</small><h3>Lovart 生成</h3><p>使用 Nano Banana Pro，严格上传顺序，生成独立候选图。</p></div>
            <div class="node"><small>OUTPUT</small><h3>月度画布</h3><p>每个 SPU 10 张合格图；最终由人工审核与下载。</p></div>
          </div>
        </section>

        <section id="roles">
          <span class="kicker">03 / SOURCE ROLES</span>
          <h2>文件、上传包和结果各有固定位置</h2>
          <p>批处理不会依赖 Lovart 的全局图片编号。每个 SPU 都先建立本地记录和 ASCII 上传包，最后一张始终是姿势线稿。</p>
          <div class="roles">
            <div class="role"><code>产品图/</code><p>必填</p><p>主商品唯一来源；按数字顺序复制为 \`product_##\`。</p></div>
            <div class="role"><code>搭配图/</code><p>可选</p><p>逐图分类为配饰、下装或不使用，不能改写主商品。</p></div>
            <div class="role"><code>对标图</code><p>仅线稿阶段</p><p>用于提取外观锁与姿势；禁止进入 Lovart 最终上传包。</p></div>
            <div class="role"><code>黑白线稿图</code><p>最终上传最后一张</p><p>复制为 \`pose_lock_reference\`，只锁姿势、裁切与人体比例。</p></div>
            <div class="role"><code>_codex_outputs/</code><p>本地证据</p><p>保存线稿 Prompt、最终 Prompt、运行日志与阻塞原因。</p></div>
            <div class="role"><code>Lovart 月项目</code><p>人工复核与下载</p><p>同月共用一个项目，日期分区，SPU 参考图在上、结果在下。</p></div>
          </div>
        </section>

        <section id="workflow">
          <span class="kicker">04 / WORKFLOW</span>
          <h2>批处理的每个 SPU 都要走完这条链</h2>
          <p>点击步骤查看交付物。任何一个 SPU 失败都只记录并跳过该款，不能让整批工作停在一处。</p>
          <div class="pipeline" id="pipeline"></div>
          <div class="stage-detail">
            <div class="stage-no" id="stageNo">1</div>
            <div><h3 id="stageTitle">扫描与预检</h3><p id="stageText">发现有效 SPU，检查产品图、对标图/线稿、搭配图和可写路径。</p></div>
            <span class="stage-tag" id="stageTag">建立清单</span>
          </div>
        </section>

        <section id="gates">
          <span class="kicker">05 / GATES</span>
          <h2>门禁通过才允许进入 Lovart</h2>
          <div class="cards">
            <div class="card warn"><h3>Gate 1：线稿合格</h3><p>没有经过 Codex 侧 AI 线稿生成与视觉检查的 \`黑白线稿图\`，不能上传 Lovart。</p></div>
            <div class="card warn"><h3>Gate 2：模型合格</h3><p>右侧 Agent 面板必须明确选择 Nano Banana Pro；其他模型一律阻塞。</p></div>
            <div class="card warn"><h3>Gate 3：逐张候选合格</h3><p>每张图都要对照姿势线稿复核；只有 \`qualified_count >= 10\` 才完成。</p></div>
            <div class="card"><h3>队列不是完成</h3><p>队列中或合格数不足 10 的 SPU 状态为 \`queued-partial\`，记录后再决定是否继续。</p></div>
          </div>
        </section>

        <section id="nano">
          <span class="kicker">06 / NANO PROMPT</span>
          <h2>Lovart 只接收明确的角色合同</h2>
          <p>上传顺序与 Prompt 是同一份合同：产品在前、搭配在中、\`pose_lock_reference\` 最后。右侧面板只使用 Nano Banana Pro 和 \`3:4 · 4K\`。</p>
          <div class="codebox"><button class="copy" data-copy="schema">复制</button><span id="schemaText">LOVART EXECUTION INSTRUCTION
Use the right-side conversation panel in Agent image-generation mode with Nano Banana Pro.
Output size: 3:4 ratio, 4K resolution, pure white #FFFFFF background.
Generate exactly 10 separate standalone image outputs for this SPU.

REFERENCE ROLE CONTRACT
PRODUCT SOURCE: product_## uploaded first.
STYLING SOURCES: accessory_## and bottoms_## uploaded after products.
LINE_ART SOURCE: pose_lock_reference uploaded last; mandatory fixed pose skeleton.
DENIED SOURCES: benchmark photo, line-art garment design, Nano Banana 2, collage, grid, environment.

POSE LOCK
Reproduce pose_lock_reference 1:1. Do not change crop, camera angle, body angle, hands, bag/phone position, or leg stance.

BATCH QUALITY
Each output: one adult female model, one outfit, one standalone ecommerce photo. No collage, grid, contact sheet, or multi-person image.</span></div>
        </section>

        <section id="usage">
          <span class="kicker">07 / USAGE</span>
          <h2>安装和调用方式</h2>
          <div class="split">
            <div class="card"><h3>安装正式 Skill</h3><div class="codebox">mkdir -p ~/.codex/skills/fashion-lovart-nano-batch
rsync -a --delete \\
  image-skill/fashion-lovart-nano-batch/skill/ \\
  ~/.codex/skills/fashion-lovart-nano-batch/</div></div>
            <div class="card"><h3>典型调用</h3><div class="codebox">[$fashion-lovart-nano-batch] /Users/chenyiming/Desktop/Ai生图测试/6月17日</div></div>
          </div>
        </section>

        <section id="mistakes">
          <span class="kicker">08 / COMMON MISTAKES</span>
          <h2>阻塞时如何恢复，不把全批卡死</h2>
          <div class="cards">
            <div class="card danger"><h3>跳过 Codex 线稿</h3><p>不能直接把对标图交给 Lovart；缺少合格线稿的 SPU 必须停在 \`LINE_ART_PREP\`。</p></div>
            <div class="card danger"><h3>模型不匹配</h3><p>显示 Nano Banana 2 或其他模型时，记录 \`blocked:model-mismatch\`，不允许静默降级。</p></div>
            <div class="card danger"><h3>把 10 张做成拼图</h3><p>结果必须是 10 张独立图片；若出现网格或少图，改为候选编号的单张补图。</p></div>
            <div class="card danger"><h3>用生成数量冒充完成</h3><p>每张候选都要放大比对线稿。只在 \`qualified_count >= 10\` 后标记完成。</p></div>
          </div>
        </section>

        <section id="markdown">
          <span class="kicker">09 / MARKDOWN SOURCE CENTER</span>
          <h2>正式规则原文和本地预览</h2>
          <p>这里收录 \`skill/\` 下的正式 Markdown。页面里改动只保存在浏览器本地草稿，不会自动覆盖仓库文件。</p>
          <div class="md-workbench">
            <div class="md-head"><div><strong id="mdTitle">智能体主流程</strong><span class="md-path" id="mdPath">SKILL.md</span></div><div class="md-actions"><button class="md-btn" id="mdReset">恢复原文</button><button class="md-btn" id="mdCopy">复制 Markdown</button><button class="md-btn primary" id="mdDownload">下载当前 .md</button></div></div>
            <div class="md-layout">
              <aside class="md-library"><input class="md-search" id="mdSearch" type="search" placeholder="搜索文档…" aria-label="搜索 Markdown 文档"><div class="md-doc-list" id="mdDocList"></div></aside>
              <div class="md-editor"><div class="md-pane"><div class="md-pane-title"><span>MARKDOWN SOURCE</span><span id="mdDraftState">原始版本</span></div><textarea id="markdownInput" spellcheck="false"></textarea></div><div class="md-pane"><div class="md-pane-title"><span>LIVE PREVIEW</span><span>实时预览</span></div><article class="md-preview" id="markdownPreview"></article></div></div>
            </div>
          </div>
        </section>

        <section id="completion">
          <span class="kicker">10 / DEFINITION OF DONE</span>
          <h2>什么才算这个智能体完成了</h2>
          <div class="done">
            <div><span class="check">✓</span><span>所有有效 SPU 都已扫描，缺失素材和失败原因都记录在本地日志</span><code>preflight</code></div>
            <div><span class="check">✓</span><span>每个进入 Lovart 的 SPU 都有 Codex 侧验收通过的黑白线稿</span><code>line-art</code></div>
            <div><span class="check">✓</span><span>Lovart 上传顺序固定，最后一张为 \`pose_lock_reference\`，模型为 Nano Banana Pro</span><code>handoff</code></div>
            <div><span class="check">✓</span><span>每款达到 10 张独立、逐张复核通过的白底电商候选图，或明确标记 queued/blocked</span><code>quality</code></div>
            <div><span class="check">✓</span><span>月项目、日期分区、SPU 块、参考图和结果已整理，图片留给人工审核下载</span><code>canvas</code></div>
          </div>
        </section>
        <footer>正式行为以 <code>skill/SKILL.md</code> 和 <code>skill/references/</code> 为准。HTML 手册用于阅读、培训和本地预览。</footer>
      </div>
    </main>
    <aside class="right">
      <div class="context"><h3>运行规格</h3><div class="spec"><div><span>模型</span><strong>Nano Banana Pro</strong></div><div><span>比例</span><strong>3:4</strong></div><div><span>像素</span><strong>4K</strong></div><div><span>背景</span><strong>#FFFFFF</strong></div></div></div>
      <div class="context"><h3>一句话理解</h3><p>Codex 先锁线稿，Lovart 再生图；一款一包，一张一验，整批不中断。</p></div>
      <div class="context"><h3>真源提醒</h3><p>安装到 Codex 的目录只需要复制 <code>skill/</code> 内容。</p></div>
    </aside>
  </div>
  <script>
    const markdownDocuments = ${docsJson};
    const stages = [
      ['1', '扫描与预检', '扫描日期文件夹，建立 SPU 清单，验证素材、路径和输出目录。', '建立清单'],
      ['2', 'LINE_ART_PREP', '调用 fashion-nano-tryon，生成、保存并检查黑白线稿；失败只阻塞当前 SPU。', '硬门禁'],
      ['3', '素材分类与 Prompt', '拆解产品，分类搭配图，写入最终 Nano Banana Pro Prompt 和上传包。', '本地交付'],
      ['4', 'Lovart 上传', '进入月度项目的当天分区，产品在前、搭配在中、pose_lock_reference 最后。', '顺序硬锁'],
      ['5', '10 张候选图', '右侧 Agent 面板使用 Nano Banana Pro 生成独立候选；不使用加速点数。', '生成'],
      ['6', '逐张复核与整理', '逐张对照线稿，补齐 qualified_count >= 10，整理 SPU 块并记录队列/阻塞。', '完成或交接'],
    ];
    const pipeline = document.getElementById('pipeline');
    const stageNo = document.getElementById('stageNo');
    const stageTitle = document.getElementById('stageTitle');
    const stageText = document.getElementById('stageText');
    const stageTag = document.getElementById('stageTag');
    function setStage(index) {
      [...pipeline.children].forEach((button, i) => button.classList.toggle('active', i === index));
      const [no, title, text, tag] = stages[index];
      stageNo.textContent = no; stageTitle.textContent = title; stageText.textContent = text; stageTag.textContent = tag;
    }
    stages.forEach((stage, index) => {
      const button = document.createElement('button');
      button.className = 'stage' + (index === 0 ? ' active' : '');
      button.innerHTML = '<small>STAGE ' + stage[0] + '</small><strong>' + stage[1] + '</strong>';
      button.onclick = () => setStage(index);
      pipeline.appendChild(button);
    });
    document.querySelectorAll('[data-copy]').forEach(button => {
      button.onclick = async () => {
        const text = document.getElementById('schemaText').textContent;
        try { await navigator.clipboard.writeText(text); } catch {}
        const old = button.textContent; button.textContent = '已复制'; setTimeout(() => button.textContent = old, 1000);
      };
    });
    const escapeMd = value => value.replace(/[&<>"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[char]));
    function inlineMarkdown(value) {
      return escapeMd(value)
        .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\x60([^\\x60]+)\\x60/g, '<code>$1</code>')
        .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
    }
    function renderMarkdown(source) {
      const lines = source.replace(/\\r/g, '').split('\\n');
      let output = '', inCode = false, code = [], list = null, table = [];
      const closeList = () => { if (list) { output += '</' + list + '>'; list = null; } };
      const flushTable = () => {
        if (!table.length) return;
        const rows = table.map(row => row.split('|').slice(1, -1).map(cell => cell.trim()));
        if (rows.length > 1 && rows[1].every(cell => /^:?-{3,}:?$/.test(cell))) {
          output += '<table><thead><tr>' + rows[0].map(cell => '<th>' + inlineMarkdown(cell) + '</th>').join('') + '</tr></thead><tbody>' + rows.slice(2).map(row => '<tr>' + row.map(cell => '<td>' + inlineMarkdown(cell) + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
        } else output += table.map(row => '<p>' + inlineMarkdown(row) + '</p>').join('');
        table = [];
      };
      for (const line of lines) {
        if (line.startsWith('\\x60\\x60\\x60')) {
          closeList(); flushTable();
          if (inCode) { output += '<pre><code>' + escapeMd(code.join('\\n')) + '</code></pre>'; code = []; }
          inCode = !inCode; continue;
        }
        if (inCode) { code.push(line); continue; }
        if (/^\\|.*\\|$/.test(line)) { closeList(); table.push(line); continue; }
        flushTable();
        if (!line.trim()) { closeList(); continue; }
        const heading = line.match(/^(#{1,4})\\s+(.*)$/);
        if (heading) { closeList(); const level = heading[1].length; output += '<h' + level + '>' + inlineMarkdown(heading[2]) + '</h' + level + '>'; continue; }
        const unordered = line.match(/^\\s*[-*]\\s+(.*)$/);
        if (unordered) { if (list !== 'ul') { closeList(); list = 'ul'; output += '<ul>'; } output += '<li>' + inlineMarkdown(unordered[1]) + '</li>'; continue; }
        const ordered = line.match(/^\\s*\\d+\\.\\s+(.*)$/);
        if (ordered) { if (list !== 'ol') { closeList(); list = 'ol'; output += '<ol>'; } output += '<li>' + inlineMarkdown(ordered[1]) + '</li>'; continue; }
        closeList();
        if (line === '---') output += '<hr>';
        else if (line.startsWith('> ')) output += '<blockquote>' + inlineMarkdown(line.slice(2)) + '</blockquote>';
        else output += '<p>' + inlineMarkdown(line) + '</p>';
      }
      closeList(); flushTable();
      return output;
    }
    const state = { active: markdownDocuments[0].id };
    const mdList = document.getElementById('mdDocList'), mdInput = document.getElementById('markdownInput'), mdPreview = document.getElementById('markdownPreview');
    const mdTitle = document.getElementById('mdTitle'), mdPath = document.getElementById('mdPath'), mdDraftState = document.getElementById('mdDraftState');
    const storageKey = id => 'fashion-lovart-nano-batch-md-draft:' + id;
    const activeDocument = () => markdownDocuments.find(doc => doc.id === state.active);
    const currentValue = doc => localStorage.getItem(storageKey(doc.id)) ?? doc.content;
    function renderDocList(query = '') {
      const term = query.trim().toLowerCase();
      mdList.innerHTML = '';
      markdownDocuments.filter(doc => !term || doc.title.toLowerCase().includes(term) || doc.relativePath.toLowerCase().includes(term)).forEach(doc => {
        const button = document.createElement('button');
        button.className = 'md-doc' + (doc.id === state.active ? ' active' : '');
        button.innerHTML = '<strong>' + doc.title + '</strong><small>' + doc.relativePath + '</small>';
        button.onclick = () => loadMarkdownDocument(doc.id);
        mdList.appendChild(button);
      });
    }
    function loadMarkdownDocument(id) {
      state.active = id;
      const doc = activeDocument();
      mdTitle.textContent = doc.title; mdPath.textContent = doc.relativePath;
      mdInput.value = currentValue(doc); mdPreview.innerHTML = renderMarkdown(mdInput.value);
      mdDraftState.textContent = localStorage.getItem(storageKey(doc.id)) === null ? '原始版本' : '本地草稿已保存';
      renderDocList(document.getElementById('mdSearch').value);
    }
    let timer;
    mdInput.addEventListener('input', () => {
      const doc = activeDocument();
      mdPreview.innerHTML = renderMarkdown(mdInput.value);
      mdDraftState.textContent = '正在保存…';
      clearTimeout(timer);
      timer = setTimeout(() => { localStorage.setItem(storageKey(doc.id), mdInput.value); mdDraftState.textContent = '本地草稿已保存'; }, 250);
    });
    document.getElementById('mdSearch').addEventListener('input', event => renderDocList(event.target.value));
    document.getElementById('mdReset').onclick = () => {
      const doc = activeDocument();
      if (!confirm('恢复“' + doc.title + '”的原始 Markdown？当前浏览器草稿将被清除。')) return;
      localStorage.removeItem(storageKey(doc.id)); loadMarkdownDocument(doc.id);
    };
    document.getElementById('mdCopy').onclick = async event => {
      try { await navigator.clipboard.writeText(mdInput.value); } catch { mdInput.select(); document.execCommand('copy'); }
      const old = event.currentTarget.textContent; event.currentTarget.textContent = '已复制'; setTimeout(() => event.currentTarget.textContent = old, 1000);
    };
    document.getElementById('mdDownload').onclick = () => {
      const doc = activeDocument();
      const blob = new Blob([mdInput.value], {type:'text/markdown;charset=utf-8'});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = doc.fileName; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 500);
    };
    const sections = [...document.querySelectorAll('main section[id]')];
    const navLinks = [...document.querySelectorAll('#sideNav a')];
    addEventListener('scroll', () => {
      const current = sections.reduce((picked, section) => section.getBoundingClientRect().top < 120 ? section : picked, sections[0]);
      navLinks.forEach(link => link.classList.toggle('active', link.getAttribute('href') === '#' + current.id));
    }, {passive: true});
    renderDocList(); loadMarkdownDocument(markdownDocuments[0].id);
  </script>
</body>
</html>
`;

fs.mkdirSync(path.dirname(outputHtml), { recursive: true });
fs.writeFileSync(outputHtml, html);
fs.mkdirSync(path.dirname(siteOutputHtml), { recursive: true });
fs.writeFileSync(siteOutputHtml, html);
console.log(outputHtml);
console.log(siteOutputHtml);
