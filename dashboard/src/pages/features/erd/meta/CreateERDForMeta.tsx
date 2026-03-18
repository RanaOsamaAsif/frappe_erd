import { Header } from "@/components/common/Header"
import { Button } from "@/components/ui/button"
import { Dialog, Transition } from "@headlessui/react"
import { Fragment, useEffect, useMemo, useRef, useState } from "react"
import { ErrorBanner } from "@/components/common/ErrorBanner/ErrorBanner"
import { FullPageLoader } from "@/components/common/FullPageLoader/FullPageLoader"
import { Input } from "@/components/ui/input"
import { useFrappeGetCall } from "frappe-react-sdk"
import { DocType } from "@/types/Core/DocType"
import { Checkbox } from "@/components/ui/checkbox"
import { useDebounce } from "@/hooks/useDebounce"
import { ERDForMetaDoctypes } from "./ERDForMetaDoctype"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { DoctypeListPopoverForMeta } from "./ERDDoctypeAndAppModal"
import { toPng } from "html-to-image"
import { Check, ChevronsUpDown, Download, X } from "lucide-react"
import { Command, CommandEmpty, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { cn } from "@/lib/utils"

const ERD_META_DOCTYPES_STORAGE_KEY = "ERDMetaDoctypes"
const ERD_META_SELECTED_MODULE_STORAGE_KEY = "ERDMetaSelectedModule"

const CreateERD = () => {
    const [open, setOpen] = useState(true)
    const [erdDoctypes, setERDDocTypes] = useState<string[]>([])

    useEffect(() => {
        const doctypes = JSON.parse(window.sessionStorage.getItem(ERD_META_DOCTYPES_STORAGE_KEY) ?? "[]")
        if (doctypes.length) {
            setERDDocTypes(doctypes)
            setOpen(false)
        }
    }, [])

    const flowRef = useRef(null)

    return (
        <div className="h-screen">
            <Header text="ERD Viewer" />
            <div className="border-r border-gray-200">
                <div className="fixed bottom-4 left-[50%] z-40 flex -translate-x-[50%] flex-row gap-2" hidden={open}>
                    <Button onClick={() => setOpen(!open)} className="w-max sm:w-max">
                        Select DocTypes ({erdDoctypes.length})
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => {
                            if (flowRef.current === null) return
                            toPng(flowRef.current, {
                                filter: (node) => !(
                                    node?.classList?.contains("react-flow__minimap") ||
                                    node?.classList?.contains("react-flow__controls")
                                ),
                            }).then((dataUrl) => {
                                const anchor = document.createElement("a")
                                anchor.setAttribute("download", "erd.png")
                                anchor.setAttribute("href", dataUrl)
                                anchor.click()
                            })
                        }}
                    >
                        <div className="flex items-center gap-2">
                            <Download size={14} /> Download
                        </div>
                    </Button>
                </div>

                <ModuleDoctypeListDrawer open={open} setOpen={setOpen} erdDoctypes={erdDoctypes} setERDDocTypes={setERDDocTypes} />

                <div className="flex h-[93vh]">
                    {erdDoctypes && <ERDForMetaDoctypes doctypes={erdDoctypes} setDocTypes={setERDDocTypes} flowRef={flowRef} />}
                </div>
            </div>
        </div>
    )
}

export interface ModuleDoctypeListDrawerProps {
    open: boolean
    setOpen: (open: boolean) => void
    erdDoctypes: string[]
    setERDDocTypes: React.Dispatch<React.SetStateAction<string[]>>
}

export const ModuleDoctypeListDrawer = ({ open, setOpen, erdDoctypes, setERDDocTypes }: ModuleDoctypeListDrawerProps) => {
    const [doctype, setDocType] = useState<string[]>(erdDoctypes)

    const onGenerateERD = () => {
        setERDDocTypes(doctype)
        window.sessionStorage.setItem(ERD_META_DOCTYPES_STORAGE_KEY, JSON.stringify(doctype))
        setOpen(false)
    }

    useEffect(() => {
        setDocType(erdDoctypes)
    }, [erdDoctypes])

    return (
        <Transition.Root show={open} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={setOpen}>
                <div className="fixed inset-0" />
                <div className="fixed inset-0 overflow-hidden">
                    <div className="absolute inset-0 overflow-hidden">
                        <div className="pointer-events-none fixed inset-y-0 left-0 flex max-w-full pr-10">
                            <Transition.Child
                                as={Fragment}
                                enter="transform transition ease-in-out duration-500 sm:duration-700"
                                enterFrom="translate-x-[-100%]"
                                enterTo="translate-x-[0]"
                                leave="transform transition ease-in-out duration-500 sm:duration-700"
                                leaveFrom="translate-x-0"
                                leaveTo="translate-x-[-100%]"
                            >
                                <Dialog.Panel className="pointer-events-auto h-full w-[480px]">
                                    <div className="flex h-full min-h-0 flex-col bg-white pt-6 shadow-xl">
                                        <div className="px-4 sm:px-6">
                                            <div className="flex items-start justify-between">
                                                <Dialog.Title className="flex items-center space-x-2">
                                                    <div className="text-base font-semibold leading-6 text-gray-900">
                                                        Select DocTypes
                                                    </div>
                                                </Dialog.Title>
                                                <div className="ml-3 flex h-7 items-center">
                                                    <button
                                                        type="button"
                                                        className="relative rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none"
                                                        onClick={() => setOpen(false)}
                                                    >
                                                        <span className="absolute -inset-2.5" />
                                                        <span className="sr-only">Close panel</span>
                                                        <X className="h-4 w-4" aria-hidden="true" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="relative mt-6 flex-1 min-h-0 px-4 sm:px-6">
                                            <ModuleList doctype={doctype} setDocType={setDocType} open={open} />
                                        </div>
                                        <div className="sticky bottom-0 flex items-center justify-end border-t bg-white p-4 text-3xl">
                                            <Button onClick={onGenerateERD} size="sm" className="bg-blue-500">
                                                Generate ERD
                                            </Button>
                                        </div>
                                    </div>
                                </Dialog.Panel>
                            </Transition.Child>
                        </div>
                    </div>
                </div>
            </Dialog>
        </Transition.Root>
    )
}

