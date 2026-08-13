import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const toolsRoot = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(toolsRoot, '..');
const skillRoot = path.join(packageRoot, 'skill');
const sourceHtml = path.join(toolsRoot, 'handbook-template.html');
const outputHtml = path.join(packageRoot, 'docs', 'handbook.html');

const specs = [
  ['skill', '智能体主流程', 'SKILL.md', 'SKILL.md'],
  ['folder', '文件夹与图片角色', 'references/folder-contract.md', 'folder-contract.md'],
  ['schema', '提示词输出结构', 'references/prompt-output-schema.md', 'prompt-output-schema.md'],
  ['lovart', 'Lovart 执行规范', 'references/lovart-execution.md', 'lovart-execution.md'],
  ['front', '正面延展模板', 'references/templates/front.md', 'front.md'],
  ['side', '侧面延展模板', 'references/templates/side.md', 'side.md'],
  ['back', '背面延展模板', 'references/templates/back.md', 'back.md'],
  ['full', '全身延展模板', 'references/templates/full.md', 'full.md'],
];

const documents = specs.map(([id, title, relativePath, fileName]) => ({
  id,
  title,
  fileName,
  relativePath,
  content: fs.readFileSync(path.join(skillRoot, relativePath), 'utf8'),
}));

let html = fs.readFileSync(sourceHtml, 'utf8');

const editorCss = `
    .md-workbench {
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #fff;
      box-shadow: var(--shadow);
    }
    .md-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line-soft);
      background: var(--surface);
    }
    .md-head-copy { min-width: 0; }
    .md-head-copy strong { display: block; font-size: 14px; }
    .md-path { display: block; overflow: hidden; color: var(--faint); font: 10px/1.5 var(--mono); text-overflow: ellipsis; white-space: nowrap; }
    .md-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; }
    .md-btn {
      padding: 7px 10px;
      color: var(--muted);
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 7px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }
    .md-btn:hover { color: var(--accent-dark); border-color: #c9c5ff; }
    .md-btn.primary { color: #fff; background: var(--accent); border-color: var(--accent); }
    .md-layout { display: grid; grid-template-columns: 210px minmax(0, 1fr); min-height: 720px; }
    .md-library { padding: 12px; background: #fafbfc; border-right: 1px solid var(--line-soft); }
    .md-search {
      width: 100%;
      height: 36px;
      margin-bottom: 10px;
      padding: 0 11px;
      color: var(--ink);
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      outline: none;
      font-size: 12px;
    }
    .md-search:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
    .md-doc-list { display: grid; gap: 4px; }
    .md-doc {
      width: 100%;
      padding: 10px;
      text-align: left;
      color: var(--muted);
      background: transparent;
      border: 0;
      border-radius: 8px;
      cursor: pointer;
    }
    .md-doc:hover { color: var(--ink); background: #fff; }
    .md-doc.active { color: var(--accent-dark); background: var(--accent-soft); }
    .md-doc strong { display: block; font-size: 12px; }
    .md-doc small { display: block; margin-top: 3px; font: 9px/1.35 var(--mono); opacity: .7; }
    .md-editor { display: grid; grid-template-columns: 1fr 1fr; min-width: 0; }
    .md-pane { min-width: 0; }
    .md-pane + .md-pane { border-left: 1px solid var(--line-soft); }
    .md-pane-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 38px;
      padding: 0 12px;
      color: var(--faint);
      background: #fbfcfd;
      border-bottom: 1px solid var(--line-soft);
      font: 10px/1 var(--mono);
      letter-spacing: .05em;
    }
    .draft-state { color: var(--success); }
    #markdownInput {
      display: block;
      width: 100%;
      height: 682px;
      resize: none;
      padding: 18px;
      color: #dfe3ef;
      background: #171927;
      border: 0;
      outline: none;
      font: 12px/1.72 var(--mono);
      tab-size: 2;
    }
    .md-preview {
      height: 682px;
      overflow: auto;
      padding: 22px;
      color: var(--ink);
      background: #fff;
      font-size: 13px;
    }
    .md-preview h1 { margin: 0 0 24px; font-size: 30px; letter-spacing: -.035em; }
    .md-preview h2 { margin: 30px 0 12px; padding-top: 8px; font-size: 21px; }
    .md-preview h3 { margin: 22px 0 10px; font-size: 16px; }
    .md-preview p { margin: 0 0 12px; color: var(--muted); }
    .md-preview ul, .md-preview ol { margin: 0 0 16px; padding-left: 22px; color: var(--muted); }
    .md-preview li { margin: 4px 0; }
    .md-preview code { padding: 2px 5px; color: var(--accent-dark); background: var(--accent-soft); border-radius: 4px; font-size: .9em; }
    .md-preview pre { overflow: auto; margin: 14px 0 18px; padding: 15px; color: #e8eaf4; background: #171927; border-radius: 9px; }
    .md-preview pre code { padding: 0; color: inherit; background: transparent; }
    .md-preview blockquote { margin: 16px 0; padding: 3px 0 3px 14px; color: var(--muted); border-left: 3px solid var(--accent); }
    .md-preview table { width: 100%; margin: 16px 0; border-collapse: collapse; font-size: 11px; }
    .md-preview th, .md-preview td { padding: 8px; text-align: left; border: 1px solid var(--line); }
    .md-preview th { background: var(--surface); }
    .md-notice { display: flex; gap: 10px; margin: 0 0 16px; padding: 13px 14px; color: #664214; background: var(--warning-soft); border: 1px solid #efd5ad; border-radius: 10px; font-size: 12px; }
    @media (max-width: 980px) {
      .md-layout { grid-template-columns: 1fr; }
      .md-library { border-right: 0; border-bottom: 1px solid var(--line-soft); }
      .md-doc-list { grid-template-columns: repeat(2, 1fr); }
      .md-editor { grid-template-columns: 1fr; }
      .md-pane + .md-pane { border-left: 0; border-top: 1px solid var(--line-soft); }
      #markdownInput, .md-preview { height: 520px; }
      .md-head { align-items: flex-start; flex-direction: column; }
    }
`;
html = html.replace('\n  </style>', editorCss + '\n  </style>');

