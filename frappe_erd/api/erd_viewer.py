import frappe
from frappe_erd.frappe_erd.code_analysis.schema_builder import get_schema_from_doctypes_json
from frappe_erd.permissions import ensure_erd_access


@frappe.whitelist()
def get_doctypes(search_text: str = "", limit: int = 100):
    """Get DocTypes for ERD selection, independent from DocType read permission."""
    ensure_erd_access()

    limit = int(limit or 100)
    limit = max(1, min(limit, 500))
    search_text = (search_text or "").strip()

    filters = [
        ["DocType", "issingle", "=", 0],
        ["DocType", "is_virtual", "=", 0],
    ]
    or_filters = None
    if search_text:
        like = f"%{search_text}%"
        or_filters = [["DocType", "name", "like", like], ["DocType", "module", "like", like]]

    return frappe.get_all(
        "DocType",
        fields=["name", "module"],
        filters=filters,
        or_filters=or_filters,
        limit_page_length=limit,
        order_by="module asc, name asc",
        ignore_permissions=True,
    )


@frappe.whitelist()
def get_meta_erd_schema_for_doctypes(doctypes: list):
    """Get ERD schema for a list of installed DocTypes."""
    ensure_erd_access()

    doctype_jsons = []
    for doctype in doctypes:
        doctype_jsons.append(frappe.get_cached_doc("DocType", doctype))

    schema = get_schema_from_doctypes_json({
        'doctypes': doctype_jsons,
        'doctype_names': doctypes,
    })

    return schema


@frappe.whitelist()
def get_meta_for_doctype(doctype):
    """Get full metadata for a DocType."""
    ensure_erd_access()
    return frappe.get_cached_doc("DocType", doctype)
