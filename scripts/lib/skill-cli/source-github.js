'use strict';

const path = require('node:path');
const { execFileSync } = require('node:child_process');

const REF_POLICIES = new Set(['branch', 'release', 'pinned']);
const MAX_TOTAL_BYTES = 20 * 1024 * 1024;
const SHA_PATTERN = /^[0-9a-f]{40}$/;

function diagnosticSource(message, target = null) {
  return { code: 'E_SOURCE', path: target, message };
}

function diagnosticSchema(message, target = null) {
  return { code: 'E_SCHEMA', path: target, message };
}

function isSafeRelativePath(value) {
  if (typeof value !== 'string' || value.length === 0) return false;
  if (value.startsWith('/') || /^[A-Za-z]:/.test(value) || value.includes('\\')) return false;
  if (Array.from(value).some((character) => character.charCodeAt(0) < 32)) return false;
  const segments = value.split('/');
  return segments.every((segment) => segment !== '' && segment !== '.' && segment !== '..');
}

function validateSource(source) {
  if (!source || typeof source !== 'object') return diagnosticSchema('来源定位必须是对象');
  if (/^[A-Za-z][A-Za-z0-9+.-]*:\/\//.test(source.repository || '')) {
    return diagnosticSchema('只接受结构化 owner/repository，不接受网页地址', source.repository);
  }
  if (typeof source.repository !== 'string' || !/^[^/\s]+\/[^/\s]+$/.test(source.repository)) {
    return diagnosticSchema('--repo 必须是 owner/repository', source.repository);
  }
  if (!isSafeRelativePath(source.path)) {
    return diagnosticSchema('来源路径必须是安全的 POSIX 相对路径', source.path);
  }
  if (typeof source.ref !== 'string' || source.ref.length === 0) {
    return diagnosticSchema('来源 ref 不能为空', source.ref);
  }
  if (!REF_POLICIES.has(source.refPolicy || 'branch')) {
    return diagnosticSchema('来源 ref_policy 不合法', source.refPolicy);
  }
  return null;
}

function normalizeFiles(files) {
  const entries = files instanceof Map ? [...files.entries()] : Object.entries(files || {});
  const normalized = new Map();
  let total = 0;
  for (const [relativePath, value] of entries) {
    if (!isSafeRelativePath(relativePath)) {
      return { error: diagnosticSource('来源文件路径越界', relativePath) };
    }
    let bytes = value;
    if (value && typeof value === 'object' && !Buffer.isBuffer(value)) {
      const mode = String(value.mode || '100644');
      if (mode === '120000' || mode === '160000') {
        return { error: diagnosticSource('来源包含链接或子模块', relativePath) };
      }
      bytes = value.bytes;
    }
    if (!Buffer.isBuffer(bytes) && typeof bytes !== 'string') {
      return { error: diagnosticSource('来源文件内容无法读取', relativePath) };
    }
    const buffer = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes, 'utf8');
    total += buffer.length;
    if (total > MAX_TOTAL_BYTES) {
      return { error: diagnosticSource('来源内容超过大小限制', relativePath) };
    }
    normalized.set(relativePath, buffer);
  }
  if (normalized.size === 0) return { error: diagnosticSource('来源没有可用文件') };
  return { files: normalized };
}

function ghApi(requestPath) {
  let raw;
  try {
    raw = execFileSync('gh', ['api', requestPath], {
      encoding: 'utf8',
      maxBuffer: 32 * 1024 * 1024,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch {
    const error = new Error('source read failed');
    error.code = 'E_SOURCE';
    throw error;
  }
  return JSON.parse(raw);
}

function resolveRevision(source) {
  const repository = source.repository;
  const policy = source.refPolicy || 'branch';
  if (policy === 'pinned') {
    if (!SHA_PATTERN.test(source.ref)) {
      const error = new Error('pinned ref must be a commit');
      error.code = 'E_SOURCE';
      throw error;
    }
    return source.ref;
  }
  if (policy === 'branch') {
    const ref = ghApi(`repos/${repository}/git/ref/heads/${source.ref}`);
    return ref.object.sha;
  }
  const release = ghApi(`repos/${repository}/releases/latest`);
  const tag = ghApi(`repos/${repository}/git/ref/tags/${release.tag_name}`);
  if (tag.object.type === 'tag') {
    const annotated = ghApi(`repos/${repository}/git/tags/${tag.object.sha}`);
    return annotated.object.sha;
  }
  return tag.object.sha;
}

function selectEntries(tree, sourcePath) {
  const prefix = sourcePath.replace(/\/+$/, '');
  const exact = tree.find((entry) => entry.path === prefix);
  if (exact && exact.type === 'blob') {
    return [{ path: path.posix.basename(prefix), entry: exact }];
  }
  const nested = tree.filter((entry) => entry.path.startsWith(`${prefix}/`));
  return nested
    .filter((entry) => entry.type === 'blob')
    .map((entry) => ({ path: entry.path.slice(prefix.length + 1), entry }));
}

function createGhReader() {
  return {
    resolve(source) {
      const revision = resolveRevision(source);
      const tree = ghApi(`repos/${source.repository}/git/trees/${revision}?recursive=1`);
      if (tree.truncated) return { ok: true, revision, truncated: true, files: new Map() };
      const entries = selectEntries(tree.tree || [], source.path);
      if (entries.length === 0) {
        const error = new Error('source path not found');
        error.code = 'E_SOURCE';
        throw error;
      }
      const files = new Map();
      for (const item of entries) {
        if (item.entry.mode === '120000' || item.entry.mode === '160000') {
          return { ok: false, message: '来源包含链接或子模块' };
        }
        const blob = ghApi(`repos/${source.repository}/git/blobs/${item.entry.sha}`);
        files.set(item.path, {
          mode: item.entry.mode,
          bytes: Buffer.from(blob.content, blob.encoding === 'base64' ? 'base64' : 'utf8'),
        });
      }
      return { ok: true, revision, truncated: false, files };
    },
  };
}

function fetchSource({ source, reader = createGhReader() }) {
  const invalid = validateSource(source);
  if (invalid) return { ok: false, diagnostics: [invalid] };

  let resolved;
  try {
    resolved = reader.resolve(source);
  } catch {
    return { ok: false, diagnostics: [diagnosticSource('来源读取失败')] };
  }
  if (!resolved || resolved.ok === false) {
    return {
      ok: false,
      diagnostics: [diagnosticSource(resolved?.message || '来源读取失败')],
    };
  }
  if (resolved.truncated) {
    return { ok: false, diagnostics: [diagnosticSource('来源文件树被截断')] };
  }
  if (typeof resolved.revision !== 'string' || !SHA_PATTERN.test(resolved.revision)) {
    return { ok: false, diagnostics: [diagnosticSource('来源修订不是不可变提交')] };
  }
  const normalized = normalizeFiles(resolved.files);
  if (normalized.error) return { ok: false, diagnostics: [normalized.error] };
  return { ok: true, revision: resolved.revision, files: normalized.files };
}

module.exports = { createGhReader, fetchSource, validateSource };
