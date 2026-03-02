import frappe
from frappe_erd.frappe_erd.code_analysis.schema_builder import get_schema_from_doctypes_json


@frappe.whitelist()
def get_meta_erd_schema_for_doctypes(doctypes: list):
    """Get ERD schema for a list of installed DocTypes."""
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
    return frappe.get_meta(doctype)
