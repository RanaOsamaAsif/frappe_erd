from . import __version__ as app_version

app_name = "frappe_erd"
app_title = "frappe-erd"
app_publisher = "frappe-erd contributors"
app_description = "ERD Viewer for Frappe"
app_email = ""
app_license = "MIT"

website_route_rules = [
    {"from_route": "/frappe-erd", "to_route": "frappe_erd"},
    {"from_route": "/frappe-erd/<path:app_path>", "to_route": "frappe_erd"},
]

after_install = "frappe_erd.install.after_install"
