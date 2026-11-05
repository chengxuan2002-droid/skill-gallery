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

  function cardFor(skill, onOpenDetail) {
    const card = element('a', 'skill-card');
    card.href = `#/skill/${encodeURIComponent(skill.slug)}`;
    card.addEventListener('click', (event) => {
      event.preventDefault();
      onOpenDetail(skill.slug);
    });
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
    footer.append(element('span', null, safeText(skill.updated_at, '未提供')));
    card.append(footer);
    return card;
  }

  function filterGroup(title, key, options, getSelected, onChange) {
    if (!options.length) return null;
    const group = element('fieldset', 'filter-group');
    group.append(element('legend', 'field-label', title));
    for (const option of options) {
      const label = element('label', 'filter-option');
      const checkbox = element('input');
      checkbox.type = 'checkbox';
      checkbox.value = option.value;
      checkbox.checked = getSelected().includes(option.value);
      checkbox.addEventListener('change', () => {
        const selected = getSelected();
        const next = checkbox.checked
          ? [...selected, option.value]
          : selected.filter((value) => value !== option.value);
        onChange({ [key]: [...new Set(next)] });
      });
      label.append(checkbox, element('span', null, `${option.value} (${option.count})`));
      group.append(label);
    }
    return group;
  }

  function renderList(app, { state, results, filterOptions }, handlers) {
    clear(app);
    let currentState = state;

    const layout = element('div', 'list-layout');
    const filters = element('aside', 'filters');
    const searchLabel = element('label', 'field-label', '搜索 Skill');
    searchLabel.htmlFor = 'skill-search';
    const searchBar = element('div', 'search-bar');
    const input = element('input', 'search-input');
    input.type = 'search';
    input.id = 'skill-search';
    input.placeholder = '搜索名称、简介、标签或正文';
    input.value = state.query;
    input.addEventListener('input', () => handlers.onChange({ query: input.value }));
    searchBar.append(input);
    filters.append(searchLabel, searchBar);

    const modeLabel = element('div', 'field-label', '搜索模式');
    const modeGroup = element('div', 'mode-toggle');
    modeGroup.setAttribute('role', 'group');
    modeGroup.setAttribute('aria-label', '搜索模式');
    const fuzzyButton = element('button', 'mode-button', '模糊');
    const exactButton = element('button', 'mode-button', '精准');
    fuzzyButton.type = 'button';
    exactButton.type = 'button';
    fuzzyButton.addEventListener('click', () => handlers.onChange({ mode: 'fuzzy' }));
    exactButton.addEventListener('click', () => handlers.onChange({ mode: 'exact' }));
    modeGroup.append(fuzzyButton, exactButton);
    filters.append(modeLabel, modeGroup);

    const groups = [
      ['标签', 'tags', filterOptions.tags, 'tags'],
      ['平台', 'platforms', filterOptions.platforms, 'platforms'],
      ['来源', 'sourceTypes', filterOptions.sourceTypes, 'sourceTypes'],
      ['作者', 'authors', filterOptions.authors, 'authors'],
    ];
    const checkboxes = new Map();
    for (const [title, key, options, stateKey] of groups) {
      const group = filterGroup(
        title,
        key,
        options,
        () => currentState[stateKey],
        handlers.onChange,
      );
      if (group) {
        for (const checkbox of group.querySelectorAll('input')) {
          checkboxes.set(`${key}:${checkbox.value}`, checkbox);
        }
        filters.append(group);
      }
    }

    const sortLabel = element('label', 'field-label', '排序');
    sortLabel.htmlFor = 'skill-sort';
    const sortSelect = element('select', 'sort-select');
    sortSelect.id = 'skill-sort';
    for (const [value, text] of [
      ['auto', '自动'],
      ['name', '名称'],
      ['updated', '更新时间'],
    ]) {
      const option = element('option', null, text);
      option.value = value;
      sortSelect.append(option);
    }
    sortSelect.value = state.sort;
    sortSelect.addEventListener('change', () => handlers.onChange({ sort: sortSelect.value }));
    filters.append(sortLabel, sortSelect);
    layout.append(filters);

    const content = element('div', 'list-content');
    const bar = element('div', 'sort-bar');
    const count = element('span', 'result-count');
    count.setAttribute('aria-live', 'polite');
    const conditions = element('div', 'active-conditions');
    const copyButton = element('button', 'btn btn-small', '复制列表链接');
    copyButton.type = 'button';
    bar.append(count, conditions, copyButton);
    content.append(bar);

    const status = element('p', 'list-status');
    status.hidden = true;
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    content.append(status);

    const grid = element('div', 'skill-grid');
    content.append(grid);
    layout.append(content);
    app.append(layout);

    function setStatus(message, stateName) {
      status.hidden = message === '';
      status.dataset.state = stateName;
      status.textContent = message;
    }

    function conditionsFor(nextState) {
      const chips = [];
      for (const [title, key, selected] of [
        ['标签', 'tags', nextState.tags],
        ['平台', 'platforms', nextState.platforms],
        ['来源', 'sourceTypes', nextState.sourceTypes],
        ['作者', 'authors', nextState.authors],
      ]) {
        for (const value of selected) {
          const chip = element('span', 'condition-chip');
          chip.append(element('span', null, `${title}：${value}`));
          const remove = element('button', 'chip-remove', '×');
          remove.type = 'button';
          remove.setAttribute('aria-label', `移除筛选 ${title} ${value}`);
          remove.addEventListener('click', () => {
            handlers.onChange({ [key]: currentState[key].filter((item) => item !== value) });
          });
          chip.append(remove);
          chips.push(chip);
        }
      }
      return chips;
    }

    function renderResults(nextState, nextResults) {
      count.textContent = `${nextResults.length} 个结果`;
      clear(conditions);
      for (const chip of conditionsFor(nextState)) conditions.append(chip);
      if (nextState.mode === 'exact')
        conditions.append(element('span', 'condition-text', '精准模式'));
      if (nextState.sort !== 'auto') {
        conditions.append(
          element('span', 'condition-text', `排序：${sortLabelText(nextState.sort)}`),
        );
      }
      const hasConditions =
        nextState.query ||
        nextState.mode !== 'fuzzy' ||
        nextState.sort !== 'auto' ||
        nextState.tags.length ||
        nextState.platforms.length ||
        nextState.sourceTypes.length ||
        nextState.authors.length;
      if (hasConditions) {
        const clearAll = element('button', 'btn btn-small', '清除全部');
        clearAll.type = 'button';
        clearAll.addEventListener('click', () => {
          handlers.onChange({
            query: '',
            mode: 'fuzzy',
            tags: [],
            platforms: [],
            sourceTypes: [],
            authors: [],
            sort: 'auto',
          });
        });
        conditions.append(clearAll);
      }
      clear(grid);
      if (nextState.skills.length === 0) {
        const empty = element('div', 'empty-state');
        empty.dataset.state = 'empty_library';
        empty.append(element('h3', null, '图库为空'));
        const retry = element('button', null, '重试');
        retry.type = 'button';
        retry.addEventListener('click', () => window.location.reload());
        empty.append(retry);
        grid.append(empty);
        return;
      }
      if (nextResults.length === 0) {
        const empty = element('div', 'empty-state');
        empty.dataset.state = 'empty_results';
        empty.append(element('h3', null, '没有匹配的 Skill'));
        const clearAll = element('button', null, '清除全部条件');
        clearAll.type = 'button';
        clearAll.addEventListener('click', () => {
          handlers.onChange({
            query: '',
            mode: 'fuzzy',
            tags: [],
            platforms: [],
            sourceTypes: [],
            authors: [],
            sort: 'auto',
          });
        });
        empty.append(clearAll);
        grid.append(empty);
        return;
      }
      for (const result of nextResults) grid.append(cardFor(result.skill, handlers.onOpenDetail));
    }

    function sortLabelText(value) {
      return value === 'name' ? '名称' : value === 'updated' ? '更新时间' : '自动';
    }

    function update(nextState, nextResults) {
      currentState = nextState;
      if (input.value !== nextState.query) input.value = nextState.query;
      fuzzyButton.setAttribute('aria-pressed', String(nextState.mode === 'fuzzy'));
      exactButton.setAttribute('aria-pressed', String(nextState.mode === 'exact'));
      fuzzyButton.classList.toggle('is-active', nextState.mode === 'fuzzy');
      exactButton.classList.toggle('is-active', nextState.mode === 'exact');
      sortSelect.value = nextState.sort;
      for (const [key, checkbox] of checkboxes) {
        const selected = nextState[key.split(':')[0]];
        checkbox.checked = selected.includes(checkbox.value);
      }
      renderResults(nextState, nextResults);
    }

    copyButton.addEventListener('click', async () => {
      copyButton.disabled = true;
      setStatus('正在复制列表链接...', 'loading');
      try {
        await handlers.copyListLink();
        setStatus('列表链接已复制', 'ready');
      } catch {
        setStatus('复制失败，请手动复制当前地址', 'copy_failed');
      } finally {
        copyButton.disabled = false;
      }
    });

    update(state, results);

    return { update };
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
