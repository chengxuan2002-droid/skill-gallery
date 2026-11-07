'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync, spawnSync } = require('node:child_process');
const test = require('node:test');

const {
  createSkillCliProject,
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

function remoteHead(project) {
  return project.git('-C', project.remoteDir, 'rev-parse', 'main');
}

function remoteFiles(project) {
  return project
    .git('-C', project.remoteDir, 'show', '--pretty=format:', '--name-only', 'main')
    .split(/\r?\n/)
    .filter(Boolean)
    .sort();
}

function remoteFile(project, relativePath) {
  return execFileSync('git', ['-C', project.remoteDir, 'show', `main:${relativePath}`]);
}

test('preview validates a candidate without writing or publishing', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project);
  const beforeStatus = project.git('status', '--porcelain');
  const beforeHead = remoteHead(project);
  const beforeWorktrees = project.git('worktree', 'list').split(/\r?\n/).length;

  const result = run(project, ['preview', candidate.contentPath, '--meta', candidate.metaPath]);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.output.status, 'previewed');
  assert.equal(result.output.slug, 'cli-single');
  assert.match(result.output.content_revision, /^[0-9a-f]{64}$/);
  assert.equal(result.output.commit_sha, null);
  assert.deepEqual(result.output.errors, []);
  assert.equal(project.git('status', '--porcelain'), beforeStatus);
  assert.equal(remoteHead(project), beforeHead);
  assert.equal(project.git('worktree', 'list').split(/\r?\n/).length, beforeWorktrees);
});

test('publishing a single-file candidate stages only the skill and record', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project);

  const result = run(project, [
    'add',
    candidate.contentPath,
    '--meta',
    candidate.metaPath,
    '--publish',
  ]);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.output.status, 'submitted');
  assert.equal(result.output.slug, 'cli-single');
  assert.equal(result.output.content_status, 'pending');
  assert.equal(result.output.deploy_status, 'pending');
  assert.match(result.output.commit_sha, /^[0-9a-f]{40}$/);
  assert.equal(result.output.commit_sha, remoteHead(project));
  assert.deepEqual(remoteFiles(project), ['catalog/cli-single.json', 'skills/cli-single.md']);
  assert.deepEqual(
    Buffer.from(remoteFile(project, 'skills/cli-single.md'), 'utf8'),
    fs.readFileSync(candidate.contentPath),
  );
  assert.equal(project.git('status', '--porcelain'), '');
});

test('publishing a directory candidate stages its complete file set', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeDirectoryCandidate(project);

  const result = run(project, [
    'add',
    candidate.contentPath,
    '--meta',
    candidate.metaPath,
    '--publish',
  ]);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.output.status, 'submitted');
  assert.deepEqual(remoteFiles(project), [
    'catalog/cli-pack.json',
    'skills/cli-pack/SKILL.md',
    'skills/cli-pack/references/note.md',
  ]);
});

test('publishing the same candidate twice returns noop without a new commit', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project);
  const args = ['add', candidate.contentPath, '--meta', candidate.metaPath, '--publish'];

  const first = run(project, args);
  assert.equal(first.status, 0, first.stderr);
  assert.equal(first.output.status, 'submitted');
  const headAfterFirst = remoteHead(project);

  const second = run(project, args);
  assert.equal(second.status, 0, second.stderr);
  assert.equal(second.output.status, 'noop');
  assert.equal(second.output.commit_sha, null);
  assert.equal(remoteHead(project), headAfterFirst);
});
