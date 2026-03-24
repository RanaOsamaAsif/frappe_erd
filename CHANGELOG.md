# Changelog

## 2026-03-24

- Added Markdown schema export for selected DocTypes to support SQL and LLM-assisted querying.
- Added the `export_markdown_schema_for_doctypes` API and wired an `Export Markdown` action into the ERD viewer.
- Expanded ERD selection to include Single DocTypes so their schema can also be exported when needed.
- Refined generated Markdown to reduce duplication, keep full join guidance in the global summary, compact per-DocType relationship sections, and replace repeated system columns with concise notes.
- Rebuilt frontend assets and updated published HTML entrypoints for the new export flow.
