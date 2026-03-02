import { PopoverContent } from "@/components/ui/popover";

export const DoctypeListPopoverForMeta = ({ doctypes, setDoctypes }: {doctypes: string[], setDoctypes: React.Dispatch<React.SetStateAction<string[]>>}) => {
    return (
        <PopoverContent className="w-[350px] p-4 bg-white shadow-lg rounded-lg">
            <div className="col-span-2 grid grid-cols-2 gap-2">
                {doctypes.map((doctype:string) => (
                    <span className="inline-flex justify-between items-center gap-x-0.5 rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10" key={doctype}>
                        {doctype}
                        <button className="group relative h-4 w-4 rounded-sm hover:bg-gray-500/20" onClick={() => setDoctypes(doctypes.filter((d) => d !== doctype))}>
                            <span className="sr-only">Remove</span>
                            <svg viewBox="0 0 14 14" className="h-4 w-4 stroke-gray-600/50 group-hover:stroke-gray-600/75">
                                <path d="M4 4l6 6m0-6l-6 6" />
                            </svg>
                            <span className="absolute -inset-1" />
                        </button>
                    </span>
                ))}
            </div>
        </PopoverContent >
    )
}
