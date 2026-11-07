'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const {
  createSkillCliProject,
  remoteBytes,
  remoteFiles,
  remoteHead,
  remoteTree,
  sampleRecord,
  writeDirectoryCandidate,
  writeSingleCandidate,
} = require('../support/skill-cli-fixture');

const root = path.resolve(__dirname, '../..');
const cli = path.join(root, 'scripts/skill-cli.js');

function run(project, args) {
  const result = spawnSync(process.execPath, [cli, ...args], {
    cwd: project.root,
    encoding: 'utf8',
  });
  const lines = result.stdout.trim().split(/\r?\n/);
  assert.equal(lines.length, 1, 'stdout must be one machine-readable line');
  return { ...result, output: JSON.parse(lines[0]) };
}

function remoteJson(project, relativePath) {
  return JSON.parse(remoteBytes(project, relativePath).toString('utf8'));
}

test('replace keeps metadata and removes attachments deleted from the new content', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeDirectoryCandidate(project, 'cli-pack', {
    display_name: 'Original Pack',
  });
  fs.writeFileSync(path.join(candidate.contentPath, 'references/old.md'), '# Old\n\nRemove me.\n');
  const added = run(project, [
    'add',
    candidate.contentPath,
    '--meta',
    candidate.metaPath,
    '--publish',
  ]);
  assert.equal(added.status, 0, added.stderr);
  const baseline = remoteHead(project);
  assert.ok(remoteFiles(project).includes('skills/cli-pack/references/old.md'));

  fs.appendFileSync(path.join(candidate.contentPath, 'SKILL.md'), '\nReplaced body.\n');
  fs.rmSync(path.join(candidate.contentPath, 'references/old.md'));

  const replaced = run(project, [
    'replace',
    'cli-pack',
    candidate.contentPath,
    '--expected-revision',
    baseline,
  ]);
  assert.equal(replaced.status, 0, replaced.stderr);
  assert.equal(replaced.output.status, 'submitted');
  assert.equal(replaced.output.commit_sha, remoteHead(project));
  assert.deepEqual(
    remoteTree(project).filter(
      (item) => item.startsWith('skills/cli-pack') || item === 'catalog/cli-pack.json',
    ),
    ['catalog/cli-pack.json', 'skills/cli-pack/SKILL.md', 'skills/cli-pack/references/note.md'],
  );
  assert.equal(remoteJson(project, 'catalog/cli-pack.json').display_name, 'Original Pack');
  assert.match(remoteBytes(project, 'skills/cli-pack/SKILL.md').toString('utf8'), /Replaced body/);
  assert.equal(project.git('status', '--porcelain'), '');
});

test('replace with a stale expected revision returns conflict without changing content', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project);
  const added = run(project, [
    'add',
    candidate.contentPath,
    '--meta',
    candidate.metaPath,
    '--publish',
  ]);
  assert.equal(added.status, 0, added.stderr);
  const head = remoteHead(project);
  const filesBefore = remoteFiles(project);

  fs.appendFileSync(candidate.contentPath, '\nChanged after baseline.\n');
  const conflict = run(project, [
    'replace',
    'cli-single',
    candidate.contentPath,
    '--expected-revision',
    'c'.repeat(40),
  ]);

  assert.equal(conflict.status, 4, conflict.stderr);
  assert.equal(conflict.output.status, 'failed');
  assert.equal(conflict.output.errors[0].code, 'E_CONFLICT');
  assert.equal(remoteHead(project), head);
  assert.deepEqual(remoteFiles(project), filesBefore);
  assert.equal(project.git('status', '--porcelain'), '');
});

test('replace with --meta updates the stored record', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project, 'cli-single', { display_name: 'Original Name' });
  const added = run(project, [
    'add',
    candidate.contentPath,
    '--meta',
    candidate.metaPath,
    '--publish',
  ]);
  assert.equal(added.status, 0, added.stderr);
  const head = remoteHead(project);

  fs.appendFileSync(candidate.contentPath, '\nUpdated body.\n');
  const metaPath = path.join(project.root, 'candidates', 'cli-single-updated.json');
  fs.writeFileSync(
    metaPath,
    `${JSON.stringify(sampleRecord('cli-single', { display_name: 'Updated Name' }), null, 2)}\n`,
  );

  const replaced = run(project, [
    'replace',
    'cli-single',
    candidate.contentPath,
    '--expected-revision',
    head,
    '--meta',
    metaPath,
  ]);
  assert.equal(replaced.status, 0, replaced.stderr);
  assert.equal(replaced.output.status, 'submitted');
  assert.equal(remoteJson(project, 'catalog/cli-single.json').display_name, 'Updated Name');
  assert.match(remoteBytes(project, 'skills/cli-single.md').toString('utf8'), /Updated body/);
});
