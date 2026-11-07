'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const { importCandidate } = require('../../scripts/lib/skill-cli/import');
const { validateSource } = require('../../scripts/lib/skill-cli/source-github');
const {
  createFakeSource,
  createSkillCliProject,
  remoteFiles,
  writeDirectoryCandidate,
  writeSingleCandidate,
} = require('../support/skill-cli-fixture');

const source = {
  repository: 'owner/repository',
  path: 'skills/cli-single.md',
  ref: 'main',
  refPolicy: 'branch',
};

test('import previews a single-file source without writing', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project);
  const reader = createFakeSource({
    files: { 'cli-single.md': fs.readFileSync(candidate.contentPath) },
  });

  const result = importCandidate({
    projectRoot: project.root,
    source,
    metaPath: candidate.metaPath,
    reader,
  });

  assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
  assert.equal(result.outcome.status, 'previewed');
  assert.equal(result.outcome.slug, 'cli-single');
  assert.match(result.outcome.content_revision, /^[0-9a-f]{64}$/);
  assert.equal(project.git('status', '--porcelain'), '');
});

test('import previews a directory source and publishes only target files', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeDirectoryCandidate(project);
  const reader = createFakeSource({
    files: {
      'SKILL.md': fs.readFileSync(path.join(candidate.contentPath, 'SKILL.md')),
      'references/note.md': fs.readFileSync(path.join(candidate.contentPath, 'references/note.md')),
    },
  });

  const preview = importCandidate({
    projectRoot: project.root,
    source: { ...source, path: 'skills/cli-pack', refPolicy: 'pinned', ref: 'b'.repeat(40) },
    metaPath: candidate.metaPath,
    reader,
  });
  assert.equal(preview.ok, true, JSON.stringify(preview.diagnostics));
  assert.equal(preview.outcome.status, 'previewed');

  const published = importCandidate({
    projectRoot: project.root,
    source: { ...source, path: 'skills/cli-pack', refPolicy: 'pinned', ref: 'b'.repeat(40) },
    metaPath: candidate.metaPath,
    publish: true,
    reader,
  });
  assert.equal(published.ok, true, JSON.stringify(published.diagnostics));
  assert.equal(published.outcome.status, 'submitted');
  assert.deepEqual(remoteFiles(project), [
    'catalog/cli-pack.json',
    'skills/cli-pack/SKILL.md',
    'skills/cli-pack/references/note.md',
  ]);
  assert.equal(project.git('status', '--porcelain'), '');
});

test('source failures fail closed with stable diagnostics', async (t) => {
  const project = createSkillCliProject(t);
  const candidate = writeSingleCandidate(project);
  const cases = [
    {
      name: 'not found',
      reader: createFakeSource({ error: { code: 'E_SOURCE', message: '404' } }),
      source,
      code: 'E_SOURCE',
    },
    {
      name: 'truncated tree',
      reader: createFakeSource({ truncated: true }),
      source,
      code: 'E_SOURCE',
    },
    {
      name: 'mutable revision',
      reader: createFakeSource({
        revision: 'main',
        files: { 'cli-single.md': fs.readFileSync(candidate.contentPath) },
      }),
      source,
      code: 'E_SOURCE',
    },
    {
      name: 'path traversal',
      reader: createFakeSource({ files: { '../evil.md': 'x' } }),
      source,
      code: 'E_SOURCE',
    },
    {
      name: 'symlink',
      reader: createFakeSource({
        files: { 'cli-single.md': { bytes: 'x', mode: '120000' } },
      }),
      source,
      code: 'E_SOURCE',
    },
    {
      name: 'missing main document',
      reader: createFakeSource({ files: { 'references/note.md': '# Note\n' } }),
      source: { ...source, path: 'skills/cli-pack' },
      metaPath: writeDirectoryCandidate(project).metaPath,
      code: 'E_MAIN_MISSING',
    },
  ];

  for (const item of cases) {
    const result = importCandidate({
      projectRoot: project.root,
      source: item.source,
      metaPath: item.metaPath || candidate.metaPath,
      reader: item.reader,
    });
    assert.equal(result.ok, false, item.name);
    assert.equal(result.diagnostics[0].code, item.code, item.name);
  }
  assert.equal(project.git('status', '--porcelain'), '');
});

test('only structured GitHub locations are accepted', () => {
  assert.equal(
    validateSource({ ...source, repository: 'https://github.com/owner/repository' }).code,
    'E_SCHEMA',
  );
  assert.equal(validateSource({ ...source, path: '../skills/example.md' }).code, 'E_SCHEMA');
  assert.equal(validateSource({ ...source, refPolicy: 'latest' }).code, 'E_SCHEMA');
  assert.equal(validateSource({ ...source, repository: 'owner' }).code, 'E_SCHEMA');
});
