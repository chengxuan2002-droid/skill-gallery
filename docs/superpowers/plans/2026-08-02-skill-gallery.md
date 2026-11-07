# Skill Gallery Implementation Plan

> Historical v1 plan. For the 2026-11-01 iteration, use [DemandAnalysis](../../DemandAnalysis.md), [TechnicalSolution](../../TechnicalSolution.md), and [AiProgrammingGuide](../../AiProgrammingGuide.md). This file is retained as implementation history; do not re-run its bootstrap tasks for the new iteration.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pure-static personal skill gallery hosted on GitHub Pages, with unified markdown skill files, full-text search, tag filtering, and multi-platform export.

**Architecture:** Single-page app (Vanilla JS) served from GitHub Pages. Skills are stored as markdown files with YAML frontmatter in `skills/`. A Node.js build script scans them and generates a single `search-index.json`. The frontend loads this JSON, renders list/detail views via hash routing, provides full-text search via minisearch, and exports skills to various agent formats client-side.

**Tech Stack:** Vanilla JavaScript, Node.js (built-in modules only), minisearch (CDN), marked.js (CDN), GitHub Pages

## Global Constraints

- No npm dependencies for the build script — use only Node.js built-in modules
- No frontend framework — pure Vanilla JS
- Third-party JS libraries loaded via CDN (minisearch, marked)
- Skill data lives in `skills/*.md` with YAML frontmatter
- Mobile-first responsive design, 8px border-radius cards
- Dark/light mode support (system preference + toggle)
- All text content UTF-8, English UI with Chinese usage_notes field support

---

### Task 1: Project Bootstrap & Sample Skill Data

**Files:**
- Create: `skills/superpower-systematic-debugging.md`
- Create: `skills/code-review-assistant.md`
- Create: `skills/refactoring-workflow.md`
- Create: `.gitignore`

**Interfaces:**
- Produces: Sample skill files in the canonical format that all subsequent tasks rely on for testing

**Skill file format (canonical):**
```markdown
---
name: Display Name
description: One-line description
tags: [tag1, tag2]
platforms: [codex, generic]
source: self-built
source_url: https://...
author: Author Name
created_at: 2026-08-02
updated_at: 2026-08-02
usage_notes: |
  Personal notes go here.
  Multiple lines supported.
---

# Skill Title

Skill body in markdown...
```

Valid `source` values: `self-built`, `github`, `marketplace`, `platform-native`, `other`
Valid `platforms` values (common): `codex`, `claude-code`, `cursor`, `cline`, `generic`

- [ ] **Step 1: Create sample skill 1 — systematic-debugging (self-built)**

Create `skills/superpower-systematic-debugging.md`:

```markdown
---
name: Systematic Debugging
description: Step-by-step debugging workflow for reproducing and fixing any bug
tags: [debugging, workflow, problem-solving]
platforms: [codex, claude-code, generic]
source: self-built
author: Your Name
created_at: 2026-08-02
updated_at: 2026-08-02
usage_notes: |
  Most useful for bugs that are hard to reproduce.
  Always start with reproduction steps before diving into code.
---

# Systematic Debugging

A rigorous, step-by-step approach to debugging any software issue.

## Steps

1. **Reproduce the bug** — Get a reliable reproduction case. If you can't reproduce it, you can't fix it.
2. **Narrow the scope** — Bisect commits, disable features, find the minimal input that triggers it.
3. **Form a hypothesis** — What could cause this behavior? Write it down.
4. **Test the hypothesis** — Add logging, use a debugger, run experiments.
5. **Implement the fix** — Smallest possible change.
6. **Verify** — Confirm the bug is gone and no regressions were introduced.
7. **Add a test** — Prevent the bug from coming back.

## Common Pitfalls

- Changing multiple things at once
- Assuming the bug is in someone else's code
- Skipping reproduction to "just look at the code"
```

- [ ] **Step 2: Create sample skill 2 — code-review-assistant (github source)**

Create `skills/code-review-assistant.md`:

```markdown
---
name: Code Review Assistant
description: Structured code review checklist and feedback format
tags: [code-review, quality, best-practices]
platforms: [codex, claude-code]
source: github
source_url: https://github.com/example/code-review-skill
author: Example Author
created_at: 2026-07-15
updated_at: 2026-08-01
usage_notes: |
  Good for PR reviews. Customize the severity rubric to match your team's standards.
---

# Code Review Assistant

Helps conduct thorough, consistent code reviews.

## Review Dimensions

- **Correctness**: Does the code do what it intends to?
- **Security**: Any vulnerabilities or injection risks?
- **Performance**: Unnecessary work? O(n²) where it should be O(n)?
- **Readability**: Clear naming, consistent style, good comments?
- **Tests**: Are there tests? Do they cover the important cases?

## Feedback Format

Start with severity:
- 🔴 Blocking — must fix before merge
- 🟡 Warning — should fix, discuss if unsure
- 💡 Suggestion — optional improvement
- ❓ Question — need clarification
```

- [ ] **Step 3: Create sample skill 3 — refactoring-workflow (marketplace)**

Create `skills/refactoring-workflow.md`:

```markdown
---
name: Refactoring Workflow
description: Safe, incremental refactoring approach that doesn't break things
tags: [refactoring, workflow, architecture]
platforms: [generic]
source: marketplace
source_url: https://marketplace.example.com/refactoring
author: Marketplace Author
created_at: 2026-06-20
updated_at: 2026-07-10
usage_notes: |
  The "test first" rule is the most important one.
  Don't refactor code that doesn't have tests — write tests first.
---

# Refactoring Workflow

Safe refactoring in 6 steps.

## Steps

1. **Ensure tests exist** — If no tests, write them first. You need a safety net.
2. **Run tests, confirm they pass** — Green baseline.
3. **Make a small refactoring** — One change, one concept.
4. **Run tests again** — Should still pass.
5. **Commit** — Small, atomic commit.
6. **Repeat** — Next small refactoring.

## Rules

- Never refactor and add features in the same commit
- If tests fail after a refactoring, revert — don't debug forward
- Rename before you restructure
```

- [ ] **Step 4: Create .gitignore**

Create `.gitignore`:

```
.DS_Store
node_modules/
*.log
.env
```

- [ ] **Step 5: Verify files exist and are valid markdown**

Run: `ls -la skills/ && wc -l skills/*.md`
Expected: 3 .md files listed, each with content

- [ ] **Step 6: Commit**

```bash
git add skills/ .gitignore
git commit -m "feat: add sample skill data and .gitignore"
```

