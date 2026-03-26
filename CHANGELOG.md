# Changelog

## 2026-03-26

- Added a new DocType impact report in the ERD drawer to surface reverse links, child-table usage, child tables, customizations, automations, reports, and direct runtime hooks for the selected DocType.
- Added the `frappe_erd.api.erd_viewer.get_doctype_impact_report` API and typed frontend payloads for the new impact-report flow.
- Kept the v1 report intentionally focused by excluding duplicate permissions output, code-reference scanning, and layout-only customizations such as section and column breaks.
- Added backend tests for the impact-report aggregation helpers and API behavior.
- Updated the browser tab title to `ERD Viewer`.
- Rebuilt frontend assets and refreshed published HTML entrypoints for the latest UI updates.

## 2026-03-24

- Added Markdown schema export for selected DocTypes to support SQL and LLM-assisted querying.
- Added the `export_markdown_schema_for_doctypes` API and wired an `Export Markdown` action into the ERD viewer.
- Expanded ERD selection to include Single DocTypes so their schema can also be exported when needed.
- Refined generated Markdown to reduce duplication, keep full join guidance in the global summary, compact per-DocType relationship sections, and replace repeated system columns with concise notes.
- Rebuilt frontend assets and updated published HTML entrypoints for the new export flow.
