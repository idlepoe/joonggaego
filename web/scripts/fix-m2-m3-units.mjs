/**
 * assets/jsons/*.json 및 data/extracted/all.json 문자열 필드에서
 * 면적·부피 단위 m2 → m², m3 → m³ (숫자로 이어지는 m20 등은 제외)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..', '..');

function fixText(s) {
  return s
    .replace(/m3(?!\d)/g, 'm³')
    .replace(/m2(?!\d)/g, 'm²');
}

function walk(v) {
  if (typeof v === 'string') return fixText(v);
  if (Array.isArray(v)) return v.map(walk);
  if (v && typeof v === 'object') {
    const out = {};
    for (const [k, val] of Object.entries(v)) {
      out[k] = walk(val);
    }
    return out;
  }
  return v;
}

function processFile(absPath) {
  const raw = fs.readFileSync(absPath, 'utf8');
  const data = JSON.parse(raw);
  const next = walk(data);
  const out = JSON.stringify(next, null, 2) + '\n';
  if (out !== raw) {
    fs.writeFileSync(absPath, out, 'utf8');
    console.log('updated', path.relative(root, absPath));
  } else {
    console.log('unchanged', path.relative(root, absPath));
  }
}

const jsonDir = path.join(root, 'assets', 'jsons');
for (const name of fs.readdirSync(jsonDir)) {
  if (!name.endsWith('.json')) continue;
  processFile(path.join(jsonDir, name));
}

const allPath = path.join(root, 'data', 'extracted', 'all.json');
if (fs.existsSync(allPath)) {
  processFile(allPath);
}
