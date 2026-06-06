interface Vulnerability {
  id: string
  file: string
  line: number
  severity: string
  category: string
  description: string
  cve?: string | null
}

interface Patch {
  vuln_id: string
  file: string
  original_code: string
  patched_code: string
  explanation: string
}

const SEVERITY_PILL: Record<string, string> = {
  CRITICAL: "pill-critical",
  HIGH:     "pill-high",
  MEDIUM:   "pill-medium",
  LOW:      "pill-low",
}

export default function VulnCard({
  vuln,
  patch,
}: {
  vuln: Vulnerability
  patch?: Patch
}) {
  const pill = SEVERITY_PILL[vuln.severity] ?? "pill-low"

  return (
    <div className="border border-sentinel-border bg-sentinel-surface rounded-xl p-4 space-y-3 animate-slide-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-medium ${pill}`}>
            {vuln.severity}
          </span>
          <span className="text-xs text-sentinel-muted font-mono">{vuln.id}</span>
          {vuln.cve && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
              {vuln.cve}
            </span>
          )}
        </div>
        <span className="text-xs text-sentinel-muted shrink-0">{vuln.category}</span>
      </div>

      {/* Description */}
      <p className="text-sm text-slate-300 leading-relaxed">{vuln.description}</p>

      {/* Location */}
      <div className="flex items-center gap-1.5 text-xs font-mono text-sentinel-muted">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <span className="truncate">{vuln.file}</span>
        {vuln.line > 0 && <span className="shrink-0 text-slate-500">:{vuln.line}</span>}
      </div>

      {/* Patch */}
      {patch && (
        <details className="group">
          <summary className="text-xs text-sentinel-green cursor-pointer select-none flex items-center gap-1.5 hover:underline">
            <svg className="w-3.5 h-3.5 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/>
            </svg>
            View suggested patch
          </summary>
          <div className="mt-3 space-y-2 text-xs font-mono">
            <div>
              <div className="text-red-400/70 mb-1">− Original</div>
              <pre className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 text-red-400 overflow-x-auto whitespace-pre-wrap break-all">
                {patch.original_code}
              </pre>
            </div>
            <div>
              <div className="text-green-400/70 mb-1">+ Patched</div>
              <pre className="bg-green-500/5 border border-green-500/20 rounded-lg p-3 text-green-400 overflow-x-auto whitespace-pre-wrap break-all">
                {patch.patched_code}
              </pre>
            </div>
            <p className="text-sentinel-muted pt-1">{patch.explanation}</p>
          </div>
        </details>
      )}
    </div>
  )
}
