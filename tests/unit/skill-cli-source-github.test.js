'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const shared = require('../../scripts/lib/github-source');
const { fetchSource } = require('../../scripts/lib/skill-cli/source-github');

const REVISION = 'a'.repeat(40);

function source() {
  return {
    repository: 'owner/repository',
    path: 'skills/example',
    ref_policy: 'branch',
    ref: 'main',
    enabled: true,
  };
}

test('fetchSource creates the default gh reader when none is injected', (t) => {
  const original = shared.createGhReader;
  let calls = 0;
  shared.createGhReader = () => {
    calls += 1;
    return {
      resolve() {
        return {
          ok: true,
          revision: REVISION,
          files: new Map([['SKILL.md', Buffer.from('# Example\n')]]),
          modes: new Map([['SKILL.md', '100644']]),
          licenseFiles: new Map(),
          licenseModes: new Map(),
        };
      },
    };
  };
  t.after(() => {
    shared.createGhReader = original;
  });

  const result = fetchSource({ source: source() });

  assert.equal(calls, 1);
  assert.equal(result.ok, true);
  assert.equal(result.revision, REVISION);
  assert.equal(result.files.get('SKILL.md').toString('utf8'), '# Example\n');
});

test('fetchSource prefers an injected reader over the gh default', (t) => {
  const original = shared.createGhReader;
  let defaultCalls = 0;
  shared.createGhReader = () => {
    defaultCalls += 1;
    throw new Error('default reader must not be used');
  };
  t.after(() => {
    shared.createGhReader = original;
  });

  const result = fetchSource({
    source: source(),
    reader: {
      resolve() {
        return {
          ok: true,
          revision: REVISION,
          files: new Map([['SKILL.md', Buffer.from('# Injected\n')]]),
          modes: new Map([['SKILL.md', '100644']]),
          licenseFiles: new Map(),
          licenseModes: new Map(),
        };
      },
    },
  });

  assert.equal(defaultCalls, 0);
  assert.equal(result.ok, true);
  assert.equal(result.files.get('SKILL.md').toString('utf8'), '# Injected\n');
});
