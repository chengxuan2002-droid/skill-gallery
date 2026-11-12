'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const test = require('node:test');

const { checkSources, runSync } = require('../../scripts/lib/source-sync');
const { createBaseline, pushBaseline } = require('../../scripts/lib/skill-cli/workspace');
const {
  createSourceSyncProject,
  fakeReader,
  main,
  syncedProject,
  writeCatalog,
  writeSkill,
} = require('../support/source-sync-fixture');

const NOW = '2026-11-12T19:17:00+08:00';
const NEXT = 'b'.repeat(40);

test('missing license blocks replacement and keeps current content', (t) => {
  const { project, skill } = syncedProject(t, { directory: true });
  const head = project.remoteHead();
  const checked = checkSources({
    projectRoot: project.root,
    now: NOW,
    reader: fakeReader({
      revision: NEXT,
      files: {
        'SKILL.md': Buffer.from(main('example', 'No license')),
        'references/note.md': Buffer.from('# Note\n'),
      },
    }),
  });
  assert.equal(checked.results[0].status, 'policy_blocked');
  assert.equal(checked.results[0].error_code, 'E_LICENSE_MISSING');
  assert.equal(checked.results[0].license_status, 'missing');
  assert.equal(project.remoteHead(), head);
  assert.equal(
    fs.readFileSync(path.join(project.skillsDir, 'example', 'SKILL.md'), 'utf8'),
    main('example'),
  );
  assert.equal(skill.record.slug, 'example');
});

test('changed license blocks replacement', (t) => {
  const { project } = syncedProject(t, { directory: true });
  const checked = checkSources({
    projectRoot: project.root,
    now: NOW,
    reader: fakeReader({
      revision: NEXT,
      files: {
        'SKILL.md': Buffer.from(main('example', 'Changed license')),
        LICENSE: Buffer.from('Apache-2.0\n'),
        'references/note.md': Buffer.from('# Note\n'),
      },
    }),
  });
  assert.equal(checked.results[0].status, 'policy_blocked');
  assert.equal(checked.results[0].error_code, 'E_LICENSE_CHANGED');
  assert.equal(checked.results[0].license_status, 'changed');
});

test('local modifications produce conflict instead of overwrite', (t) => {
  const { project } = syncedProject(t);
  fs.appendFileSync(path.join(project.skillsDir, 'example.md'), '\nLocal edit.\n');
  const checked = checkSources({
    projectRoot: project.root,
    now: NOW,
    reader: fakeReader({
      revision: NEXT,
      files: { 'example.md': Buffer.from(main('example', 'Remote edit')) },
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
  });
  assert.equal(checked.results[0].status, 'conflict');
  assert.equal(checked.results[0].error_code, 'E_CONFLICT_LOCAL');
  assert.equal(
    fs.readFileSync(path.join(project.skillsDir, 'example.md'), 'utf8').includes('Local edit'),
    true,
  );
});

test('first sync with different content requires a baseline', (t) => {
  const project = createSourceSyncProject(t);
  const skill = writeSkill(project, 'example');
  writeCatalog(project, skill.record);
  project.initRemote();
  const checked = checkSources({
    projectRoot: project.root,
    now: NOW,
    reader: fakeReader({
      revision: NEXT,
      files: { 'example.md': Buffer.from(main('example', 'First candidate')) },
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
  });
  assert.equal(checked.results[0].status, 'conflict');
  assert.equal(checked.results[0].error_code, 'E_CONFLICT_BASELINE');
  const head = project.remoteHead();
  assert.equal(project.remoteHead(), head);
});

test('first sync with identical content records a baseline commit', (t) => {
  const project = createSourceSyncProject(t);
  const skill = writeSkill(project, 'example');
  writeCatalog(project, skill.record);
  project.initRemote();
  const synced = runSync({
    projectRoot: project.root,
    reader: fakeReader({
      revision: NEXT,
      files: { 'example.md': Buffer.from(main('example')) },
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
    apply: true,
    push: true,
    now: NOW,
  });
  assert.equal(synced.exitCode, 0, JSON.stringify(synced.report));
  assert.equal(synced.report.changed, true);
  assert.equal(synced.report.sources[0].status, 'updated');
  const remote = JSON.parse(project.remoteShow('catalog/example.json'));
  assert.equal(remote.source_tracking.last_synced_revision, NEXT);
  assert.equal(remote.source_tracking.last_synced_digest, synced.report.sources[0].content_digest);
  assert.equal(remote.display_name, 'Site example');
  assert.equal(remote.notes, 'Site notes');
});

test('invalid candidate paths fail closed', (t) => {
  const { project } = syncedProject(t);
  const checked = checkSources({
    projectRoot: project.root,
    now: NOW,
    reader: fakeReader({
      revision: NEXT,
      files: { '../evil.md': Buffer.from('x') },
      licenseFiles: { LICENSE: Buffer.from('MIT\n') },
    }),
  });
  assert.equal(checked.results[0].status, 'failed');
  assert.equal(checked.results[0].error_code, 'E_PATH');
});

test('push refuses a remote baseline that advanced', (t) => {
  const { project } = syncedProject(t);
  const baseline = createBaseline(project.root);
  const clone = fs.mkdtempSync(path.join(os.tmpdir(), 'source-sync-advance-'));
  t.after(() => fs.rmSync(clone, { recursive: true, force: true }));
  try {
    execFileSync('git', ['clone', '-q', project.remoteDir, clone], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    execFileSync('git', ['config', 'user.name', 'Advance'], { cwd: clone });
    execFileSync('git', ['config', 'user.email', 'advance@example.invalid'], { cwd: clone });
    fs.writeFileSync(path.join(clone, 'remote.txt'), 'advanced\n');
    execFileSync('git', ['add', 'remote.txt'], { cwd: clone });
    execFileSync('git', ['commit', '-q', '-m', 'advance'], { cwd: clone });
    execFileSync('git', ['push', '-q', 'origin', 'main'], { cwd: clone });
    assert.throws(
      () => pushBaseline(baseline.root, baseline.branch, { expectedHead: baseline.head }),
      (error) => error.code === 'E_CONFLICT',
    );
  } finally {
    baseline.cleanup();
  }
});

test('unknown slug and disabled source do not write', (t) => {
  const { project } = syncedProject(t);
  const head = project.remoteHead();
  const result = runSync({
    projectRoot: project.root,
    slug: 'missing',
    apply: true,
    push: true,
    now: NOW,
    reader: fakeReader({}),
  });
  assert.equal(result.exitCode, 0);
  assert.equal(result.report.changed, false);
  assert.equal(project.remoteHead(), head);
});
