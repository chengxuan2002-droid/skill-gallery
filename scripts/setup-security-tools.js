const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { spawnSync } = require('node:child_process');

function verifyArchive(bytes, expected) {
  if (createHash('sha256').update(bytes).digest('hex') !== expected) {
    throw new Error('ARCHIVE_HASH_MISMATCH');
  }
}

function version(binary, flag) {
  const result = spawnSync(binary, [flag], { encoding: 'utf8', timeout: 30000 });
  return result.status === 0 ? result.stdout.trim().replace(/^v/, '') : null;
}

async function install() {
  const root = path.resolve(__dirname, '..');
  const tools = require('../config/security-tools.json');
  const bin = path.join(root, '.tools/bin');
  fs.mkdirSync(bin, { recursive: true });
  const gitleaks = path.join(bin, 'gitleaks');
  if (version(gitleaks, 'version') !== tools.gitleaks.version) {
    const platform = `${process.platform}_${process.arch}`;
    const expected = tools.gitleaks.sha256[platform];
    if (!expected) throw new Error('UNSUPPORTED_PLATFORM');
    const archiveName = `gitleaks_${tools.gitleaks.version}_${platform}.tar.gz`;
    const url = `https://github.com/gitleaks/gitleaks/releases/download/v${tools.gitleaks.version}/${archiveName}`;
    const response = await fetch(url, { signal: AbortSignal.timeout(120000) });
    if (!response.ok) throw new Error('SCANNER_DOWNLOAD_FAILED');
    const bytes = Buffer.from(await response.arrayBuffer());
    verifyArchive(bytes, expected);
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-gallery-tools-'));
    try {
      const archive = path.join(temp, 'gitleaks.tar.gz');
      fs.writeFileSync(archive, bytes, { mode: 0o600 });
      const extract = spawnSync('tar', ['-xzf', archive, '-C', temp, 'gitleaks']);
      if (extract.status !== 0) throw new Error('SCANNER_EXTRACTION_FAILED');
      fs.copyFileSync(path.join(temp, 'gitleaks'), gitleaks);
      fs.chmodSync(gitleaks, 0o755);
    } finally {
      fs.rmSync(temp, { recursive: true, force: true });
    }
  }
  const semgrep = path.join(bin, 'semgrep');
  if (version(semgrep, '--version') !== tools.semgrep.version) {
    const result = spawnSync(
      'uv',
      ['tool', 'install', '--python', tools.semgrep.python, `semgrep==${tools.semgrep.version}`],
      {
        env: { ...process.env, UV_TOOL_DIR: path.join(root, '.tools/uv'), UV_TOOL_BIN_DIR: bin },
        encoding: 'utf8',
        timeout: 300000,
        maxBuffer: 8 * 1024 * 1024,
      },
    );
    if (result.status !== 0) throw new Error('SEMGREP_INSTALL_FAILED');
  }
  if (
    version(gitleaks, 'version') !== tools.gitleaks.version ||
    version(semgrep, '--version') !== tools.semgrep.version
  ) {
    throw new Error('SCANNER_VERSION_MISMATCH');
  }
  return { status: 'passed', gitleaks: tools.gitleaks.version, semgrep: tools.semgrep.version };
}

if (require.main === module) {
  install().then(
    (result) => console.log(JSON.stringify(result)),
    (error) => {
      const code = /^[A-Z_]+$/.test(error.message) ? error.message : 'SCANNER_SETUP_FAILED';
      console.log(JSON.stringify({ status: 'error', code }));
      process.exitCode = 2;
    },
  );
}

module.exports = { verifyArchive };
