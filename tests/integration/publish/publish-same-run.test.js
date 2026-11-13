'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const YAML = require('yaml');

const root = path.resolve(__dirname, '../../..');
const workflowDir = path.join(root, '.github/workflows');
const PUBLISH_MARKERS = ['deploy-pages@', 'upload-pages-artifact@', 'publish-check.js'];

function readWorkflows() {
  return fs
    .readdirSync(workflowDir)
    .filter((name) => /\.ya?ml$/.test(name))
    .sort()
    .map((name) => {
      const text = fs.readFileSync(path.join(workflowDir, name), 'utf8');
      return { name, text, workflow: YAML.parse(text) };
    });
}

function asArray(value) {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

test('publishing stays in one workflow and one run without workflow_run chaining', () => {
  const workflows = readWorkflows();
  const publishing = workflows.filter((item) =>
    PUBLISH_MARKERS.some((marker) => item.text.includes(marker)),
  );
  assert.deepEqual(
    publishing.map((item) => item.name),
    ['maintain.yml'],
    'only maintain.yml may verify, upload or deploy the site',
  );

  for (const item of workflows) {
    assert.equal(item.workflow.on?.workflow_run, undefined, `${item.name} must not chain runs`);
    assert.doesNotMatch(item.text, /workflow_run/, item.name);
  }

  const maintain = workflows.find((item) => item.name === 'maintain.yml').workflow;
  const build = maintain.jobs.build;
  const deploy = maintain.jobs.deploy;
  assert.ok(build, 'build job is missing');
  assert.ok(deploy, 'deploy job is missing');

  assert.deepEqual(asArray(deploy.needs), ['build']);
  assert.ok(asArray(build.needs).includes('sync'), 'build must wait for source sync');
  assert.match(String(build.if), /needs\.sync\.result/, 'build must honor sync result');
  assert.match(
    String(deploy.if),
    /needs\.build\.result == 'success'/,
    'deploy must run after a successful build even when sync is skipped',
  );
});

test('the workflow structure can add a sync job ahead of build without a second deploy entry', () => {
  const maintain = readWorkflows().find((item) => item.name === 'maintain.yml').workflow;
  const build = maintain.jobs.build;
  const deploy = maintain.jobs.deploy;

  assert.ok(asArray(deploy.needs).includes('build'));
  assert.ok(asArray(build.needs).includes('sync'));
  assert.match(String(build.if), /needs\.sync\.result/);
  assert.match(String(deploy.if), /needs\.build\.result == 'success'/);
  assert.doesNotMatch(String(deploy.if || ''), /github\.event_name/);
  assert.equal(maintain.on.workflow_dispatch !== undefined, true);

  const deploySteps = deploy.steps.filter((step) =>
    String(step.uses || '').startsWith('actions/deploy-pages@'),
  );
  assert.equal(deploySteps.length, 1, 'a single deploy step keeps retries idempotent');
});
