'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const YAML = require('yaml');

const root = path.resolve(__dirname, '../..');
const workflowPath = path.join(root, '.github/workflows/maintain.yml');
const workflowText = fs.readFileSync(workflowPath, 'utf8');
const workflow = YAML.parse(workflowText);

function steps(job) {
  return job && Array.isArray(job.steps) ? job.steps : [];
}

function jobs() {
  return Object.entries(workflow.jobs || {});
}

test('workflow and build jobs keep read-only repository permissions', () => {
  assert.deepEqual(workflow.permissions, { contents: 'read' });
  assert.equal(workflow.env, undefined);

  const build = workflow.jobs.build;
  assert.ok(build);
  if (build.permissions !== undefined) {
    assert.deepEqual(build.permissions, { contents: 'read' });
  }
  assert.equal(build.env, undefined);

  for (const [name, job] of jobs()) {
    if (name === 'deploy') continue;
    assert.equal(job.env, undefined, name);
    for (const [scope, access] of Object.entries(job.permissions || {})) {
      assert.notEqual(access, 'write', `${name} must not request ${scope}: write`);
    }
  }
  assert.doesNotMatch(workflowText, /write-all/);
});

test('deploy adds only pages and id-token writes', () => {
  const deploy = workflow.jobs.deploy;
  assert.ok(deploy);
  assert.deepEqual(deploy.permissions, {
    contents: 'read',
    pages: 'write',
    'id-token': 'write',
  });

  for (const [name, job] of jobs()) {
    if (name === 'deploy') continue;
    const permissions = job.permissions || {};
    assert.equal(permissions.pages, undefined, name);
    assert.equal(permissions['id-token'], undefined, name);
  }
});

test('checkouts avoid persisted credentials and no secrets or PATs are referenced', () => {
  let checkoutCount = 0;
  for (const [name, job] of jobs()) {
    const checkouts = steps(job).filter((step) =>
      String(step.uses || '').startsWith('actions/checkout@'),
    );
    assert.ok(checkouts.length > 0, `${name} must check out the repository`);
    for (const checkout of checkouts) {
      assert.equal(checkout.with?.['persist-credentials'], false, name);
      checkoutCount += 1;
    }
  }
  assert.ok(checkoutCount >= 2);

  assert.doesNotMatch(workflowText, /\$\{\{\s*secrets\./);
  assert.doesNotMatch(workflowText, /\bsecrets\s*:/);
  assert.doesNotMatch(workflowText, /github\.token/i);
  assert.doesNotMatch(workflowText, /\bGH_PAT\b|\bPAT_TOKEN\b|personal[ _-]?access[ _-]?token/i);
  assert.equal(workflow.on.pull_request, undefined);
  assert.equal(workflow.on.pull_request_target, undefined);
  assert.equal(workflow.on.workflow_run, undefined);
  assert.doesNotMatch(workflowText, /pull_request|workflow_run|issue_comment|repository_dispatch/i);
});

test('step summaries stay on the sanitized status allowlist', () => {
  const summarySteps = jobs()
    .flatMap(([, job]) => steps(job))
    .filter((step) => String(step.run || '').includes('publish-summary.js'));
  assert.ok(summarySteps.length >= 2);

  for (const step of summarySteps) {
    const env = step.env || {};
    assert.ok(Object.keys(env).length > 0, step.name);
    for (const [key, value] of Object.entries(env)) {
      assert.match(key, /^PUBLISH_[A-Z0-9_]+$/, `${step.name} exposes ${key}`);
      assert.equal(typeof value, 'string', `${key} must stay a literal or expression`);
      assert.doesNotMatch(
        value,
        /secrets\b|github\.token|token|password|cookie|authorization|credential/i,
        `${key} must not reference sensitive context`,
      );
    }
  }
});
