import frappe
from frappe_erd.frappe_erd.code_analysis.schema_builder import get_schema_from_doctypes_json
from frappe_erd.frappe_erd.code_analysis.markdown_schema_export import build_markdown_schema_export
from frappe_erd.permissions import ensure_erd_access


@frappe.whitelist()
def get_doctype_modules():
    """Get installed DocType modules for the ERD picker."""
    ensure_erd_access()

    modules = frappe.get_all(
        "DocType",
        fields=["module"],
        filters=[
            ["DocType", "is_virtual", "=", 0],
            ["DocType", "module", "!=", ""],
        ],
        distinct=True,
        order_by="module asc",
        ignore_permissions=True,
    )

    return [module.module for module in modules if module.module]


@frappe.whitelist()
def get_doctypes(search_text: str = "", module: str | None = None, limit: int | None = None):
    """Get DocTypes for ERD selection, independent from DocType read permission."""
    ensure_erd_access()

    search_text = (search_text or "").strip()
    module = (module or "").strip()

    filters = [
        ["DocType", "is_virtual", "=", 0],
    ]
    if module:
        filters.append(["DocType", "module", "=", module])

    or_filters = None
    if search_text:
        like = f"%{search_text}%"
        or_filters = [["DocType", "name", "like", like]]

    limit_page_length = 0
    if limit is not None and str(limit).strip():
        parsed_limit = int(limit)
        limit_page_length = max(1, min(parsed_limit, 5000))

    return frappe.get_all(
        "DocType",
        fields=["name", "module"],
        filters=filters,
        or_filters=or_filters,
        limit_page_length=limit_page_length,
        order_by="module asc, name asc",
        ignore_permissions=True,
    )


@frappe.whitelist()
def get_meta_erd_schema_for_doctypes(doctypes: list):
    """Get ERD schema for a list of installed DocTypes."""
    ensure_erd_access()

    doctype_jsons = []
    for doctype in doctypes:
        doctype_jsons.append(frappe.get_meta(doctype))

    schema = get_schema_from_doctypes_json({
        'doctypes': doctype_jsons,
        'doctype_names': doctypes,
    })

    return schema


@frappe.whitelist()
def get_meta_for_doctype(doctype):
    """Get full metadata for a DocType."""
    ensure_erd_access()
    return frappe.get_meta(doctype)


@frappe.whitelist()
def export_markdown_schema_for_doctypes(doctypes: list, include_external_stubs: int | bool = 1):
    """Export selected DocTypes as a Markdown schema guide for SQL and LLM use."""
    ensure_erd_access()
    return build_markdown_schema_export(doctypes, _coerce_bool(include_external_stubs))


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no"}
    return bool(value)
