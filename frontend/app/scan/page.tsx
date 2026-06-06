"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { startScan } from "@/lib/api"

export default function ScanPage() {
  const router = useRouter()
  const [url, setUrl]       = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError("")
    try {
      const { scan_id } = await startScan(url.trim())
      router.push(`/scan/${scan_id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start scan")
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      {/* Back */}
      <a href="/" className="absolute top-6 left-6 text-sentinel-muted hover:text-white text-sm flex items-center gap-1.5 transition-colors">
        ← Home
      </a>

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="mb-10 text-center">
          <div className="inline-block text-sentinel-cyan mb-4">
            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold mb-2">VulnSentinel</h1>
          <p className="text-sentinel-muted text-sm">
            Paste a public GitHub URL. Five agents will audit it autonomously.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-sentinel-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
              </svg>
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="w-full pl-11 pr-4 py-3.5 bg-sentinel-surface border border-sentinel-border rounded-xl
                         text-sm font-mono placeholder:text-sentinel-muted
                         focus:outline-none focus:border-sentinel-cyan/50 focus:ring-1 focus:ring-sentinel-cyan/20
                         transition-colors"
            />
          </div>

          {error && (
            <p className="text-sentinel-red text-sm px-1">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="w-full py-3.5 rounded-xl font-medium text-sm
                       bg-sentinel-cyan text-black
                       hover:bg-sentinel-cyan/90 active:scale-[0.98]
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-all duration-150"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Starting scan…
              </span>
            ) : "Launch Security Scan"}
          </button>
        </form>

        {/* What happens */}
        <div className="mt-10 border border-sentinel-border rounded-xl p-5 space-y-3">
          <p className="text-xs text-sentinel-muted font-mono uppercase tracking-wider">What happens next</p>
          {[
            ["🧠", "Orchestrator", "Plans scan strategy"],
            ["🔍", "Scanner Agent", "Clones repo, runs Semgrep + Bandit"],
            ["⚠️", "Vuln Analyzer", "Maps findings to OWASP / CVEs"],
            ["💀", "Exploit Reasoner", "Assesses real-world exploitability"],
            ["🔧", "Fix Suggester", "Generates code patches"],
          ].map(([icon, name, desc]) => (
            <div key={name} className="flex items-center gap-3 text-sm">
              <span className="text-base w-6 text-center">{icon}</span>
              <span className="text-slate-300 font-medium w-36">{name}</span>
              <span className="text-sentinel-muted">{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
