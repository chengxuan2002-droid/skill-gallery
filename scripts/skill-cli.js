#!/usr/bin/env node
'use strict';

const { parseArgs } = require('./lib/skill-cli/args');
const { exitCodeFor, serializeResult } = require('./lib/skill-cli/output');

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
  emit(failure([{ code: 'E_INPUT', path: null, message: '命令尚未实现' }]));
}

try {
  main(process.argv.slice(2));
} catch {
  emit(failure([{ code: 'E_INPUT', path: null, message: '命令失败' }]));
}
