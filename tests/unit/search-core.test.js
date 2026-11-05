const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const MiniSearch = require('minisearch');

const root = path.resolve(__dirname, '../..');
const searchSource = fs.readFileSync(path.join(root, 'assets/app-search.js'), 'utf8');
const fixture = JSON.parse(
  fs.readFileSync(path.join(root, 'tests/fixtures/search/fixed-skills.json'), 'utf8'),
);

function loadSearch() {
  const context = { URL, URLSearchParams, MiniSearch };
  context.globalThis = context;
  vm.runInNewContext(searchSource, context, { filename: 'assets/app-search.js' });
  assert.equal(typeof context.SkillGallerySearch, 'object');
  return context.SkillGallerySearch;
}

function slugs(results) {
  return Array.from(results, (result) => result.skill.slug);
}

function plainState(state) {
  return {
    query: state.query,
    mode: state.mode,
    tags: Array.from(state.tags),
    platforms: Array.from(state.platforms),
    sourceTypes: Array.from(state.sourceTypes),
    authors: Array.from(state.authors),
    sort: state.sort,
  };
}

function search(api, query, mode, options = {}) {
  const engine = api.createSearchEngine(fixture.skills, MiniSearch);
  return api.searchSkills({
    skills: fixture.skills,
    engine,
    query,
    mode,
    ...options,
  });
}

test('normalizes text with NFC, lower case and collapsed whitespace', () => {
  const api = loadSearch();
  assert.equal(api.normalizeText('  Debugging\n\tWorkflow  '), 'debugging workflow');
  assert.equal(api.normalizeText('e\u0301'), 'é');
});

test('exact mode matches normalized substrings, quoted phrases and does not correct typos', () => {
  const api = loadSearch();
  assert.deepEqual(slugs(search(api, 'debug', 'exact')), ['systematic-debugging']);
  assert.deepEqual(slugs(search(api, '"文档转换"', 'exact')), ['document-converter']);
  assert.deepEqual(slugs(search(api, 'debuging', 'exact')), []);
});

test('fuzzy mode tolerates English typos and Chinese substrings', () => {
  const api = loadSearch();
  assert.ok(slugs(search(api, 'debuging', 'fuzzy')).includes('systematic-debugging'));
  assert.deepEqual(slugs(search(api, '文档转换', 'fuzzy')), ['document-converter']);
});

test('filters use OR inside a dimension and AND across dimensions', () => {
  const api = loadSearch();
  assert.deepEqual(slugs(search(api, '', 'fuzzy', { tags: ['debugging', 'handoff'] })), [
    'handoff-codex',
    'systematic-debugging',
  ]);
  assert.deepEqual(
    slugs(search(api, '', 'fuzzy', { platforms: ['codex'], authors: ['Example Author'] })),
    ['handoff-codex', 'systematic-debugging'],
  );
  assert.deepEqual(slugs(search(api, '', 'fuzzy', { sourceTypes: ['github'] })), [
    'document-converter',
  ]);
  assert.deepEqual(
    slugs(search(api, '', 'fuzzy', { authors: ['Example Author'], sourceTypes: ['github'] })),
    [],
  );
});

test('sorts by relevance, updated time and stable slug tie-break', () => {
  const api = loadSearch();
  assert.deepEqual(slugs(search(api, '', 'fuzzy', { sort: 'updated' })), [
    'long-code-sample',
    'document-converter',
    'handoff-codex',
    'systematic-debugging',
    'code-review-assistant',
    'tie-alpha',
    'tie-beta',
    'missing-metadata',
  ]);
  assert.deepEqual(slugs(search(api, 'same score sample', 'exact')), ['tie-alpha', 'tie-beta']);
});

test('builds filter options from actual values only', () => {
  const api = loadSearch();
  const options = api.buildFilterOptions(fixture.skills);
  assert.deepEqual(
    Array.from(options.sourceTypes, (item) => item.value),
    ['github', 'self-built'],
  );
  assert.equal(options.authors.find((item) => item.value === 'Example Author').count, 3);
  assert.equal(
    options.tags.some((item) => item.value === 'debugging'),
    true,
  );
});

test('parses and builds list hashes with defaults, arrays and safe fallbacks', () => {
  const api = loadSearch();
  assert.deepEqual(plainState(api.parseListHash('')), {
    query: '',
    mode: 'fuzzy',
    tags: [],
    platforms: [],
    sourceTypes: [],
    authors: [],
    sort: 'auto',
  });
  assert.deepEqual(plainState(api.parseListHash('#/')), plainState(api.parseListHash('')));
  const parsed = api.parseListHash(
    '#/?q=debug&mode=exact&tag=debugging&tag=workflow&platform=codex&source=self-built&author=Example+Author&sort=name',
  );
  assert.equal(parsed.query, 'debug');
  assert.equal(parsed.mode, 'exact');
  assert.deepEqual(Array.from(parsed.tags), ['debugging', 'workflow']);
  assert.deepEqual(Array.from(parsed.platforms), ['codex']);
  assert.deepEqual(Array.from(parsed.sourceTypes), ['self-built']);
  assert.deepEqual(Array.from(parsed.authors), ['Example Author']);
  assert.equal(parsed.sort, 'name');
  assert.equal(api.parseListHash('#/?mode=unknown&sort=unknown').mode, 'fuzzy');
  assert.equal(api.parseListHash('#/?mode=unknown&sort=unknown').sort, 'auto');
  assert.equal(api.buildListHash(api.parseListHash('#/')), '#/');
  assert.equal(
    api.buildListHash({
      query: '文档转换',
      mode: 'fuzzy',
      tags: ['文档工具'],
      platforms: [],
      sourceTypes: [],
      authors: [],
      sort: 'auto',
    }),
    '#/?q=%E6%96%87%E6%A1%A3%E8%BD%AC%E6%8D%A2&tag=%E6%96%87%E6%A1%A3%E5%B7%A5%E5%85%B7',
  );
});

test('builds canonical detail and list share URLs under the site prefix', () => {
  const api = loadSearch();
  assert.equal(
    api.buildDetailShareUrl('http://127.0.0.1:8000/skill-gallery/index.html', 'handoff-codex'),
    'http://127.0.0.1:8000/skill-gallery/#/skill/handoff-codex',
  );
  assert.equal(
    api.buildListShareUrl('http://127.0.0.1:8000/skill-gallery/', {
      query: 'debug',
      mode: 'exact',
      tags: ['debugging'],
      platforms: [],
      sourceTypes: [],
      authors: [],
      sort: 'name',
    }),
    'http://127.0.0.1:8000/skill-gallery/#/?q=debug&mode=exact&tag=debugging&sort=name',
  );
});
