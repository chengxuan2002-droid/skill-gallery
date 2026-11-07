#!/usr/bin/env node
'use strict';

const { parseArgs } = require('./lib/skill-cli/args');
const { loadCandidate } = require('./lib/skill-cli/candidate');
const { exitCodeFor, serializeResult } = require('./lib/skill-cli/output');
const { publishCandidate } = require('./lib/skill-cli/publish');

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

function commandResult(parsed) {
  if (parsed.command === 'preview' || parsed.command === 'add') {
    const loaded = loadCandidate({ inputPath: parsed.input, metaPath: parsed.metaPath });
    if (!loaded.ok) return failure(loaded.diagnostics);
    if (parsed.command === 'add' && parsed.publish) {
      const published = publishCandidate({
        projectRoot: process.cwd(),
        candidate: loaded.candidate,
      });
      if (!published.ok) return failure(published.diagnostics);
      return { ...published.outcome, errors: [] };
    }
    return previewOutcome(loaded.candidate);
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

function main(argv) {
  const parsed = parseArgs(argv);
  if (!parsed.ok) {
    emit(failure(parsed.diagnostics));
    return;
  }
  emit(commandResult(parsed));
}

try {
  main(process.argv.slice(2));
} catch {
  emit(failure([{ code: 'E_INPUT', path: null, message: '命令失败' }]));
}
