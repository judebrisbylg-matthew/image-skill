import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const toolsRoot = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(toolsRoot, '..');
const skillRoot = path.join(packageRoot, 'skill');
const outputHtml = path.join(packageRoot, 'docs', 'handbook.html');
const siteOutputHtml = path.join(packageRoot, '..', 'docs', 'fashion-nano-tryon', 'index.html');

const documents = [
  ['skill', '智能体主流程', 'SKILL.md', 'SKILL.md'],
  ['roles', '图片角色合同', 'references/source-role-contract.md', 'source-role-contract.md'],
  ['gates', '阶段确认门槛', 'references/workflow-gates.md', 'workflow-gates.md'],
  ['schema', 'Nano Prompt 结构', 'references/nano-prompt-schema.md', 'nano-prompt-schema.md'],
  ['checklist', '质检清单', 'references/quality-checklist.md', 'quality-checklist.md'],
  ['example', '示例流程', 'examples/sample-workflow.md', 'sample-workflow.md'],
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
  <meta name="description" content="fashion-nano-tryon Skill 可视化工作手册" />
  <title>Fashion Nano Tryon · 可视化工作手册</title>
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
    <div class="brand"><div class="mark">N</div><div><strong>Fashion Nano Tryon</strong><small>线稿辅助白底试穿 · 可视化工作手册</small></div></div>
    <span class="pill">仓库随附 Skill</span>
  </header>
  <div class="shell">
    <aside class="left">
      <p class="rail-label">指南</p>
      <nav class="nav" id="sideNav">
        <a href="#overview" class="active"><span>概览</span><span>01</span></a>
        <a href="#architecture"><span>整体框架</span><span>02</span></a>
        <a href="#roles"><span>图片角色</span><span>03</span></a>
        <a href="#workflow"><span>六阶段流程</span><span>04</span></a>
        <a href="#gates"><span>确认门槛</span><span>05</span></a>
        <a href="#nano"><span>Nano Prompt</span><span>06</span></a>
        <a href="#usage"><span>安装使用</span><span>07</span></a>
        <a href="#mistakes"><span>常见错误</span><span>08</span></a>
        <a href="#markdown"><span>Markdown 原文</span><span>09</span></a>
        <a href="#completion"><span>完成标准</span><span>10</span></a>
      </nav>
    </aside>
    <main>
      <div class="content">
        <section id="overview">
          <span class="kicker">01 / OVERVIEW</span>
          <h1>把多参考图试穿，拆成<span>可控流程</span></h1>
          <p class="lede">\`fashion-nano-tryon\` 用黑白线稿先锁住对标图的动作、构图和人体比例，再把产品图、配饰图、下装图和人物外观锁合成 Nano Banana Pro 可执行的白底电商试穿 prompt。它不是直接生图工具，而是一个防混图的提示词工作流。</p>
          <div class="hero">
            <div class="hero-card"><b>3:4</b><p>默认输出 \`3:4 ratio, 4K output\`，纯白 \`#FFFFFF\` 背景，服务 Nano Banana Pro 的高端电商目录图。</p></div>
            <div class="metrics">
              <div class="metric accent"><b>6</b><span>从角色映射到最终 prompt 的阶段</span></div>
              <div class="metric"><b>3</b><span>不可跳过的确认门槛</span></div>
              <div class="metric"><b>1</b><span>主商品唯一来源：产品图</span></div>
              <div class="metric"><b>0</b><span>不继承对标图原服装设计</span></div>
            </div>
          </div>
        </section>

        <section id="architecture">
          <span class="kicker">02 / ARCHITECTURE</span>
          <h2>仓库、Skill、线稿和 Nano 的关系</h2>
          <p>正式规则放在 \`skill/\`，HTML 只是给新人看的工作手册。不要把手册里的本地草稿当成正式规则。</p>
          <div class="map">
            <div class="node"><small>INPUT</small><h3>产品 / 搭配 / 对标图</h3><p>多张参考图先按角色分配，避免一股脑混合。</p></div>
            <div class="node"><small>STAGE 1</small><h3>对标图转线稿</h3><p>保留姿势、裁切、手位、比例，弱化颜色和服装细节。</p></div>
            <div class="node core"><small>CORE</small><h3>fashion-nano-tryon</h3><p>执行确认门槛、产品拆解和最终 prompt 组织。</p></div>
            <div class="node"><small>FINAL</small><h3>Nano Banana Pro Prompt</h3><p>用短块结构锁定来源合同和防混图规则。</p></div>
            <div class="node"><small>OUTPUT</small><h3>白底电商试穿图</h3><p>单人、单图、纯白背景、高端棚拍质感。</p></div>
          </div>
        </section>

        <section id="roles">
          <span class="kicker">03 / SOURCE ROLES</span>
          <h2>每张图只做自己该做的事</h2>
          <p>这套框架的关键是“角色合同”。Nano Banana Pro 很擅长融合，所以 prompt 必须先把哪些来源能控制什么写死。</p>
          <div class="roles">
            <div class="role"><code>PRODUCT SOURCE</code><p>产品多角度图</p><p>只控制最终主商品的身份、款式、颜色、结构、材质、工艺和体量。</p></div>
            <div class="role"><code>BENCHMARK SOURCE</code><p>对标模特图</p><p>生成线稿前用于分析动作、构图和人物外观锁。</p></div>
            <div class="role"><code>LINE_ART SOURCE</code><p>批准后的黑白线稿</p><p>只控制姿势、身体比例、手位、腿位、拍摄距离、裁切和空间关系。</p></div>
            <div class="role"><code>MODEL APPEARANCE LOCK</code><p>对标图提取文字</p><p>只控制肤色、可见皮肤一致性、发色、发型和基础外观。</p></div>
            <div class="role"><code>ACCESSORY / BOTTOMS</code><p>搭配图</p><p>只控制明确提供的配饰和下装，不允许改写主商品。</p></div>
            <div class="role"><code>DENIED SOURCES</code><p>禁止来源</p><p>对标图原服装、线稿原服装、人台比例、随机配饰、随机肤色、文字和背景。</p></div>
          </div>
        </section>

        <section id="workflow">
          <span class="kicker">04 / WORKFLOW</span>
          <h2>六阶段流程，一步都别省</h2>
          <p>点击阶段可以查看该阶段到底交付什么。这里故意慢半拍，因为线稿确认是整套控制力的地基。</p>
          <div class="pipeline" id="pipeline"></div>
          <div class="stage-detail">
            <div class="stage-no" id="stageNo">0</div>
            <div><h3 id="stageTitle">参考图角色映射</h3><p id="stageText">确认产品图、对标图、配饰图、下装图各自的控制边界。</p></div>
            <span class="stage-tag" id="stageTag">确认来源</span>
          </div>
        </section>

        <section id="gates">
          <span class="kicker">05 / GATES</span>
          <h2>三个门槛，专门拦住失控</h2>
          <div class="cards">
            <div class="card warn"><h3>Gate 1：先确认线稿策略</h3><p>没有确认线稿策略和人物外观锁定前，不写线稿 prompt。</p></div>
            <div class="card warn"><h3>Gate 2：先确认线稿可用</h3><p>没有批准线稿前，不做产品拆解和最终 prompt。</p></div>
            <div class="card warn"><h3>Gate 3：先确认产品和最终策略</h3><p>没有确认产品拆解和最终白底策略前，不输出 Nano Banana Pro prompt。</p></div>
            <div class="card"><h3>批处理例外</h3><p>\`fashion-lovart-nano-batch\` 自动调用时可以默认确认，但仍要产出完整阶段内容。</p></div>
          </div>
        </section>

        <section id="nano">
          <span class="kicker">06 / NANO PROMPT</span>
          <h2>最终 prompt 用短块结构，不写成长作文</h2>
          <p>短块结构能帮助 Nano Banana Pro 明确每个来源的职责，尤其适合多参考图、防混图、保商品身份的场景。</p>
          <div class="codebox"><button class="copy" data-copy="schema">复制</button><span id="schemaText">FINAL OUTPUT
Create one high-end fashion ecommerce studio photo, 3:4 ratio, 4K output, pure white #FFFFFF background.

REFERENCE ROLE CONTRACT
PRODUCT SOURCE: ...
LINE_ART SOURCE: ...
MODEL APPEARANCE LOCK: ...
ACCESSORY SOURCES: ...
BOTTOMS SOURCE: ...
DENIED SOURCES: ...

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
...</span></div>
        </section>

        <section id="usage">
          <span class="kicker">07 / USAGE</span>
          <h2>安装和调用方式</h2>
          <div class="split">
            <div class="card"><h3>安装正式 Skill</h3><div class="codebox">mkdir -p ~/.codex/skills/fashion-nano-tryon
rsync -a --delete \\
  image-skill/fashion-nano-tryon/skill/ \\
  ~/.codex/skills/fashion-nano-tryon/</div></div>
            <div class="card"><h3>典型调用</h3><div class="codebox">[$fashion-nano-tryon] 图1-图4是产品图；图5-图8是搭配图；图9是对标图。执行流程</div></div>
          </div>
        </section>

        <section id="mistakes">
          <span class="kicker">08 / COMMON MISTAKES</span>
          <h2>新人最容易踩的坑</h2>
          <div class="cards">
            <div class="card danger"><h3>跳过黑白线稿</h3><p>Nano 会直接混合对标图、商品图和搭配图，动作、肤色、构图都容易漂。</p></div>
            <div class="card danger"><h3>把对标图原服装带入最终图</h3><p>对标图只控制姿势和外观锁，不控制主商品款式。</p></div>
            <div class="card danger"><h3>用线稿推断肤色</h3><p>线稿没有颜色，肤色必须来自对标图阶段提取的文字锁定。</p></div>
            <div class="card danger"><h3>写旧尺寸</h3><p>默认写 \`3:4 ratio, 4K output\`，不要写回 \`2048x3072\` 或 \`2:3\`。</p></div>
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
          <h2>什么才算这个 skill 做对了</h2>
          <div class="done">
            <div><span class="check">✓</span><span>保留线稿策略、线稿 prompt、批准线稿、产品拆解、最终策略和最终 prompt</span><code>workflow</code></div>
            <div><span class="check">✓</span><span>主商品只来自产品图，对标图和线稿都不能改写商品身份</span><code>product</code></div>
            <div><span class="check">✓</span><span>姿势、裁切、身体比例和手位来自线稿</span><code>line-art</code></div>
            <div><span class="check">✓</span><span>肤色和头发来自人物外观锁，不从黑白线稿随机推断</span><code>appearance</code></div>
            <div><span class="check">✓</span><span>最终 prompt 是 Nano Banana Pro 短块结构，规格为 3:4 / 4K / #FFFFFF</span><code>final</code></div>
          </div>
        </section>
        <footer>正式行为以 <code>skill/SKILL.md</code> 和 <code>skill/references/</code> 为准。HTML 手册用于阅读、培训和本地预览。</footer>
      </div>
    </main>
    <aside class="right">
      <div class="context"><h3>运行规格</h3><div class="spec"><div><span>模型</span><strong>Nano Banana Pro</strong></div><div><span>比例</span><strong>3:4</strong></div><div><span>像素</span><strong>4K</strong></div><div><span>背景</span><strong>#FFFFFF</strong></div></div></div>
      <div class="context"><h3>一句话理解</h3><p>商品图控衣服，线稿控动作，对标图控肤色发型，搭配图控配饰下装。</p></div>
      <div class="context"><h3>真源提醒</h3><p>安装到 Codex 的目录只需要复制 <code>skill/</code> 内容。</p></div>
    </aside>
  </div>
  <script>
    const markdownDocuments = ${docsJson};
    const stages = [
      ['0', '角色映射', '确认产品图、对标图、配饰图、下装图各自的控制边界。', '确认来源'],
      ['1', '线稿策略', '分析对标图，锁定姿势、比例、裁切、手位、腿位和人物外观。', '必须确认'],
      ['2', '线稿 Prompt', '输出中英文黑白铅笔线稿 prompt，等待用户生成或上传批准线稿。', '等待线稿'],
      ['3', '产品拆解', '只从产品图拆解主商品，不借用线稿或对标图服装细节。', '必须确认'],
      ['4', '最终策略', '确认来源合同、防混图规则、配饰可见性和白底输出规格。', '必须确认'],
      ['5', '最终 Prompt', '输出 Nano Banana Pro 结构化英文 prompt。', '最终交付'],
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
    const storageKey = id => 'fashion-nano-md-draft:' + id;
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
