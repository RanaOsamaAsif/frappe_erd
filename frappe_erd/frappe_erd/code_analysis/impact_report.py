from __future__ import annotations

from typing import Any

import frappe
from frappe import _


LINK_FIELD_TYPES = ("Link", "Table", "Table MultiSelect")
CHILD_TABLE_FIELD_TYPES = ("Table", "Table MultiSelect")
LAYOUT_ONLY_FIELD_TYPES = ("Section Break", "Column Break", "Tab Break", "Fold", "Heading")
RUNTIME_HOOK_FAMILIES = (
    "doc_events",
    "override_doctype_class",
    "permission_query_conditions",
    "has_permission",
)


def build_doctype_impact_report(doctype: str) -> dict[str, Any]:
    doctype = (doctype or "").strip()
    if not doctype:
        frappe.throw(_("Select a DocType to inspect."), frappe.ValidationError)

    if not frappe.db.exists("DocType", doctype):
        frappe.throw(_("Unknown DocType: {0}").format(doctype), frappe.ValidationError)

    meta = frappe.get_meta(doctype)

    reverse_links = _collect_reverse_links(doctype)
    child_table_usage = [
        row for row in reverse_links if row.get("fieldtype") in CHILD_TABLE_FIELD_TYPES
    ]
    child_tables = _collect_child_tables(meta)
    customizations = _collect_customizations(doctype)
    automation_and_reports = _collect_automation_and_reports(doctype)
    runtime_hooks = _collect_runtime_hooks(doctype)

    customizations_count = sum(len(records) for records in customizations.values())
    automation_count = sum(len(records) for records in automation_and_reports.values())
    runtime_hook_count = sum(len(records) for records in runtime_hooks.values())

    return {
        "doctype": doctype,
        "summary": {
            "reverse_links": len(reverse_links),
            "child_table_usage": len(child_table_usage),
            "child_tables": len(child_tables),
            "custom_fields": len(customizations["custom_fields"]),
            "property_setters": len(customizations["property_setters"]),
            "customizations": customizations_count,
            "workflows": len(automation_and_reports["workflows"]),
            "notifications": len(automation_and_reports["notifications"]),
            "webhooks": len(automation_and_reports["webhooks"]),
            "client_scripts": len(automation_and_reports["client_scripts"]),
            "server_scripts": len(automation_and_reports["server_scripts"]),
            "reports": len(automation_and_reports["reports"]),
            "print_formats": len(automation_and_reports["print_formats"]),
            "automation_and_reports": automation_count,
            "doc_events_hooks": len(runtime_hooks["doc_events"]),
            "override_doctype_class_hooks": len(runtime_hooks["override_doctype_class"]),
            "permission_query_conditions_hooks": len(runtime_hooks["permission_query_conditions"]),
            "has_permission_hooks": len(runtime_hooks["has_permission"]),
            "runtime_hooks": runtime_hook_count,
        },
        "reverse_links": reverse_links,
        "child_table_usage": child_table_usage,
        "child_tables": child_tables,
        "customizations": customizations,
        "automation_and_reports": automation_and_reports,
        "runtime_hooks": runtime_hooks,
    }


