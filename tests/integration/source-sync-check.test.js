'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const { snapshotSkill } = require('../../scripts/lib/content-store');
const { checkSources, runSync } = require('../../scripts/lib/source-sync');
const {
  createSourceSyncProject,
  fakeReader,
  main,
  writeCatalog,
  writeSkill,
} = require('../support/source-sync-fixture');

const NOW = '2026-11-12T19:17:00+08:00';
const REVISION = 'a'.repeat(40);

function digestOf(project, value) {
  const result = snapshotSkill({ projectRoot: project.root, record: value });
  assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
  return result.snapshot.digest;
}

function setup(t, { directory = false, content = main('example') } = {}) {
  const project = createSourceSyncProject(t);
  const skill = writeSkill(project, 'example', { directory, content });
  const digest = digestOf(project, skill.record);
  const value = {
    ...skill.record,
    source_tracking: {
      ...skill.record.source_tracking,
      last_synced_revision: REVISION,
      last_synced_digest: digest,
      synced_at: '2026-11-01T00:00:00+08:00',
    },
  };
  writeCatalog(project, value);
  project.initRemote();
  return { project, skill, digest, record: value };
}

test('check reports unchanged without writing or committing', (t) => {
  const { project, skill } = setup(t);
  const head = project.head();
  const checked = checkSources({
    projectRoot: project.root,
    now: NOW,
    reader: fakeReader({
      revision: REVISION,
      files: skill.files,
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
  });
  assert.equal(checked.ok, true);
  assert.equal(checked.results[0].status, 'unchanged');
  assert.equal(checked.results[0].checked_at, NOW);
  assert.equal(checked.results[0].resolved_revision, REVISION);
  assert.equal(checked.results[0].license_status, 'present');
  assert.equal(project.head(), head);
  assert.equal(project.git('status', '--porcelain'), '');
});

test('check reports candidate for changed bytes and is idempotent', (t) => {
  const { project } = setup(t);
  const changed = main('example', 'New body');
  const reader = fakeReader({
    revision: 'b'.repeat(40),
    files: { 'example.md': Buffer.from(changed) },
    licenseFiles: { LICENSE: Buffer.from('MIT\n') },
  });
  const first = runSync({ projectRoot: project.root, reader, now: NOW });
  assert.equal(first.exitCode, 0);
  assert.equal(first.report.sources[0].status, 'candidate');
  assert.equal(first.report.changed, false);
  assert.equal(first.report.commit_status, 'not_applicable');
  assert.equal(project.git('status', '--porcelain'), '');

  const second = runSync({ projectRoot: project.root, reader, now: NOW });
  assert.equal(second.report.sources[0].status, 'candidate');
  assert.equal(second.report.sources[0].content_digest, first.report.sources[0].content_digest);
  assert.equal(project.git('status', '--porcelain'), '');
});

test('one source failure does not stop another source check', (t) => {
  const { project } = setup(t);
  const other = writeSkill(project, 'other');
  const otherRecord = {
    ...other.record,
    source_tracking: {
      ...other.record.source_tracking,
      last_synced_digest: digestOf(project, other.record),
    },
  };
  writeCatalog(project, otherRecord);
  const reader = {
    resolve(source) {
      if (source.path.includes('other')) {
        return { ok: false, code: 'E_SOURCE_TIMEOUT', message: 'timeout' };
      }
      return {
        ok: true,
        revision: REVISION,
        files: new Map([['example.md', Buffer.from(main('example'))]]),
        licenseFiles: new Map([['LICENSE', Buffer.from('MIT\n')]]),
      };
    },
  };
  const checked = checkSources({ projectRoot: project.root, now: NOW, reader });
  assert.equal(checked.ok, true);
  const bySlug = Object.fromEntries(checked.results.map((item) => [item.slug, item]));
  assert.equal(bySlug.example.status, 'unchanged');
  assert.equal(bySlug.other.status, 'failed');
  assert.equal(bySlug.other.error_code, 'E_SOURCE_TIMEOUT');
});

test('disabled and unconfigured sources are reported only when targeted', (t) => {
  const project = createSourceSyncProject(t);
  const skill = writeSkill(project, 'example');
  writeCatalog(project, {
    ...skill.record,
    source_tracking: { ...skill.record.source_tracking, enabled: false },
  });
  project.initRemote();

  const disabled = runSync({
    projectRoot: project.root,
    slug: 'example',
    reader: fakeReader({ files: skill.files }),
    now: NOW,
  });
  assert.equal(disabled.report.sources[0].status, 'unsupported');
  assert.equal(disabled.report.sources[0].error_code, 'E_SOURCE_DISABLED');

  const batch = runSync({
    projectRoot: project.root,
    reader: fakeReader({ files: skill.files }),
    now: NOW,
  });
  assert.deepEqual(batch.report.sources, []);

  const missing = runSync({
    projectRoot: project.root,
    slug: 'missing',
    reader: fakeReader({ files: skill.files }),
    now: NOW,
  });
  assert.equal(missing.report.sources[0].status, 'unsupported');
  assert.equal(missing.report.sources[0].error_code, 'E_SOURCE_NOT_FOUND');
});

test('truncated and unavailable sources fail closed with stable codes', (t) => {
  const { project } = setup(t);
  for (const [reader, code] of [
    [fakeReader({ truncated: true }), 'E_SOURCE_TRUNCATED'],
    [fakeReader({ error: { code: 'E_SOURCE_UNAVAILABLE' } }), 'E_SOURCE_UNAVAILABLE'],
    [fakeReader({ error: { code: 'E_SOURCE_RATE_LIMIT' } }), 'E_SOURCE_RATE_LIMIT'],
  ]) {
    const checked = checkSources({ projectRoot: project.root, now: NOW, reader });
    assert.equal(checked.results[0].status, 'failed');
    assert.equal(checked.results[0].error_code, code);
  }
  assert.equal(project.git('status', '--porcelain'), '');
  assert.equal(project.head(), project.remoteHead());
  assert.equal(fs.existsSync(path.join(project.root, 'skills', 'example.md')), true);
});
