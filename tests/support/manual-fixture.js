'use strict';

const fs = require('node:fs');
const path = require('node:path');
const yauzl = require('yauzl');

const { createDetailFixtureProject } = require('./search-fixture');
const { listTree, sha256 } = require('./fixtures');

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

function addAttachment(project, relativePath, content) {
  const target = path.join(project.skillsDir, 'manual-pack', ...relativePath.split('/'));
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content);
}

function makeManualProject(t) {
  const project = createDetailFixtureProject();
  t.after(() => project.cleanup());
  addManualSkills(project);
  return project;
}

function snapshot(root) {
  const { files } = listTree(root);
  return new Map(
    files.map((relativePath) => {
      const bytes = fs.readFileSync(path.join(root, ...relativePath.split('/')));
      return [relativePath, { size: bytes.length, sha256: sha256(bytes) }];
    }),
  );
}

module.exports = {
  PACK_BODY,
  SINGLE_BODY,
  addAttachment,
  addManualSkills,
  makeManualProject,
  readJson,
  readZip,
  record,
  sha256,
  snapshot,
  writeRecord,
};
