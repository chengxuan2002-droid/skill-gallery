'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const test = require('node:test');

const {
  addAttachment,
  makeManualProject,
  readJson,
  readZip,
  record,
  sha256,
  snapshot,
  writeRecord,
} = require('../support/manual-fixture');

function git(root, ...args) {
  return execFileSync('git', args, {
    cwd: root,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
}

test('manual single-file and directory skills publish through the existing build', async (t) => {
  const project = makeManualProject(t);
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
  const project = makeManualProject(t);
  const first = await project.buildPreview();
  assert.equal(first.ok, true, JSON.stringify(first.diagnostics));
  const firstRevision = readJson(first.distDir, 'manifest.json').contentRevision;
  const source = fs.readFileSync(path.join(project.skillsDir, 'manual-single.md'));

  writeRecord(
    project.root,
    record('manual-single', {
      display_name: 'Manual Single Renamed',
      description: 'Metadata-only edit',
      notes: '站内备注更新',
    }),
  );
  const second = await project.buildPreview();
  assert.equal(second.ok, true, JSON.stringify(second.diagnostics));

  const manifest = readJson(second.distDir, 'manifest.json');
  assert.notEqual(manifest.contentRevision, firstRevision);
  const detail = readJson(second.distDir, 'details/manual-single.json');
  assert.equal(detail.display_name, 'Manual Single Renamed');
  assert.equal(detail.notes, '站内备注更新');
  assert.deepEqual(fs.readFileSync(path.join(project.skillsDir, 'manual-single.md')), source);
  assert.deepEqual(
    fs.readFileSync(path.join(second.distDir, ...detail.raw_url.split('/'))),
    source,
  );
});

test('invalid manual batches fail closed and preserve the previous dist', async (t) => {
  const secret = ['ghp', '_', 'A'.repeat(24)].join('');
  const cases = [
    {
      name: 'missing required field',
      mutate(project) {
        const value = record('manual-single', { display_name: 'Manual Single' });
        delete value.display_name;
        writeRecord(project.root, value);
      },
      code: 'E_SCHEMA',
    },
    {
      name: 'missing attachment',
      mutate(project) {
        fs.rmSync(path.join(project.skillsDir, 'manual-pack/references/note.md'));
      },
      code: 'E_REFERENCE_MISSING',
    },
    {
      name: 'path traversal',
      mutate(project) {
        writeRecord(
          project.root,
          record('manual-single', { content_path: 'skills/../index.html' }),
        );
      },
      code: 'E_PATH',
    },
    {
      name: 'credential content',
      mutate(project) {
        fs.writeFileSync(
          path.join(project.skillsDir, 'manual-pack/references/leak.txt'),
          `token: ${secret}\n`,
        );
      },
      code: 'E_SECRET',
    },
  ];

  for (const item of cases) {
    const project = makeManualProject(t);
    const first = await project.buildPreview();
    assert.equal(first.ok, true, `${item.name}: ${JSON.stringify(first.diagnostics)}`);
    const before = snapshot(first.distDir);

    item.mutate(project);
    const failed = await project.buildPreview();
    assert.equal(failed.ok, false, item.name);
    assert.equal(failed.diagnostics[0].code, item.code, item.name);
    assert.equal(JSON.stringify(failed.diagnostics).includes(secret), false, item.name);
    assert.deepEqual([...snapshot(first.distDir).entries()], [...before.entries()], item.name);
  }
});

test('explicit replacement keeps one version and removes deleted attachments', async (t) => {
  const project = makeManualProject(t);
  addAttachment(project, 'references/old.md', '# Old\n\nRemoved on replace.\n');
  const first = await project.buildPreview();
  assert.equal(first.ok, true, JSON.stringify(first.diagnostics));
  const firstDetail = readJson(first.distDir, 'details/manual-pack.json');
  assert.ok(firstDetail.files.some((file) => file.path === 'references/old.md'));
  const firstZip = await readZip(path.join(first.distDir, ...firstDetail.download_url.split('/')));
  assert.ok(firstZip.some((entry) => entry.path === 'manual-pack/references/old.md'));
  const firstRevision = readJson(first.distDir, 'manifest.json').contentRevision;

  fs.appendFileSync(path.join(project.skillsDir, 'manual-pack/SKILL.md'), '\nUpdated body.\n');
  fs.rmSync(path.join(project.skillsDir, 'manual-pack/references/old.md'));

  const second = await project.buildPreview();
  assert.equal(second.ok, true, JSON.stringify(second.diagnostics));
  const detail = readJson(second.distDir, 'details/manual-pack.json');
  assert.equal(
    detail.files.some((file) => file.path === 'references/old.md'),
    false,
  );
  const entries = await readZip(path.join(second.distDir, ...detail.download_url.split('/')));
  assert.equal(
    entries.some((entry) => entry.path === 'manual-pack/references/old.md'),
    false,
  );
  const index = readJson(second.distDir, 'assets/search-index.json');
  assert.equal(index.skills.filter((item) => item.slug === 'manual-pack').length, 1);
  assert.notEqual(readJson(second.distDir, 'manifest.json').contentRevision, firstRevision);
});

test('removing a manual skill deletes it from index, details and downloads', async (t) => {
  const project = makeManualProject(t);
  const first = await project.buildPreview();
  assert.equal(first.ok, true, JSON.stringify(first.diagnostics));
  assert.ok(fs.existsSync(path.join(first.distDir, 'details/manual-single.json')));

  fs.rmSync(path.join(project.skillsDir, 'manual-single.md'));
  fs.rmSync(path.join(project.root, 'catalog/manual-single.json'));

  const second = await project.buildPreview();
  assert.equal(second.ok, true, JSON.stringify(second.diagnostics));
  const index = readJson(second.distDir, 'assets/search-index.json');
  assert.equal(
    index.skills.some((item) => item.slug === 'manual-single'),
    false,
  );
  assert.ok(index.skills.some((item) => item.slug === 'manual-pack'));
  assert.equal(fs.existsSync(path.join(second.distDir, 'details/manual-single.json')), false);
  const manifest = readJson(second.distDir, 'manifest.json');
  assert.equal(
    manifest.artifacts.some((item) => item.path.startsWith('skills/manual-single/')),
    false,
  );
});

test('a controlled revert restores the baseline revision and slugs', async (t) => {
  const project = makeManualProject(t);
  fs.writeFileSync(path.join(project.root, '.gitignore'), 'dist/\n');
  git(project.root, 'init', '-q');
  git(project.root, 'config', 'user.name', 'Manual Drill');
  git(project.root, 'config', 'user.email', 'manual@example.invalid');
  git(project.root, 'add', '-A');
  git(project.root, 'commit', '-q', '-m', 'baseline');
  const first = await project.buildPreview();
  assert.equal(first.ok, true, JSON.stringify(first.diagnostics));
  const baselineRevision = readJson(first.distDir, 'manifest.json').contentRevision;
  const baselineSlugs = readJson(first.distDir, 'assets/search-index.json')
    .skills.map((item) => item.slug)
    .sort();

  writeRecord(
    project.root,
    record('manual-single', {
      display_name: 'Manual Single',
      notes: 'recovery drill change',
    }),
  );
  git(project.root, 'add', '-A');
  git(project.root, 'commit', '-q', '-m', 'content change');
  const changed = await project.buildPreview();
  assert.equal(changed.ok, true, JSON.stringify(changed.diagnostics));
  assert.notEqual(readJson(changed.distDir, 'manifest.json').contentRevision, baselineRevision);

  git(project.root, 'revert', '--no-edit', 'HEAD');
  const recovered = await project.buildPreview();
  assert.equal(recovered.ok, true, JSON.stringify(recovered.diagnostics));
  assert.equal(readJson(recovered.distDir, 'manifest.json').contentRevision, baselineRevision);
  assert.deepEqual(
    readJson(recovered.distDir, 'assets/search-index.json')
      .skills.map((item) => item.slug)
      .sort(),
    baselineSlugs,
  );
});

test('rebuilding unchanged manual content keeps the revision and artifact set', async (t) => {
  const project = makeManualProject(t);
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
