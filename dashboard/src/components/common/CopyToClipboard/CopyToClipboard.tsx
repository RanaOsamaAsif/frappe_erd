import { Copy, Check } from 'lucide-react'
import { useState } from 'react'

const CopyButton = ({ value, className = '' }: { value: string, className?: string }) => {
  const [copied, setCopied] = useState(false)

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(value ?? '')
      setCopied(true)
      setTimeout(() => setCopied(false), 1200)
    } catch {
      setCopied(false)
    }
  }

  return (
    <button type="button" onClick={onCopy} className={className} aria-label="Copy to clipboard" title="Copy">
      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
    </button>
  )
}

export default CopyButton
