#!/usr/bin/env node
'use strict';

const { parseArgs } = require('./lib/skill-cli/args');
const { loadCandidate } = require('./lib/skill-cli/candidate');
const { importCandidate } = require('./lib/skill-cli/import');
const { exitCodeFor, serializeResult } = require('./lib/skill-cli/output');
const { publishCandidate } = require('./lib/skill-cli/publish');
const { replaceCandidate } = require('./lib/skill-cli/replace');
const { createGhRunReader, statusOutcome, waitForPublishedRun } = require('./lib/skill-cli/status');

function failure(errors) {
  return {
    status: 'failed',
    slug: null,
    content_revision: null,
    content_status: 'failed',
    deploy_status: 'pending',
    commit_sha: null,
    run_url: null,
    public_url: null,
    errors,
  };
}

function previewOutcome(candidate) {
  return {
    status: 'previewed',
    slug: candidate.slug,
    content_revision: candidate.digest,
    content_status: 'previewed',
    deploy_status: 'pending',
    commit_sha: null,
    run_url: null,
    public_url: null,
    errors: [],
  };
}

async function waitForPublished(outcome) {
  if (!outcome.commit_sha) return outcome;
  const reader = createGhRunReader();
  const waited = await waitForPublishedRun({
    commitSha: outcome.commit_sha,
    findRun: reader.findByCommit,
    reader,
  });
  return waited ?? outcome;
}

async function publishOutcome(published, wait) {
  if (!published.ok) return failure(published.diagnostics);
  if (!wait) return { ...published.outcome, errors: [] };
  const outcome = await waitForPublished(published.outcome);
  return { ...outcome, errors: outcome.errors ?? [] };
}

async function commandResult(parsed) {
  if (parsed.command === 'preview' || parsed.command === 'add') {
    const loaded = loadCandidate({ inputPath: parsed.input, metaPath: parsed.metaPath });
    if (!loaded.ok) return failure(loaded.diagnostics);
    if (parsed.command === 'add' && parsed.publish) {
      return publishOutcome(
        publishCandidate({ projectRoot: process.cwd(), candidate: loaded.candidate }),
        parsed.wait,
      );
    }
    return previewOutcome(loaded.candidate);
  }
  if (parsed.command === 'import') {
    return publishOutcome(
      importCandidate({
        projectRoot: process.cwd(),
        source: parsed.source,
        metaPath: parsed.metaPath,
        publish: parsed.publish,
      }),
      parsed.wait,
    );
  }
  if (parsed.command === 'replace') {
    return publishOutcome(
      replaceCandidate({
        projectRoot: process.cwd(),
        slug: parsed.slug,
        inputPath: parsed.input,
        metaPath: parsed.metaPath,
        expectedRevision: parsed.expectedRevision,
      }),
      parsed.wait,
    );
  }
  if (parsed.command === 'status') {
    try {
      return statusOutcome(parsed.runId, createGhRunReader().get(parsed.runId));
    } catch {
      return failure([{ code: 'E_SOURCE', path: null, message: '运行状态读取失败' }]);
    }
  }
  return failure([{ code: 'E_INPUT', path: null, message: '命令尚未实现' }]);
}

function emit(result) {
  process.stdout.write(`${serializeResult(result)}\n`);
  if (Array.isArray(result.errors) && result.errors.length > 0) {
    process.stderr.write(`${result.errors.map((error) => error.code).join(',')}\n`);
  }
  process.exitCode = exitCodeFor(result);
}

async function main(argv) {
  const parsed = parseArgs(argv);
  if (!parsed.ok) {
    emit(failure(parsed.diagnostics));
    return;
  }
  emit(await commandResult(parsed));
}

main(process.argv.slice(2)).catch(() => {
  emit(failure([{ code: 'E_INPUT', path: null, message: '命令失败' }]));
});