interface GetDoctypesResponse {
    message: Pick<DocType, "name" | "module">[]
}

interface GetDoctypeModulesResponse {
    message: string[]
}

export const ModuleList = ({
    doctype,
    setDocType,
    open,
}: {
    doctype: string[]
    setDocType: React.Dispatch<React.SetStateAction<string[]>>
    open: boolean
}) => {
    const [filter, setFilter] = useState("")
    const [selectedModule, setSelectedModule] = useState(() => window.sessionStorage.getItem(ERD_META_SELECTED_MODULE_STORAGE_KEY) ?? "")
    const [modulePickerOpen, setModulePickerOpen] = useState(false)

    const debouncedInput = useDebounce(filter, 500)

    useEffect(() => {
        if (open) {
            setFilter("")
        }
    }, [open])

    useEffect(() => {
        if (selectedModule) {
            window.sessionStorage.setItem(ERD_META_SELECTED_MODULE_STORAGE_KEY, selectedModule)
            return
        }

        window.sessionStorage.removeItem(ERD_META_SELECTED_MODULE_STORAGE_KEY)
    }, [selectedModule])

    const { data: moduleData, error: moduleError, isLoading: modulesLoading } = useFrappeGetCall<GetDoctypeModulesResponse>(
        "frappe_erd.api.erd_viewer.get_doctype_modules"
    )

    const { data, error, isLoading } = useFrappeGetCall<GetDoctypesResponse>(
        "frappe_erd.api.erd_viewer.get_doctypes",
        {
            search_text: debouncedInput,
            module: selectedModule,
        },
    )

    const doctypes = data?.message ?? []
    const visibleDoctypeNames = useMemo(() => doctypes.map((doc) => doc.name), [doctypes])
    const visibleDoctypeSet = useMemo(() => new Set(visibleDoctypeNames), [visibleDoctypeNames])
    const selectedDoctypeSet = useMemo(() => new Set(doctype), [doctype])
    const selectedVisibleCount = useMemo(
        () => visibleDoctypeNames.filter((name) => selectedDoctypeSet.has(name)).length,
        [visibleDoctypeNames, selectedDoctypeSet]
    )

    const allVisibleSelected = doctypes.length > 0 && selectedVisibleCount === doctypes.length
    const someVisibleSelected = selectedVisibleCount > 0 && !allVisibleSelected
    const modules = moduleData?.message ?? []

    const updateDocTypes = (updater: (currentDoctypes: string[]) => string[]) => {
        setDocType((currentDoctypes) => updater(currentDoctypes))
    }

    const addVisibleDoctypes = () => {
        updateDocTypes((currentDoctypes) => [...new Set([...currentDoctypes, ...visibleDoctypeNames])])
    }

    const removeVisibleDoctypes = () => {
        updateDocTypes((currentDoctypes) => currentDoctypes.filter((name) => !visibleDoctypeSet.has(name)))
    }

    if (moduleError || error) {
        return <ErrorBanner error={moduleError ?? error} />
    }

    if (modulesLoading) {
        return <FullPageLoader className="w-[240px]" />
    }

    return (
        <div className="flex h-full min-h-0 flex-col gap-3 pb-4">
            <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                    <div className="min-w-[180px] flex-1">
                        <Input
                            placeholder="Filter DocType..."
                            value={filter}
                            onChange={(event) => setFilter(event.target.value)}
                            className="w-full"
                            autoFocus
                        />
                    </div>
                    <div className="min-w-[220px] flex-1">
                        <Popover open={modulePickerOpen} onOpenChange={setModulePickerOpen}>
                            <div className="flex items-center gap-2">
                                <PopoverTrigger asChild>
                                    <Button variant="outline" role="combobox" aria-expanded={modulePickerOpen} className="w-full justify-between">
                                        <span className="truncate">{selectedModule || "All modules"}</span>
                                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                    </Button>
                                </PopoverTrigger>
                                {selectedModule ? (
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="icon"
                                        className="h-9 w-9 shrink-0"
                                        aria-label="Clear module filter"
                                        onClick={(event) => {
                                            event.preventDefault()
                                            event.stopPropagation()
                                            setSelectedModule("")
                                            setModulePickerOpen(false)
                                        }}
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                ) : null}
                            </div>
                            <DoctypeModulePopover
                                modules={modules}
                                selectedModule={selectedModule}
                                onSelectModule={(module) => {
                                    setSelectedModule(module)
                                    setModulePickerOpen(false)
                                }}
                            />
                        </Popover>
                    </div>
                </div>

                {!modules.length ? (
                    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                        No modules are available for ERD selection.
                    </div>
                ) : (
                    <div className="space-y-2">
                        <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                            <div className="flex flex-wrap items-center gap-2 text-sm">
                                <Checkbox
                                    id="select-all-visible"
                                    checked={allVisibleSelected ? true : someVisibleSelected ? "indeterminate" : false}
                                    onCheckedChange={(checked) => {
                                        if (checked) {
                                            addVisibleDoctypes()
                                            return
                                        }
                                        removeVisibleDoctypes()
                                    }}
                                    disabled={!doctypes.length}
                                />
                                <label htmlFor="select-all-visible" className="text-sm font-medium text-slate-700">
                                    Select all visible
                                </label>
                                <span className="text-xs text-slate-500">
                                    {selectedVisibleCount} of {doctypes.length} selected{selectedModule ? ` in ${selectedModule}` : " in visible list"}
                                </span>
                                {doctype.length ? (
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <Button type="button" variant="outline" size="sm" className="ml-auto h-8">
                                                View selected
                                            </Button>
                                        </PopoverTrigger>
                                        <DoctypeListPopoverForMeta doctypes={doctype} setDoctypes={setDocType} />
                                    </Popover>
                                ) : null}
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    className="h-8"
                                    onClick={removeVisibleDoctypes}
                                    disabled={!selectedVisibleCount}
                                >
                                    Unselect All Visible
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    className="h-8 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700"
                                    onClick={() => setDocType([])}
                                    disabled={!doctype.length}
                                >
                                    Clear All Selections
                                </Button>
                            </div>
                        </div>

                        <div className="text-xs text-slate-500">
                            Showing {doctypes.length} DocType{doctypes.length === 1 ? "" : "s"}{selectedModule ? ` in ${selectedModule}` : ""}
                        </div>
                    </div>
                )}
            </div>

            {isLoading ? (
                <FullPageLoader className="w-[240px]" />
            ) : (
                <div className="min-h-0 flex-1 overflow-hidden rounded-lg border border-slate-200">
                    {doctypes.length ? (
                        <ul role="list" className="h-full divide-y divide-gray-200 overflow-y-auto">
                            {doctypes.map((doc) => {
                                const isChecked = selectedDoctypeSet.has(doc.name)
                                return (
                                    <li className="flex items-center justify-between px-4 py-3" key={doc.name}>
                                        <div className="flex min-w-0 flex-col pr-4">
                                            <label htmlFor={doc.name} className="truncate text-sm font-medium text-slate-900">
                                                {doc.name}
                                            </label>
                                            <span className="text-xs text-slate-500">{doc.module}</span>
                                        </div>
                                        <Checkbox
                                            id={doc.name}
                                            checked={isChecked}
                                            onCheckedChange={(checked) => {
                                                if (checked) {
                                                    updateDocTypes((currentDoctypes) => [...new Set([...currentDoctypes, doc.name])])
                                                    return
                                                }
                                                updateDocTypes((currentDoctypes) => currentDoctypes.filter((name) => name !== doc.name))
                                            }}
                                        />
                                    </li>
                                )
                            })}
                        </ul>
                    ) : (
                        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
                            No DocTypes match the current filters{selectedModule ? ` in ${selectedModule}` : ""}.
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

const DoctypeModulePopover = ({
    modules,
    selectedModule,
    onSelectModule,
}: {
    modules: string[]
    selectedModule: string
    onSelectModule: (module: string) => void
}) => {
    return (
        <PopoverContent className="w-[280px] p-0" align="start">
            <Command>
                <CommandInput placeholder="Search modules..." />
                <CommandList className="max-h-[280px]">
                    <CommandEmpty>No modules found.</CommandEmpty>
                    <CommandItem onSelect={() => onSelectModule("")}>
                        <Check className={cn("mr-2 h-4 w-4", selectedModule ? "opacity-0" : "opacity-100")} />
                        All modules
                    </CommandItem>
                    {modules.map((module) => (
                        <CommandItem key={module} value={module} onSelect={() => onSelectModule(module)}>
                            <Check className={cn("mr-2 h-4 w-4", selectedModule === module ? "opacity-100" : "opacity-0")} />
                            <span className="truncate">{module}</span>
                        </CommandItem>
                    ))}
                </CommandList>
            </Command>
        </PopoverContent>
    )
}

export default CreateERD