def _collect_reverse_links(doctype: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    docfields = frappe.get_all(
        "DocField",
        fields=["name", "parent", "fieldname", "label", "fieldtype"],
        filters={
            "fieldtype": ["in", LINK_FIELD_TYPES],
            "options": doctype,
        },
        order_by="parent asc, idx asc",
        ignore_permissions=True,
    )
    rows.extend(
        _with_confidence(
            [
                {
                    "source_doctype": row.get("parent"),
                    "source_fieldname": row.get("fieldname"),
                    "label": row.get("label") or row.get("fieldname"),
                    "fieldtype": row.get("fieldtype"),
                    "is_custom_field": False,
                    "source_record": row.get("name"),
                }
                for row in docfields
            ],
            "high",
        )
    )

    custom_fields = frappe.get_all(
        "Custom Field",
        fields=["name", "dt", "fieldname", "label", "fieldtype"],
        filters={
            "fieldtype": ["in", LINK_FIELD_TYPES],
            "options": doctype,
        },
        order_by="dt asc, modified asc",
        ignore_permissions=True,
    )
    rows.extend(
        _with_confidence(
            [
                {
                    "source_doctype": row.get("dt"),
                    "source_fieldname": row.get("fieldname"),
                    "label": row.get("label") or row.get("fieldname"),
                    "fieldtype": row.get("fieldtype"),
                    "is_custom_field": True,
                    "source_record": row.get("name"),
                }
                for row in custom_fields
            ],
            "high",
        )
    )

    return sorted(
        rows,
        key=lambda row: (
            cstr(row.get("source_doctype")),
            cstr(row.get("source_fieldname")),
            cstr(row.get("source_record")),
        ),
    )


def _collect_child_tables(meta: Any) -> list[dict[str, Any]]:
    rows = []
    for field in meta.get("fields", []) or []:
        if field.get("fieldtype") not in CHILD_TABLE_FIELD_TYPES or not field.get("options"):
            continue
        rows.append(
            {
                "child_doctype": field.get("options"),
                "fieldname": field.get("fieldname"),
                "label": field.get("label") or field.get("fieldname"),
                "is_custom_field": bool(field.get("is_custom_field")),
                "confidence": "high",
            }
        )

    return sorted(rows, key=lambda row: (cstr(row.get("child_doctype")), cstr(row.get("fieldname"))))


def _collect_customizations(doctype: str) -> dict[str, list[dict[str, Any]]]:
    custom_fields = _with_confidence(
        frappe.get_all(
            "Custom Field",
            fields=[
                "name",
                "fieldname",
                "label",
                "fieldtype",
                "options",
                "module",
                "modified",
            ],
            filters={
                "dt": doctype,
                "fieldtype": ["not in", LAYOUT_ONLY_FIELD_TYPES],
            },
            order_by="modified desc",
            ignore_permissions=True,
        ),
        "high",
    )
    property_setters = _with_confidence(
        frappe.get_all(
            "Property Setter",
            fields=[
                "name",
                "doctype_or_field",
                "field_name",
                "property",
                "property_type",
                "value",
                "modified",
            ],
            filters={
                "doc_type": doctype,
                "property": ["!=", "field_order"],
            },
            order_by="modified desc",
            ignore_permissions=True,
        ),
        "high",
    )

    return {
        "custom_fields": custom_fields,
        "property_setters": property_setters,
    }


def _collect_automation_and_reports(doctype: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "workflows": _with_confidence(
            frappe.get_all(
                "Workflow",
                fields=["name", "workflow_name", "is_active", "modified"],
                filters={"document_type": doctype},
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
        "notifications": _with_confidence(
            frappe.get_all(
                "Notification",
                fields=["name", "subject", "event", "enabled", "channel", "modified"],
                filters={"document_type": doctype},
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
        "webhooks": _with_confidence(
            frappe.get_all(
                "Webhook",
                fields=["name", "webhook_docevent", "request_url", "enabled", "modified"],
                filters={"webhook_doctype": doctype},
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
        "client_scripts": _with_confidence(
            frappe.get_all(
                "Client Script",
                fields=["name", "view", "enabled", "modified"],
                filters={"dt": doctype},
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
        "server_scripts": _with_confidence(
            frappe.get_all(
                "Server Script",
                fields=["name", "script_type", "doctype_event", "disabled", "modified"],
                filters={
                    "reference_doctype": doctype,
                    "script_type": ["in", ["DocType Event", "Permission Query"]],
                },
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
        "reports": _with_confidence(
            frappe.get_all(
                "Report",
                fields=["name", "report_name", "report_type", "is_standard", "disabled", "modified"],
                filters={"ref_doctype": doctype},
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
        "print_formats": _with_confidence(
            frappe.get_all(
                "Print Format",
                fields=[
                    "name",
                    "standard",
                    "custom_format",
                    "disabled",
                    "print_format_type",
                    "modified",
                ],
                filters={"doc_type": doctype, "print_format_for": "DocType"},
                order_by="modified desc",
                ignore_permissions=True,
            ),
            "high",
        ),
    }


def _collect_runtime_hooks(doctype: str) -> dict[str, list[dict[str, Any]]]:
    collected: dict[str, list[dict[str, Any]]] = {hook_family: [] for hook_family in RUNTIME_HOOK_FAMILIES}

    for app_name in frappe.get_installed_apps():
        app_hooks = frappe.get_hooks(app_name=app_name)

        doc_events = (app_hooks.get("doc_events") or {}).get(doctype)
        if isinstance(doc_events, dict):
            for event, methods in sorted(doc_events.items()):
                collected["doc_events"].append(
                    {
                        "app_name": app_name,
                        "event": event,
                        "methods": _normalize_hook_values(methods),
                        "confidence": "high",
                    }
                )

        override = (app_hooks.get("override_doctype_class") or {}).get(doctype)
        if override:
            collected["override_doctype_class"].append(
                {
                    "app_name": app_name,
                    "methods": _normalize_hook_values(override),
                    "confidence": "high",
                }
            )

        permission_query_conditions = (app_hooks.get("permission_query_conditions") or {}).get(doctype)
        if permission_query_conditions:
            collected["permission_query_conditions"].append(
                {
                    "app_name": app_name,
                    "methods": _normalize_hook_values(permission_query_conditions),
                    "confidence": "high",
                }
            )

        has_permission = (app_hooks.get("has_permission") or {}).get(doctype)
        if has_permission:
            collected["has_permission"].append(
                {
                    "app_name": app_name,
                    "methods": _normalize_hook_values(has_permission),
                    "confidence": "high",
                }
            )

    return collected


def _with_confidence(records: list[dict[str, Any]], confidence: str) -> list[dict[str, Any]]:
    return [{**record, "confidence": confidence} for record in records]


def _normalize_hook_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [cstr(entry) for entry in value if entry]
    if value:
        return [cstr(value)]
    return []


def cstr(value: Any) -> str:
    return "" if value is None else str(value)
