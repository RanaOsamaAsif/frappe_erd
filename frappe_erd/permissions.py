import frappe

ERD_ALLOWED_ROLES = {"ERD Viewer", "System Manager"}


def has_erd_access(user: str | None = None) -> bool:
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    return bool(set(frappe.get_roles(user)).intersection(ERD_ALLOWED_ROLES))


def ensure_erd_access():
    if has_erd_access():
        return
    frappe.throw("You are not permitted to access ERD Viewer.", frappe.PermissionError)
