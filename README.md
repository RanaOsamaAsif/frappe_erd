# frappe-erd

A focused ERD Viewer app for the Frappe Framework.

## What it does

- Build an ERD from selected Frappe DocTypes
- Visualize table relationships and field structures
- Inspect DocType metadata in a side drawer
- Export the ERD view as an image

## Tech

- Backend: Frappe + Python
- Frontend: React + Vite + `frappe-react-sdk` + React Flow

## Install

```bash
bench get-app https://github.com/RanaOsamaAsif/frappe_erd.git
bench --site your-site install-app frappe_erd
```

## Route

- App: `/erd-viewer`

## Access Control

- `frappe-erd` uses a dedicated role named `ERD Viewer`.
- Assign this role to users who should access the ERD UI and APIs.
- Users without `ERD Viewer` (or `System Manager`) cannot access ERD, and do not need direct `DocType` permission.

## API methods kept

- `frappe_erd.api.erd_viewer.get_meta_erd_schema_for_doctypes`
- `frappe_erd.api.erd_viewer.get_meta_for_doctype`

## Credits and Attribution

This project is forked from [The Commit Company - Commit](https://github.com/The-commit-company/commit).

Credit and thanks to The Commit Company and the original Commit contributors for building and open-sourcing the upstream project. `frappe-erd` was extracted and adapted from that codebase to provide a standalone ERD Viewer focused specifically on schema visualization for the Frappe/ERPNext ecosystem.

The goal of this fork is to keep the ERD functionality lightweight, easier to adopt, and simpler to maintain as an independent app.

## License

This project is released under AGPL-3.0. Please also review and respect the upstream project's license and credits.

## Contributing

Suggestions, feature requests, and pull requests are welcome.
