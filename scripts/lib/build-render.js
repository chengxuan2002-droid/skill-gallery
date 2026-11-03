const path = require('node:path');
const sanitizeHtml = require('sanitize-html');

const { createDiagnostic } = require('./diagnostics');

const HEADINGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
const ALLOWED_TAGS = [
  ...HEADINGS,
  'p',
  'br',
  'hr',
  'ul',
  'ol',
  'li',
  'blockquote',
  'strong',
  'em',
  'del',
  'pre',
  'code',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
  'a',
  'img',
];
const ALLOWED_ATTRIBUTES = {
  a: ['href', 'rel', 'target'],
  img: ['src', 'alt', 'title'],
  code: ['class'],
  h1: ['id'],
  h2: ['id'],
  h3: ['id'],
  h4: ['id'],
  h5: ['id'],
  h6: ['id'],
  '*': [],
};

function diagnostic(code, relativePath, message) {
  return createDiagnostic(code, { path: relativePath, message });
}

function aliasFor(text) {
  return (
    text
      .normalize('NFC')
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^\p{L}\p{N}_-]/gu, '') || 'section'
  );
}

function collectHeadings(tokens, result = []) {
  for (const token of tokens) {
    if (token.type === 'heading') {
      result.push(
        (token.text || '')
          .replace(/`([^`]*)`/g, '$1')
          .replace(/<[^>]*>/g, '')
          .replace(/[*_~]/g, ''),
      );
      continue;
    }
    if (Array.isArray(token.tokens)) collectHeadings(token.tokens, result);
    if (Array.isArray(token.items)) {
      for (const item of token.items) {
        if (Array.isArray(item.tokens)) collectHeadings(item.tokens, result);
      }
    }
  }
  return result;
}

function aliasMap(tokens) {
  const used = new Set();
  const aliases = new Map();
  collectHeadings(tokens).forEach((text, index) => {
    const base = aliasFor(text);
    let alias = base;
    let suffix = 0;
    while (used.has(alias)) {
      suffix += 1;
      alias = `${base}-${suffix}`;
    }
    used.add(alias);
    aliases.set(alias, `#skill-heading-${index + 1}`);
  });
  return aliases;
}

function localReferencePath(value, options) {
  if (typeof value !== 'string' || value.length === 0) return null;
  if (value.startsWith('#') || value.startsWith('?')) return null;
  if (/^https?:\/\//i.test(value)) return null;
  if (/^[a-z][a-z0-9+.-]*:/i.test(value)) return null;
  const withoutFragment = value.split('#')[0].split('?')[0];
  if (!withoutFragment) return null;
  let decoded;
  try {
    decoded = decodeURIComponent(withoutFragment);
  } catch {
    options.errors.push(diagnostic('E_PATH', options.relativePath, '引用编码不合法'));
    return null;
  }
  const relative = path.posix.normalize(path.posix.join(options.baseDir, decoded));
  if (relative === '..' || relative.startsWith('../') || relative.startsWith('/')) {
    options.errors.push(diagnostic('E_PATH', options.relativePath, '引用越过 Skill 边界'));
    return null;
  }
  return relative;
}

function resolveFragment(value, aliases) {
  if (value === '#') return '#';
  let decoded;
  try {
    decoded = decodeURIComponent(value.slice(1));
  } catch {
    return null;
  }
  return aliases.get(aliasFor(decoded)) ?? null;
}

function resolveReference(value, options) {
  if (typeof value !== 'string' || value.length === 0) return null;
  if (value.startsWith('#')) return resolveFragment(value, options.aliases);
  if (value.startsWith('?')) {
    const hash = value.indexOf('#');
    return hash === -1 ? '#' : resolveFragment(value.slice(hash), options.aliases);
  }
  if (/^https?:\/\//i.test(value)) return value;
  if (/^[a-z][a-z0-9+.-]*:/i.test(value)) return null;
  const relative = localReferencePath(value, options);
  if (relative === null) return null;
  if (!options.fileSet.has(relative)) {
    options.errors.push(
      diagnostic('E_REFERENCE_MISSING', options.relativePath, '引用的本地附件不存在'),
    );
    return null;
  }
  return options.image ? (options.mediaUrls.get(relative) ?? null) : options.fileUrls.get(relative);
}

function rasterType(bytes) {
  if (bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    return { ext: 'png' };
  }
  if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) return { ext: 'jpg' };
  if (/^GIF8[79]a$/.test(bytes.subarray(0, 6).toString('latin1'))) return { ext: 'gif' };
  if (
    bytes.subarray(0, 4).toString('latin1') === 'RIFF' &&
    bytes.subarray(8, 12).toString('latin1') === 'WEBP'
  ) {
    return { ext: 'webp' };
  }
  if (
    bytes.subarray(4, 8).toString('latin1') === 'ftyp' &&
    ['avif', 'avis'].includes(bytes.subarray(8, 12).toString('latin1'))
  ) {
    return { ext: 'avif' };
  }
  return null;
}

function headingTransforms(rendered) {
  const transforms = {};
  for (const tag of HEADINGS) {
    transforms[tag] = (tagName) => {
      rendered.heading += 1;
      return { tagName, attribs: { id: `skill-heading-${rendered.heading}` } };
    };
  }
  return transforms;
}

async function renderMarkdown(markdown, options) {
  const { marked } = await import('marked');
  const tokens = marked.lexer(markdown);
  const errors = [];
  const imageRequests = options.imageRequests ?? [];
  const rendered = { heading: 0 };
  const referenceOptions = {
    aliases: aliasMap(tokens),
    baseDir: options.baseDir,
    fileSet: options.fileSet,
    fileUrls: options.fileUrls,
    imageRequests,
    mediaUrls: options.mediaUrls,
    relativePath: options.relativePath,
    errors,
  };
  const transforms = {
    ...headingTransforms(rendered),
    a: (tagName, attribs) => {
      const next = { ...attribs };
      const mapped = resolveReference(attribs.href, { ...referenceOptions, image: false });
      if (mapped === null) delete next.href;
      else next.href = mapped;
      if (/^https?:\/\//i.test(next.href || '')) {
        next.rel = 'noopener noreferrer';
        next.target = '_blank';
      }
      return { tagName, attribs: next };
    },
    img: (tagName, attribs) => {
      const next = { ...attribs };
      const local = localReferencePath(attribs.src, referenceOptions);
      if (local !== null && options.fileSet.has(local)) imageRequests.push(local);
      const mapped = resolveReference(attribs.src, { ...referenceOptions, image: true });
      if (mapped === null) delete next.src;
      else next.src = mapped;
      return { tagName, attribs: next };
    },
  };

  const html = marked.parse(markdown, { gfm: true });
  const body = sanitizeHtml(html, {
    allowedTags: ALLOWED_TAGS,
    allowedAttributes: ALLOWED_ATTRIBUTES,
    allowedSchemes: ['http', 'https'],
    allowProtocolRelative: false,
    transformTags: transforms,
  });
  const contentText = sanitizeHtml(body, { allowedTags: [], allowedAttributes: {} });
  return { body, contentText, errors, images: imageRequests };
}

module.exports = { rasterType, renderMarkdown };
