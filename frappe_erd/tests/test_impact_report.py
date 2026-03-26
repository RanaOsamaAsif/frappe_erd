from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from frappe_erd.api.erd_viewer import get_doctype_impact_report
from frappe_erd.frappe_erd.code_analysis.impact_report import (
    _collect_automation_and_reports,
    _collect_customizations,
    _collect_reverse_links,
    _collect_runtime_hooks,
    build_doctype_impact_report,
)


class TestImpactReport(FrappeTestCase):
    def test_collect_reverse_links_includes_docfields_and_custom_fields(self):
        def fake_get_all(doctype, **kwargs):
            if doctype == "DocField":
                return [
                    {
                        "name": "df-link",
                        "parent": "Sales Invoice",
                        "fieldname": "customer",
                        "label": "Customer",
                        "fieldtype": "Link",
                    }
                ]
            if doctype == "Custom Field":
                return [
                    {
                        "name": "cf-link",
                        "dt": "Delivery Note",
                        "fieldname": "customer_link",
                        "label": "Customer Link",
                        "fieldtype": "Link",
                    }
                ]
            return []

        with patch(
            "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_all",
            side_effect=fake_get_all,
        ):
            report = _collect_reverse_links("Customer")

        self.assertEqual(len(report), 2)
        self.assertEqual(report[0]["source_doctype"], "Delivery Note")
        self.assertEqual(report[0]["is_custom_field"], True)
        self.assertEqual(report[1]["source_doctype"], "Sales Invoice")
        self.assertEqual(report[1]["confidence"], "high")

    def test_build_doctype_impact_report_derives_child_table_usage_from_reverse_links(self):
        meta = SimpleNamespace(get=lambda key, default=None: {"fields": [], "permissions": []}.get(key, default))

        with (
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.db.exists",
                return_value=True,
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_meta",
                return_value=meta,
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report._collect_reverse_links",
                return_value=[
                    {
                        "source_doctype": "Sales Invoice",
                        "source_fieldname": "customer",
                        "label": "Customer",
                        "fieldtype": "Link",
                        "is_custom_field": False,
                        "source_record": "df-1",
                        "confidence": "high",
                    },
                    {
                        "source_doctype": "Workflow",
                        "source_fieldname": "states",
                        "label": "States",
                        "fieldtype": "Table",
                        "is_custom_field": False,
                        "source_record": "df-2",
                        "confidence": "high",
                    },
                ],
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report._collect_child_tables",
                return_value=[],
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report._collect_customizations",
                return_value={"custom_fields": [], "property_setters": []},
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report._collect_automation_and_reports",
                return_value={
                    "workflows": [],
                    "notifications": [],
                    "webhooks": [],
                    "client_scripts": [],
                    "server_scripts": [],
                    "reports": [],
                    "print_formats": [],
                },
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report._collect_runtime_hooks",
                return_value={
                    "doc_events": [],
                    "override_doctype_class": [],
                    "permission_query_conditions": [],
                    "has_permission": [],
                },
            ),
        ):
            report = build_doctype_impact_report("Workflow Document State")

        self.assertEqual(report["summary"]["reverse_links"], 2)
        self.assertEqual(report["summary"]["child_table_usage"], 1)
        self.assertEqual(report["child_table_usage"][0]["source_doctype"], "Workflow")

    def test_collect_customizations_uses_custom_fields_and_property_setters(self):
        def fake_get_all(doctype, **kwargs):
            if doctype == "Custom Field":
                self.assertEqual(
                    kwargs["filters"]["fieldtype"],
                    ["not in", ("Section Break", "Column Break", "Tab Break", "Fold", "Heading")],
                )
                return [{"name": "cf-1", "fieldname": "customer_tier", "label": "Customer Tier"}]
            if doctype == "Property Setter":
                self.assertEqual(kwargs["filters"]["property"], ["!=", "field_order"])
                return [{"name": "ps-1", "property": "read_only", "value": "1"}]
            return []

        with patch(
            "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_all",
            side_effect=fake_get_all,
        ):
            report = _collect_customizations("Customer")

        self.assertEqual(len(report["custom_fields"]), 1)
        self.assertEqual(len(report["property_setters"]), 1)
        self.assertEqual(report["custom_fields"][0]["confidence"], "high")
        self.assertEqual(report["property_setters"][0]["confidence"], "high")

    def test_collect_automation_and_reports_reads_all_configured_sources(self):
        def fake_get_all(doctype, **kwargs):
            return [{"name": f"{doctype}-1"}]

        with patch(
            "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_all",
            side_effect=fake_get_all,
        ):
            report = _collect_automation_and_reports("ToDo")

        self.assertEqual(sorted(report.keys()), [
            "client_scripts",
            "notifications",
            "print_formats",
            "reports",
            "server_scripts",
            "webhooks",
            "workflows",
        ])
        self.assertEqual(report["reports"][0]["name"], "Report-1")
        self.assertEqual(report["reports"][0]["confidence"], "high")

    def test_collect_runtime_hooks_returns_exact_doctype_matches_only(self):
        hook_payload = {
            "doc_events": {
                "ToDo": {"on_update": ["app.todo.on_update"]},
                "*": {"on_update": ["app.any.on_update"]},
            },
            "override_doctype_class": {"ToDo": ["app.todo.CustomToDo"]},
            "permission_query_conditions": {"ToDo": ["app.todo.permission_query"]},
            "has_permission": {"ToDo": ["app.todo.has_permission"]},
        }

        with (
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_installed_apps",
                return_value=["test_app"],
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_hooks",
                return_value=hook_payload,
            ),
        ):
            report = _collect_runtime_hooks("ToDo")

        self.assertEqual(len(report["doc_events"]), 1)
        self.assertEqual(report["doc_events"][0]["event"], "on_update")
        self.assertEqual(report["override_doctype_class"][0]["methods"], ["app.todo.CustomToDo"])
        self.assertEqual(report["permission_query_conditions"][0]["methods"], ["app.todo.permission_query"])
        self.assertEqual(report["has_permission"][0]["methods"], ["app.todo.has_permission"])

    def test_api_raises_permission_error_when_access_is_denied(self):
        with patch(
            "frappe_erd.api.erd_viewer.ensure_erd_access",
            side_effect=frappe.PermissionError("Not permitted"),
        ):
            with self.assertRaises(frappe.PermissionError):
                get_doctype_impact_report("ToDo")

    def test_api_raises_validation_error_for_unknown_doctype(self):
        with (
            patch("frappe_erd.api.erd_viewer.ensure_erd_access", return_value=None),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.db.exists",
                return_value=False,
            ),
        ):
            with self.assertRaises(frappe.ValidationError):
                get_doctype_impact_report("Unknown DocType")

    def test_build_doctype_impact_report_returns_empty_sections_with_all_keys(self):
        meta = SimpleNamespace(get=lambda key, default=None: {"fields": [], "permissions": []}.get(key, default))

        with (
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.db.exists",
                return_value=True,
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_meta",
                return_value=meta,
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_all",
                return_value=[],
            ),
            patch(
                "frappe_erd.frappe_erd.code_analysis.impact_report.frappe.get_installed_apps",
                return_value=[],
            ),
        ):
            report = build_doctype_impact_report("ToDo")

        self.assertEqual(report["reverse_links"], [])
        self.assertEqual(report["child_table_usage"], [])
        self.assertEqual(report["child_tables"], [])
        self.assertEqual(report["customizations"]["custom_fields"], [])
        self.assertEqual(report["customizations"]["property_setters"], [])
        self.assertEqual(report["automation_and_reports"]["workflows"], [])
        self.assertEqual(report["runtime_hooks"]["doc_events"], [])
