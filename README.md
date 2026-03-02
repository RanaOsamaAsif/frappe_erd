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
bench get-app https://github.com/RanaOsamaAsif/frappe-erd
bench --site your-site install-app frappe_erd
```

## Route

- App: `/frappe-erd`

## API methods kept

- `frappe_erd.api.erd_viewer.get_meta_erd_schema_for_doctypes`
- `frappe_erd.api.erd_viewer.get_meta_for_doctype`
