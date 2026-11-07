'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const { parseArgs } = require('../../scripts/lib/skill-cli/args');
const { EXIT_CODES, exitCodeFor, serializeResult } = require('../../scripts/lib/skill-cli/output');

const SHA = 'a'.repeat(40);

test('parses valid preview/add/import/replace/status invocations', () => {
  const preview = parseArgs(['preview', 'skills/example.md', '--meta', 'catalog/example.json']);
  assert.equal(preview.ok, true, JSON.stringify(preview.diagnostics));
  assert.equal(preview.command, 'preview');
  assert.equal(preview.input, 'skills/example.md');
  assert.equal(preview.metaPath, 'catalog/example.json');
  assert.equal(preview.publish, false);
  assert.equal(preview.wait, false);
  assert.equal(preview.json, true);

  const add = parseArgs([
    'add',
    'skills/example',
    '--meta',
    'catalog/example.json',
    '--publish',
    '--wait',
  ]);
  assert.equal(add.ok, true, JSON.stringify(add.diagnostics));
  assert.equal(add.publish, true);
  assert.equal(add.wait, true);

  const imported = parseArgs([
    'import',
    '--repo',
    'owner/repository',
    '--path',
    'skills/example',
    '--ref',
    'main',
    '--meta',
    'catalog/example.json',
  ]);
  assert.equal(imported.ok, true, JSON.stringify(imported.diagnostics));
  assert.deepEqual(imported.source, {
    repository: 'owner/repository',
    path: 'skills/example',
    ref: 'main',
    refPolicy: 'branch',
  });

  const replace = parseArgs([
    'replace',
    'example',
    'skills/new',
    '--expected-revision',
    SHA,
    '--meta',
    'catalog/example.json',
  ]);
  assert.equal(replace.ok, true, JSON.stringify(replace.diagnostics));
  assert.equal(replace.slug, 'example');
  assert.equal(replace.expectedRevision, SHA);
  assert.equal(replace.metaPath, 'catalog/example.json');

  const status = parseArgs(['status', '--run', '12345']);
  assert.equal(status.ok, true, JSON.stringify(status.diagnostics));
  assert.equal(status.runId, '12345');
});

test('rejects invalid invocations with stable usage or schema diagnostics', () => {
  const cases = [
    { argv: [], code: 'E_USAGE' },
    { argv: ['unknown'], code: 'E_USAGE' },
    { argv: ['add', 'skills/example'], code: 'E_USAGE' },
    { argv: ['preview', 'skills/example', '--meta', 'meta.json', '--publish'], code: 'E_USAGE' },
    { argv: ['add', 'skills/example', '--meta', 'meta.json', '--wait'], code: 'E_USAGE' },
    {
      argv: ['import', '--repo', 'owner/repo', '--path', 'skills/x', '--meta', 'meta.json'],
      code: 'E_USAGE',
    },
    {
      argv: ['replace', 'example', 'skills/new', '--expected-revision', 'not-a-sha'],
      code: 'E_SCHEMA',
    },
    { argv: ['replace', 'BadSlug', 'skills/new', '--expected-revision', SHA], code: 'E_SCHEMA' },
    { argv: ['replace', 'example', 'skills/new'], code: 'E_USAGE' },
    { argv: ['status'], code: 'E_USAGE' },
    { argv: ['status', '--run', '123', '--publish'], code: 'E_USAGE' },
    { argv: ['add', 'skills/example', '--meta', 'meta.json', '--unknown'], code: 'E_USAGE' },
  ];

  for (const item of cases) {
    const result = parseArgs(item.argv);
    assert.equal(result.ok, false, item.argv.join(' '));
    assert.equal(result.diagnostics[0].code, item.code, item.argv.join(' '));
  }
});

test('maps statuses and stable error codes to contract exit codes', () => {
  assert.equal(EXIT_CODES.OK, 0);
  assert.equal(EXIT_CODES.USAGE, 2);
  assert.equal(EXIT_CODES.UNAUTHORIZED, 3);
  assert.equal(EXIT_CODES.CONFLICT, 4);
  assert.equal(EXIT_CODES.SOURCE, 5);
  assert.equal(EXIT_CODES.BUILD, 6);
  assert.equal(EXIT_CODES.DEPLOY, 7);
  assert.equal(EXIT_CODES.TIMEOUT, 8);

  for (const status of ['ok', 'previewed', 'noop', 'submitted', 'published']) {
    assert.equal(exitCodeFor({ status }), 0, status);
  }
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_CONFLICT' }] }), 4);
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_UNAUTHORIZED' }] }), 3);
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_SOURCE' }] }), 5);
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_BUILD' }] }), 6);
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_DEPLOY' }] }), 7);
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_TIMEOUT' }] }), 8);
  assert.equal(exitCodeFor({ status: 'failed', errors: [{ code: 'E_SCHEMA' }] }), 2);
});

test('serializes one line of closed fields and never echoes secret values', () => {
  const line = serializeResult({
    status: 'failed',
    slug: 'example',
    content_revision: null,
    content_status: 'failed',
    deploy_status: 'pending',
    commit_sha: null,
    run_url: null,
    public_url: null,
    errors: [
      { code: 'E_SECRET', path: 'skills/example.md', message: 'SECRET-02', token: 'ghp_RUNTIME' },
    ],
    token: 'ghp_RUNTIME',
  });
  assert.equal(line.includes('\n'), false);
  const parsed = JSON.parse(line);
  assert.deepEqual(Object.keys(parsed).sort(), [
    'commit_sha',
    'content_revision',
    'content_status',
    'deploy_status',
    'errors',
    'public_url',
    'run_url',
    'slug',
    'status',
  ]);
  assert.equal(JSON.stringify(parsed).includes('ghp_RUNTIME'), false);
  assert.deepEqual(Object.keys(parsed.errors[0]).sort(), ['code', 'message', 'path']);
});
