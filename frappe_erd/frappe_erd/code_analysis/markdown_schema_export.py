from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime


DISALLOWED_FIELD_TYPES = {
    "Section Break",
    "Tab Break",
    "Fold",
    "Column Break",
    "Heading",
    "HTML",
    "Image",
    "Icon",
    "Button",
}
RELATION_FIELD_TYPES = {"Link", "Table", "Table MultiSelect"}
COMMON_SYSTEM_FIELDNAMES = {"name", "creation", "modified", "modified_by", "owner", "docstatus"}
CHILD_TABLE_SYSTEM_FIELDNAMES = {"parent", "parenttype", "parentfield", "idx"}


def build_markdown_schema_export(doctypes: list[str], include_external_stubs: bool = True) -> dict[str, str]:
    selected_doctypes = _normalize_doctypes(doctypes)
    if not selected_doctypes:
        frappe.throw(_("Select at least one DocType to export."), frappe.ValidationError)

    missing_doctypes = [doctype for doctype in selected_doctypes if not frappe.db.exists("DocType", doctype)]
    if missing_doctypes:
        frappe.throw(
            _("Unknown DocType(s): {0}").format(", ".join(missing_doctypes)),
            frappe.ValidationError,
        )

    selected_doctype_set = set(selected_doctypes)
    doctypes_context = []
    relationships = []
    inbound_relationships_by_target = defaultdict(list)
    external_stubs_by_doctype = defaultdict(list)
    modules = set()
    storage_table_count = 0

    for doctype in selected_doctypes:
        meta = frappe.get_meta(doctype)
        doctype_context = _build_doctype_context(meta, selected_doctype_set)
        doctypes_context.append(doctype_context)

        if doctype_context["module"]:
            modules.add(doctype_context["module"])
        if not doctype_context["issingle"]:
            storage_table_count += 1

        for relationship in doctype_context["outbound_relationships"]:
            relationships.append(relationship)
            target_doctype = relationship.get("target_doctype")
            if target_doctype and relationship.get("target_selected"):
                inbound_relationships_by_target[target_doctype].append(relationship)
            elif (
                include_external_stubs
                and target_doctype
                and relationship["relationship_type"] != "dynamic"
            ):
                external_stubs_by_doctype[target_doctype].append(relationship)

    for doctype_context in doctypes_context:
        doctype_name = doctype_context["name"]
        doctype_context["inbound_relationships"] = sorted(
            [
                relationship
                for relationship in inbound_relationships_by_target.get(doctype_name, [])
                if not (
                    relationship.get("source_doctype") == doctype_name
                    and relationship.get("target_doctype") == doctype_name
                )
            ],
            key=_relationship_sort_key,
        )
        doctype_context["external_relationships"] = sorted(
            [
                relationship
                for relationship in doctype_context["outbound_relationships"]
                if relationship.get("target_doctype")
                and not relationship.get("target_selected")
                and relationship["relationship_type"] != "dynamic"
            ],
            key=_relationship_sort_key,
        )

    external_stubs = []
    if include_external_stubs:
        external_stubs = [
            {
                "name": doctype_name,
                "references": sorted(references, key=_relationship_sort_key),
            }
            for doctype_name, references in sorted(external_stubs_by_doctype.items())
        ]

    generated_at = now_datetime()
    context = {
        "generated_at": generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "selected_doctypes": selected_doctypes,
        "doctypes": doctypes_context,
        "modules": sorted(modules),
        "doctype_count": len(doctypes_context),
        "storage_table_count": storage_table_count,
        "relationship_count": len(relationships),
        "internal_relationship_count": sum(1 for relationship in relationships if relationship.get("target_selected")),
        "external_relationship_count": sum(1 for relationship in relationships if relationship.get("target_doctype") and not relationship.get("target_selected")),
        "external_stubs": external_stubs,
    }

    filename = f"erd-schema-{generated_at.strftime('%Y-%m-%d')}.md"
    return {
        "filename": filename,
        "markdown": render_markdown_schema_export(context),
    }


