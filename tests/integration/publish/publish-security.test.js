'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const { createPublishFixtureProject } = require('../../support/publish-fixture');
const { verifyArtifact } = require('../../../scripts/lib/publish');

const root = path.resolve(__dirname, '../../..');
const cli = path.join(root, 'scripts/publish-check.js');

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function copyDist(t, source) {
  const copy = fs.mkdtempSync(path.join(os.tmpdir(), 'publish-security-'));
  t.after(() => fs.rmSync(copy, { recursive: true, force: true }));
  fs.cpSync(source, copy, { recursive: true });
  return copy;
}

function readManifest(distDir) {
  return JSON.parse(fs.readFileSync(path.join(distDir, 'manifest.json'), 'utf8'));
}

function writeManifest(distDir, manifest) {
  fs.writeFileSync(path.join(distDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
}

function appendArtifact(distDir, relativePath, content) {
  const bytes = Buffer.from(content, 'utf8');
  const target = path.join(distDir, ...relativePath.split('/'));
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, bytes);
  const manifest = readManifest(distDir);
  manifest.artifacts.push({ path: relativePath, size: bytes.length, sha256: sha256(bytes) });
  writeManifest(distDir, manifest);
}

function appendManifestEntry(distDir, entry) {
  const manifest = readManifest(distDir);
  manifest.artifacts.push(entry);
  writeManifest(distDir, manifest);
}

function assertNoEcho(value, secret) {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  assert.equal(text.includes(secret), false, 'diagnostics must not echo the secret value');
}

function runCli(distDir) {
  const result = spawnSync(process.execPath, [cli, 'artifact', '--dist', distDir], {
    encoding: 'utf8',
  });
  const lines = result.stdout.trim().split(/\r?\n/);
  assert.equal(lines.length, 1, 'stdout must be one machine-readable line');
  return { ...result, output: JSON.parse(lines[0]) };
}

function tokenValue() {
  return ['ghp', '_', 'A'.repeat(24)].join('');
}

function privateKeyBlock() {
  return [
    ['-----BEGIN', 'OPENSSH PRIVATE KEY-----'].join(' '),
    'runtime-private-material',
    ['-----END', 'OPENSSH PRIVATE KEY-----'].join(' '),
  ].join('\n');
}

async function buildFixture(t) {
  const project = createPublishFixtureProject();
  t.after(() => project.cleanup());
  const built = await project.buildDist();
  assert.equal(built.ok, true, JSON.stringify(built.diagnostics));
  return { project, built };
}

test('credential file names are rejected without echoing their contents', async (t) => {
  const { project, built } = await buildFixture(t);
  const secret = tokenValue();
  const cases = [
    { relativePath: '.env', content: `api_key=${secret}\n` },
    { relativePath: 'assets/tls.pem', content: 'YOUR_CERTIFICATE_HERE\n' },
    { relativePath: 'assets/tls.key', content: 'YOUR_KEY_HERE\n' },
    { relativePath: 'assets/id_rsa', content: 'YOUR_KEY_HERE\n' },
    { relativePath: '.git-credentials', content: 'https://user:YOUR_PASSWORD_HERE@example.com\n' },
  ];

  for (const item of cases) {
    const dist = copyDist(t, built.distDir);
    project.writeCredentialFile(item.relativePath, item.content, dist);
    const result = verifyArtifact(dist);
    assert.equal(result.ok, false, item.relativePath);
    assert.equal(result.status, 'failed', item.relativePath);
    assert.equal(result.diagnostics[0].code, 'E_ARTIFACT_CREDENTIAL_PATH', item.relativePath);
    assert.equal(result.diagnostics[0].path, item.relativePath, item.relativePath);
    assertNoEcho(result, secret);
    assertNoEcho(result, 'YOUR_PASSWORD_HERE');
  }
});

test('token prefixes inside allowed files are rejected and never echoed', async (t) => {
  const { built } = await buildFixture(t);
  const secret = tokenValue();
  const dist = copyDist(t, built.distDir);
  appendArtifact(dist, 'assets/leak.txt', `token: ${secret}\n`);

  const result = verifyArtifact(dist);
  assert.equal(result.ok, false);
  assert.equal(result.status, 'failed');
  assert.equal(result.diagnostics[0].code, 'E_SECRET');
  assert.equal(result.diagnostics[0].path, 'assets/leak.txt');
  assertNoEcho(result, secret);

  const cliResult = runCli(dist);
  assert.equal(cliResult.status, 6, cliResult.stderr);
  assert.equal(cliResult.output.status, 'failed');
  assert.equal(cliResult.output.diagnostics[0].code, 'E_SECRET');
  assert.equal(cliResult.stderr.trim(), 'E_SECRET');
  assertNoEcho(cliResult.stdout, secret);
  assertNoEcho(cliResult.stderr, secret);
});

test('runtime private key blocks are rejected and never echoed', async (t) => {
  const { built } = await buildFixture(t);
  const dist = copyDist(t, built.distDir);
  appendArtifact(dist, 'assets/key-material.txt', `${privateKeyBlock()}\n`);

  const result = verifyArtifact(dist);
  assert.equal(result.ok, false);
  assert.equal(result.diagnostics[0].code, 'E_SECRET');
  assert.equal(result.diagnostics[0].path, 'assets/key-material.txt');
  assertNoEcho(result, 'runtime-private-material');
});

test('unsafe, absolute and duplicate manifest paths are rejected', async (t) => {
  const { built } = await buildFixture(t);
  const digest = sha256(Buffer.from('x'));
  const cases = [
    { name: 'parent traversal', entry: { path: '../outside.txt', size: 1, sha256: digest } },
    { name: 'absolute posix path', entry: { path: '/etc/passwd', size: 1, sha256: digest } },
    {
      name: 'absolute windows path',
      entry: { path: 'C:/Windows/win.ini', size: 1, sha256: digest },
    },
    { name: 'backslash separator', entry: { path: 'assets\\evil.js', size: 1, sha256: digest } },
    { name: 'control character', entry: { path: 'assets/\u0000evil.js', size: 1, sha256: digest } },
    { name: 'dot segment', entry: { path: 'assets/./evil.js', size: 1, sha256: digest } },
  ];

  for (const item of cases) {
    const dist = copyDist(t, built.distDir);
    appendManifestEntry(dist, item.entry);
    const result = verifyArtifact(dist);
    assert.equal(result.ok, false, item.name);
    assert.equal(result.diagnostics[0].code, 'E_ARTIFACT_PATH', item.name);
  }

  const duplicate = copyDist(t, built.distDir);
  appendManifestEntry(duplicate, { ...readManifest(duplicate).artifacts[0] });
  const duplicateResult = verifyArtifact(duplicate);
  assert.equal(duplicateResult.ok, false);
  assert.equal(duplicateResult.diagnostics[0].code, 'E_ARTIFACT_DUPLICATE');
});

test('scripts inside dist stay inert and are never executed', async (t) => {
  const project = createPublishFixtureProject();
  t.after(() => project.cleanup());
  const sentinel = path.join(os.tmpdir(), `skill-gallery-publish-sentinel-${crypto.randomUUID()}`);
  t.after(() => fs.rmSync(sentinel, { force: true }));

  const scriptDir = path.join(project.root, 'skills/complete-detail/scripts');
  fs.mkdirSync(scriptDir, { recursive: true });
  const scriptPath = path.join(scriptDir, 'publish-sentinel.js');
  fs.writeFileSync(
    scriptPath,
    `require('node:fs').writeFileSync(${JSON.stringify(sentinel)}, 'executed');\n`,
  );

  const built = await project.buildDist();
  assert.equal(built.ok, true, JSON.stringify(built.diagnostics));

  const expectedPath = `skills/complete-detail/${sha256(fs.readFileSync(scriptPath))}.bin`;
  assert.ok(readManifest(built.distDir).artifacts.some((item) => item.path === expectedPath));
  assert.equal(fs.existsSync(path.join(built.distDir, ...expectedPath.split('/'))), true);

  const result = verifyArtifact(built.distDir);
  assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
  assert.equal(fs.existsSync(sentinel), false);

  const cliResult = runCli(built.distDir);
  assert.equal(cliResult.status, 0, cliResult.stderr);
  assert.equal(cliResult.output.status, 'verified');
  assert.equal(fs.existsSync(sentinel), false);
});
