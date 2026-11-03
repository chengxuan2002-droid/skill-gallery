const app = document.getElementById('app');
const skillCount = document.getElementById('skill-count');
const views = window.SkillGalleryViews;
const detailView = window.SkillGalleryDetail;
const actions = window.SkillGalleryActions;
const state = {
  skills: [],
  query: '',
  mini: null,
  revision: null,
  routeToken: 0,
};

function buildMini(skills) {
  if (!window.MiniSearch) return null;
  const mini = new window.MiniSearch({
    fields: ['display_name', 'description', 'tags', 'platforms', 'usage', 'notes', 'content_text'],
    idField: 'slug',
    storeFields: ['slug'],
  });
  mini.addAll(skills);
  return mini;
}

function filterSkills() {
  const query = state.query.trim();
  if (!query) return state.skills;
  if (state.mini) {
    const matched = new Set(
      state.mini.search(query, { prefix: true, fuzzy: 0.2 }).map((result) => result.id),
    );
    return state.skills.filter((skill) => matched.has(skill.slug));
  }
  const lowered = query.toLowerCase();
  return state.skills.filter((skill) =>
    [skill.display_name, skill.description, ...(skill.tags || []), ...(skill.platforms || [])]
      .join(' ')
      .toLowerCase()
      .includes(lowered),
  );
}

function createDetailActions(detail, token) {
  const isCurrent = () => token === state.routeToken;
  return {
    loadRaw: () => actions.loadRaw(detail, isCurrent),
    copyText: (text) => actions.copyText(text),
    shareLink: () => actions.shareLink(detail.slug),
    downloadPrimary: () => actions.downloadPrimary(detail, isCurrent),
    downloadFile: (file) => actions.downloadFile(file, isCurrent),
  };
}

async function loadDetail(item, token) {
  views.loadingView(app);
  try {
    const response = await fetch(`details/${encodeURIComponent(item.slug)}.json`, {
      cache: 'no-store',
    });
    if (!response.ok) throw new Error('detail');
    const detail = await response.json();
    if (token !== state.routeToken) return;
    if (
      !detail ||
      detail.schemaVersion !== 1 ||
      detail.contentRevision !== state.revision ||
      detail.slug !== item.slug ||
      detail.digest !== item.digest
    ) {
      views.errorView(
        app,
        '内容快照已更新，请刷新页面',
        () => window.location.reload(),
        'snapshot_mismatch',
      );
      return;
    }
    detailView.renderDetail(app, detail, createDetailActions(detail, token));
  } catch {
    if (token === state.routeToken) {
      views.errorView(app, '无法加载该 Skill，请重试', () => route(), 'load_failed');
    }
  }
}

async function route() {
  const token = ++state.routeToken;
  const match = window.location.hash.match(/^#\/skill\/(.+)$/);
  if (!match) {
    document.title = 'Skill Gallery';
    views.renderList(app, state, filterSkills);
    return;
  }
  let slug;
  try {
    slug = decodeURIComponent(match[1]);
  } catch {
    views.notFound(app);
    return;
  }
  const item = state.skills.find((skill) => skill.slug === slug);
  if (!item) {
    views.notFound(app);
    return;
  }
  await loadDetail(item, token);
}

async function loadIndex() {
  views.loadingView(app);
  try {
    const response = await fetch('assets/search-index.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('index');
    const index = await response.json();
    if (!index || index.schemaVersion !== 1 || !Array.isArray(index.skills)) {
      throw new Error('schema');
    }
    state.skills = index.skills;
    state.revision = index.contentRevision;
    state.mini = buildMini(index.skills);
    skillCount.textContent = `${index.skills.length} 个 Skill`;
    route();
  } catch {
    views.errorView(app, '无法加载图库，请重试', loadIndex);
  }
}

function setupTheme() {
  const toggle = document.getElementById('theme-toggle');
  const saved = localStorage.getItem('skill-gallery-theme');
  if (saved) document.documentElement.dataset.theme = saved;
  if (!toggle) return;
  toggle.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('skill-gallery-theme', next);
    toggle.textContent = next === 'dark' ? '☀️' : '🌙';
  });
}

setupTheme();
window.addEventListener('hashchange', route);
loadIndex();
