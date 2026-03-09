#!/usr/bin/env node
/**
 * Generate a pageless PDF from case-studies content
 * -------------------------------------------------
 * Uses Puppeteer to render case-studies-pdf-content.html as a single continuous
 * PDF page (no visible page breaks). Run: npm run pdf:case-studies
 */

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
import { fileURLToPath } from 'url';
import { dirname, join, resolve } from 'path';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const ROOT = resolve(__dirname, '..');
const INPUT_HTML = join(ROOT, 'case-studies-pdf-content.html');
const OUTPUT_PDF = join(ROOT, 'case-studies.pdf');

async function main() {
  if (!existsSync(INPUT_HTML)) {
    console.error('Missing case-studies-pdf-content.html');
    process.exit(1);
  }

  const puppeteer = require('puppeteer');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  // Load the HTML file
  const fileUrl = `file://${INPUT_HTML}`;
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });

  // Generate multi-page PDF with proper A4 pages (one case study per page)
  await page.pdf({
    path: OUTPUT_PDF,
    printBackground: true,
    format: 'A4',
    margin: { top: '20mm', right: '20mm', bottom: '20mm', left: '20mm' },
    displayHeaderFooter: false,
  });

  await browser.close();
  console.log(`Pageless PDF saved: ${OUTPUT_PDF}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
