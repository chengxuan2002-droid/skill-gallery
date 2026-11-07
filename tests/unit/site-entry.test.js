'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.resolve(__dirname, '../..');
const indexPath = path.join(root, 'index.html');

function readFooter() {
  const html = fs.readFileSync(indexPath, 'utf8');
  const match = html.match(/<footer[\s\S]*?<\/footer>/i);
  return match ? match[0] : '';
}

test('site footer exposes a low-weight management link to the trusted repository', () => {
  const footer = readFooter();
  const link = footer.match(
    /<a\b[^>]*href="https:\/\/github\.com\/chengxuan2002-droid\/skill-gallery"[^>]*>([\s\S]*?)<\/a\s*>/i,
  );
  assert.ok(link, 'footer management link is missing');
  const tag = link[0];
  assert.match(tag, /target="_blank"/);
  assert.match(tag, /rel="noopener"/);
  assert.match(link[1].trim(), /管理|Manage/i);
});

test('public home page exposes no login form or upload input', () => {
  const html = fs.readFileSync(indexPath, 'utf8');
  assert.equal(/<form\b/i.test(html), false);
  assert.equal(/<input\b[^>]*type\s*=\s*["']file["']/i.test(html), false);
  assert.doesNotMatch(html, /type\s*=\s*["']password["']/i);
  assert.doesNotMatch(html, /上传|Upload/i);
});