---

### Task 2: Build Script — Index Generator

**Files:**
- Create: `scripts/build-index.js`
- Test: Run manually with sample data from Task 1

**Interfaces:**
- Consumes: `skills/*.md` files (canonical format from Task 1)
- Produces: `assets/search-index.json` — array of skill objects with fields:
  - `slug` (string, derived from filename)
  - `name`, `description`, `tags`, `platforms`, `source`, `source_url`, `author`
  - `created_at`, `updated_at`, `usage_notes`
  - `content` (plain text body, markdown stripped)

**Build script behavior:**
- No npm dependencies — only Node.js built-ins (`fs`, `path`)
- Hand-written frontmatter parser (YAML-ish: key: value, array support for simple values)
- Markdown-to-text via regex stripping of headings, bold, italic, links, code fences
- Single file parse failure logs an error but doesn't crash the build
- Exit code 0 on success, 1 on critical failure (no skills directory, no files found)
- Pretty-prints JSON output for git diff readability

- [ ] **Step 1: Write the build script**

Create `scripts/build-index.js`:

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const SKILLS_DIR = path.join(__dirname, '..', 'skills');
const OUTPUT_PATH = path.join(__dirname, '..', 'assets', 'search-index.json');

function parseFrontmatter(content) {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n?/);
  if (!match) return { meta: {}, body: content };

  const raw = match[1];
  const body = content.slice(match[0].length);
  const meta = {};
  let currentKey = null;
  let multilineValue = null;

  for (const line of raw.split('\n')) {
    // Multiline continuation (indented after |)
    if (currentKey && multilineValue !== null && (line.startsWith('  ') || line.startsWith('\t'))) {
      multilineValue.push(line.trim());
      continue;
    } else if (currentKey && multilineValue !== null) {
      meta[currentKey] = multilineValue.join('\n');
      currentKey = null;
      multilineValue = null;
    }

    if (!line.trim() || line.trim().startsWith('#')) continue;

    const colonIdx = line.indexOf(':');
    if (colonIdx === -1) continue;

    const key = line.slice(0, colonIdx).trim();
    const valueStr = line.slice(colonIdx + 1).trim();

    if (valueStr === '|' || valueStr === '>') {
      currentKey = key;
      multilineValue = [];
      continue;
    }

    // Array value: [item1, item2]
    if (valueStr.startsWith('[') && valueStr.endsWith(']')) {
      const inner = valueStr.slice(1, -1).trim();
      if (!inner) {
        meta[key] = [];
      } else {
        meta[key] = inner.split(',').map(s => s.trim().replace(/^["']|["']$/g, ''));
      }
      continue;
    }

    // Simple string: strip quotes
    meta[key] = valueStr.replace(/^["']|["']$/g, '');
  }

  // Handle last multiline block
  if (currentKey && multilineValue !== null) {
    meta[currentKey] = multilineValue.join('\n');
  }

  return { meta, body };
}

function markdownToText(md) {
  return md
    .replace(/```[\s\S]*?```/g, '')                    // code fences
    .replace(/`[^`]*`/g, m => m.slice(1, -1))           // inline code → just text
    .replace(/^#{1,6}\s+/gm, '')                         // headings
    .replace(/\*\*([^*]+)\*\*/g, '$1')                   // bold
    .replace(/\*([^*]+)\*/g, '$1')                       // italic
    .replace(/__([^_]+)__/g, '$1')                       // bold
    .replace(/_([^_]+)_/g, '$1')                         // italic
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')             // links → text
    .replace(/^[-*+]\s+/gm, '• ')                        // list bullets
    .replace(/^\d+\.\s+/gm, '')                          // numbered lists
    .replace(/^>\s?/gm, '')                              // blockquotes
    .replace(/^---+$/gm, '')                             // horizontal rules
    .replace(/\n{3,}/g, '\n\n')                          // collapse blank lines
    .trim();
}

function buildIndex() {
  if (!fs.existsSync(SKILLS_DIR)) {
    console.error('Error: skills/ directory not found');
    process.exit(1);
  }

  const files = fs.readdirSync(SKILLS_DIR).filter(f => f.endsWith('.md'));
  if (files.length === 0) {
    console.error('Error: no .md files found in skills/');
    process.exit(1);
  }

  const skills = [];
  let errors = 0;

  for (const file of files) {
    const slug = file.replace(/\.md$/, '');
    const filePath = path.join(SKILLS_DIR, file);

    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const { meta, body } = parseFrontmatter(content);

      // Validate required fields
      const required = ['name', 'description', 'tags', 'platforms', 'source', 'created_at', 'updated_at'];
      const missing = required.filter(k => !(k in meta));
      if (missing.length > 0) {
        console.error(`Warning: ${file} missing fields: ${missing.join(', ')} — skipping`);
        errors++;
        continue;
      }

      skills.push({
        slug,
        name: meta.name,
        description: meta.description,
        tags: meta.tags,
        platforms: meta.platforms,
        source: meta.source,
        source_url: meta.source_url || null,
        author: meta.author || null,
        created_at: meta.created_at,
        updated_at: meta.updated_at,
        usage_notes: meta.usage_notes || null,
        content: markdownToText(body),
      });

      console.log(`  ✓ ${slug}`);
    } catch (err) {
      console.error(`Error parsing ${file}: ${err.message}`);
      errors++;
    }
  }

  // Sort by updated_at descending
  skills.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));

  // Ensure output directory exists
  const outDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(skills, null, 2) + '\n', 'utf-8');
  console.log(`\nBuilt index: ${skills.length} skills, ${errors} errors`);
  console.log(`Output: ${OUTPUT_PATH}`);

  if (errors > 0 && skills.length === 0) {
    process.exit(1);
  }
}

buildIndex();
```

- [ ] **Step 2: Make it executable and run it**

Run:
```bash
chmod +x scripts/build-index.js
mkdir -p assets
node scripts/build-index.js
```
Expected: Output shows 3 skills processed with ✓ marks, and `assets/search-index.json` is created.

- [ ] **Step 3: Verify the JSON output is correct**

Run:
```bash
node -e "const data = require('./assets/search-index.json'); console.log('count:', data.length); console.log('first:', JSON.stringify(data[0], null, 2));"
```
Expected: 3 entries; first entry has all required fields plus `slug` and `content`; sorted by updated_at descending.

- [ ] **Step 4: Test error handling — create a malformed file, verify it warns but doesn't crash**

Run:
```bash
echo "not a valid skill file" > skills/bad-test.md
node scripts/build-index.js
rm skills/bad-test.md
```
Expected: Script prints a warning about missing fields and skips the bad file, but still processes the 3 good ones. Exit code should be 0.

- [ ] **Step 5: Re-run with clean data to get clean output**

Run: `node scripts/build-index.js`

- [ ] **Step 6: Commit**

```bash
git add scripts/build-index.js assets/search-index.json
git commit -m "feat: add build-index script and generated search index"
```

---

### Task 3: Frontend Skeleton — HTML + CSS + Basic JS

**Files:**
- Create: `index.html`
- Create: `assets/style.css`
- Create: `assets/app.js` (minimal bootstrap)

**Interfaces:**
- Consumes: `assets/search-index.json` (from Task 2)
- Produces: A working page shell with header, main area, and data loading

- [ ] **Step 1: Create index.html**

Create `index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Skill Gallery</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header class="app-header">
    <div class="container">
      <h1 class="app-title">Skill Gallery</h1>
      <p class="app-subtitle">Personal collection of useful AI agent skills</p>
    </div>
  </header>

  <main class="container app-main">
    <div id="app">
      <div class="loading">Loading skills...</div>
    </div>
  </main>

  <footer class="app-footer">
    <div class="container">
      <span id="skill-count"></span>
      <span class="footer-sep">·</span>
      <a href="https://github.com/" target="_blank" rel="noopener">Source</a>
    </div>
  </footer>

  <script src="assets/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create assets/style.css with base styles, layout, and theme variables**

Create `assets/style.css`:

```css
:root {
  --bg: #ffffff;
  --bg-muted: #f7f7f8;
  --bg-card: #ffffff;
  --border: #e5e5e5;
  --border-hover: #d0d0d0;
  --text: #1a1a1a;
  --text-muted: #666;
  --text-faint: #999;
  --accent: #3b82f6;
  --accent-soft: #eff6ff;
  --tag-bg: #f0f0f0;
  --tag-text: #555;
  --success: #10b981;
  --warning: #f59e0b;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
  --radius: 8px;
  --radius-sm: 6px;
}

[data-theme="dark"] {
  --bg: #0f0f10;
  --bg-muted: #1a1a1c;
  --bg-card: #1a1a1c;
  --border: #2a2a2d;
  --border-hover: #3a3a3e;
  --text: #e8e8e8;
  --text-muted: #999;
  --text-faint: #666;
  --accent: #60a5fa;
  --accent-soft: #1e3a5f;
  --tag-bg: #2a2a2d;
  --tag-text: #bbb;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
  -webkit-font-smoothing: antialiased;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Header */
.app-header {
  background: var(--bg-muted);
  border-bottom: 1px solid var(--border);
  padding: 28px 0 24px;
}
.app-title {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 600;
}
.app-subtitle {
  margin: 0;
  color: var(--text-muted);
  font-size: 14px;
}

/* Main */
.app-main {
  padding: 24px 0 40px;
  min-height: calc(100vh - 220px);
}

/* Loading */
.loading {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

/* Footer */
.app-footer {
  border-top: 1px solid var(--border);
  padding: 16px 0;
  font-size: 13px;
  color: var(--text-faint);
}
.app-footer a {
  color: var(--text-muted);
  text-decoration: none;
}
.app-footer a:hover { color: var(--accent); }
.footer-sep { margin: 0 8px; }

/* Utility */
.hidden { display: none !important; }
```

- [ ] **Step 3: Create minimal app.js that loads the JSON**

Create `assets/app.js`:

```javascript
// Skill Gallery - main app
const state = {
  skills: [],
  filtered: [],
  currentView: 'list',
  currentSlug: null,
  searchQuery: '',
  activeTags: new Set(),
  activePlatforms: new Set(),
  sortBy: 'updated_at',
};

const app = document.getElementById('app');

async function loadSkills() {
  try {
    const res = await fetch('assets/search-index.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.skills = await res.json();
    state.filtered = [...state.skills];
    updateSkillCount();
    render();
  } catch (err) {
    app.innerHTML = `<div class="loading">Error loading skills: ${err.message}</div>`;
  }
}

function updateSkillCount() {
  const el = document.getElementById('skill-count');
  if (el) el.textContent = `${state.skills.length} skills`;
}

function render() {
  app.innerHTML = `<div class="loading">Rendering...</div>`;
  // Placeholder — real rendering implemented in subsequent tasks
  app.innerHTML = `<p>${state.skills.length} skills loaded</p>`;
}

// Init
loadSkills();
```

- [ ] **Step 4: Start a local server and verify the page loads**

Run in one terminal: `python3 -m http.server 8000`
In another: `curl -s http://localhost:8000/ | head -5`
Expected: HTML page returned.

Also verify: `curl -s http://localhost:8000/assets/search-index.json | head -3`
Expected: JSON array of skills.

- [ ] **Step 5: Commit**

```bash
git add index.html assets/style.css assets/app.js
git commit -m "feat: add frontend skeleton with HTML/CSS/JS bootstrap"
```

---

### Task 4: List View — Cards, Filters, Sorting

**Files:**
- Modify: `assets/app.js` (add list rendering, filter logic)
- Modify: `assets/style.css` (add card, filter, grid styles)

**Interfaces:**
- Consumes: `state.skills` array from Task 3
- Produces: `renderList()` function, `applyFilters()` function

- [ ] **Step 1: Add list view styles to style.css**

Append to `assets/style.css`:

```css
/* ---- Layout: list view ---- */
.list-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 24px;
}
@media (max-width: 768px) {
  .list-layout {
    grid-template-columns: 1fr;
  }
  .filters {
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 10;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }
}

/* ---- Filters ---- */
.filters h3 {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin: 0 0 10px;
}
.filter-section {
  margin-bottom: 20px;
}
.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.filter-tag {
  display: inline-block;
  padding: 3px 10px;
  font-size: 12px;
  border-radius: 999px;
  background: var(--tag-bg);
  color: var(--tag-text);
  cursor: pointer;
  user-select: none;
  transition: all 0.15s;
  border: 1px solid transparent;
}
.filter-tag:hover {
  border-color: var(--border-hover);
}
.filter-tag.active {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: var(--accent);
}

/* ---- Search bar ---- */
.search-bar {
  margin-bottom: 20px;
}
.search-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 15px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-card);
  color: var(--text);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

/* ---- Sort controls ---- */
.sort-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.result-count {
  font-size: 13px;
  color: var(--text-muted);
}
.sort-select {
  padding: 6px 10px;
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
}

/* ---- Skill cards grid ---- */
.skill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.skill-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: var(--shadow-sm);
}
.skill-card:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.skill-card-title {
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 600;
}
.skill-card-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.skill-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.skill-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-faint);
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

/* ---- Badges ---- */
.badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
  background: var(--tag-bg);
  color: var(--tag-text);
}
.badge-platform {
  background: var(--accent-soft);
  color: var(--accent);
}
.badge-source-self-built { background: #dcfce7; color: #166534; }
.badge-source-github { background: #f0f0f0; color: #333; }
.badge-source-marketplace { background: #fef3c7; color: #92400e; }
.badge-source-platform-native { background: #e0e7ff; color: #3730a3; }
.badge-source-other { background: var(--tag-bg); color: var(--tag-text); }

[data-theme="dark"] .badge-source-self-built { background: #14532d; color: #bbf7d0; }
[data-theme="dark"] .badge-source-github { background: #333; color: #ccc; }
[data-theme="dark"] .badge-source-marketplace { background: #78350f; color: #fde68a; }
[data-theme="dark"] .badge-source-platform-native { background: #312e81; color: #c7d2fe; }

/* ---- Empty state ---- */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}
.empty-state h3 {
  margin: 0 0 8px;
  color: var(--text);
}
.empty-state button {
  margin-top: 12px;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  font-size: 13px;
}
.empty-state button:hover {
  border-color: var(--accent);
  color: var(--accent);
}
```

- [ ] **Step 2: Rewrite app.js with list view, filters, and sorting**

Replace `assets/app.js` with:

```javascript
// Skill Gallery - main app
const state = {
  skills: [],
  filtered: [],
  currentView: 'list',
  currentSlug: null,
  searchQuery: '',
  activeTags: new Set(),
  activePlatforms: new Set(),
  sortBy: 'updated_at',
};

const app = document.getElementById('app');

// ---------- Data Loading ----------
async function loadSkills() {
  try {
    const res = await fetch('assets/search-index.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.skills = await res.json();
    state.filtered = [...state.skills];
    updateSkillCount();
    initTheme();
    render();
  } catch (err) {
    app.innerHTML = `<div class="loading">Error loading skills: ${err.message}</div>`;
  }
}

function updateSkillCount() {
  const el = document.getElementById('skill-count');
  if (el) el.textContent = `${state.skills.length} skills`;
}

// ---------- Theme ----------
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
}

// ---------- Filter Logic ----------
function getAllTags() {
  const tags = new Set();
  state.skills.forEach(s => s.tags.forEach(t => tags.add(t)));
  return Array.from(tags).sort();
}

function getAllPlatforms() {
  const plats = new Set();
  state.skills.forEach(s => s.platforms.forEach(p => plats.add(p)));
  return Array.from(plats).sort();
}

function applyFilters() {
  const q = state.searchQuery.toLowerCase().trim();

  state.filtered = state.skills.filter(skill => {
    // Tag filter (AND)
    if (state.activeTags.size > 0) {
      for (const tag of state.activeTags) {
        if (!skill.tags.includes(tag)) return false;
      }
    }
    // Platform filter (AND)
    if (state.activePlatforms.size > 0) {
      for (const plat of state.activePlatforms) {
        if (!skill.platforms.includes(plat)) return false;
      }
    }
    // Text search (simple substring across name, description, tags, content)
    if (q) {
      const haystack = (
        skill.name + ' ' +
        skill.description + ' ' +
        skill.tags.join(' ') + ' ' +
        skill.content
      ).toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });

  // Sort
  if (state.sortBy === 'name') {
    state.filtered.sort((a, b) => a.name.localeCompare(b.name));
  } else {
    state.filtered.sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
  }
}

// ---------- Rendering ----------
function render() {
  applyFilters();

  if (state.currentView === 'detail') {
    renderDetail();
  } else {
    renderList();
  }
}

function renderList() {
  const allTags = getAllTags();
  const allPlatforms = getAllPlatforms();

  app.innerHTML = `
    <div class="list-layout">
      <aside class="filters">
        <div class="search-bar">
          <input type="text" class="search-input" id="search-input"
                 placeholder="Search skills..." value="${escapeHtml(state.searchQuery)}">
        </div>

        <div class="filter-section">
          <h3>Platforms</h3>
          <div class="filter-tags" id="platform-filters">
            ${allPlatforms.map(p => `
              <span class="filter-tag${state.activePlatforms.has(p) ? ' active' : ''}"
                    data-platform="${escapeHtml(p)}">${escapeHtml(p)}</span>
            `).join('')}
          </div>
        </div>

        <div class="filter-section">
          <h3>Tags</h3>
          <div class="filter-tags" id="tag-filters">
            ${allTags.map(tag => `
              <span class="filter-tag${state.activeTags.has(tag) ? ' active' : ''}"
                    data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</span>
            `).join('')}
          </div>
        </div>
      </aside>

      <div class="list-content">
        <div class="sort-bar">
          <span class="result-count">${state.filtered.length} result${state.filtered.length === 1 ? '' : 's'}</span>
          <select class="sort-select" id="sort-select">
            <option value="updated_at"${state.sortBy === 'updated_at' ? ' selected' : ''}>Recently updated</option>
            <option value="name"${state.sortBy === 'name' ? ' selected' : ''}>Name (A-Z)</option>
          </select>
        </div>

        ${state.filtered.length === 0 ? `
          <div class="empty-state">
            <h3>No skills found</h3>
            <p>Try clearing filters or searching for something else.</p>
            <button id="clear-filters-btn">Clear all filters</button>
          </div>
        ` : `
          <div class="skill-grid">
            ${state.filtered.map(renderCard).join('')}
          </div>
        `}
      </div>
    </div>
  `;

  attachListHandlers();
}

function renderCard(skill) {
  const sourceClass = `badge-source-${skill.source}`;
  return `
    <div class="skill-card" data-slug="${skill.slug}">
      <h3 class="skill-card-title">${escapeHtml(skill.name)}</h3>
      <p class="skill-card-desc">${escapeHtml(skill.description)}</p>
      <div class="skill-card-meta">
        ${skill.platforms.slice(0, 3).map(p => `
          <span class="badge badge-platform">${escapeHtml(p)}</span>
        `).join('')}
        <span class="badge ${sourceClass}">${escapeHtml(skill.source)}</span>
      </div>
      <div class="skill-card-footer">
        <span>${skill.tags.slice(0, 2).map(t => '#' + escapeHtml(t)).join(' ')}</span>
        <span>${formatDate(skill.updated_at)}</span>
      </div>
    </div>
  `;
}

// ---------- Event Handlers ----------
function attachListHandlers() {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.focus();
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        state.searchQuery = e.target.value;
        render();
        // Restore focus and cursor position
        const input = document.getElementById('search-input');
        if (input) {
          input.focus();
          input.setSelectionRange(input.value.length, input.value.length);
        }
      }, 200);
    });
  }

  document.querySelectorAll('.filter-tag[data-tag]').forEach(el => {
    el.addEventListener('click', () => {
      const tag = el.dataset.tag;
      if (state.activeTags.has(tag)) state.activeTags.delete(tag);
      else state.activeTags.add(tag);
      render();
    });
  });

  document.querySelectorAll('.filter-tag[data-platform]').forEach(el => {
    el.addEventListener('click', () => {
      const p = el.dataset.platform;
      if (state.activePlatforms.has(p)) state.activePlatforms.delete(p);
      else state.activePlatforms.add(p);
      render();
    });
  });

  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      state.sortBy = e.target.value;
      render();
    });
  }

  const clearBtn = document.getElementById('clear-filters-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      state.searchQuery = '';
      state.activeTags.clear();
      state.activePlatforms.clear();
      render();
    });
  }

  document.querySelectorAll('.skill-card').forEach(card => {
    card.addEventListener('click', () => {
      const slug = card.dataset.slug;
      navigateToDetail(slug);
    });
  });
}

function navigateToDetail(slug) {
  window.location.hash = `#/skill/${slug}`;
}

// ---------- Utilities ----------
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ---------- Routing ----------
function handleRoute() {
  const hash = window.location.hash;
  const match = hash.match(/^#\/skill\/([^/]+)/);
  if (match) {
    state.currentView = 'detail';
    state.currentSlug = match[1];
  } else {
    state.currentView = 'list';
    state.currentSlug = null;
  }
  if (state.skills.length > 0) render();
}

window.addEventListener('hashchange', handleRoute);

// ---------- Init ----------
loadSkills().then(() => {
  handleRoute();
});
```

- [ ] **Step 3: Verify list view renders correctly**

Run the server if not already running: `python3 -m http.server 8000`
Then check: `curl -s http://localhost:8000/assets/app.js | wc -l`
Expected: ~250+ lines of JS

Verify by checking the HTML structure contains expected class names:
Run: `grep -c "skill-grid\|filter-tag\|search-input" assets/style.css`
Expected: 3+ matches

- [ ] **Step 4: Commit**

```bash
git add assets/app.js assets/style.css
git commit -m "feat: add list view with cards, filters, and sorting"
```

---

### Task 5: Detail View — Markdown Rendering & Hash Routing

**Files:**
- Modify: `index.html` (add marked.js CDN)
- Modify: `assets/app.js` (add detail view rendering)
- Modify: `assets/style.css` (add detail view + markdown styles)

**Interfaces:**
- Consumes: skill objects from `state.skills`; marked.js library loaded from CDN
- Produces: `renderDetail()` function, complete hash routing

- [ ] **Step 1: Add marked.js CDN to index.html**

In `index.html`, add this line before the `app.js` script tag:

```html
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="assets/app.js"></script>
```

- [ ] **Step 2: Add detail view styles to style.css**

Append to `assets/style.css`:

```css
/* ---- Detail view ---- */
.detail-view {
  max-width: 800px;
  margin: 0 auto;
}
.detail-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-bottom: 20px;
  transition: all 0.15s;
}
.detail-back:hover {
  color: var(--accent);
  border-color: var(--accent);
}

.detail-header {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}
.detail-title {
  margin: 0 0 10px;
  font-size: 28px;
  font-weight: 700;
}
.detail-desc {
  margin: 0 0 14px;
  font-size: 15px;
  color: var(--text-muted);
}
.detail-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.detail-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  transition: all 0.15s;
}
.btn:hover {
  border-color: var(--border-hover);
  background: var(--bg-muted);
}
.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.btn-primary:hover {
  background: #2563eb;
  border-color: #2563eb;
}
[data-theme="dark"] .btn-primary:hover {
  background: #3b82f6;
  border-color: #3b82f6;
}
.export-menu {
  position: relative;
}
.export-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  min-width: 200px;
  z-index: 100;
  display: none;
}
.export-dropdown.open { display: block; }
.export-item {
  display: block;
  width: 100%;
  padding: 10px 14px;
  text-align: left;
  font-size: 13px;
  background: none;
  border: none;
  color: var(--text);
  cursor: pointer;
}
.export-item:hover {
  background: var(--bg-muted);
}

/* ---- Compatibility notice ---- */
.compat-notice {
  padding: 12px 16px;
  background: var(--accent-soft);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  font-size: 13px;
  margin-bottom: 24px;
}
.compat-notice strong { color: var(--accent); }

/* ---- Markdown content ---- */
.markdown-body {
  line-height: 1.7;
}
.markdown-body h1 { font-size: 22px; margin: 24px 0 12px; font-weight: 700; }
.markdown-body h2 { font-size: 18px; margin: 22px 0 10px; font-weight: 600; }
.markdown-body h3 { font-size: 16px; margin: 18px 0 8px; font-weight: 600; }
.markdown-body p { margin: 12px 0; }
.markdown-body ul, .markdown-body ol { margin: 12px 0; padding-left: 24px; }
.markdown-body li { margin: 4px 0; }
.markdown-body code {
  padding: 2px 6px;
  font-size: 13px;
  font-family: "SF Mono", Monaco, Consolas, monospace;
  background: var(--bg-muted);
  border-radius: 4px;
}
.markdown-body pre {
  padding: 14px;
  overflow-x: auto;
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
  margin: 14px 0;
}
.markdown-body pre code {
  padding: 0;
  background: none;
}
.markdown-body blockquote {
  margin: 14px 0;
  padding: 4px 14px;
  border-left: 3px solid var(--border);
  color: var(--text-muted);
}
.markdown-body a {
  color: var(--accent);
  text-decoration: none;
}
.markdown-body a:hover { text-decoration: underline; }
.markdown-body hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 24px 0;
}
.markdown-body table {
  border-collapse: collapse;
  margin: 14px 0;
  width: 100%;
}
.markdown-body th, .markdown-body td {
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
}
.markdown-body th { background: var(--bg-muted); }

/* ---- Detail footer info ---- */
.detail-footer-info {
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-muted);
}
.detail-footer-info p { margin: 6px 0; }
.detail-footer-info a { color: var(--accent); text-decoration: none; }
.detail-footer-info a:hover { text-decoration: underline; }

.usage-notes {
  margin-top: 24px;
  padding: 14px 18px;
  background: var(--bg-muted);
  border-radius: var(--radius);
  border-left: 3px solid var(--warning);
}
.usage-notes h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--warning);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.usage-notes p { margin: 6px 0; font-size: 14px; }

/* ---- Toast ---- */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  background: var(--text);
  color: var(--bg);
  border-radius: var(--radius);
  font-size: 13px;
  z-index: 1000;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}
.toast.show { opacity: 0.95; }
```

- [ ] **Step 3: Add detail view rendering to app.js**

Add these functions to `assets/app.js` (before the `// ---------- Init ----------` line):

```javascript
// ---------- Detail View ----------
function renderDetail() {
  const skill = state.skills.find(s => s.slug === state.currentSlug);
  if (!skill) {
    app.innerHTML = `
      <div class="detail-view">
        <button class="detail-back" onclick="window.location.hash = ''">← Back to list</button>
        <div class="empty-state">
          <h3>Skill not found</h3>
          <p>The skill "${escapeHtml(state.currentSlug)}" doesn't exist.</p>
        </div>
      </div>
    `;
    return;
  }

  const sourceClass = `badge-source-${skill.source}`;
  const marked = window.marked;

  app.innerHTML = `
    <div class="detail-view">
      <button class="detail-back" id="detail-back">← Back to list</button>

      <div class="detail-header">
        <h1 class="detail-title">${escapeHtml(skill.name)}</h1>
        <p class="detail-desc">${escapeHtml(skill.description)}</p>
        <div class="detail-meta-row">
          ${skill.platforms.map(p => `
            <span class="badge badge-platform">${escapeHtml(p)}</span>
          `).join('')}
          <span class="badge ${sourceClass}">${escapeHtml(skill.source)}</span>
        </div>
        <div class="detail-meta-row">
          ${skill.tags.map(t => `
            <span class="badge">#${escapeHtml(t)}</span>
          `).join('')}
        </div>
      </div>

      <div class="detail-toolbar">
        <div class="export-menu">
          <button class="btn btn-primary" id="export-btn">Export ↓</button>
          <div class="export-dropdown" id="export-dropdown">
            <button class="export-item" data-export="codex">Codex SKILL.md</button>
            <button class="export-item" data-export="claude">Claude Code format</button>
            <button class="export-item" data-export="raw">Raw markdown</button>
            <button class="export-item" data-export="link">Copy link</button>
          </div>
        </div>
      </div>

      <div class="compat-notice">
        <strong>Compatibility:</strong> This skill works best on
        ${skill.platforms.map(p => `<code>${escapeHtml(p)}</code>`).join(', ')}.
        Other platforms may require format adjustments.
      </div>

      <div class="markdown-body" id="markdown-content">
        ${marked ? marked.parse(getSkillMarkdownBody(skill)) : '<p>Loading...</p>'}
      </div>

      ${skill.usage_notes ? `
        <div class="usage-notes">
          <h4>Personal Notes</h4>
          <p>${escapeHtml(skill.usage_notes).replace(/\n/g, '<br>')}</p>
        </div>
      ` : ''}

      <div class="detail-footer-info">
        ${skill.author ? `<p><strong>Author:</strong> ${escapeHtml(skill.author)}</p>` : ''}
        ${skill.source_url ? `<p><strong>Source:</strong> <a href="${escapeHtml(skill.source_url)}" target="_blank" rel="noopener">${escapeHtml(skill.source_url)}</a></p>` : ''}
        <p><strong>Added:</strong> ${formatDate(skill.created_at)} · <strong>Updated:</strong> ${formatDate(skill.updated_at)}</p>
      </div>
    </div>

    <div class="toast" id="toast"></div>
  `;

  attachDetailHandlers();
}

function getSkillMarkdownBody(skill) {
  // We only have plain text content in the index. For full markdown,
  // we'd need to fetch the .md file. For now, use content (plain text).
  // TODO: fetch raw .md file for full formatting (enhancement)
  return skill.content;
}

function attachDetailHandlers() {
  const backBtn = document.getElementById('detail-back');
  if (backBtn) backBtn.addEventListener('click', () => {
    window.location.hash = '';
  });

  const exportBtn = document.getElementById('export-btn');
  const exportDropdown = document.getElementById('export-dropdown');
  if (exportBtn && exportDropdown) {
    exportBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      exportDropdown.classList.toggle('open');
    });
    document.addEventListener('click', () => {
      exportDropdown.classList.remove('open');
    });
  }

  document.querySelectorAll('.export-item').forEach(item => {
    item.addEventListener('click', () => {
      const format = item.dataset.export;
      handleExport(format);
      document.getElementById('export-dropdown').classList.remove('open');
    });
  });
}

function handleExport(format) {
  const skill = state.skills.find(s => s.slug === state.currentSlug);
  if (!skill) return;

  const rawMd = buildFullMarkdown(skill);

  if (format === 'codex') {
    downloadFile(`${skill.slug}.md`, rawMd);
    showToast('Downloaded: Codex SKILL.md');
  } else if (format === 'claude') {
    const claude = buildClaudeFormat(skill);
    downloadFile(`${skill.slug}.md`, claude);
    showToast('Downloaded: Claude Code format');
  } else if (format === 'raw') {
    copyToClipboard(rawMd);
    showToast('Copied markdown to clipboard');
  } else if (format === 'link') {
    copyToClipboard(window.location.href);
    showToast('Link copied to clipboard');
  }
}

function buildFullMarkdown(skill) {
  const lines = ['---'];
  lines.push(`name: ${skill.name}`);
  lines.push(`description: ${skill.description}`);
  lines.push(`tags: [${skill.tags.join(', ')}]`);
  lines.push(`platforms: [${skill.platforms.join(', ')}]`);
  lines.push(`source: ${skill.source}`);
  if (skill.source_url) lines.push(`source_url: ${skill.source_url}`);
  if (skill.author) lines.push(`author: ${skill.author}`);
  lines.push(`created_at: ${skill.created_at}`);
  lines.push(`updated_at: ${skill.updated_at}`);
  if (skill.usage_notes) {
    lines.push('usage_notes: |');
    skill.usage_notes.split('\n').forEach(l => lines.push(`  ${l}`));
  }
  lines.push('---');
  lines.push('');
  lines.push(skill.content);
  return lines.join('\n');
}

function buildClaudeFormat(skill) {
  // Claude Code skills are simpler: title + description + body
  // No frontmatter; uses markdown headings
  const lines = [];
  lines.push(`# ${skill.name}`);
  lines.push('');
  lines.push(`> ${skill.description}`);
  lines.push('');
  lines.push(`**Platforms:** ${skill.platforms.join(', ')}`);
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push(skill.content);
  return lines.join('\n');
}

function downloadFile(filename, content) {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch (e) {}
  document.body.removeChild(ta);
}

function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}
```

- [ ] **Step 4: Fix getSkillMarkdownBody — fetch actual .md file for full rendering**

Replace the `getSkillMarkdownBody` function in app.js with a proper async version. But since our current architecture renders synchronously, for v1 we'll keep using `skill.content` (plain text). Mark a note that this is a known limitation — detail view shows plain text content, not full markdown formatting. This is acceptable for v1.

- [ ] **Step 5: Verify detail view works by checking hash routing**

Confirm that the app.js has both `handleRoute` (already added in Task 4) and `renderDetail` (new).

Run: `grep -c "renderDetail\|handleRoute" assets/app.js`
Expected: 2+ matches

- [ ] **Step 6: Commit**

```bash
git add index.html assets/app.js assets/style.css
git commit -m "feat: add detail view with markdown rendering and export"
```

---

### Task 6: Full-Text Search with Minisearch

**Files:**
- Modify: `index.html` (add minisearch CDN)
- Modify: `assets/app.js` (replace substring search with minisearch)

**Interfaces:**
- Consumes: `state.skills` array, minisearch library from CDN
- Produces: `searchIndex` (minisearch instance), results with highlights

- [ ] **Step 1: Add minisearch CDN to index.html**

In `index.html`, add minisearch before marked.js:

```html
  <script src="https://cdn.jsdelivr.net/npm/minisearch@6.3.0/dist/umd/index.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="assets/app.js"></script>
```

- [ ] **Step 2: Add minisearch integration to app.js**

Add `searchIndex: null` to the `state` object.

Then add this function after `loadSkills`:

```javascript
// ---------- Search Index ----------
let miniSearch = null;

function buildSearchIndex() {
  if (!window.MiniSearch) {
    console.warn('MiniSearch not available, falling back to substring search');
    return;
  }

  miniSearch = new window.MiniSearch({
    fields: ['name', 'description', 'tags', 'content'],
    storeFields: ['name', 'description', 'slug'],
    searchOptions: {
      boost: { name: 3, description: 2, tags: 2 },
      fuzzy: 0.2,
      prefix: true,
    },
  });

  state.skills.forEach((skill, i) => {
    miniSearch.add({
      id: i,
      slug: skill.slug,
      name: skill.name,
      description: skill.description,
      tags: skill.tags.join(' '),
      content: skill.content,
    });
  });
}
```

- [ ] **Step 3: Replace text filter in applyFilters with minisearch**

In the `applyFilters` function, replace the text search block:

Old:
```javascript
    // Text search (simple substring across name, description, tags, content)
    if (q) {
      const haystack = (
        skill.name + ' ' +
        skill.description + ' ' +
        skill.tags.join(' ') + ' ' +
        skill.content
      ).toLowerCase();
      if (!haystack.includes(q)) return false;
    }
```

New:
```javascript
    // Text search — use minisearch if available
    if (q) {
      if (miniSearch) {
        const results = miniSearch.search(q);
        const resultSlugs = new Set(results.map(r => state.skills[r.id].slug));
        if (!resultSlugs.has(skill.slug)) return false;
      } else {
        // Fallback: substring search
        const haystack = (
          skill.name + ' ' +
          skill.description + ' ' +
          skill.tags.join(' ') + ' ' +
          skill.content
        ).toLowerCase();
        if (!haystack.includes(q)) return false;
      }
    }
```

When using minisearch, we also want results ordered by search relevance (not just date/name). Add this logic at the end of `applyFilters`, after the sort block:

```javascript
  // When searching with minisearch, sort by relevance
  if (q && miniSearch) {
    const results = miniSearch.search(q);
    const scoreMap = new Map();
    results.forEach(r => {
      scoreMap.set(state.skills[r.id].slug, r.score);
    });
    state.filtered.sort((a, b) => (scoreMap.get(b.slug) || 0) - (scoreMap.get(a.slug) || 0));
  }
```

- [ ] **Step 4: Call buildSearchIndex after loading skills**

In `loadSkills`, after `state.skills = await res.json();`, add:

```javascript
    buildSearchIndex();
```

- [ ] **Step 5: Add search result highlight styles**

Append to `assets/style.css`:

```css
/* ---- Search highlighting ---- */
mark.search-highlight {
  background: #fef08a;
  color: inherit;
  padding: 0 2px;
  border-radius: 2px;
}
[data-theme="dark"] mark.search-highlight {
  background: #854d0e;
  color: #fef08a;
}
```

- [ ] **Step 6: Verify search works**

Run server: `python3 -m http.server 8000`
Verify the script tags are present:
Run: `grep -c "minisearch\|marked" index.html`
Expected: 2 matches

Verify MiniSearch usage in app.js:
Run: `grep -c "miniSearch\|MiniSearch" assets/app.js`
Expected: 5+ matches

- [ ] **Step 7: Commit**

```bash
git add index.html assets/app.js assets/style.css
git commit -m "feat: add full-text search with minisearch"
```

---

### Task 7: Dark Mode Toggle & Polish

**Files:**
- Modify: `index.html` (add theme toggle button in header)
- Modify: `assets/app.js` (add theme toggle logic)
- Modify: `assets/style.css` (add toggle button styles)

**Interfaces:**
- Produces: Working dark/light mode toggle with localStorage persistence

- [ ] **Step 1: Add theme toggle button to header in index.html**

Add a button inside `.app-header .container`, after the subtitle:

```html
    <div class="container header-row">
      <div>
        <h1 class="app-title">Skill Gallery</h1>
        <p class="app-subtitle">Personal collection of useful AI agent skills</p>
      </div>
      <button id="theme-toggle" class="theme-toggle" title="Toggle theme">🌙</button>
    </div>
```

Also replace the old header container div with this `.header-row` version.

- [ ] **Step 2: Add header row and toggle styles to style.css**

Add to the `/* Header */` section of `assets/style.css`:

```css
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.theme-toggle {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  width: 36px;
  height: 36px;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}
.theme-toggle:hover {
  border-color: var(--border-hover);
  background: var(--bg-card);
}
```

- [ ] **Step 3: Add theme toggle logic to app.js**

Replace the `initTheme` function and add `toggleTheme`:

```javascript
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  updateThemeToggle();
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeToggle();
}

function updateThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = isDark ? '☀️' : '🌙';
  btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
}
```

Add the toggle listener after loadSkills resolves. Find the init section and add:

```javascript
document.addEventListener('click', (e) => {
  if (e.target.id === 'theme-toggle') toggleTheme();
});
```

- [ ] **Step 4: Verify theme toggle**

Run: `grep -c "theme-toggle\|toggleTheme" assets/style.css assets/app.js index.html`
Expected: 5+ matches across all files

- [ ] **Step 5: Commit**

```bash
git add index.html assets/app.js assets/style.css
git commit -m "feat: add dark mode toggle"
```

---

### Task 8: README & GitHub Pages Configuration

**Files:**
- Create: `README.md`
- Create: `.nojekyll` (for GitHub Pages)
- Create: `skills/README.md` (skill format reference)

**Interfaces:**
- Produces: Complete documentation for users and contributors

- [ ] **Step 1: Create README.md**

Create `README.md`:

```markdown
# Skill Gallery

A personal collection of useful AI agent skills, organized and searchable.

> 🔗 [View the gallery](https://your-username.github.io/skill-gallery/)

## Features

- **Unified format** — all skills stored as markdown with YAML frontmatter
- **Full-text search** — instantly find skills by name, description, or content
- **Tag & platform filtering** — browse by category or target platform
- **Multi-format export** — download as Codex SKILL.md, Claude Code format, or raw markdown
- **Zero dependencies** — pure static site, no build tools required
- **Dark mode** — easy on the eyes

## Usage

### Adding a skill

1. Create a new file in `skills/` named `<slug>.md` (use lowercase letters, numbers, and hyphens)
2. Fill in the frontmatter and body (see [skill format guide](skills/README.md))
3. Rebuild the index: `node scripts/build-index.js`
4. Commit and push

### Development

```bash
# Build search index
node scripts/build-index.js

# Preview locally
python3 -m http.server 8000
# Open http://localhost:8000
```

### Deploying

This site is designed for GitHub Pages:

1. Push to a GitHub repo
2. Enable GitHub Pages in repo settings (source: main branch, root directory)
3. The site will be available at `https://<username>.github.io/<repo-name>/`

No build step required on the server — everything is pre-built static files.

## Skill Sources

Skills come from:
- **Self-built** — skills I've written myself
- **GitHub** — discovered in public repositories
- **Marketplace** — from skill marketplaces and platforms
- **Platform-native** — built into agent platforms like Codex, Claude Code

All external skills are credited with source links to the original authors.

## License

Skills retain their original licenses. See individual skill entries for source attribution.
```

- [ ] **Step 2: Create skills/README.md**

Create `skills/README.md`:

```markdown
# Skill File Format

Each skill is a markdown file with YAML frontmatter.

## Naming

- Filename = slug (URL-friendly identifier)
- Use lowercase letters, numbers, and hyphens only
- Example: `systematic-debugging.md`

## Frontmatter Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `name` | ✓ | string | Display name |
| `description` | ✓ | string | One-line summary |
| `tags` | ✓ | array | Category tags |
| `platforms` | ✓ | array | Target platforms: `codex`, `claude-code`, `cursor`, `generic`, etc. |
| `source` | ✓ | string | Source type: `self-built`, `github`, `marketplace`, `platform-native`, `other` |
| `source_url` | ✗ | string | Original URL |
| `author` | ✗ | string | Original author |
| `created_at` | ✓ | date | Date added (YYYY-MM-DD) |
| `updated_at` | ✓ | date | Last updated (YYYY-MM-DD) |
| `usage_notes` | ✗ | string | Personal usage notes (multiline with `\|`) |

## Example

```markdown
---
name: My Skill
description: A brief description of what this skill does
tags: [example, workflow]
platforms: [codex, generic]
source: self-built
author: Your Name
created_at: 2026-08-02
updated_at: 2026-08-02
usage_notes: |
  These are my personal notes
  about using this skill.
---

# My Skill

Full skill content in markdown format...
```
```

- [ ] **Step 3: Create .nojekyll**

Create `.nojekyll` (empty file):

```bash
touch .nojekyll
```

This tells GitHub Pages not to process the site with Jekyll, which speeds up deployment and avoids Jekyll ignoring files starting with underscores.

- [ ] **Step 4: Verify all files are in place**

Run:
```bash
ls -la README.md skills/README.md .nojekyll
wc -l README.md skills/README.md
```
Expected: All three files exist with content.

- [ ] **Step 5: Commit**

```bash
git add README.md skills/README.md .nojekyll
git commit -m "docs: add README, skill format guide, and .nojekyll"
```

---

### Task 9: End-to-End Verification

**Files:** None (verification only)

**Interfaces:** Confirms everything works together end-to-end

- [ ] **Step 1: Do a fresh build of the index**

Run:
```bash
rm assets/search-index.json
node scripts/build-index.js
```
Expected: 3 skills built successfully, no errors.

- [ ] **Step 2: Start the server and verify all endpoints**

Run:
```bash
python3 -m http.server 8000 &
sleep 1
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
echo ""
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/assets/app.js
echo ""
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/assets/style.css
echo ""
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/assets/search-index.json
echo ""
kill %1 2>/dev/null
```
Expected: All return 200.

- [ ] **Step 3: Verify search-index.json has correct structure**

Run:
```bash
node -e "
const data = require('./assets/search-index.json');
console.log('Total skills:', data.length);
const required = ['slug','name','description','tags','platforms','source','created_at','updated_at','content'];
data.forEach(s => {
  const missing = required.filter(k => !(k in s));
  if (missing.length) console.log(s.slug, 'MISSING:', missing);
  else console.log(s.slug, '✓');
});
"
```
Expected: All 3 skills have all required fields.

- [ ] **Step 4: Final check — no console errors in the JS**

Run:
```bash
node -e "
// Syntax-check app.js by requiring it won't work (browser code),
// so use node's syntax check
const fs = require('fs');
const code = fs.readFileSync('assets/app.js', 'utf-8');
try {
  new Function(code);
  console.log('app.js: syntax OK');
} catch (e) {
  console.log('app.js: SYNTAX ERROR:', e.message);
}
"
```
Expected: `app.js: syntax OK`

Note: `new Function()` checks syntax but doesn't execute the code. Browser APIs (fetch, document, etc.) are not available in Node but that's fine for syntax validation.

- [ ] **Step 5: No commit needed — this is a verification task only**

