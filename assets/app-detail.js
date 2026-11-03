(function () {
  const { element, clear, safeText, safeHref } = window.SkillGalleryViews;

  function bindBodyAnchors(root, files, onFileLink) {
    root.addEventListener('click', (event) => {
      const anchor = event.target.closest('a');
      if (!anchor || !root.contains(anchor)) return;
      const href = anchor.getAttribute('href') || '';
      if (href.startsWith('#')) {
        event.preventDefault();
        let id;
        try {
          id = decodeURIComponent(href.slice(1));
        } catch {
          return;
        }
        const target = Array.from(root.querySelectorAll('[id]')).find((node) => node.id === id);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith('/')) return;
      const file = (files || []).find((item) => item.url === href);
      if (!file) return;
      event.preventDefault();
      onFileLink(anchor, file);
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

  function errorMessage(error, fallback) {
    return error && error.code && typeof error.message === 'string' && error.message
      ? error.message
      : fallback;
  }

  function renderDetail(app, detail, actions) {
    clear(app);
    const view = element('div', 'detail-view');
    const back = element('button', 'detail-back', '← 返回列表');
    back.type = 'button';
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
    const status = element('p', 'detail-status');
    status.hidden = true;
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');

    const rawPanel = element('div', 'raw-panel');
    rawPanel.hidden = true;
    const rawText = element('textarea', 'raw-text');
    rawText.readOnly = true;
    rawText.spellcheck = false;
    rawText.setAttribute('aria-label', '完整原文');
    rawPanel.append(rawText);

    const manualPanel = element('div', 'manual-panel');
    manualPanel.hidden = true;
    const manualLabel = element('label', null, '复制失败，请手动选择：');
    manualLabel.htmlFor = 'manual-copy';
    const manualInput = element('input', 'manual-input');
    manualInput.id = 'manual-copy';
    manualInput.type = 'text';
    manualInput.readOnly = true;
    manualPanel.append(manualLabel, manualInput);

    let rawContent = null;
    function setStatus(message, state) {
      status.hidden = message === '';
      status.dataset.state = state;
      status.textContent = message;
    }
    function setBusy(button, busy) {
      button.disabled = busy;
      button.setAttribute('aria-busy', String(busy));
    }
    async function showRaw() {
      const result = await actions.loadRaw();
      if (!result || result.stale) return false;
      rawContent = result.text;
      rawText.value = result.text;
      rawPanel.hidden = false;
      return true;
    }
    async function downloadAttachment(link, file) {
      link.setAttribute('aria-busy', 'true');
      setStatus(`正在校验 ${file.path}…`, 'loading');
      try {
        const result = await actions.downloadFile(file);
        if (!result || result.stale) return;
        setStatus('资源已校验，下载已发起', 'ready');
      } catch (error) {
        setStatus(errorMessage(error, '下载失败，资源不可用'), 'download_failed');
      } finally {
        link.removeAttribute('aria-busy');
      }
    }

    const rawButton = element('button', 'btn', '查看原文');
    rawButton.type = 'button';
    rawButton.addEventListener('click', async () => {
      setBusy(rawButton, true);
      setStatus('正在校验原文…', 'loading');
      try {
        if (await showRaw()) setStatus('原文已校验；可从文本区选取完整内容', 'ready');
      } catch (error) {
        setStatus(errorMessage(error, '原文不可用'), 'raw_unavailable');
      } finally {
        setBusy(rawButton, false);
      }
    });

    const copyButton = element('button', 'btn', '复制原文');
    copyButton.type = 'button';
    copyButton.addEventListener('click', async () => {
      setBusy(copyButton, true);
      setStatus('正在校验并复制原文…', 'loading');
      try {
        if (rawContent === null && !(await showRaw())) return;
        await actions.copyText(rawContent);
        setStatus('原文已复制', 'ready');
      } catch (error) {
        if (error && error.code === 'copy_failed') {
          rawPanel.hidden = false;
          setStatus('复制失败，请手动选择下方原文', 'copy_failed');
          if (rawContent !== null) rawText.value = rawContent;
        } else {
          setStatus(errorMessage(error, '原文不可用'), 'raw_unavailable');
        }
      } finally {
        setBusy(copyButton, false);
      }
    });

    const shareButton = element('button', 'btn', '复制分享链接');
    shareButton.type = 'button';
    const shareLink = actions.shareLink();
    shareButton.addEventListener('click', async () => {
      setBusy(shareButton, true);
      setStatus('正在复制分享链接…', 'loading');
      try {
        await actions.copyText(shareLink);
        setStatus('分享链接已复制', 'ready');
        manualPanel.hidden = true;
      } catch {
        manualInput.value = shareLink;
        manualPanel.hidden = false;
        setStatus('复制失败，请手动复制下方链接', 'copy_failed');
      } finally {
        setBusy(shareButton, false);
      }
    });

    toolbar.append(rawButton, copyButton);
    if (detail.download_url && detail.download_name) {
      const downloadButton = element('button', 'btn btn-primary', detail.download_name);
      downloadButton.type = 'button';
      downloadButton.addEventListener('click', async () => {
        setBusy(downloadButton, true);
        setStatus('正在校验下载资源…', 'loading');
        try {
          const result = await actions.downloadPrimary();
          if (!result || result.stale) return;
          setStatus('资源已校验，下载已发起', 'ready');
        } catch (error) {
          setStatus(errorMessage(error, '下载失败，资源不可用'), 'download_failed');
        } finally {
          setBusy(downloadButton, false);
        }
      });
      toolbar.append(downloadButton);
    }
    toolbar.append(shareButton);
    view.append(toolbar, status, manualPanel, rawPanel);

    const body = element('div', 'markdown-body');
    body.innerHTML = typeof detail.body_html === 'string' ? detail.body_html : '';
    bindBodyAnchors(body, detail.files || [], downloadAttachment);
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
        link.addEventListener('click', (event) => {
          event.preventDefault();
          downloadAttachment(link, file);
        });
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

  window.SkillGalleryDetail = { renderDetail };
})();
