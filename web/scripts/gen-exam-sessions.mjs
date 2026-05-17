import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(webRoot, '..');
const jsonDir = path.join(repoRoot, 'assets', 'jsons');

const SESSION_FILE = /^\d{4}-\d{2}-\d{2}\.json$/;

function main() {
  const names = fs.readdirSync(jsonDir);
  const stems = names
    .filter((n) => SESSION_FILE.test(n))
    .map((n) => n.replace(/\.json$/i, ''))
    .sort((a, b) => b.localeCompare(a, 'en'));

  const out = { sessions: stems };
  const outPath = path.join(jsonDir, 'exam-sessions.json');
  fs.writeFileSync(outPath, `${JSON.stringify(out, null, 2)}\n`, 'utf8');
  console.log(`Wrote ${outPath} (${stems.length} sessions)`);
}

main();
