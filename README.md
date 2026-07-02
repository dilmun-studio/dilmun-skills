# dilmun-skills

Open-source **Claude Code skills, agents, and plugins** by [Dilmun (دلمون)](https://github.com/dilmun) — a software & design studio.

This repository is a [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces): each product lives in its own folder under `plugins/` and is registered in `.claude-plugin/marketplace.json`.

## Install

```
/plugin marketplace add dilmun/dilmun-skills
/plugin install <plugin-name>@dilmun-skills
```

## Products

| Plugin | What it does |
| --- | --- |
| _(first products coming soon)_ | |

## Principles

- **Key-free by default** — every product works without paid API keys; paid integrations, if any, are optional and off by default.
- **Small and self-contained** — the least code that solves the problem, no bundled frameworks.
- **Tested claims only** — anything the README states has been verified.

## Repository layout

```
.claude-plugin/marketplace.json   # marketplace manifest (registry of all plugins)
plugins/<name>/                   # one self-contained plugin per folder
  .claude-plugin/plugin.json      #   plugin manifest
  skills/<skill-name>/SKILL.md    #   skills (model-invoked)
  commands/ agents/ hooks/        #   optional components
```

## ملخص بالعربية

مستودع **دلمون** للمنتجات مفتوحة المصدر: سكلز ووكلاء وإضافات لـ Claude Code، منشورة كسوق إضافات (plugin marketplace) — كل منتج بمجلد مستقل تحت `plugins/`، مجاني وبلا مفاتيح مدفوعة، برخصة MIT.

---

MIT License — © 2026 Dilmun (دلمون)
