export type ImpactConfidence = "high" | "medium"

export interface ImpactLinkedRecord {
    source_doctype: string
    source_fieldname: string
    label: string
    fieldtype: string
    is_custom_field: boolean
    source_record: string
    confidence: ImpactConfidence
}

export interface ImpactChildTable {
    child_doctype: string
    fieldname: string
    label: string
    is_custom_field: boolean
    confidence: ImpactConfidence
}

export interface ImpactCustomField {
    name: string
    fieldname?: string
    label?: string
    fieldtype?: string
    options?: string
    module?: string
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactPropertySetter {
    name: string
    doctype_or_field?: string
    field_name?: string
    property?: string
    property_type?: string
    value?: string
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactWorkflow {
    name: string
    workflow_name?: string
    is_active?: 0 | 1
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactNotification {
    name: string
    subject?: string
    event?: string
    enabled?: 0 | 1
    channel?: string
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactWebhook {
    name: string
    webhook_docevent?: string
    request_url?: string
    enabled?: 0 | 1
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactClientScript {
    name: string
    view?: string
    enabled?: 0 | 1
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactServerScript {
    name: string
    script_type?: string
    doctype_event?: string
    disabled?: 0 | 1
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactReportRecord {
    name: string
    report_name?: string
    report_type?: string
    is_standard?: "No" | "Yes"
    disabled?: 0 | 1
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactPrintFormat {
    name: string
    standard?: "No" | "Yes"
    custom_format?: 0 | 1
    disabled?: 0 | 1
    print_format_type?: string
    modified?: string
    confidence: ImpactConfidence
}

export interface ImpactRuntimeHook {
    app_name: string
    methods: string[]
    confidence: ImpactConfidence
}

export interface ImpactDocEventHook extends ImpactRuntimeHook {
    event: string
}

export interface ImpactSummary {
    reverse_links: number
    child_table_usage: number
    child_tables: number
    custom_fields: number
    property_setters: number
    customizations: number
    workflows: number
    notifications: number
    webhooks: number
    client_scripts: number
    server_scripts: number
    reports: number
    print_formats: number
    automation_and_reports: number
    doc_events_hooks: number
    override_doctype_class_hooks: number
    permission_query_conditions_hooks: number
    has_permission_hooks: number
    runtime_hooks: number
}

export interface DoctypeImpactReport {
    doctype: string
    summary: ImpactSummary
    reverse_links: ImpactLinkedRecord[]
    child_table_usage: ImpactLinkedRecord[]
    child_tables: ImpactChildTable[]
    customizations: {
        custom_fields: ImpactCustomField[]
        property_setters: ImpactPropertySetter[]
    }
    automation_and_reports: {
        workflows: ImpactWorkflow[]
        notifications: ImpactNotification[]
        webhooks: ImpactWebhook[]
        client_scripts: ImpactClientScript[]
        server_scripts: ImpactServerScript[]
        reports: ImpactReportRecord[]
        print_formats: ImpactPrintFormat[]
    }
    runtime_hooks: {
        doc_events: ImpactDocEventHook[]
        override_doctype_class: ImpactRuntimeHook[]
        permission_query_conditions: ImpactRuntimeHook[]
        has_permission: ImpactRuntimeHook[]
    }
}
