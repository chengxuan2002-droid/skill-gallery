'use strict';

const { isDigest, isNonEmptyString, isPlainObject } = require('./catalog-values');
const { createDiagnostic } = require('./diagnostics');
const { normalizeRelativePath } = require('./paths');

const LICENSE_TRACKING_KEYS = new Set(['path', 'sha256']);

function diagnose(diagnostics, code, context, message) {
  diagnostics.push(createDiagnostic(code, { ...context, message }));
}

function normalizeSourceLicense(value, slug, diagnostics) {
  const license = value ?? null;
  if (license === null) return null;
  if (!isPlainObject(license)) {
    diagnose(
      diagnostics,
      'E_SCHEMA',
      { slug },
      'source_tracking.last_synced_license 必须是对象或 null',
    );
    return null;
  }
  for (const key of Object.keys(license)) {
    if (!LICENSE_TRACKING_KEYS.has(key)) {
      diagnose(diagnostics, 'E_SCHEMA', { slug }, 'source_tracking.last_synced_license 含未知字段');
    }
  }
  let validPath = false;
  if (!isNonEmptyString(license.path)) {
    diagnose(
      diagnostics,
      'E_SCHEMA',
      { slug },
      'source_tracking.last_synced_license.path 必须是非空字符串',
    );
  } else if (!normalizeRelativePath(license.path).ok) {
    diagnose(
      diagnostics,
      'E_SCHEMA',
      { slug, path: license.path },
      'source_tracking.last_synced_license.path 必须是安全相对路径',
    );
  } else {
    validPath = true;
  }
  const validDigest = isDigest(license.sha256);
  if (!validDigest) {
    diagnose(
      diagnostics,
      'E_SCHEMA',
      { slug },
      'source_tracking.last_synced_license.sha256 不合法',
    );
  }
  return validPath && validDigest ? { path: license.path, sha256: license.sha256 } : null;
}

module.exports = { normalizeSourceLicense };
