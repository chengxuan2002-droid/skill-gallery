'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const { createReport, renderSummary } = require('../../scripts/lib/source-sync-report');
const { checkSources, runSync, selectTargets } = require('../../scripts/lib/source-sync');
const { parseArgs } = require('../../scripts/sync-skills');
const { makeTempProject } = require('../support/fixtures');

const NOW = '2026-11-12T19:17:00+08:00';

function report(overrides = {}) {
  return createReport({
    runId: 'run-1',
    trigger: 'schedule',
    startedAt: NOW,
    finishedAt: NOW,
    sources: [
      {
        slug: 'example',
        source: {
          provider: 'github',
          repository: 'owner/repository',
          path: 'skills/example',
          ref_policy: 'branch',
          ref: 'main',
          enabled: true,
          last_synced_digest: 'should-not-leak',
        },
        status: 'unchanged',
        resolved_revision: 'a'.repeat(40),
        content_digest: 'b'.repeat(64),
        previous_digest: 'b'.repeat(64),
        license_status: 'present',
        error_code: null,
        checked_at: NOW,
        token: 'ghp_secret',
      },
    ],
    ...overrides,
  });
}

test('report keeps only closed fields and stable statuses', () => {
  const value = report();
  assert.equal(value.run_id, 'run-1');
  assert.equal(value.trigger, 'schedule');
  assert.equal(value.commit_status, 'not_applicable');
  assert.equal(value.content_status, 'noop');
  assert.equal(value.deploy_status, 'pending');
  assert.equal(value.sources[0].slug, 'example');
  assert.equal(value.sources[0].source.repository, 'owner/repository');
  assert.equal('last_synced_digest' in value.sources[0].source, false);
  assert.equal('token' in value.sources[0], false);
});

test('invalid report values fail closed without throwing', () => {
  const value = createReport({
    trigger: 'unknown',
    commitStatus: 'unknown',
    contentStatus: 'unknown',
    deployStatus: 'unknown',
    sources: [{ status: 'unknown', license_status: 'unknown', checked_at: 'not-a-date' }],
  });
  assert.equal(value.trigger, 'manual');
  assert.equal(value.commit_status, 'failed');
  assert.equal(value.content_status, 'failed');
  assert.equal(value.deploy_status, 'pending');
  assert.equal(value.sources[0].status, 'failed');
  assert.equal(value.sources[0].license_status, 'not_applicable');
  assert.equal(value.sources[0].checked_at, null);
});

test('summary renders status but not credentials or response bodies', () => {
  const summary = renderSummary(
    report({
      errors: [{ code: 'E_CONFLICT', path: 'catalog/example.json', message: 'token=ghp_secret' }],
    }),
  );
  assert.match(summary, /Source sync/);
  assert.match(summary, /unchanged/);
  assert.match(summary, /E_CONFLICT/);
  assert.equal(summary.includes('ghp_secret'), false);
  assert.equal(summary.includes('should-not-leak'), false);
});

test('selectTargets returns unsupported for unknown slug and skips disabled sources', () => {
  const now = NOW;
  const unknown = selectTargets([], 'missing', now);
  assert.equal(unknown.result.status, 'unsupported');
  assert.equal(unknown.result.error_code, 'E_SOURCE_NOT_FOUND');

  const records = [
    { slug: 'enabled', source_tracking: { enabled: true } },
    { slug: 'disabled', source_tracking: { enabled: false } },
    { slug: 'none', source_tracking: null },
  ];
  const selected = selectTargets(records, null, now);
  assert.deepEqual(
    selected.targets.map((item) => item.slug),
    ['enabled'],
  );
});

test('checkSources and runSync return catalog failures with exit 2', () => {
  const project = makeTempProject();
  try {
    const checked = checkSources({ projectRoot: project.root, now: NOW });
    assert.equal(checked.ok, false);
    const synced = runSync({ projectRoot: project.root, now: NOW });
    assert.equal(synced.exitCode, 2);
    assert.equal(synced.report.commit_status, 'failed');
  } finally {
    project.cleanup();
  }
});

test('CLI accepts supported options and rejects unsafe combinations', () => {
  const valid = parseArgs(['--apply', '--push', '--slug', 'example', '--json']);
  assert.equal(valid.ok, true);
  assert.equal(valid.options.slug, 'example');
  assert.equal(valid.options.apply, true);
  assert.equal(valid.options.push, true);

  assert.equal(parseArgs(['--push']).code, 'E_USAGE');
  assert.equal(parseArgs(['--slug', '../x']).code, 'E_USAGE');
  assert.equal(parseArgs(['--report']).code, 'E_USAGE');
  assert.equal(parseArgs(['--url', 'https://example.com']).code, 'E_USAGE');
  assert.equal(parseArgs(['--help']).options.help, true);
});

test('runSync without apply never writes or commits', () => {
  const project = makeTempProject();
  try {
    fs.mkdirSync(path.join(project.root, 'catalog'));
    fs.writeFileSync(
      path.join(project.root, 'catalog', 'example.json'),
      `${JSON.stringify(
        {
          schemaVersion: 1,
          slug: 'example',
          display_name: 'Example',
          description: 'Example',
          content_path: 'skills/example.md',
          tags: [],
          platforms: [],
          allowed_dot_paths: [],
          source_tracking: {
            provider: 'github',
            repository: 'owner/repository',
            path: 'skills/example',
            ref_policy: 'branch',
            ref: 'main',
            enabled: true,
            last_synced_revision: null,
            last_synced_digest: null,
            synced_at: null,
          },
        },
        null,
        2,
      )}\n`,
    );
    fs.writeFileSync(
      path.join(project.root, 'skills', 'example.md'),
      '---\nname: example\n---\n\n# Example\n',
    );
    const reader = {
      resolve() {
        return {
          ok: true,
          revision: 'a'.repeat(40),
          files: new Map([['example.md', Buffer.from('---\nname: example\n---\n\n# Example\n')]]),
          licenseFiles: new Map([['LICENSE', Buffer.from('MIT\n')]]),
        };
      },
    };
    const synced = runSync({ projectRoot: project.root, reader, now: NOW });
    assert.equal(synced.exitCode, 0);
    assert.equal(synced.report.changed, false);
    assert.equal(synced.report.sources[0].status, 'unchanged');
  } finally {
    project.cleanup();
  }
});
