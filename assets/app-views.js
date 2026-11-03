(function () {
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function clear(node) {
    node.replaceChildren();
  }

  function safeText(value, fallback = '未提供') {
    return value === null || value === undefined || value === '' ? fallback : String(value);
  }

  function safeHref(value) {
    if (typeof value !== 'string' || value.length === 0) return null;
    if (/^[a-z][a-z0-9+.-]*:/i.test(value)) return /^https?:/i.test(value) ? value : null;
    if (value.startsWith('/') || value.split('/').includes('..')) return null;
    return value;
  }

  function loadingView(app) {
    clear(app);
    app.append(element('div', 'loading', '加载中...'));
  }

  function errorView(app, message, retry, state = 'load_failed') {
    clear(app);
    const box = element('div', 'empty-state');
    box.dataset.state = state;
    box.append(element('h3', null, message));
    if (retry) {
      const button = element('button', null, '重试');
      button.type = 'button';
      button.addEventListener('click', retry);
      box.append(button);
    }
    app.append(box);
  }

  function notFound(app) {
    errorView(
      app,
      '未找到该 Skill',
      () => {
        window.location.hash = '';
      },
      'not_found',
    );
  }

  function cardFor(skill) {
    const card = element('a', 'skill-card');
    card.href = `#/skill/${encodeURIComponent(skill.slug)}`;
    card.append(element('h3', 'skill-card-title', safeText(skill.display_name, skill.slug)));
    card.append(element('p', 'skill-card-desc', safeText(skill.description)));
    const meta = element('div', 'skill-card-meta');
    for (const platform of skill.platforms || []) {
      meta.append(element('span', 'badge badge-platform', platform));
    }
    for (const tag of skill.tags || []) meta.append(element('span', 'badge', `#${tag}`));
    card.append(meta);
    const footer = element('div', 'skill-card-footer');
    footer.append(element('span', null, safeText(skill.declared_version, '未声明版本')));
    footer.append(element('span', null, safeText(skill.updated_at, '未提供日期')));
    card.append(footer);
    return card;
  }

  function renderList(app, state, filterSkills) {
    clear(app);
    const layout = element('div', 'list-layout');
    const filters = element('aside', 'filters');
    filters.append(element('h3', null, '搜索'));
    const searchBar = element('div', 'search-bar');
    const input = element('input', 'search-input');
    input.type = 'search';
    input.placeholder = '搜索名称、简介或标签';
    input.value = state.query;
    input.setAttribute('aria-label', '搜索 Skill');
    searchBar.append(input);
    filters.append(searchBar);
    layout.append(filters);

    const content = element('div', 'list-content');
    const bar = element('div', 'sort-bar');
    const count = element('span', 'result-count');
    bar.append(count);
    content.append(bar);
    const grid = element('div', 'skill-grid');
    content.append(grid);
    layout.append(content);
    app.append(layout);

    const update = () => {
      const filtered = filterSkills();
      count.textContent = `${filtered.length} 个结果`;
      clear(grid);
      if (filtered.length === 0) {
        const empty = element('div', 'empty-state');
        empty.append(element('h3', null, '没有匹配的 Skill'));
        const button = element('button', null, '清除搜索');
        button.type = 'button';
        button.addEventListener('click', () => {
          state.query = '';
          input.value = '';
          update();
        });
        empty.append(button);
        grid.append(empty);
        return;
      }
      for (const skill of filtered) grid.append(cardFor(skill));
    };
    input.addEventListener('input', () => {
      state.query = input.value;
      update();
    });
    update();
  }

  window.SkillGalleryViews = {
    clear,
    element,
    errorView,
    loadingView,
    notFound,
    renderList,
    safeHref,
    safeText,
  };
})();