html = html.replace(
  '</head>',
  '  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22%3E%3Crect width=%2264%22 height=%2264%22 rx=%2214%22 fill=%22%23635bff%22/%3E%3Cpath d=%22M18 17h28v7H25v9h18v7H25v9h21v7H18z%22 fill=%22white%22/%3E%3C/svg%3E">\n</head>'
);

html = html.replace(
  '<a href="#completion"><span>完成标准</span><span>10</span></a>',
  '<a href="#markdown"><span>Markdown 编辑</span><span>10</span></a>\n        <a href="#completion"><span>完成标准</span><span>11</span></a>'
);

const editorSection = `
        <section id="markdown">
          <span class="section-kicker">10 / MARKDOWN SOURCE CENTER</span>
          <h2>完整规则原文，也能随时二次修改</h2>
          <p class="section-intro">这里收录当前 Skill 的全部 8 份 Markdown 源文件。修改会即时预览并自动保存为浏览器本地草稿，不会直接覆盖已安装的正式 Skill。</p>
          <div class="md-notice"><strong>安全说明</strong><span>页面内编辑只保存在当前浏览器的 localStorage。确认修改后，可复制或下载 Markdown，再人工替换正式文件。</span></div>
          <div class="md-workbench">
            <div class="md-head">
              <div class="md-head-copy"><strong id="mdTitle">智能体主流程</strong><span class="md-path" id="mdPath">SKILL.md</span></div>
              <div class="md-actions">
                <button class="md-btn" id="mdReset">恢复原文</button>
                <button class="md-btn" id="mdCopy">复制 Markdown</button>
                <button class="md-btn primary" id="mdDownload">下载当前 .md</button>
              </div>
            </div>
            <div class="md-layout">
              <aside class="md-library">
                <input class="md-search" id="mdSearch" type="search" placeholder="搜索文档…" aria-label="搜索 Markdown 文档">
                <div class="md-doc-list" id="mdDocList"></div>
              </aside>
              <div class="md-editor">
                <div class="md-pane">
                  <div class="md-pane-title"><span>MARKDOWN SOURCE</span><span class="draft-state" id="mdDraftState">原始版本</span></div>
                  <textarea id="markdownInput" spellcheck="false" aria-label="Markdown 编辑器"></textarea>
                </div>
                <div class="md-pane">
                  <div class="md-pane-title"><span>LIVE PREVIEW</span><span>实时预览</span></div>
                  <article class="md-preview" id="markdownPreview"></article>
                </div>
              </div>
            </div>
          </div>
        </section>

`;
html = html.replace('        <section id="completion">', editorSection + '        <section id="completion">');
html = html.replace('<span class="section-kicker">10 / DEFINITION OF DONE</span>', '<span class="section-kicker">11 / DEFINITION OF DONE</span>');

