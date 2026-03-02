import frappe


def after_install():
    ensure_erd_role()


def ensure_erd_role():
    if frappe.db.exists("Role", "ERD Viewer"):
        return

    role = frappe.new_doc("Role")
    role.role_name = "ERD Viewer"
    role.desk_access = 1
    role.insert(ignore_permissions=True)
