'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const { makeTempProject } = require('./fixtures');
const { snapshotSkill } = require('../../scripts/lib/content-store');

function git(cwd, ...args) {
  return execFileSync('git', args, {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  }).trim();
}

function record(slug, tracking = {}) {
  return {
    schemaVersion: 1,
    slug,
    display_name: `Site ${slug}`,
    description: 'Site description',
    tags: ['site-tag'],
    platforms: ['generic'],
    allowed_dot_paths: [],
    source_type: 'github',
    usage: 'Site usage',
    notes: 'Site notes',
    content_path: `skills/${slug}.md`,
    source_tracking: {
      provider: 'github',
      repository: 'owner/repository',
      path: `skills/${slug}.md`,
      ref_policy: 'branch',
      ref: 'main',
      enabled: true,
      last_synced_revision: null,
      last_synced_digest: null,
      synced_at: null,
      ...tracking,
    },
    author: null,
    homepage_url: null,
    repository_url: 'https://github.com/owner/repository',
    license: null,
    created_at: '2026-11-01',
    updated_at: '2026-11-01',
    declared_version: null,
  };
}

function main(slug, body = 'Body') {
  return `---\nname: ${slug}\ndescription: Fixture skill\n---\n\n# ${slug}\n\n${body}\n`;
}

function writeSkill(project, slug, { directory = false, content = main(slug) } = {}) {
  const base = record(slug);
  if (directory) {
    const root = path.join(project.skillsDir, slug);
    fs.mkdirSync(path.join(root, 'references'), { recursive: true });
    fs.writeFileSync(path.join(root, 'SKILL.md'), content);
    fs.writeFileSync(path.join(root, 'LICENSE'), 'MIT\n');
    fs.writeFileSync(path.join(root, 'references', 'note.md'), '# Note\n');
    return {
      files: {
        'SKILL.md': Buffer.from(content),
        LICENSE: Buffer.from('MIT\n'),
        'references/note.md': Buffer.from('# Note\n'),
      },
      record: {
        ...base,
        content_path: `skills/${slug}/SKILL.md`,
        source_tracking: { ...base.source_tracking, path: `skills/${slug}` },
      },
    };
  }
  fs.writeFileSync(path.join(project.skillsDir, `${slug}.md`), content);
  return {
    files: { [`${slug}.md`]: Buffer.from(content) },
    record: base,
  };
}

function writeCatalog(project, value) {
  fs.mkdirSync(path.join(project.root, 'catalog'), { recursive: true });
  fs.writeFileSync(
    path.join(project.root, 'catalog', `${value.slug}.json`),
    `${JSON.stringify(value, null, 2)}\n`,
  );
}

function initializeRepository(project) {
  fs.writeFileSync(path.join(project.root, '.gitignore'), 'dist/\n');
  fs.writeFileSync(
    path.join(project.root, '.gitattributes'),
    '* text=auto eol=lf\nskills/** -text\n',
  );
  git(project.root, 'init', '-q', '-b', 'main');
  git(project.root, 'config', 'user.name', 'Source Sync Fixture');
  git(project.root, 'config', 'user.email', 'source-sync@example.invalid');
  git(project.root, 'add', '-A');
  git(project.root, 'commit', '-q', '-m', 'baseline');
  const remoteDir = fs.mkdtempSync(path.join(os.tmpdir(), 'source-sync-remote-'));
  git(remoteDir, 'init', '-q', '--bare');
  git(remoteDir, 'symbolic-ref', 'HEAD', 'refs/heads/main');
  git(project.root, 'remote', 'add', 'origin', remoteDir);
  git(project.root, 'push', '-q', '-u', 'origin', 'main');
  return remoteDir;
}

function createSourceSyncProject(t) {
  const project = makeTempProject();
  t.after(() => project.cleanup());
  let remoteDir = null;
  function initRemote() {
    remoteDir = initializeRepository(project);
    t.after(() => fs.rmSync(remoteDir, { recursive: true, force: true }));
    return remoteDir;
  }
  return {
    ...project,
    get remoteDir() {
      return remoteDir;
    },
    initRemote,
    git: (...args) => git(project.root, ...args),
    head: () => git(project.root, 'rev-parse', 'HEAD'),
    remoteHead: () => git(remoteDir, 'rev-parse', 'main'),
    remoteFiles: () =>
      git(remoteDir, 'ls-tree', '-r', '--name-only', 'main').split(/\r?\n/).filter(Boolean).sort(),
    remoteShow: (relativePath) =>
      execFileSync('git', ['-C', remoteDir, 'show', `main:${relativePath}`], {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
      }),
    readRecord: (slug) =>
      JSON.parse(fs.readFileSync(path.join(project.root, 'catalog', `${slug}.json`), 'utf8')),
  };
}

function fakeReader({
  revision = 'a'.repeat(40),
  files = {},
  modes = {},
  licenseFiles = {},
  licenseModes = {},
  error = null,
  truncated = false,
} = {}) {
  return {
    resolve() {
      if (error) return { ok: false, ...error };
      return {
        ok: true,
        revision,
        truncated,
        files: new Map(Object.entries(files)),
        modes,
        licenseFiles: new Map(Object.entries(licenseFiles)),
        licenseModes,
      };
    },
  };
}

function syncedProject(t, options = {}) {
  const project = createSourceSyncProject(t);
  const skill = writeSkill(project, 'example', options);
  const snapshot = snapshotSkill({ projectRoot: project.root, record: skill.record });
  if (!snapshot.ok) throw new Error(JSON.stringify(snapshot.diagnostics));
  const value = {
    ...skill.record,
    declared_version: '1.0.0',
    source_tracking: {
      ...skill.record.source_tracking,
      last_synced_revision: 'a'.repeat(40),
      last_synced_digest: snapshot.snapshot.digest,
      synced_at: '2026-11-01T00:00:00+08:00',
    },
  };
  writeCatalog(project, value);
  project.initRemote();
  return { project, skill, digest: snapshot.snapshot.digest, record: value };
}

module.exports = {
  createSourceSyncProject,
  fakeReader,
  main,
  record,
  syncedProject,
  writeCatalog,
  writeSkill,
};
