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
