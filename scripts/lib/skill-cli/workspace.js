'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

function git(cwd, ...args) {
  try {
    return execFileSync('git', args, {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    }).trim();
  } catch (error) {
    const failure = new Error('git command failed');
    failure.code = 'E_CONFLICT';
    failure.stderr = error.stderr?.toString() ?? '';
    throw failure;
  }
}

function remoteBranch(projectRoot) {
  try {
    const ref = git(projectRoot, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD');
    return ref.replace(/^origin\//, '');
  } catch {
    return 'main';
  }
}

function createBaseline(projectRoot) {
  git(projectRoot, 'fetch', '--quiet', 'origin');
  const branch = remoteBranch(projectRoot);
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-cli-worktree-'));
  const tree = path.join(temp, 'tree');
  git(projectRoot, 'worktree', 'add', '--detach', tree, `origin/${branch}`);
  return {
    root: tree,
    branch,
    head: git(tree, 'rev-parse', 'HEAD'),
    cleanup() {
      try {
        git(projectRoot, 'worktree', 'remove', '--force', tree);
      } catch {
        fs.rmSync(tree, { recursive: true, force: true });
      }
      fs.rmSync(temp, { recursive: true, force: true });
    },
  };
}

function removeSkill(root, slug) {
  fs.rmSync(path.join(root, 'skills', `${slug}.md`), { force: true });
  fs.rmSync(path.join(root, 'skills', slug), { recursive: true, force: true });
}

function writeFiles(root, files, record) {
  for (const file of files) {
    const target = path.join(root, ...file.path.split('/'));
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, file.bytes);
  }
  const recordPath = path.join(root, 'catalog', `${record.slug}.json`);
  fs.mkdirSync(path.dirname(recordPath), { recursive: true });
  fs.writeFileSync(recordPath, `${JSON.stringify(record, null, 2)}\n`);
}

function trackedSkillPaths(root, slug) {
  return git(root, 'ls-files', '--', `skills/${slug}.md`, `skills/${slug}`)
    .split(/\r?\n/)
    .filter(Boolean);
}

function commitFiles({ root, files, record, replace = false }) {
  const paths = [...files.map((file) => file.path), `catalog/${record.slug}.json`];
  if (replace) {
    paths.push(...trackedSkillPaths(root, record.slug));
  }
  git(root, 'add', '-A', '--', ...new Set(paths));
  const action = replace ? 'replace' : 'add';
  git(root, 'commit', '-q', '-m', `ingest: ${action} ${record.slug}`);
  return git(root, 'rev-parse', 'HEAD');
}

function pushBaseline(root, branch) {
  git(root, 'push', '--quiet', 'origin', `HEAD:${branch}`);
}

module.exports = {
  commitFiles,
  createBaseline,
  pushBaseline,
  removeSkill,
  remoteBranch,
  trackedSkillPaths,
  writeFiles,
};
