import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const testRoot = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(testRoot, '..');
const handbook = path.join(packageRoot, 'docs', 'handbook.html');
const pagesCopy = path.resolve(packageRoot, '..', 'docs', 'fashion-lovart-nano-batch', 'index.html');

assert.ok(fs.existsSync(handbook), 'The package handbook must be generated.');
assert.ok(fs.existsSync(pagesCopy), 'The GitHub Pages handbook copy must be generated.');

const html = fs.readFileSync(handbook, 'utf8');
for (const expected of [
  'Codex 先做线稿，Lovart 再做',
  '白底图',
  'LINE_ART_PREP',
  'FINAL_TRYON',
  '10',
  'qualified_count',
  'Nano Banana Pro',
  'pose_lock_reference',
  'queued-partial',
]) {
  assert.ok(html.includes(expected), `Handbook is missing: ${expected}`);
}

console.log('fashion-lovart-nano-batch handbook contract passed');
