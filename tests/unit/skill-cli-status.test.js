'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const { deriveRunStatus, statusOutcome, waitForRun } = require('../../scripts/lib/skill-cli/status');

function completedRun(overrides = {}) {
  return {
    status: 'completed',
    conclusion: 'success',
    headSha: 'a'.repeat(40),
    url: 'https://github.com/owner/repository/actions/runs/1',
    jobs: [
      { name: 'build', conclusion: 'success', steps: [] },
      {
        name: 'deploy',
        conclusion: 'success',
        steps: [{ name: 'Deploy to GitHub Pages', conclusion: 'success' }],
      },
    ],
    ...overrides,
  };
}

test('derives published when build and deploy succeed', () => {
  const derived = deriveRunStatus(completedRun());
  assert.equal(derived.content_status, 'built');
  assert.equal(derived.deploy_status, 'published');

  const outcome = statusOutcome('1', completedRun());
  assert.equal(outcome.status, 'published');
  assert.equal(outcome.commit_sha, 'a'.repeat(40));
  assert.deepEqual(outcome.errors, []);
});

test('derives superseded when the deploy step is skipped after a successful build', () => {
  const run = completedRun({
    jobs: [
      { name: 'build', conclusion: 'success', steps: [] },
      {
        name: 'deploy',
        conclusion: 'success',
        steps: [{ name: 'Deploy to GitHub Pages', conclusion: 'skipped' }],
      },
    ],
  });
  const derived = deriveRunStatus(run);
  assert.equal(derived.content_status, 'built');
  assert.equal(derived.deploy_status, 'superseded');

  const outcome = statusOutcome('1', run);
  assert.equal(outcome.status, 'superseded');
  assert.equal(outcome.errors[0].code, 'E_SUPERSEDED');
});

test('separates build failure from deployment and never reports published', () => {
  const run = completedRun({
    conclusion: 'failure',
    jobs: [
      { name: 'build', conclusion: 'failure', steps: [] },
      { name: 'deploy', conclusion: 'skipped', steps: [] },
    ],
  });
  const derived = deriveRunStatus(run);
  assert.equal(derived.content_status, 'failed');
  assert.equal(derived.deploy_status, 'pending');
  const outcome = statusOutcome('1', run);
  assert.equal(outcome.status, 'failed');
  assert.equal(outcome.errors[0].code, 'E_BUILD');
});

test('reports deployment failure while keeping the built content status', () => {
  const run = completedRun({
    conclusion: 'failure',
    jobs: [
      { name: 'build', conclusion: 'success', steps: [] },
      {
        name: 'deploy',
        conclusion: 'failure',
        steps: [{ name: 'Deploy to GitHub Pages', conclusion: 'failure' }],
      },
    ],
  });
  const derived = deriveRunStatus(run);
  assert.equal(derived.content_status, 'built');
  assert.equal(derived.deploy_status, 'failed');
  const outcome = statusOutcome('1', run);
  assert.equal(outcome.status, 'failed');
  assert.equal(outcome.errors[0].code, 'E_DEPLOY');
});

test('keeps pending states pending', () => {
  const queued = deriveRunStatus({
    status: 'queued',
    conclusion: null,
    jobs: [],
    headSha: 'a'.repeat(40),
    url: 'https://github.com/owner/repository/actions/runs/2',
  });
  assert.equal(queued.content_status, 'pending');
  assert.equal(queued.deploy_status, 'pending');

  const deploying = deriveRunStatus({
    status: 'in_progress',
    conclusion: null,
    jobs: [
      { name: 'build', conclusion: 'success', steps: [] },
      {
        name: 'deploy',
        conclusion: null,
        steps: [{ name: 'Deploy to GitHub Pages', conclusion: null }],
      },
    ],
    headSha: 'a'.repeat(40),
    url: 'https://github.com/owner/repository/actions/runs/3',
  });
  assert.equal(deploying.deploy_status, 'deploying');
  assert.equal(statusOutcome('3', {
    status: 'in_progress',
    conclusion: null,
    jobs: deploying.jobs,
    headSha: deploying.head_sha,
    url: deploying.run_url,
  }).status, 'pending');
});

test('waitForRun stops at terminal states and times out without reporting published', async () => {
  let clock = 0;
  const now = () => clock;
  const sleep = async (ms) => {
    clock += ms;
  };

  const pendingRun = {
    status: 'in_progress',
    conclusion: null,
    jobs: [{ name: 'build', conclusion: null, steps: [] }],
    headSha: 'a'.repeat(40),
    url: 'https://github.com/owner/repository/actions/runs/4',
  };
  const publishedRun = completedRun();

  const queued = [pendingRun, publishedRun];
  const done = await waitForRun({
    runId: '4',
    reader: { get: () => queued.shift() },
    timeoutMs: 100,
    intervalMs: 10,
    now,
    sleep,
  });
  assert.equal(done.timeout, false);
  assert.equal(done.outcome.status, 'published');

  clock = 0;
  const timedOut = await waitForRun({
    runId: '5',
    reader: { get: () => pendingRun },
    timeoutMs: 30,
    intervalMs: 10,
    now,
    sleep,
  });
  assert.equal(timedOut.timeout, true);
  assert.equal(timedOut.outcome.status, 'pending');
  assert.equal(timedOut.outcome.errors[0].code, 'E_TIMEOUT');
  assert.notEqual(timedOut.outcome.status, 'published');
});
