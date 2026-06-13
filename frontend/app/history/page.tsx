"use client"

import { useEffect, useState, useMemo } from "react"
import { useRouter } from "next/navigation"
import { listScanHistory, deleteScanHistory, type ScanHistoryRecord } from "@/lib/api"

const RISK_PILL: Record<string, string> = {
  CRITICAL: "pill-critical",
  HIGH:     "pill-high",
  MEDIUM:   "pill-medium",
  LOW:      "pill-low",
  UNKNOWN:  "text-sentinel-muted border-sentinel-border",
}

const SEV_COLORS: Record<string, string> = {
  critical: "text-sentinel-red",
  high:     "text-orange-400",
  medium:   "text-yellow-400",
  low:      "text-blue-400",
}

function truncateUrl(url: string, max = 55): string {
  if (url.length <= max) return url
  return url.slice(0, max - 1) + "…"
}

function formatDate(ts: number): string {
  return new Date(ts * 1000).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false,
  })
}

export default function HistoryPage() {
  const router = useRouter()
  const [records,   setRecords]   = useState<ScanHistoryRecord[]>([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState("")
  const [search,    setSearch]    = useState("")
  const [deleting,  setDeleting]  = useState<string | null>(null)
  const [confirmed, setConfirmed] = useState<string | null>(null)

  useEffect(() => {
    listScanHistory()
      .then(setRecords)
      .catch(() => setError("Could not load scan history — is the backend running?"))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return records
    return records.filter(
      (r) =>
        r.repo_url.toLowerCase().includes(q) ||
        r.scan_date.includes(q) ||
        r.overall_risk.toLowerCase().includes(q),
    )
  }, [records, search])

  async function handleDelete(scan_id: string) {
    if (confirmed !== scan_id) {
      setConfirmed(scan_id)
      return
    }
    setDeleting(scan_id)
    setConfirmed(null)
    try {
      await deleteScanHistory(scan_id)
      setRecords((prev) => prev.filter((r) => r.scan_id !== scan_id))
    } catch {
      setError("Failed to delete scan.")
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="min-h-screen bg-sentinel-bg text-slate-200 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 shrink-0 flex items-center gap-4 px-5 py-3
                          border-b border-sentinel-border bg-sentinel-surface">
        <a href="/scan" className="text-sentinel-muted hover:text-white transition-colors text-sm">
          ← VulnSentinel
        </a>
        <span className="text-sentinel-border">·</span>
        <span className="text-sm font-semibold text-white">Scan History</span>

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-sentinel-muted font-mono">
            {records.length} scan{records.length !== 1 ? "s" : ""}
          </span>
          <a
            href="/scan"
            className="text-xs px-3 py-1.5 rounded-lg bg-sentinel-cyan/10 text-sentinel-cyan
                       border border-sentinel-cyan/20 hover:bg-sentinel-cyan/20 transition-colors font-medium"
          >
            + New Scan
          </a>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-5 py-8">
        {/* Search */}
        <div className="relative mb-6">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sentinel-muted pointer-events-none"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z"/>
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setConfirmed(null) }}
            placeholder="Filter by URL, date or risk level…"
            className="w-full pl-9 pr-4 py-2.5 bg-sentinel-surface border border-sentinel-border rounded-xl
                       text-sm font-mono placeholder:text-sentinel-muted
                       focus:outline-none focus:border-sentinel-cyan/50 focus:ring-1 focus:ring-sentinel-cyan/20
                       transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-sentinel-muted hover:text-white transition-colors"
            >
              ✕
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 px-4 py-3 rounded-xl border border-sentinel-red/40 bg-sentinel-red/10 text-sentinel-red text-sm">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 rounded-xl bg-sentinel-surface border border-sentinel-border animate-pulse" />
            ))}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-14 h-14 rounded-full bg-sentinel-surface border border-sentinel-border
                            flex items-center justify-center mb-4">
              <svg className="w-7 h-7 text-sentinel-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round"
                      d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
              </svg>
            </div>
            {search ? (
              <>
                <p className="text-sentinel-muted font-medium">No scans match your filter</p>
                <button onClick={() => setSearch("")} className="mt-3 text-sm text-sentinel-cyan hover:underline">
                  Clear filter
                </button>
              </>
            ) : (
              <>
                <p className="text-sentinel-muted font-medium">No scans yet</p>
                <p className="text-sentinel-muted text-sm mt-1">Run a scan and it will appear here automatically.</p>
                <a href="/scan"
                   className="mt-5 text-sm px-4 py-2 rounded-xl bg-sentinel-cyan/10 text-sentinel-cyan
                              border border-sentinel-cyan/20 hover:bg-sentinel-cyan/20 transition-colors">
                  Start your first scan
                </a>
              </>
            )}
          </div>
        )}

        {/* Cards */}
        {!loading && filtered.length > 0 && (
          <div className="space-y-3">
            {filtered.map((r) => (
              <div
                key={r.scan_id}
                className="bg-sentinel-surface border border-sentinel-border rounded-xl p-4
                           hover:border-sentinel-cyan/30 transition-colors group"
              >
                <div className="flex items-start gap-4">
                  {/* Left: URL + meta */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className="text-sm font-mono text-white font-medium truncate max-w-sm"
                        title={r.repo_url}
                      >
                        {truncateUrl(r.repo_url)}
                      </span>
                      <span className={`text-xs font-mono px-2 py-0.5 rounded-full border ${RISK_PILL[r.overall_risk] ?? RISK_PILL.UNKNOWN}`}>
                        {r.overall_risk} RISK
                      </span>
                    </div>

                    <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                      <span className="text-xs text-sentinel-muted font-mono">{formatDate(r.timestamp)}</span>
                      <span className="text-xs text-sentinel-muted font-mono">scan/{r.scan_id}</span>
                      <span className="text-xs text-sentinel-muted">
                        Risk score:
                        <span className={`ml-1 font-semibold font-mono ${
                          r.risk_score >= 75 ? "text-sentinel-red"
                            : r.risk_score >= 50 ? "text-orange-400"
                            : r.risk_score >= 25 ? "text-yellow-400"
                            : "text-sentinel-green"
                        }`}>{r.risk_score}/100</span>
                      </span>
                    </div>

                    {/* Severity breakdown */}
                    <div className="flex items-center gap-4 mt-2">
                      {(["critical", "high", "medium", "low"] as const).map((sev) => (
                        <span key={sev} className="text-xs font-mono">
                          <span className={`font-semibold ${SEV_COLORS[sev]}`}>
                            {r.severity[sev]}
                          </span>
                          <span className="text-sentinel-muted ml-1">{sev}</span>
                        </span>
                      ))}
                      <span className="text-xs text-sentinel-muted ml-auto">
                        {r.total_vulns} total finding{r.total_vulns !== 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>

                  {/* Right: actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => router.push(`/history/${r.scan_id}`)}
                      className="text-xs px-3 py-1.5 rounded-lg bg-sentinel-cyan/10 text-sentinel-cyan
                                 border border-sentinel-cyan/20 hover:bg-sentinel-cyan/20
                                 transition-colors font-medium whitespace-nowrap"
                    >
                      View Report
                    </button>

                    <button
                      onClick={() => handleDelete(r.scan_id)}
                      disabled={deleting === r.scan_id}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors whitespace-nowrap
                        ${confirmed === r.scan_id
                          ? "bg-sentinel-red/20 text-sentinel-red border-sentinel-red/40 hover:bg-sentinel-red/30"
                          : "bg-transparent text-sentinel-muted border-sentinel-border hover:text-sentinel-red hover:border-sentinel-red/40"
                        } disabled:opacity-40 disabled:cursor-not-allowed`}
                    >
                      {deleting === r.scan_id ? "Deleting…" : confirmed === r.scan_id ? "Confirm?" : "Delete"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
