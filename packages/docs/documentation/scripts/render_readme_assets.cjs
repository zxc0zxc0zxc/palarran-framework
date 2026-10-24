#!/usr/bin/env node
// Render reviewed original SVG diagrams. Requires an existing browser environment.
const fs = require('fs');
const path = require('path');

async function main() {
  if (!process.env.PALARRAN_PLAYWRIGHT || !process.env.PALARRAN_CHROMIUM) {
    throw new Error('Set PALARRAN_PLAYWRIGHT and PALARRAN_CHROMIUM to existing local installations. No dependencies are installed automatically.');
  }
  const { chromium } = require(process.env.PALARRAN_PLAYWRIGHT);
  let sourceRoot = __dirname;
  while (!fs.existsSync(path.join(sourceRoot, 'assets', 'architecture.svg'))) {
    const parent = path.dirname(sourceRoot);
    if (parent === sourceRoot) throw new Error('Palarran asset root not found.');
    sourceRoot = parent;
  }
  const assets = path.join(sourceRoot, 'assets');
  const browser = await chromium.launch({ executablePath: process.env.PALARRAN_CHROMIUM, headless: true });
  try {
    for (const name of ['architecture', 'development-pipeline', 'framework-features', 'parallel-worktrees', 'agent-message-bus']) {
      const page = await browser.newPage({ viewport: { width: 1800, height: 1060 }, deviceScaleFactor: 1 });
      try {
        await page.route('**/*', route => route.abort());
        const svg = fs.readFileSync(path.join(assets, name + '.svg'), 'utf8');
        await page.setContent('<html><body style="margin:0;background:transparent">' + svg + '</body></html>');
        await page.locator('body > svg').screenshot({ path: path.join(assets, name + '.png'), omitBackground: true });
        process.stdout.write(name + ': rendered\n');
      } finally { await page.close(); }
    }
  } finally { await browser.close(); }
}
main().catch(error => { process.stderr.write(error.message + '\n'); process.exitCode = 1; });
