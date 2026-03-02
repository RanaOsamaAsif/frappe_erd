import { FrappeError } from 'frappe-react-sdk'
import { useMemo } from 'react'
import { CircleAlert } from 'lucide-react'

interface ErrorBannerProps extends React.HTMLAttributes<HTMLDivElement> {
    error?: FrappeError | null,
    overrideHeading?: string,
}

interface ParsedErrorMessage {
    message: string,
    title?: string,
    indicator?: string,
}


export const getErrorMessage = (error?: FrappeError | null): string => {
    const messages = getErrorMessages(error)
    return messages.map(m => m.message).join('\n')
}

const getErrorMessages = (error?: FrappeError | null): ParsedErrorMessage[] => {
    if (!error) return []
    let eMessages: ParsedErrorMessage[] = error?._server_messages ? JSON.parse(error?._server_messages) : []
    eMessages = eMessages.map((m: any) => {
        try {
            return JSON.parse(m)
        } catch (e) {
            return m
        }
    })

    if (eMessages.length === 0) {
        const indexOfFirstColon = error?.exception?.indexOf(':')
        if (indexOfFirstColon) {
            const exception = error?.exception?.slice(indexOfFirstColon + 1)
            if (exception) {
                eMessages = [{
                    message: exception,
                    title: "Error"
                }]
            }
        }

        if (eMessages.length === 0) {
            eMessages = [{
                message: error?.message,
                title: "Error",
                indicator: "red"
            }]
        }
    }
    return eMessages

}

export const ErrorBanner = ({ error }: ErrorBannerProps) => {
    const messages = useMemo(() => getErrorMessages(error), [error])

    if (!error) return null

    return (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 w-full">
            <div className="flex w-full">
                <div className="flex-shrink-0">
                    <CircleAlert className='h-5 w-5 text-red-400' />
                </div>
                <div className="ml-2">
                    <p className="text-sm text-red-700 whitespace-pre-wrap">
                        {messages.map((m) => m.message).join('\n')}
                    </p>
                </div>
            </div>
        </div>
    )
}
