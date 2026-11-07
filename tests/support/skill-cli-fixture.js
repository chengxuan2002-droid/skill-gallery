'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const { createDetailFixtureProject } = require('./search-fixture');

function git(cwd, ...args) {
  return execFileSync('git', args, {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
}

function sampleRecord(slug, overrides = {}) {
  return {
    schemaVersion: 1,
    slug,
    display_name: slug,
    description: 'CLI fixture skill',
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

function initializeRepository(project) {
  const root = project.root;
  fs.writeFileSync(path.join(root, '.gitignore'), 'dist/\ncandidates/\n');
  fs.writeFileSync(path.join(root, '.gitattributes'), '* text=auto eol=lf\nskills/** -text\n');
  git(root, 'init', '-q', '-b', 'main');
  git(root, 'config', 'user.name', 'CLI Fixture');
  git(root, 'config', 'user.email', 'cli-fixture@example.invalid');
  git(root, 'add', '-A');
  git(root, 'commit', '-q', '-m', 'baseline');

  const remoteDir = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-cli-remote-'));
  git(remoteDir, 'init', '-q', '--bare');
  git(remoteDir, 'symbolic-ref', 'HEAD', 'refs/heads/main');
  git(root, 'remote', 'add', 'origin', remoteDir);
  git(root, 'push', '-q', '-u', 'origin', 'main');
  return remoteDir;
}

function createSkillCliProject(t) {
  const project = createDetailFixtureProject();
  t.after(() => project.cleanup());
  const remoteDir = initializeRepository(project);
  t.after(() => fs.rmSync(remoteDir, { recursive: true, force: true }));
  return {
    ...project,
    remoteDir,
    git: (...args) => git(project.root, ...args),
    head: () => git(project.root, 'rev-parse', 'HEAD'),
  };
}

function writeSingleCandidate(project, slug = 'cli-single', overrides = {}) {
  const candidateDir = path.join(project.root, 'candidates');
  fs.mkdirSync(candidateDir, { recursive: true });
  const contentPath = path.join(candidateDir, `${slug}.md`);
  fs.writeFileSync(
    contentPath,
    `---\nname: ${slug}\ndescription: CLI candidate\n---\n\n# ${slug}\n\nCandidate body.\n`,
  );
  const record = sampleRecord(slug, overrides);
  const metaPath = path.join(candidateDir, `${slug}.json`);
  fs.writeFileSync(metaPath, `${JSON.stringify(record, null, 2)}\n`);
  return { contentPath, metaPath, record };
}

function writeDirectoryCandidate(project, slug = 'cli-pack', overrides = {}) {
  const candidateDir = path.join(project.root, 'candidates', slug);
  fs.mkdirSync(path.join(candidateDir, 'references'), { recursive: true });
  const mainPath = path.join(candidateDir, 'SKILL.md');
  fs.writeFileSync(
    mainPath,
    `---\nname: ${slug}\ndescription: CLI directory candidate\n---\n\n# ${slug}\n\nRead [note](references/note.md).\n`,
  );
  fs.writeFileSync(path.join(candidateDir, 'references/note.md'), '# Note\n\nAttachment.\n');
  const record = sampleRecord(slug, {
    content_path: `skills/${slug}/SKILL.md`,
    ...overrides,
  });
  const metaPath = path.join(project.root, 'candidates', `${slug}.json`);
  fs.writeFileSync(metaPath, `${JSON.stringify(record, null, 2)}\n`);
  return { contentPath: candidateDir, mainPath, metaPath, record };
}

function createFakeSource({ revision = 'b'.repeat(40), files = {} } = {}) {
  return {
    revision,
    files: new Map(Object.entries(files)),
  };
}

function createFakeRuns(statuses = {}) {
  return {
    get(runId) {
      return statuses[runId] ?? null;
    },
  };
}

function remoteHead(project) {
  return execFileSync('git', ['-C', project.remoteDir, 'rev-parse', 'main'], {
    encoding: 'utf8',
  }).trim();
}

function remoteFiles(project) {
  return execFileSync(
    'git',
    ['-C', project.remoteDir, 'show', '--pretty=format:', '--name-only', 'main'],
    { encoding: 'utf8' },
  )
    .split(/\r?\n/)
    .filter(Boolean)
    .sort();
}

function remoteBytes(project, relativePath) {
  return execFileSync('git', ['-C', project.remoteDir, 'show', `main:${relativePath}`]);
}

function remoteTree(project) {
  return execFileSync('git', ['-C', project.remoteDir, 'ls-tree', '-r', '--name-only', 'main'], {
    encoding: 'utf8',
  })
    .split(/\r?\n/)
    .filter(Boolean)
    .sort();
}

function readJson(root, relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, ...relativePath.split('/')), 'utf8'));
}

module.exports = {
  createFakeRuns,
  createFakeSource,
  createSkillCliProject,
  readJson,
  remoteBytes,
  remoteFiles,
  remoteHead,
  remoteTree,
  sampleRecord,
  writeDirectoryCandidate,
  writeSingleCandidate,
};