const docsJson = JSON.stringify(documents).replace(/<\/script/gi, '<\\/script');
const editorJs = `
    const markdownDocuments = ${docsJson};
    const markdownState = { active: markdownDocuments[0].id };
    const mdList = document.getElementById('mdDocList');
    const mdInput = document.getElementById('markdownInput');
    const mdPreview = document.getElementById('markdownPreview');
    const mdTitle = document.getElementById('mdTitle');
    const mdPath = document.getElementById('mdPath');
    const mdDraftState = document.getElementById('mdDraftState');
    const storageKey = id => 'fashion-lovart-md-draft:' + id;
    const escapeHtml = value => value.replace(/[&<>\"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[char]));
    function inlineMarkdown(value) {
      return escapeHtml(value)
        .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*([^*]+)\\*/g, '<em>$1</em>')
        .replace(/\\x60([^\\x60]+)\\x60/g, '<code>$1</code>')
        .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
    }
    function renderMarkdown(source) {
      const lines = source.replace(/\\r/g, '').split('\\n');
      let output = '', inCode = false, code = [], list = null, table = [];
      const closeList = () => { if (list) { output += '</' + list + '>'; list = null; } };
      const flushTable = () => {
        if (!table.length) return;
        const rows = table.map(row => row.split('|').slice(1,-1).map(cell => cell.trim()));
        if (rows.length > 1 && rows[1].every(cell => /^:?-{3,}:?$/.test(cell))) {
          output += '<table><thead><tr>' + rows[0].map(cell => '<th>' + inlineMarkdown(cell) + '</th>').join('') + '</tr></thead><tbody>' + rows.slice(2).map(row => '<tr>' + row.map(cell => '<td>' + inlineMarkdown(cell) + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
        } else output += table.map(row => '<p>' + inlineMarkdown(row) + '</p>').join('');
        table = [];
      };
      for (const line of lines) {
        if (line.startsWith('\\x60\\x60\\x60')) {
          closeList(); flushTable();
          if (inCode) { output += '<pre><code>' + escapeHtml(code.join('\\n')) + '</code></pre>'; code = []; }
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
        if (line.startsWith('> ')) output += '<blockquote>' + inlineMarkdown(line.slice(2)) + '</blockquote>';
        else if (line === '---') output += '<hr>';
        else output += '<p>' + inlineMarkdown(line) + '</p>';
      }
      closeList(); flushTable();
      if (inCode) output += '<pre><code>' + escapeHtml(code.join('\\n')) + '</code></pre>';
      return output;
    }
    function activeDocument() { return markdownDocuments.find(doc => doc.id === markdownState.active); }
    function currentValue(doc) { return localStorage.getItem(storageKey(doc.id)) ?? doc.content; }
    function renderDocList(query = '') {
      const term = query.trim().toLowerCase();
      mdList.innerHTML = '';
      markdownDocuments.filter(doc => !term || doc.title.toLowerCase().includes(term) || doc.relativePath.toLowerCase().includes(term)).forEach(doc => {
        const button = document.createElement('button');
        button.className = 'md-doc' + (doc.id === markdownState.active ? ' active' : '');
        button.innerHTML = '<strong>' + doc.title + '</strong><small>' + doc.relativePath + '</small>';
        button.onclick = () => loadMarkdownDocument(doc.id);
        mdList.appendChild(button);
      });
    }
    function loadMarkdownDocument(id) {
      markdownState.active = id;
      const doc = activeDocument();
      mdTitle.textContent = doc.title;
      mdPath.textContent = doc.relativePath;
      mdInput.value = currentValue(doc);
      mdPreview.innerHTML = renderMarkdown(mdInput.value);
      mdDraftState.textContent = localStorage.getItem(storageKey(doc.id)) === null ? '原始版本' : '本地草稿已保存';
      renderDocList(document.getElementById('mdSearch').value);
      mdInput.scrollTop = 0; mdPreview.scrollTop = 0;
    }
    let mdSaveTimer;
    mdInput.addEventListener('input', () => {
      const doc = activeDocument();
      mdPreview.innerHTML = renderMarkdown(mdInput.value);
      mdDraftState.textContent = '正在保存…';
      clearTimeout(mdSaveTimer);
      mdSaveTimer = setTimeout(() => { localStorage.setItem(storageKey(doc.id), mdInput.value); mdDraftState.textContent = '本地草稿已保存'; }, 250);
    });
    document.getElementById('mdSearch').addEventListener('input', event => renderDocList(event.target.value));
    document.getElementById('mdReset').onclick = () => {
      const doc = activeDocument();
      if (!confirm('恢复“' + doc.title + '”的原始 Markdown？当前浏览器草稿将被清除。')) return;
      localStorage.removeItem(storageKey(doc.id));
      loadMarkdownDocument(doc.id);
    };
    document.getElementById('mdCopy').onclick = async event => {
      try { await navigator.clipboard.writeText(mdInput.value); }
      catch { mdInput.focus(); mdInput.select(); document.execCommand('copy'); }
      const old = event.currentTarget.textContent; event.currentTarget.textContent = '已复制'; setTimeout(() => event.currentTarget.textContent = old, 1100);
    };
    document.getElementById('mdDownload').onclick = () => {
      const doc = activeDocument();
      const blob = new Blob([mdInput.value], {type:'text/markdown;charset=utf-8'});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = doc.fileName; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 500);
    };
    renderDocList();
    loadMarkdownDocument(markdownDocuments[0].id);

`;
html = html.replace('    const sections = [...document.querySelectorAll(\'main section[id]\')];', editorJs + "    const sections = [...document.querySelectorAll('main section[id]')];");

fs.writeFileSync(outputHtml, html);
console.log(outputHtml);
