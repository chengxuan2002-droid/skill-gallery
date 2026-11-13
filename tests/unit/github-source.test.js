'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  createGhReader,
  fetchSource,
  findLicense,
  validateSource,
} = require('../../scripts/lib/github-source');

const SHA_A = 'a'.repeat(40);
const SHA_B = 'b'.repeat(40);

function source(overrides = {}) {
  return {
    provider: 'github',
    repository: 'owner/repository',
    path: 'skills/example',
    ref_policy: 'branch',
    ref: 'main',
    enabled: true,
    ...overrides,
  };
}

function reader({ revision = SHA_A, files = {}, modes = {}, truncated = false, error } = {}) {
  return {
    resolve() {
      if (error) return { ok: false, ...error };
      return { ok: true, revision, truncated, files: new Map(Object.entries(files)), modes };
    },
  };
}

function mainFile() {
  return { 'SKILL.md': Buffer.from('---\nname: example\n---\n\n# Example\n') };
}

test('validateSource accepts structured branch, release and pinned sources', () => {
  assert.equal(validateSource(source()), null);
  assert.equal(validateSource(source({ ref_policy: 'release', ref: 'latest' })), null);
  assert.equal(validateSource(source({ ref_policy: 'pinned', ref: SHA_A })), null);
});

test('validateSource rejects URLs, unsafe paths and invalid pinned revisions', () => {
  for (const invalid of [
    source({ repository: 'https://github.com/owner/repository' }),
    source({ repository: 'owner' }),
    source({ path: '../outside' }),
    source({ path: '/absolute' }),
    source({ path: 'skills\\example' }),
    source({ ref_policy: 'tag' }),
    source({ ref_policy: 'pinned', ref: 'main' }),
    source({ ref: '' }),
  ]) {
    const diagnostic = validateSource(invalid);
    assert.ok(diagnostic, JSON.stringify(invalid));
    assert.equal(diagnostic.code, 'E_SCHEMA');
  }
});

test('fetchSource returns immutable revision, bytes, modes and license', () => {
  const files = {
    ...mainFile(),
    LICENSE: Buffer.from('MIT\n'),
  };
  const result = fetchSource({
    source: source(),
    reader: reader({ files, modes: { 'SKILL.md': '100644', LICENSE: '100644' } }),
  });
  assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
  assert.equal(result.revision, SHA_A);
  assert.equal(result.files.get('SKILL.md').toString('utf8').includes('# Example'), true);
  assert.equal(result.modes.get('SKILL.md'), '100644');
  assert.equal(result.license.path, 'LICENSE');
});

test('fetchSource rejects truncated trees and links or submodules', () => {
  const truncated = fetchSource({
    source: source(),
    reader: reader({ files: mainFile(), truncated: true }),
  });
  assert.equal(truncated.ok, false);
  assert.equal(truncated.diagnostics[0].code, 'E_SOURCE_TRUNCATED');

  for (const mode of ['120000', '160000']) {
    const linked = fetchSource({
      source: source(),
      reader: reader({ files: mainFile(), modes: { 'SKILL.md': mode } }),
    });
    assert.equal(linked.ok, false, mode);
    assert.equal(linked.diagnostics[0].code, 'E_SOURCE_LINK');
  }
});

test('fetchSource enforces file count, total bytes and main document limits', () => {
  const many = {};
  for (let index = 0; index < 501; index += 1) many[`file-${index}.md`] = Buffer.from('x');
  const count = fetchSource({ source: source(), reader: reader({ files: many }) });
  assert.equal(count.ok, false);
  assert.equal(count.diagnostics[0].code, 'E_LIMIT');

  const huge = { 'SKILL.md': Buffer.alloc(20 * 1024 * 1024 + 1) };
  const total = fetchSource({ source: source(), reader: reader({ files: huge }) });
  assert.equal(total.ok, false);
  assert.equal(total.diagnostics[0].code, 'E_LIMIT');

  const main = { 'SKILL.md': Buffer.alloc(1024 * 1024 + 1) };
  const mainLimit = fetchSource({
    source: source(),
    reader: reader({ files: main }),
    mainRelative: 'SKILL.md',
  });
  assert.equal(mainLimit.ok, false);
  assert.equal(mainLimit.diagnostics[0].code, 'E_LIMIT');
});

test('findLicense picks a deterministic license file in the source subtree', () => {
  assert.equal(findLicense(new Map([['docs/readme.md', Buffer.from('x')]])), null);
  const license = findLicense(
    new Map([
      ['NOTICE', Buffer.from('notice')],
      ['LICENSE', Buffer.from('license')],
      ['references/a.md', Buffer.from('a')],
    ]),
  );
  assert.equal(license.path, 'LICENSE');
});

test('createGhReader resolves branch, release and pinned revisions', () => {
  const calls = [];
  const execute = (requestPath) => {
    calls.push(requestPath);
    if (requestPath.endsWith('/git/ref/heads/main')) return { object: { sha: SHA_A } };
    if (requestPath.endsWith('/releases/latest'))
      return { tag_name: 'v1.0.0', draft: false, prerelease: false };
    if (requestPath.endsWith('/git/ref/tags/v1.0.0'))
      return { object: { type: 'commit', sha: SHA_B } };
    if (requestPath.includes('/git/trees/')) return { truncated: false, tree: [] };
    throw new Error(`unexpected request ${requestPath}`);
  };
  const gh = createGhReader({ execute });

  assert.equal(gh.resolveRevision(source()), SHA_A);
  assert.equal(gh.resolveRevision(source({ ref_policy: 'release', ref: 'latest' })), SHA_B);
  assert.equal(gh.resolveRevision(source({ ref_policy: 'pinned', ref: SHA_A })), SHA_A);
  assert.ok(calls.length >= 3);
});

test('createGhReader maps missing release to unavailable and retries transient failures', () => {
  let attempts = 0;
  const missing = createGhReader({
    execute() {
      const error = new Error('gh failed');
      error.stderr = 'gh: Not Found (HTTP 404)';
      throw error;
    },
  });
  assert.throws(
    () => missing.resolveRevision(source({ ref_policy: 'release', ref: 'latest' })),
    (error) => error.code === 'E_SOURCE_UNAVAILABLE',
  );

  const transient = createGhReader({
    retries: 3,
    execute() {
      attempts += 1;
      if (attempts < 3) {
        const error = new Error('gh failed');
        error.stderr = 'gh: Server Error (HTTP 502)';
        throw error;
      }
      return { object: { sha: SHA_A } };
    },
  });
  assert.equal(transient.resolveRevision(source()), SHA_A);
  assert.equal(attempts, 3);
});

test('fetchSource diagnostics stay sanitized', () => {
  const result = fetchSource({
    source: source(),
    reader: reader({ error: { message: 'token=ghp_secret response body' } }),
  });
  assert.equal(result.ok, false);
  assert.equal(JSON.stringify(result.diagnostics).includes('ghp_secret'), false);
});
