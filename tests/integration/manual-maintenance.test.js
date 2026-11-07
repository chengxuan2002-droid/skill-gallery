'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const yauzl = require('yauzl');

const { createDetailFixtureProject } = require('../support/search-fixture');
const { sha256 } = require('../support/fixtures');

const SINGLE_BODY = [
  '---',
  'name: Manual Single',
  'description: Manual maintenance single-file sample',
  '---',
  '',
  '# Manual Single',
  '',
  'Manual single-file body.',
  '',
].join('\n');

const PACK_BODY = [
  '---',
  'name: Manual Pack',
  'description: Manual maintenance directory sample',
  '---',
  '',
  '# Manual Pack',
  '',
  'Read [note](references/note.md).',
  '',
].join('\n');

function record(slug, overrides = {}) {
  return {
    schemaVersion: 1,
    slug,
    display_name: slug,
    description: '手动维护样例',
    tags: [],
    platforms: [],
    allowed_dot_paths: [],
    source_type: 'self-built',
    usage: null,
    notes: null,
    content_path: `skills/${slug}.md`,
    source_tracking: null,
    author: null,
    homepage_url: null,
    repository_url: null,
    license: null,
    created_at: null,
    updated_at: null,
    declared_version: null,
    ...overrides,
  };
}

function writeRecord(root, value) {
  fs.writeFileSync(
    path.join(root, 'catalog', `${value.slug}.json`),
    `${JSON.stringify(value, null, 2)}\n`,
  );
}

function readJson(root, relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, ...relativePath.split('/')), 'utf8'));
}

function readZip(zipPath) {
  return new Promise((resolve, reject) => {
    yauzl.open(zipPath, { lazyEntries: true }, (error, zipFile) => {
      if (error) return reject(error);
      const entries = [];
      zipFile.on('error', reject);
      zipFile.on('entry', (entry) => {
        if (entry.fileName.endsWith('/')) {
          zipFile.readEntry();
          return;
        }
        zipFile.openReadStream(entry, (streamError, stream) => {
          if (streamError) return reject(streamError);
          const chunks = [];
          stream.on('data', (chunk) => chunks.push(chunk));
          stream.on('end', () => {
            entries.push({ path: entry.fileName, bytes: Buffer.concat(chunks) });
            zipFile.readEntry();
          });
          stream.on('error', reject);
        });
      });
      zipFile.on('end', () => resolve(entries));
      zipFile.readEntry();
    });
  });
}

function addManualSkills(project) {
  fs.writeFileSync(path.join(project.skillsDir, 'manual-single.md'), SINGLE_BODY);
  writeRecord(
    project.root,
    record('manual-single', {
      display_name: 'Manual Single',
      description: 'Manual maintenance single-file sample',
    }),
  );

  const packRoot = path.join(project.skillsDir, 'manual-pack');
  fs.mkdirSync(path.join(packRoot, 'references'), { recursive: true });
  fs.writeFileSync(path.join(packRoot, 'SKILL.md'), PACK_BODY);
  fs.writeFileSync(path.join(packRoot, 'references/note.md'), '# Note\n\nManual attachment.\n');
  writeRecord(
    project.root,
    record('manual-pack', {
      display_name: 'Manual Pack',
      description: 'Manual maintenance directory sample',
      content_path: 'skills/manual-pack/SKILL.md',
    }),
  );
}

function makeProject(t) {
  const project = createDetailFixtureProject();
  t.after(() => project.cleanup());
  addManualSkills(project);
  return project;
}

test('manual single-file and directory skills publish through the existing build', async (t) => {
  const project = makeProject(t);
  const built = await project.buildPreview();
  assert.equal(built.ok, true, JSON.stringify(built.diagnostics));

  const index = readJson(built.distDir, 'assets/search-index.json');
  const manifest = readJson(built.distDir, 'manifest.json');
  const slugs = index.skills.map((item) => item.slug);
  assert.ok(slugs.includes('manual-single'));
  assert.ok(slugs.includes('manual-pack'));

  const singleSource = fs.readFileSync(path.join(project.skillsDir, 'manual-single.md'));
  const single = readJson(built.distDir, 'details/manual-single.json');
  assert.equal(single.contentRevision, manifest.contentRevision);
  assert.equal(single.raw_url, single.download_url);
  assert.equal(single.download_sha256, sha256(singleSource));
  assert.deepEqual(
    fs.readFileSync(path.join(built.distDir, ...single.raw_url.split('/'))),
    singleSource,
  );

  const packSource = path.join(project.skillsDir, 'manual-pack');
  const pack = readJson(built.distDir, 'details/manual-pack.json');
  assert.equal(pack.contentRevision, manifest.contentRevision);
  assert.equal(pack.download_url, 'downloads/manual-pack.zip');
  assert.ok(pack.files.some((file) => file.path === 'references/note.md'));
  const zipBytes = fs.readFileSync(path.join(built.distDir, ...pack.download_url.split('/')));
  assert.equal(pack.download_size, zipBytes.length);
  const entries = await readZip(path.join(built.distDir, ...pack.download_url.split('/')));
  const byPath = new Map(entries.map((entry) => [entry.path, entry.bytes]));
  for (const relative of ['SKILL.md', 'references/note.md']) {
    assert.deepEqual(
      byPath.get(`manual-pack/${relative}`),
      fs.readFileSync(path.join(packSource, relative)),
    );
  }
});

test('metadata-only edits keep the original bytes unchanged', async (t) => {
  const project = makeProject(t);
  const first = await project.buildPreview();
  assert.equal(first.ok, true, JSON.stringify(first.diagnostics));
  const firstRevision = readJson(first.distDir, 'manifest.json').contentRevision;
  const source = fs.readFileSync(path.join(project.skillsDir, 'manual-single.md'));

  const value = record('manual-single', {
    display_name: 'Manual Single Renamed',
    description: 'Metadata-only edit',
    notes: '站内备注更新',
  });
  writeRecord(project.root, value);
  const second = await project.buildPreview();
  assert.equal(second.ok, true, JSON.stringify(second.diagnostics));

  const manifest = readJson(second.distDir, 'manifest.json');
  assert.notEqual(manifest.contentRevision, firstRevision);
  const detail = readJson(second.distDir, 'details/manual-single.json');
  assert.equal(detail.display_name, 'Manual Single Renamed');
  assert.equal(detail.notes, '站内备注更新');
  assert.deepEqual(fs.readFileSync(path.join(project.skillsDir, 'manual-single.md')), source);
  const raw = fs.readFileSync(path.join(second.distDir, ...detail.raw_url.split('/')));
  assert.deepEqual(raw, source);
});

test('rebuilding unchanged manual content keeps the revision and artifact set', async (t) => {
  const project = makeProject(t);
  const first = await project.buildPreview();
  assert.equal(first.ok, true, JSON.stringify(first.diagnostics));
  const firstManifest = readJson(first.distDir, 'manifest.json');
  const firstPaths = firstManifest.artifacts.map((artifact) => artifact.path);

  const second = await project.buildPreview();
  assert.equal(second.ok, true, JSON.stringify(second.diagnostics));
  const secondManifest = readJson(second.distDir, 'manifest.json');
  assert.equal(secondManifest.contentRevision, firstManifest.contentRevision);
  assert.deepEqual(
    secondManifest.artifacts.map((artifact) => artifact.path),
    firstPaths,
  );
});
