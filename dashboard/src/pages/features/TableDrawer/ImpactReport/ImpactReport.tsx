import { ErrorBanner } from "@/components/common/ErrorBanner/ErrorBanner"
import { FullPageLoader } from "@/components/common/FullPageLoader/FullPageLoader"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { cn, convertFrappeTimestampToReadableDate } from "@/lib/utils"
import {
    DoctypeImpactReport,
    ImpactChildTable,
    ImpactConfidence,
    ImpactCustomField,
    ImpactDocEventHook,
    ImpactLinkedRecord,
    ImpactPrintFormat,
    ImpactPropertySetter,
    ImpactReportRecord,
    ImpactRuntimeHook,
    ImpactServerScript,
    ImpactNotification,
    ImpactWebhook,
    ImpactWorkflow,
    ImpactClientScript,
} from "@/types/ImpactReport"
import { useFrappeGetCall } from "frappe-react-sdk"
import { Radar } from "lucide-react"
import { ReactNode, useMemo } from "react"

interface ImpactReportProps {
    doctype: string
    enabled: boolean
}

interface ImpactReportResponse {
    message: DoctypeImpactReport
}

interface ImpactSectionProps {
    title: string
    count: number
    confidence: ImpactConfidence
    emptyText: string
    children: ReactNode
}

interface ImpactTableColumn<T> {
    header: string
    cell: (row: T) => ReactNode
    className?: string
}

const confidenceBadgeClassName: Record<ImpactConfidence, string> = {
    high: "bg-emerald-50 text-emerald-700 border-emerald-200",
    medium: "bg-amber-50 text-amber-700 border-amber-200",
}

const ImpactSection = ({ title, count, confidence, emptyText, children }: ImpactSectionProps) => {
    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                    <CardTitle className="text-base">{title}</CardTitle>
                    <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-slate-200 text-slate-600">
                            {count} item{count === 1 ? "" : "s"}
                        </Badge>
                        <Badge variant="outline" className={cn("capitalize", confidenceBadgeClassName[confidence])}>
                            {confidence} confidence
                        </Badge>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {count === 0 ? (
                    <div className="rounded-md border border-dashed px-4 py-6 text-sm text-muted-foreground">
                        {emptyText}
                    </div>
                ) : children}
            </CardContent>
        </Card>
    )
}

