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

  function errorView(app, message, retry) {
    clear(app);
    const box = element('div', 'empty-state');
    box.append(element('h3', null, message));
    if (retry) {
      const button = element('button', null, '重试');
      button.addEventListener('click', retry);
      box.append(button);
    }
    app.append(box);
  }

  function notFound(app) {
    errorView(app, '未找到该 Skill', () => {
      window.location.hash = '';
    });
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

  function bindBodyAnchors(root) {
    root.addEventListener('click', (event) => {
      const anchor = event.target.closest('a[href^="#"]');
      if (!anchor || !root.contains(anchor)) return;
      event.preventDefault();
      let id;
      try {
        id = decodeURIComponent(anchor.getAttribute('href').slice(1));
      } catch {
        return;
      }
      const target = Array.from(root.querySelectorAll('[id]')).find((node) => node.id === id);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  function metaRow(label, value) {
    const row = element('div', 'detail-meta-row');
    row.append(element('span', 'badge', `${label}：${safeText(value)}`));
    return row;
  }

  function linkRow(label, value) {
    const row = element('div', 'detail-meta-row');
    const href = safeHref(value);
    if (!href) {
      row.append(element('span', 'badge', `${label}：未提供`));
      return row;
    }
    row.append(element('span', 'badge', `${label}：`));
    const link = element('a', null, href);
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    row.append(link);
    return row;
  }

  function renderDetail(app, detail) {
    clear(app);
    const view = element('div', 'detail-view');
    const back = element('button', 'detail-back', '← 返回列表');
    back.addEventListener('click', () => {
      window.location.hash = '';
    });
    view.append(back);

    const header = element('div', 'detail-header');
    header.append(element('h1', 'detail-title', safeText(detail.display_name, detail.slug)));
    header.append(element('p', 'detail-desc', safeText(detail.description)));
    const badges = element('div', 'detail-meta-row');
    for (const platform of detail.platforms || []) {
      badges.append(element('span', 'badge badge-platform', platform));
    }
    for (const tag of detail.tags || []) badges.append(element('span', 'badge', `#${tag}`));
    header.append(badges);
    header.append(metaRow('作者', detail.author));
    header.append(metaRow('声明版本', detail.declared_version));
    header.append(metaRow('许可', detail.license));
    header.append(metaRow('创建时间', detail.created_at));
    header.append(metaRow('更新时间', detail.updated_at));
    header.append(linkRow('官网', detail.homepage_url));
    header.append(linkRow('开源地址', detail.repository_url));
    view.append(header);

    const toolbar = element('div', 'detail-toolbar');
    const rawHref = safeHref(detail.raw_url);
    if (rawHref) {
      const raw = element('a', 'btn', '查看原文');
      raw.href = rawHref;
      raw.target = '_blank';
      raw.rel = 'noopener noreferrer';
      toolbar.append(raw);
    }
    const downloadHref = safeHref(detail.download_url);
    if (downloadHref) {
      const download = element('a', 'btn btn-primary', detail.download_name || '下载原件');
      download.href = downloadHref;
      if (detail.download_name) download.download = detail.download_name;
      toolbar.append(download);
    }
    view.append(toolbar);

    const body = element('div', 'markdown-body');
    body.innerHTML = typeof detail.body_html === 'string' ? detail.body_html : '';
    bindBodyAnchors(body);
    view.append(body);

    if (Array.isArray(detail.files) && detail.files.length > 0) {
      const section = element('div', 'detail-files');
      section.append(element('h4', null, '附件'));
      const list = element('ul', 'file-list');
      for (const file of detail.files) {
        const href = safeHref(file.url);
        if (!href) continue;
        const itemNode = element('li');
        const link = element('a', null, `${file.path}（${file.size} 字节）`);
        link.href = href;
        link.download = file.download_name || '';
        itemNode.append(link);
        list.append(itemNode);
      }
      section.append(list);
      view.append(section);
    }

    const info = element('div', 'detail-footer-info');
    info.append(metaRow('来源', detail.source_type));
    if (detail.usage) {
      const usage = element('div', 'usage-notes');
      usage.append(element('h4', null, '用法'));
      usage.append(element('p', null, detail.usage));
      info.append(usage);
    }
    if (detail.notes) {
      const notes = element('div', 'usage-notes');
      notes.append(element('h4', null, '备注'));
      notes.append(element('p', null, detail.notes));
      info.append(notes);
    }
    view.append(info);
    app.append(view);
    document.title = `${safeText(detail.display_name, detail.slug)} · Skill Gallery`;
  }

  window.SkillGalleryViews = {
    errorView,
    loadingView,
    notFound,
    renderDetail,
    renderList,
    safeText,
  };
})();
