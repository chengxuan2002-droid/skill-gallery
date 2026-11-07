'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const { createRunStatus, renderSummary } = require('../../scripts/lib/publish');
const { createSummaryStatus } = require('../../scripts/lib/publish-summary');

const target = 'a'.repeat(40);
const revision = 'rev-1';

function status(overrides = {}) {
  return {
    runId: 'run-1',
    trigger: 'push',
    targetSha: target,
    commitStatus: 'not_applicable',
    contentRevision: revision,
    contentStatus: 'noop',
    deployStatus: 'published',
    reason: null,
    startedAt: null,
    finishedAt: null,
    runUrl: 'https://github.com/example/skill-gallery/actions/runs/1',
    ...overrides,
  };
}

test('noop content is recorded without creating a new content commit', () => {
  for (const commitStatus of ['not_applicable', 'committed']) {
    for (const deployStatus of ['published', 'superseded']) {
      const result = createRunStatus(status({ commitStatus, deployStatus }));
      assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
      assert.equal(result.status.content_status, 'noop');
      assert.equal(result.status.commit_status, commitStatus);
      assert.equal(result.status.deploy_status, deployStatus);
      assert.equal(result.status.content_revision, revision);
      assert.equal(result.status.target_sha, target);
    }
  }
});

test('a noop retry keeps the same target commit and content revision', () => {
  const first = createRunStatus(status({ deployStatus: 'failed' }));
  const retry = createRunStatus(status({ deployStatus: 'published' }));
  assert.equal(first.ok, true);
  assert.equal(retry.ok, true);
  assert.equal(first.status.target_sha, retry.status.target_sha);
  assert.equal(first.status.content_revision, retry.status.content_revision);
  assert.equal(first.status.content_status, 'noop');
  assert.equal(retry.status.content_status, 'noop');
});

test('summary distinguishes noop from built and never reports superseded as published', () => {
  const result = createRunStatus(status({ deployStatus: 'superseded', reason: 'E_SUPERSEDED' }));
  assert.equal(result.ok, true);
  const markdown = renderSummary(result.status);

  assert.match(markdown, /Content status: noop/);
  assert.match(markdown, /Deploy status: superseded/);
  assert.doesNotMatch(markdown, /Content status: built/);
  assert.doesNotMatch(markdown, /Deploy status: published/);
});

test('the CI summary helper maps an unchanged run to noop', () => {
  const result = createSummaryStatus({
    PUBLISH_RUN_ID: 'run-2',
    PUBLISH_TRIGGER: 'workflow_dispatch',
    PUBLISH_TARGET_SHA: target,
    PUBLISH_COMMIT_STATUS: 'not_applicable',
    PUBLISH_CONTENT_REVISION: revision,
    PUBLISH_CONTENT_STATUS: 'noop',
    PUBLISH_PHASE: 'deploy',
    PUBLISH_DEPLOY_OUTCOME: 'success',
    PUBLISH_JOB_STATUS: 'success',
    PUBLISH_RUN_URL: 'https://github.com/example/skill-gallery/actions/runs/2',
  });

  assert.equal(result.ok, true, JSON.stringify(result.diagnostics));
  assert.equal(result.status.content_status, 'noop');
  assert.equal(result.status.deploy_status, 'published');
  assert.equal(result.status.commit_status, 'not_applicable');
  assert.equal(result.status.target_sha, target);
});