const ImpactTable = <T,>({ rows, columns }: { rows: T[]; columns: ImpactTableColumn<T>[] }) => {
    return (
        <div className="rounded-md border">
            <Table>
                <TableHeader>
                    <TableRow>
                        {columns.map((column) => (
                            <TableHead key={column.header} className={column.className}>
                                {column.header}
                            </TableHead>
                        ))}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {rows.map((row, index) => (
                        <TableRow key={index}>
                            {columns.map((column) => (
                                <TableCell key={column.header} className={column.className}>
                                    {column.cell(row)}
                                </TableCell>
                            ))}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    )
}

const formatDate = (timestamp?: string) => {
    return timestamp ? convertFrappeTimestampToReadableDate(timestamp) : "—"
}

const formatBoolean = (value?: number | boolean | string) => {
    return value ? "Yes" : "No"
}

const renderCustomFieldBadge = (isCustomField?: boolean) => {
    if (!isCustomField) {
        return <Badge variant="outline">Standard</Badge>
    }

    return <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">Custom</Badge>
}

const renderMethods = (methods: string[]) => {
    if (!methods.length) {
        return "—"
    }
    return methods.join(", ")
}

const AutomationSection = <T extends { name: string }>({
    title,
    rows,
    columns,
}: {
    title: string
    rows: T[]
    columns: ImpactTableColumn<T>[]
}) => {
    if (!rows.length) {
        return null
    }

    return (
        <div className="space-y-2">
            <div className="text-sm font-medium text-slate-700">{title}</div>
            <ImpactTable rows={rows} columns={columns} />
        </div>
    )
}

export const ImpactReport = ({ doctype, enabled }: ImpactReportProps) => {
    const { data, error, isLoading } = useFrappeGetCall<ImpactReportResponse>(
        "frappe_erd.api.erd_viewer.get_doctype_impact_report",
        { doctype },
        enabled && doctype ? undefined : null,
        {
            revalidateOnFocus: false,
            revalidateIfStale: false,
        },
    )

    const report = data?.message

    const summaryCards = useMemo(() => {
        if (!report) {
            return []
        }

        return [
            { label: "Reverse Links", value: report.summary.reverse_links },
            { label: "Child Usage", value: report.summary.child_table_usage },
            { label: "Child Tables", value: report.summary.child_tables },
            { label: "Customizations", value: report.summary.customizations },
            { label: "Automation", value: report.summary.automation_and_reports },
            { label: "Hooks", value: report.summary.runtime_hooks },
        ]
    }, [report])

    if (!enabled) {
        return (
            <div className="rounded-md border border-dashed px-4 py-6 text-sm text-muted-foreground">
                Open this tab to load the impact report for <span className="font-medium text-slate-900">{doctype}</span>.
            </div>
        )
    }

    if (isLoading && !report) {
        return <FullPageLoader className="min-h-[240px]" />
    }

    if (error) {
        return <ErrorBanner error={error} />
    }

    if (!report) {
        return null
    }

    return (
        <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {summaryCards.map((card) => (
                    <Card key={card.label}>
                        <CardContent className="flex items-center justify-between p-4">
                            <div className="text-sm text-muted-foreground">{card.label}</div>
                            <div className="text-2xl font-semibold text-slate-900">{card.value}</div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <ImpactSection
                title="Reverse Links"
                count={report.reverse_links.length}
                confidence="high"
                emptyText={`No DocField or Custom Field records point to ${doctype}.`}
            >
                <ImpactTable<ImpactLinkedRecord>
                    rows={report.reverse_links}
                    columns={[
                        { header: "Source DocType", cell: (row) => row.source_doctype },
                        { header: "Field", cell: (row) => row.label || row.source_fieldname },
                        { header: "Type", cell: (row) => row.fieldtype },
                        { header: "Custom", cell: (row) => renderCustomFieldBadge(row.is_custom_field) },
                        { header: "Record", cell: (row) => row.source_record || "—" },
                    ]}
                />
            </ImpactSection>

            <ImpactSection
                title="Child Table Usage"
                count={report.child_table_usage.length}
                confidence="high"
                emptyText={`${doctype} is not attached as a child table in the current metadata scan.`}
            >
                <ImpactTable<ImpactLinkedRecord>
                    rows={report.child_table_usage}
                    columns={[
                        { header: "Parent DocType", cell: (row) => row.source_doctype },
                        { header: "Field", cell: (row) => row.label || row.source_fieldname },
                        { header: "Type", cell: (row) => row.fieldtype },
                        { header: "Custom", cell: (row) => renderCustomFieldBadge(row.is_custom_field) },
                        { header: "Record", cell: (row) => row.source_record || "—" },
                    ]}
                />
            </ImpactSection>

            <ImpactSection
                title="Child Tables"
                count={report.child_tables.length}
                confidence="high"
                emptyText={`${doctype} does not define any child table fields.`}
            >
                <ImpactTable<ImpactChildTable>
                    rows={report.child_tables}
                    columns={[
                        { header: "Child DocType", cell: (row) => row.child_doctype },
                        { header: "Field", cell: (row) => row.label || row.fieldname },
                        { header: "Custom", cell: (row) => renderCustomFieldBadge(row.is_custom_field) },
                    ]}
                />
            </ImpactSection>

            <ImpactSection
                title="Customizations"
                count={report.summary.customizations}
                confidence="high"
                emptyText={`No Custom Field or Property Setter records were found for ${doctype}.`}
            >
                <div className="space-y-4">
                    <AutomationSection<ImpactCustomField>
                        title="Custom Fields"
                        rows={report.customizations.custom_fields}
                        columns={[
                            { header: "Field", cell: (row) => row.label || row.fieldname || row.name },
                            { header: "Type", cell: (row) => row.fieldtype || "—" },
                            { header: "Options", cell: (row) => row.options || "—" },
                            { header: "Modified", cell: (row) => formatDate(row.modified) },
                        ]}
                    />
                    <AutomationSection<ImpactPropertySetter>
                        title="Property Setters"
                        rows={report.customizations.property_setters}
                        columns={[
                            { header: "Property", cell: (row) => row.property || "—" },
                            { header: "Applied On", cell: (row) => row.doctype_or_field || "—" },
                            { header: "Field", cell: (row) => row.field_name || "—" },
                            { header: "Value", cell: (row) => row.value || "—" },
                            { header: "Modified", cell: (row) => formatDate(row.modified) },
                        ]}
                    />
                </div>
            </ImpactSection>

            <ImpactSection
                title="Automation And Reports"
                count={report.summary.automation_and_reports}
                confidence="high"
                emptyText={`No workflows, scripts, webhooks, reports, or print formats reference ${doctype}.`}
            >
                <div className="space-y-4">
                    <AutomationSection<ImpactWorkflow>
                        title="Workflows"
                        rows={report.automation_and_reports.workflows}
                        columns={[
                            { header: "Name", cell: (row) => row.workflow_name || row.name },
                            { header: "Active", cell: (row) => formatBoolean(row.is_active) },
                            { header: "Modified", cell: (row) => formatDate(row.modified) },
                        ]}
                    />
                    <AutomationSection<ImpactNotification>
                        title="Notifications"
                        rows={report.automation_and_reports.notifications}
                        columns={[
                            { header: "Name", cell: (row) => row.name },
                            { header: "Event", cell: (row) => row.event || "—" },
                            { header: "Channel", cell: (row) => row.channel || "—" },
                            { header: "Enabled", cell: (row) => formatBoolean(row.enabled) },
                        ]}
                    />
                    <AutomationSection<ImpactWebhook>
                        title="Webhooks"
                        rows={report.automation_and_reports.webhooks}
                        columns={[
                            { header: "Name", cell: (row) => row.name },
                            { header: "Doc Event", cell: (row) => row.webhook_docevent || "—" },
                            { header: "Enabled", cell: (row) => formatBoolean(row.enabled) },
                            { header: "URL", cell: (row) => row.request_url || "—" },
                        ]}
                    />
                    <AutomationSection<ImpactClientScript>
                        title="Client Scripts"
                        rows={report.automation_and_reports.client_scripts}
                        columns={[
                            { header: "Name", cell: (row) => row.name },
                            { header: "View", cell: (row) => row.view || "—" },
                            { header: "Enabled", cell: (row) => formatBoolean(row.enabled) },
                            { header: "Modified", cell: (row) => formatDate(row.modified) },
                        ]}
                    />
                    <AutomationSection<ImpactServerScript>
                        title="Server Scripts"
                        rows={report.automation_and_reports.server_scripts}
                        columns={[
                            { header: "Name", cell: (row) => row.name },
                            { header: "Type", cell: (row) => row.script_type || "—" },
                            { header: "Doc Event", cell: (row) => row.doctype_event || "—" },
                            { header: "Disabled", cell: (row) => formatBoolean(row.disabled) },
                        ]}
                    />
                    <AutomationSection<ImpactReportRecord>
                        title="Reports"
                        rows={report.automation_and_reports.reports}
                        columns={[
                            { header: "Name", cell: (row) => row.report_name || row.name },
                            { header: "Type", cell: (row) => row.report_type || "—" },
                            { header: "Standard", cell: (row) => row.is_standard || "—" },
                            { header: "Disabled", cell: (row) => formatBoolean(row.disabled) },
                        ]}
                    />
                    <AutomationSection<ImpactPrintFormat>
                        title="Print Formats"
                        rows={report.automation_and_reports.print_formats}
                        columns={[
                            { header: "Name", cell: (row) => row.name },
                            { header: "Type", cell: (row) => row.print_format_type || "—" },
                            { header: "Standard", cell: (row) => row.standard || "—" },
                            { header: "Disabled", cell: (row) => formatBoolean(row.disabled) },
                        ]}
                    />
                </div>
            </ImpactSection>

            <ImpactSection
                title="Runtime Hooks"
                count={report.summary.runtime_hooks}
                confidence="high"
                emptyText={`No exact ${doctype} hook registrations were found in the installed apps.`}
            >
                <div className="space-y-4">
                    <AutomationSection<ImpactDocEventHook>
                        title="Doc Events"
                        rows={report.runtime_hooks.doc_events}
                        columns={[
                            { header: "App", cell: (row) => row.app_name },
                            { header: "Event", cell: (row) => row.event },
                            { header: "Methods", cell: (row) => renderMethods(row.methods) },
                        ]}
                    />
                    <AutomationSection<ImpactRuntimeHook>
                        title="override_doctype_class"
                        rows={report.runtime_hooks.override_doctype_class}
                        columns={[
                            { header: "App", cell: (row) => row.app_name },
                            { header: "Methods", cell: (row) => renderMethods(row.methods) },
                        ]}
                    />
                    <AutomationSection<ImpactRuntimeHook>
                        title="permission_query_conditions"
                        rows={report.runtime_hooks.permission_query_conditions}
                        columns={[
                            { header: "App", cell: (row) => row.app_name },
                            { header: "Methods", cell: (row) => renderMethods(row.methods) },
                        ]}
                    />
                    <AutomationSection<ImpactRuntimeHook>
                        title="has_permission"
                        rows={report.runtime_hooks.has_permission}
                        columns={[
                            { header: "App", cell: (row) => row.app_name },
                            { header: "Methods", cell: (row) => renderMethods(row.methods) },
                        ]}
                    />
                </div>
            </ImpactSection>

            <Alert>
                <Radar className="h-4 w-4" />
                <AlertTitle>Scope notes</AlertTitle>
                <AlertDescription>
                    This v1 report excludes wildcard hooks, Dynamic Link inference, and layout-only fields like section or column breaks so the results stay high-signal and site-specific.
                </AlertDescription>
            </Alert>
        </div>
    )
}
