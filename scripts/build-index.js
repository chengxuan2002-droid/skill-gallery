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

  const files = fs.readdirSync(SKILLS_DIR).filter(f => {
    if (!f.endsWith('.md')) return false;
    if (f.toLowerCase() === 'readme.md') return false;
    return true;
  });
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
