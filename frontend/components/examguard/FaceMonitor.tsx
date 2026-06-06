"use client"

import { useEffect, useRef, useState } from "react"

interface Props {
  onFaceEvent: (faceCount: number, confidence: number) => void
  active: boolean
}

export default function FaceMonitor({ onFaceEvent, active }: Props) {
  const videoRef  = useRef<HTMLVideoElement>(null)
  const [camError, setCamError] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)

  useEffect(() => {
    if (!active) return
    let stream: MediaStream | null = null

    navigator.mediaDevices
      .getUserMedia({ video: { width: 320, height: 240, facingMode: "user" } })
      .then((s) => {
        stream = s
        if (videoRef.current) {
          videoRef.current.srcObject = s
          videoRef.current.play()
          setStreaming(true)
        }
      })
      .catch(() => setCamError("Camera access denied"))

    // Send a face event every 3 s (replace with real face-api.js inference)
    const interval = setInterval(() => {
      // Placeholder: always reports 1 face with high confidence
      // Swap this with actual face-api.js detection result
      onFaceEvent(1, 0.97)
    }, 3000)

    return () => {
      clearInterval(interval)
      stream?.getTracks().forEach((t) => t.stop())
      setStreaming(false)
    }
  }, [active, onFaceEvent])

  if (camError) {
    return (
      <div className="aspect-video rounded-xl bg-sentinel-surface border border-sentinel-border flex flex-col items-center justify-center gap-2">
        <svg className="w-8 h-8 text-sentinel-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"/>
        </svg>
        <p className="text-sentinel-muted text-xs">{camError}</p>
      </div>
    )
  }

  return (
    <div className="relative aspect-video rounded-xl overflow-hidden bg-black border border-sentinel-border">
      <video
        ref={videoRef}
        muted
        playsInline
        className="w-full h-full object-cover scale-x-[-1]"
      />
      {!streaming && (
        <div className="absolute inset-0 flex items-center justify-center bg-sentinel-surface">
          <svg className="w-6 h-6 animate-spin text-sentinel-muted" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </div>
      )}
      {streaming && (
        <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 rounded-full px-2 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-sentinel-green animate-pulse" />
          <span className="text-[10px] font-mono text-sentinel-green">LIVE</span>
        </div>
      )}
    </div>
  )
}
