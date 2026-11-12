'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const YAML = require('yaml');

const root = path.resolve(__dirname, '../../..');
const workflowPath = path.join(root, '.github/workflows/maintain.yml');

function workflow() {
  return YAML.parse(fs.readFileSync(workflowPath, 'utf8'));
}

function steps(job) {
  return job && Array.isArray(job.steps) ? job.steps : [];
}

function asArray(value) {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

test('sync runs daily at 03:17 Asia/Shanghai and supports manual sync', () => {
  const value = workflow();
  assert.ok(value.on.schedule);
  assert.deepEqual(
    value.on.schedule.map((item) => item.cron),
    ['17 19 * * *'],
  );
  assert.equal(value.on.workflow_dispatch.inputs.sync.type, 'boolean');
  assert.equal(value.on.workflow_dispatch.inputs.sync.default, false);
  assert.equal(value.on.workflow_dispatch.inputs.slug.type, 'string');
  assert.equal(value.on.pull_request, undefined);
  assert.equal(value.on.pull_request_target, undefined);
  assert.equal(value.on.workflow_run, undefined);
});

test('sync is the only write job and build/deploy stay minimal', () => {
  const value = workflow();
  const sync = value.jobs.sync;
  const build = value.jobs.build;
  const deploy = value.jobs.deploy;
  assert.ok(sync);
  assert.deepEqual(sync.permissions, { contents: 'write' });
  assert.deepEqual(build.permissions ?? { contents: 'read' }, { contents: 'read' });
  assert.deepEqual(deploy.permissions, {
    contents: 'read',
    pages: 'write',
    'id-token': 'write',
  });
  for (const [name, job] of Object.entries(value.jobs)) {
    for (const scope of ['pages', 'id-token']) {
      if (name === 'deploy') continue;
      assert.equal(job.permissions?.[scope], undefined, name);
    }
  }
});

test('sync job uses the locked toolchain and a restricted token', () => {
  const sync = workflow().jobs.sync;
  assert.equal(sync['timeout-minutes'], 30);
  const syncSteps = steps(sync);
  const checkout = syncSteps.find((step) =>
    String(step.uses || '').startsWith('actions/checkout@'),
  );
  assert.ok(checkout);
  assert.equal(checkout.with['persist-credentials'], false);
  assert.ok(syncSteps.some((step) => String(step.uses || '').startsWith('actions/setup-node@')));
  assert.ok(syncSteps.some((step) => String(step.run || '').includes('npm ci')));
  assert.ok(syncSteps.some((step) => String(step.run || '').includes('gh auth setup-git')));
  const syncStep = syncSteps.find((step) => String(step.run || '').includes('sync-skills.js'));
  assert.ok(syncStep);
  assert.equal(syncStep.env.GH_TOKEN, '${{ github.token }}');
  assert.match(String(syncStep.run), /--apply/);
  assert.match(String(syncStep.run), /--push/);
  assert.equal(syncStep.env.SYNC_SLUG, '${{ inputs.slug }}');
  for (const name of ['build', 'deploy']) {
    for (const step of steps(workflow().jobs[name])) {
      assert.doesNotMatch(JSON.stringify(step.env ?? {}), /GH_TOKEN|github\.token/);
    }
  }
});

test('sync feeds the same run into build and deploy by target SHA', () => {
  const value = workflow();
  const sync = value.jobs.sync;
  const build = value.jobs.build;
  const deploy = value.jobs.deploy;
  assert.equal(sync.outputs.changed, '${{ steps.sync.outputs.changed }}');
  assert.equal(sync.outputs.commit_sha, '${{ steps.sync.outputs.commit_sha }}');
  assert.equal(sync.outputs.commit_status, '${{ steps.sync.outputs.commit_status }}');
  assert.match(String(sync.if), /schedule/);
  assert.match(String(sync.if), /inputs\.sync/);
  assert.ok(asArray(build.needs).includes('sync'));
  assert.match(String(build.if), /needs\.sync\.result/);
  assert.match(String(build.if), /changed/);
  assert.match(String(deploy.needs), /build/);

  const buildCheckout = steps(build).find((step) =>
    String(step.uses || '').startsWith('actions/checkout@'),
  );
  assert.match(String(buildCheckout.with.ref), /needs\.sync\.outputs\.commit_sha/);
  assert.equal(build.outputs.target_sha, '${{ steps.target.outputs.sha }}');
  assert.equal(
    build.outputs.commit_status,
    "${{ needs.sync.outputs.commit_status || 'not_applicable' }}",
  );
  assert.match(String(build.outputs.target_sha), /target/);

  const deployCheckout = steps(deploy).find((step) =>
    String(step.uses || '').startsWith('actions/checkout@'),
  );
  assert.match(String(deployCheckout.with.ref), /needs\.build\.outputs\.target_sha/);
  const freshness = steps(deploy).find((step) => step.id === 'freshness');
  assert.match(String(freshness.run), /needs\.build\.outputs\.target_sha|PUBLISH_TARGET_SHA/);
  const summary = steps(deploy).find((step) => step.name === 'Write publish summary');
  assert.match(String(summary.env.PUBLISH_TARGET_SHA), /needs\.build\.outputs\.target_sha/);
  assert.match(String(summary.env.PUBLISH_COMMIT_STATUS), /needs\.build\.outputs\.commit_status/);
});

test('workflow actions stay pinned and no secrets or workflow chaining are introduced', () => {
  const text = fs.readFileSync(workflowPath, 'utf8');
  const value = workflow();
  assert.doesNotMatch(text, /\$\{\{\s*secrets\./);
  assert.doesNotMatch(text, /\bGH_PAT\b|\bPAT_TOKEN\b|personal[ _-]?access[ _-]?token/i);
  assert.doesNotMatch(text, /pull_request|workflow_run|issue_comment|repository_dispatch/i);
  assert.doesNotMatch(text, /write-all/);
  for (const job of Object.values(value.jobs)) {
    for (const step of steps(job)) {
      if (step.uses) assert.match(step.uses, /@[0-9a-f]{40}$/, step.uses);
    }
  }
});
