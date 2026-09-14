import { cpSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const source = resolve(root, 'static');
const output = resolve(root, 'dist');
const apiUrl = (process.env.VITE_API_URL || '').replace(/\/$/, '');

rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
mkdirSync(resolve(output, 'static'), { recursive: true });
cpSync(source, resolve(output, 'static'), { recursive: true });
cpSync(resolve(source, 'index.html'), resolve(output, 'index.html'));
writeFileSync(
  resolve(output, 'static', 'config.js'),
  `window.NOTICESENSE_API_URL = ${JSON.stringify(apiUrl)};\n`,
  'utf8',
);

console.log(`Built static SPA in ${output}`);
console.log(`API URL: ${apiUrl || '(same origin)'}`);