def render_markdown_schema_export(context: dict[str, Any]) -> str:
    lines: list[str] = [
        "# ERD Schema Export",
        "",
        f"- Generated at: `{context['generated_at']}`",
        f"- Selected DocTypes: {_render_code_list(context['selected_doctypes'])}",
        f"- Modules: {_render_code_list(context['modules']) if context['modules'] else '_None_'}",
        f"- Selected DocType count: `{context['doctype_count']}`",
        f"- Selected storage table count: `{context['storage_table_count']}`",
        f"- Relationships from selected DocTypes: `{context['relationship_count']}`",
        "",
        "This file is intended to help humans and LLMs write SQL for the selected Frappe DocTypes.",
        "",
        "## LLM Quick Context",
        "",
        "### Query Rules",
        "",
        "- Normal DocTypes map to SQL tables named `tab<DocType>`.",
        "- Single DocTypes store values in `tabSingles`, not in `tab<DocType>`.",
        "- Child tables join with `child.parent = parent.name` and usually require `child.parenttype = '<Parent DocType>'`.",
        "- Prefer `Link`, `Table`, and `Table MultiSelect` relationships over string matching when filtering or joining.",
        "- Field tables below omit repeated system columns; refer to the note above each field table for storage details.",
        "",
        "### Selected DocTypes At A Glance",
        "",
        "| DocType | Module | Storage | Flags | Relationship summary |",
        "| --- | --- | --- | --- | --- |",
    ]

    for doctype in context["doctypes"]:
        lines.append(
            "| {name} | {module} | {storage} | {flags} | {relationships} |".format(
                name=_escape_markdown_table_cell(doctype["name"]),
                module=_escape_markdown_table_cell(doctype["module"] or "-"),
                storage=_escape_markdown_table_cell(doctype["storage_table"]),
                flags=_escape_markdown_table_cell(_format_flags(doctype)),
                relationships=_escape_markdown_table_cell(_format_relationship_counts(doctype)),
            )
        )

    lines.extend(
        [
            "",
            "### Relationship Summary",
            "",
        ]
    )

    relationship_lines = _render_relationship_summary(context["doctypes"])
    if relationship_lines:
        lines.extend(relationship_lines)
    else:
        lines.append("- No relationships found between the selected DocTypes.")

    for doctype in context["doctypes"]:
        lines.extend(
            [
                "",
                f"## DocType: `{doctype['name']}`",
                "",
                f"- Module: `{doctype['module'] or '-'}`",
                f"- Storage: `{doctype['storage_table']}`",
                f"- Flags: {_format_flags(doctype)}",
            ]
        )

        if doctype["description"]:
            lines.append(f"- Description: {_escape_markdown_inline(doctype['description'])}")
        if doctype["autoname"]:
            lines.append(f"- Autoname: `{doctype['autoname']}`")
        if doctype["title_field"]:
            lines.append(f"- Title field: `{doctype['title_field']}`")
        if doctype["search_fields"]:
            lines.append(f"- Search fields: `{doctype['search_fields']}`")

        lines.extend(
            [
                "",
                "### Relationships",
                "",
            ]
        )
        lines.extend(_render_doctype_relationships(doctype))
        lines.extend(
            [
                "",
                "### Fields",
                "",
                _get_field_table_note(doctype),
                "",
                "| fieldname | label | fieldtype | options/target | reqd | unique | search_index | hidden | read_only | default | fetch_from | is_custom_field | description |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )

        for field in _get_display_fields(doctype):
            lines.append(
                "| {fieldname} | {label} | {fieldtype} | {options_target} | {reqd} | {unique} | {search_index} | {hidden} | {read_only} | {default} | {fetch_from} | {is_custom_field} | {description} |".format(
                    fieldname=_escape_markdown_table_cell(field["fieldname"]),
                    label=_escape_markdown_table_cell(field["label"]),
                    fieldtype=_escape_markdown_table_cell(field["fieldtype"]),
                    options_target=_escape_markdown_table_cell(field["options_target"]),
                    reqd=_escape_markdown_table_cell(_format_bool(field["reqd"])),
                    unique=_escape_markdown_table_cell(_format_bool(field["unique"])),
                    search_index=_escape_markdown_table_cell(_format_bool(field["search_index"])),
                    hidden=_escape_markdown_table_cell(_format_bool(field["hidden"])),
                    read_only=_escape_markdown_table_cell(_format_bool(field["read_only"])),
                    default=_escape_markdown_table_cell(field["default"]),
                    fetch_from=_escape_markdown_table_cell(field["fetch_from"]),
                    is_custom_field=_escape_markdown_table_cell(_format_bool(field["is_custom_field"])),
                    description=_escape_markdown_table_cell(field["description"]),
                )
            )

    if context["external_stubs"]:
        lines.extend(
            [
                "",
                "## External Linked DocTypes",
                "",
            ]
        )
        for stub in context["external_stubs"]:
            lines.extend(
                [
                    f"### `{stub['name']}`",
                    "",
                    "Referenced by:",
                ]
            )
            for reference in stub["references"]:
                lines.append(
                    "- `{source}.{field}` ({fieldtype}) from `{doctype}`. {join_note}".format(
                        source=reference["source_doctype"],
                        field=reference["source_fieldname"],
                        fieldtype=reference["fieldtype"],
                        doctype=reference["source_doctype"],
                        join_note=reference["canonical_join"],
                    )
                )
            lines.append("")

        if lines[-1] == "":
            lines.pop()

    return "\n".join(lines).strip() + "\n"


def _build_doctype_context(meta: Any, selected_doctype_set: set[str]) -> dict[str, Any]:
    doctype_name = _get_value(meta, "name")
    issingle = bool(_get_value(meta, "issingle"))
    istable = bool(_get_value(meta, "istable"))
    module = _get_value(meta, "module", "")

    fields = _build_system_fields(doctype_name, issingle=issingle, istable=istable)
    outbound_relationships = []

    for field in _get_value(meta, "fields", []) or []:
        fieldtype = _get_value(field, "fieldtype")
        if fieldtype in DISALLOWED_FIELD_TYPES:
            continue

        field_context = _build_field_context(field)
        fields.append(field_context)

        if fieldtype in RELATION_FIELD_TYPES and field_context["options_target"]:
            target_doctype = field_context["options_target"]
            outbound_relationships.append(
                _build_relationship(
                    source_doctype=doctype_name,
                    source_issingle=issingle,
                    source_field=field_context,
                    relationship_type=_relationship_type_for_field(fieldtype),
                    target_doctype=target_doctype,
                    target_selected=target_doctype in selected_doctype_set,
                    target_issingle=_doctype_is_single(target_doctype),
                )
            )
        elif fieldtype == "Dynamic Link":
            outbound_relationships.append(
                _build_relationship(
                    source_doctype=doctype_name,
                    source_issingle=issingle,
                    source_field=field_context,
                    relationship_type="dynamic",
                    target_doctype="",
                    target_selected=False,
                    dynamic_target_field=_get_value(field, "options", ""),
                )
            )

    return {
        "name": doctype_name,
        "module": module,
        "istable": istable,
        "issingle": issingle,
        "is_submittable": bool(_get_value(meta, "is_submittable")),
        "is_tree": bool(_get_value(meta, "is_tree")),
        "storage_table": "tabSingles" if issingle else f"tab{doctype_name}",
        "description": _sanitize_inline_text(_get_value(meta, "description", "")),
        "autoname": _sanitize_inline_text(_get_value(meta, "autoname", "")),
        "title_field": _sanitize_inline_text(_get_value(meta, "title_field", "")),
        "search_fields": _sanitize_inline_text(_get_value(meta, "search_fields", "")),
        "fields": fields,
        "outbound_relationships": sorted(outbound_relationships, key=_relationship_sort_key),
    }


def _build_system_fields(doctype_name: str, issingle: bool, istable: bool) -> list[dict[str, Any]]:
    if issingle:
        return []

    fields = [
        _build_system_field(
            fieldname="name",
            label="Document ID",
            fieldtype="Data",
            options_target="PRIMARY KEY",
            reqd=1,
            unique=1,
            read_only=1,
            description="System column used as the primary key for the document.",
        ),
        _build_system_field(
            fieldname="creation",
            label="Created On",
            fieldtype="Datetime",
            read_only=1,
            description="System column storing when the row was created.",
        ),
        _build_system_field(
            fieldname="modified",
            label="Modified On",
            fieldtype="Datetime",
            read_only=1,
            description="System column storing when the row was last updated.",
        ),
        _build_system_field(
            fieldname="modified_by",
            label="Modified By",
            fieldtype="Link",
            options_target="User",
            read_only=1,
            description="System column storing the user who last updated the row.",
        ),
        _build_system_field(
            fieldname="owner",
            label="Owner",
            fieldtype="Link",
            options_target="User",
            read_only=1,
            description="System column storing the user who created the row.",
        ),
        _build_system_field(
            fieldname="docstatus",
            label="DocStatus",
            fieldtype="Int",
            default="0",
            read_only=1,
            description="System column with workflow state: 0 draft, 1 submitted, 2 cancelled.",
        ),
    ]

    if istable:
        fields.extend(
            [
                _build_system_field(
                    fieldname="parent",
                    label="Parent",
                    fieldtype="Link",
                    options_target="Parent document name",
                    reqd=1,
                    read_only=1,
                    description="System column used to join child rows back to the parent document name.",
                ),
                _build_system_field(
                    fieldname="parenttype",
                    label="Parent DocType",
                    fieldtype="Data",
                    reqd=1,
                    read_only=1,
                    description="System column storing the parent DocType name for the child row.",
                ),
                _build_system_field(
                    fieldname="parentfield",
                    label="Parent Field",
                    fieldtype="Data",
                    read_only=1,
                    description="System column storing the table field on the parent DocType.",
                ),
                _build_system_field(
                    fieldname="idx",
                    label="Row Order",
                    fieldtype="Int",
                    default="0",
                    read_only=1,
                    description="System column storing the row order inside the parent document.",
                ),
            ]
        )

    return fields


def _build_system_field(**field: Any) -> dict[str, Any]:
    return {
        "fieldname": field.get("fieldname", ""),
        "label": field.get("label", ""),
        "fieldtype": field.get("fieldtype", ""),
        "options_target": field.get("options_target", ""),
        "reqd": field.get("reqd", 0),
        "unique": field.get("unique", 0),
        "search_index": field.get("search_index", 0),
        "hidden": field.get("hidden", 0),
        "read_only": field.get("read_only", 0),
        "default": field.get("default", ""),
        "fetch_from": field.get("fetch_from", ""),
        "is_custom_field": 0,
        "description": _sanitize_inline_text(field.get("description", "")),
    }


def _build_field_context(field: Any) -> dict[str, Any]:
    fieldtype = _get_value(field, "fieldtype", "")
    options = _get_value(field, "options", "")
    options_target = _sanitize_options(fieldtype, options)

    if fieldtype == "Dynamic Link" and options:
        options_target = f"DocType from field `{options}`"

    return {
        "fieldname": _sanitize_inline_text(_get_value(field, "fieldname", "")),
        "label": _sanitize_inline_text(_get_value(field, "label", _get_value(field, "fieldname", ""))),
        "fieldtype": _sanitize_inline_text(fieldtype),
        "options_target": options_target,
        "reqd": _get_value(field, "reqd", 0),
        "unique": _get_value(field, "unique", 0),
        "search_index": _get_value(field, "search_index", 0),
        "hidden": _get_value(field, "hidden", 0),
        "read_only": _get_value(field, "read_only", 0),
        "default": _sanitize_inline_text(_get_value(field, "default", "")),
        "fetch_from": _sanitize_inline_text(_get_value(field, "fetch_from", "")),
        "is_custom_field": _get_value(field, "is_custom_field", 0),
        "description": _sanitize_inline_text(_get_value(field, "description", "")),
    }


def _build_relationship(
    source_doctype: str,
    source_issingle: bool,
    source_field: dict[str, Any],
    relationship_type: str,
    target_doctype: str,
    target_selected: bool,
    target_issingle: bool = False,
    dynamic_target_field: str = "",
) -> dict[str, Any]:
    fieldtype = source_field["fieldtype"]
    fieldname = source_field["fieldname"]

    if relationship_type == "child_table":
        canonical_join = (
            f"Canonical SQL join: `tab{target_doctype}`.`parent` = `tab{source_doctype}`.`name` "
            f"and `tab{target_doctype}`.`parenttype` = '{source_doctype}'."
        )
        if source_issingle:
            canonical_join = (
                f"Child rows live in `tab{target_doctype}` and usually filter on "
                f"`parenttype = '{source_doctype}'`; the parent is a Single DocType stored in `tabSingles`."
            )
    elif relationship_type == "dynamic":
        canonical_join = (
            f"Dynamic target DocType is stored in `{dynamic_target_field}`; the linked record name is in `{fieldname}`."
        )
    else:
        canonical_join = (
            f"Canonical SQL join: `tab{source_doctype}`.`{fieldname}` = `tab{target_doctype}`.`name`."
        )
        if source_issingle:
            canonical_join = (
                f"Source DocType is Single, so `{fieldname}` is stored in `tabSingles` where "
                f"`doctype = '{source_doctype}'` and `field = '{fieldname}'`."
            )
        elif target_issingle:
            canonical_join = (
                f"Target DocType `{target_doctype}` is Single and stored in `tabSingles`; "
                f"the link value usually matches the Single DocType name."
            )

    return {
        "source_doctype": source_doctype,
        "source_fieldname": fieldname,
        "fieldtype": fieldtype,
        "relationship_type": relationship_type,
        "target_doctype": target_doctype,
        "target_selected": target_selected,
        "canonical_join": canonical_join,
        "dynamic_target_field": dynamic_target_field,
        "is_self_reference": source_doctype == target_doctype if target_doctype else False,
    }


def _render_relationship_summary(doctypes: list[dict[str, Any]]) -> list[str]:
    lines = []

    for doctype in doctypes:
        for relationship in doctype["outbound_relationships"]:
            if relationship["relationship_type"] == "dynamic":
                lines.append(
                    "- `{source}.{field}` is a `Dynamic Link`. {join_note}".format(
                        source=relationship["source_doctype"],
                        field=relationship["source_fieldname"],
                        join_note=relationship["canonical_join"],
                    )
                )
                continue

            target_scope = "selected" if relationship.get("target_selected") else "external"
            lines.append(
                "- `{source}.{field}` ({fieldtype} -> {target}) [{scope}] {join_note}".format(
                    source=relationship["source_doctype"],
                    field=relationship["source_fieldname"],
                    fieldtype=relationship["fieldtype"],
                    target=relationship["target_doctype"],
                    scope=target_scope,
                    join_note=relationship["canonical_join"],
                )
            )

    return lines


def _render_doctype_relationships(doctype: dict[str, Any]) -> list[str]:
    link_relationships = [
        relationship
        for relationship in doctype["outbound_relationships"]
        if relationship["relationship_type"] == "link" and relationship.get("target_selected")
    ]
    child_relationships = [
        relationship
        for relationship in doctype["outbound_relationships"]
        if relationship["relationship_type"] == "child_table"
    ]
    dynamic_relationships = [
        relationship
        for relationship in doctype["outbound_relationships"]
        if relationship["relationship_type"] == "dynamic"
    ]
    inbound_relationships = doctype["inbound_relationships"]
    external_relationships = doctype["external_relationships"]

    if not any([link_relationships, child_relationships, dynamic_relationships, inbound_relationships, external_relationships]):
        return ["- No query-relevant relationships found for this DocType."]

    lines = []

    if link_relationships:
        lines.append("- Outbound links:")
        for relationship in link_relationships:
            lines.append(f"  - {_format_compact_relationship_line(relationship)}")

    if child_relationships:
        lines.append("- Child tables:")
        for relationship in child_relationships:
            lines.append(f"  - {_format_compact_relationship_line(relationship)}")

    if dynamic_relationships:
        lines.append("- Dynamic links:")
        for relationship in dynamic_relationships:
            lines.append(f"  - {_format_compact_relationship_line(relationship)}")

    if inbound_relationships:
        lines.append("- Inbound references (within selected scope):")
        for relationship in inbound_relationships:
            lines.append(f"  - {_format_compact_relationship_line(relationship, current_doctype=doctype['name'])}")

    if external_relationships:
        lines.append("- External references:")
        for relationship in external_relationships:
            lines.append(f"  - {_format_compact_relationship_line(relationship)}")

    return lines


def _format_relationship_counts(doctype: dict[str, Any]) -> str:
    outbound = len(doctype["outbound_relationships"])
    inbound = len(doctype["inbound_relationships"])
    external = len(doctype["external_relationships"])
    return f"outbound {outbound}, inbound {inbound} (selected scope), external {external}"


def _format_flags(doctype: dict[str, Any]) -> str:
    flags = []
    if doctype["issingle"]:
        flags.append("Single")
    if doctype["istable"]:
        flags.append("Child Table")
    if doctype["is_submittable"]:
        flags.append("Submittable")
    if doctype["is_tree"]:
        flags.append("Tree")

    return ", ".join(flags) if flags else "Standard"


def _format_bool(value: Any) -> str:
    return "Yes" if bool(value) else ""


def _relationship_sort_key(relationship: dict[str, Any]) -> tuple[str, str, str]:
    return (
        relationship.get("source_doctype", ""),
        relationship.get("source_fieldname", ""),
        relationship.get("target_doctype", ""),
    )


def _relationship_type_for_field(fieldtype: str) -> str:
    if fieldtype in {"Table", "Table MultiSelect"}:
        return "child_table"
    return "link"


def _get_display_fields(doctype: dict[str, Any]) -> list[dict[str, Any]]:
    hidden_fieldnames = set(COMMON_SYSTEM_FIELDNAMES)
    if doctype["istable"]:
        hidden_fieldnames.update(CHILD_TABLE_SYSTEM_FIELDNAMES)
    return [field for field in doctype["fields"] if field["fieldname"] not in hidden_fieldnames]


def _get_field_table_note(doctype: dict[str, Any]) -> str:
    if doctype["issingle"]:
        return (
            "> Fields for this Single DocType are stored as rows in `tabSingles`, keyed by "
            "`doctype`, `field`, and `value`. Repeated system columns are omitted below."
        )

    common_fields = "`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`"
    if doctype["istable"]:
        child_fields = "`parent`, `parenttype`, `parentfield`, `idx`"
        return f"> Repeated system columns are omitted below: {common_fields}, {child_fields}."

    return f"> Repeated system columns are omitted below: {common_fields}."


def _format_compact_relationship_line(relationship: dict[str, Any], current_doctype: str | None = None) -> str:
    if relationship["relationship_type"] == "dynamic":
        dynamic_target_field = relationship.get("dynamic_target_field") or "another field"
        return (
            f"`{relationship['source_fieldname']}` -> dynamic "
            f"(resolved at runtime via `{dynamic_target_field}`)"
        )

    if current_doctype and relationship["target_doctype"] == current_doctype:
        base = f"`{relationship['source_doctype']}.{relationship['source_fieldname']}` -> `{current_doctype}`"
    else:
        base = f"`{relationship['source_fieldname']}` -> `{relationship['target_doctype']}`"

    if not relationship.get("target_selected"):
        base = f"{base} [external]"

    return base


def _normalize_doctypes(doctypes: Any) -> list[str]:
    parsed_doctypes = doctypes
    if isinstance(doctypes, str):
        parsed_doctypes = frappe.parse_json(doctypes)

    if not isinstance(parsed_doctypes, list):
        return []

    normalized = []
    seen = set()
    for doctype in parsed_doctypes:
        if not isinstance(doctype, str):
            continue

        value = doctype.strip()
        if not value or value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return normalized


def _sanitize_options(fieldtype: str, options: str) -> str:
    value = _sanitize_inline_text(options)
    if not value:
        return ""

    if fieldtype == "Select":
        return " / ".join(part.strip() for part in value.splitlines() if part.strip())

    return value


def _sanitize_inline_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def _escape_markdown_table_cell(value: Any) -> str:
    text = _sanitize_inline_text(value)
    if not text:
        return ""
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("`", "\\`").replace("\n", "<br>")


def _render_code_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def _escape_markdown_inline(value: Any) -> str:
    text = _sanitize_inline_text(value)
    if not text:
        return ""
    return text.replace("`", "\\`").replace("\n", " ")


def _get_value(item: Any, key: str, default: Any = None) -> Any:
    if item is None:
        return default

    if isinstance(item, dict):
        return item.get(key, default)

    getter = getattr(item, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            pass

    return getattr(item, key, default)


def _doctype_is_single(doctype: str) -> bool:
    if not doctype:
        return False
    return bool(frappe.db.get_value("DocType", doctype, "issingle"))
