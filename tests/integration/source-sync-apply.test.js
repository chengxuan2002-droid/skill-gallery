'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const { snapshotSkill } = require('../../scripts/lib/content-store');
const { runSync } = require('../../scripts/lib/source-sync');
const {
  createSourceSyncProject,
  fakeReader,
  main,
  writeCatalog,
  writeSkill,
} = require('../support/source-sync-fixture');

const NOW = '2026-11-12T19:17:00+08:00';
const REVISION = 'a'.repeat(40);
const NEXT = 'b'.repeat(40);

function digestOf(project, value) {
  const result = snapshotSkill({ projectRoot: project.root, record: value });
  assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
  return result.snapshot.digest;
}

function setup(t, options = {}) {
  const project = createSourceSyncProject(t);
  const skill = writeSkill(project, 'example', options);
  const digest = digestOf(project, skill.record);
  const value = {
    ...skill.record,
    declared_version: '1.0.0',
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

function remoteJson(project, relativePath) {
  return JSON.parse(project.remoteShow(relativePath));
}

test('apply replaces a directory, removes deleted attachments and keeps site metadata', (t) => {
  const { project, record } = setup(t, { directory: true });
  const files = {
    'SKILL.md': Buffer.from(main('example', 'Version 2')),
    LICENSE: Buffer.from('MIT\n'),
    'references/new.md': Buffer.from('# New\n'),
  };
  const synced = runSync({
    projectRoot: project.root,
    reader: fakeReader({ revision: NEXT, files }),
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(synced.exitCode, 0, JSON.stringify(synced.report));
  assert.equal(synced.report.changed, true);
  assert.equal(synced.report.commit_status, 'committed');
  assert.equal(synced.report.sources[0].status, 'updated');
  assert.equal(synced.report.sources[0].resolved_revision, NEXT);

  const remote = remoteJson(project, 'catalog/example.json');
  assert.equal(remote.slug, record.slug);
  assert.equal(remote.display_name, record.display_name);
  assert.deepEqual(remote.tags, record.tags);
  assert.equal(remote.notes, record.notes);
  assert.equal(remote.usage, record.usage);
  assert.equal(remote.declared_version, '1.0.0');
  assert.equal(remote.source_tracking.last_synced_revision, NEXT);
  assert.equal(remote.source_tracking.last_synced_digest, synced.report.sources[0].content_digest);
  assert.equal(remote.source_tracking.last_synced_license.path, 'LICENSE');
  assert.match(remote.source_tracking.last_synced_license.sha256, /^[0-9a-f]{64}$/);
  assert.equal(remote.source_tracking.synced_at, NOW);

  const names = project.remoteFiles();
  assert.deepEqual(names, [
    '.gitattributes',
    '.gitignore',
    'catalog/example.json',
    'skills/example/LICENSE',
    'skills/example/SKILL.md',
    'skills/example/references/new.md',
  ]);
  assert.equal(names.includes('skills/example/references/note.md'), false);
  assert.equal(project.git('rev-list', '--count', 'origin/main'), '2');
});

test('apply detects content changes when the declared version is unchanged', (t) => {
  const { project } = setup(t);
  const synced = runSync({
    projectRoot: project.root,
    reader: fakeReader({
      revision: NEXT,
      files: { 'example.md': Buffer.from(main('example', 'Same version, new body')) },
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(synced.exitCode, 0, JSON.stringify(synced.report));
  assert.equal(synced.report.sources[0].status, 'updated');
  const remote = remoteJson(project, 'catalog/example.json');
  assert.equal(remote.declared_version, '1.0.0');
  assert.equal(remote.source_tracking.last_synced_digest, synced.report.sources[0].content_digest);
  assert.equal(remote.source_tracking.last_synced_license.path, 'LICENSE');
  assert.match(remote.source_tracking.last_synced_license.sha256, /^[0-9a-f]{64}$/);
  assert.equal(project.remoteShow('skills/example.md').includes('Same version, new body'), true);
});

test('apply switches a single file to a directory without changing the slug', (t) => {
  const { project } = setup(t);
  const synced = runSync({
    projectRoot: project.root,
    reader: fakeReader({
      revision: NEXT,
      files: {
        'SKILL.md': Buffer.from(main('example', 'Directory now')),
        LICENSE: Buffer.from('MIT\n'),
        'references/a.md': Buffer.from('# A\n'),
      },
    }),
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(synced.exitCode, 0, JSON.stringify(synced.report));
  const remote = remoteJson(project, 'catalog/example.json');
  assert.equal(remote.content_path, 'skills/example/SKILL.md');
  const names = project.remoteFiles();
  assert.equal(names.includes('skills/example.md'), false);
  assert.equal(names.includes('skills/example/SKILL.md'), true);
  assert.equal(names.includes('skills/example/references/a.md'), true);
  assert.equal(project.git('rev-list', '--count', 'origin/main'), '2');
});

test('second apply is a no-op after the pushed commit', (t) => {
  const { project } = setup(t);
  const reader = fakeReader({
    revision: NEXT,
    files: { 'example.md': Buffer.from(main('example', 'Once')) },
    licenseFiles: { LICENSE: Buffer.from('MIT\n') },
  });
  const first = runSync({
    projectRoot: project.root,
    reader,
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(first.exitCode, 0, JSON.stringify(first.report));
  project.git('pull', '--ff-only', 'origin', 'main');
  const head = project.remoteHead();
  const second = runSync({
    projectRoot: project.root,
    reader,
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(second.exitCode, 0, JSON.stringify(second.report));
  assert.equal(second.report.changed, false);
  assert.equal(second.report.sources[0].status, 'unchanged');
  assert.equal(project.remoteHead(), head);
  assert.equal(project.git('rev-list', '--count', 'origin/main'), '2');
});

test('local project root is not modified by a pushed sync', (t) => {
  const { project, record } = setup(t);
  const before = project.head();
  runSync({
    projectRoot: project.root,
    reader: fakeReader({
      revision: NEXT,
      files: { 'example.md': Buffer.from(main('example', 'Remote only')) },
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(project.head(), before);
  assert.equal(project.readRecord('example').source_tracking.last_synced_revision, REVISION);
  assert.equal(record.source_tracking.last_synced_revision, REVISION);
});
