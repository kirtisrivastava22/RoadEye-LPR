"use client"

import { useEffect, useRef, useState } from "react"
import {
  Play,
  Square,
  CheckCircle2,
  Clock,
  Camera,
  Copy,
} from "lucide-react"

type Detection = {
  plate: string
  confidence: number
  timestamp: string
}

export default function LivePage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const rafRef = useRef<number | null>(null)

  const [active, setActive] = useState(false)
  const [detections, setDetections] = useState<Detection[]>([])
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  /* ---------- START CAMERA ---------- */
  const start = async () => {
    if (active) return

    const stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.current!.srcObject = stream
    await videoRef.current!.play()

    videoRef.current!.onloadedmetadata = () => {
      canvasRef.current!.width = videoRef.current!.videoWidth
      canvasRef.current!.height = videoRef.current!.videoHeight
    }

    const ws = new WebSocket("ws://localhost:8000/ws/webcam")
    ws.binaryType = "arraybuffer"
    wsRef.current = ws

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)

      /* Draw annotated frame */
      if (data.frame) {
        const img = new Image()
        img.src = `data:image/jpeg;base64,${data.frame}`
        img.onload = () => {
          const ctx = canvasRef.current!.getContext("2d")!
          ctx.clearRect(
            0,
            0,
            canvasRef.current!.width,
            canvasRef.current!.height
          )
          ctx.drawImage(img, 0, 0)
        }
      }

      /* Store detection */
      if (data.plate) {
        setDetections((prev) => {
          if (prev[0]?.plate === data.plate) return prev
          return [
            {
              plate: data.plate,
              confidence: data.confidence,
              timestamp: new Date().toLocaleTimeString(),
            },
            ...prev,
          ].slice(0, 20)
        })
      }
    }

    sendFrames()
    setActive(true)
  }

  /* ---------- SEND FRAMES ---------- */
  const sendFrames = () => {
    const offscreen = document.createElement("canvas")
    const ctx = offscreen.getContext("2d")!

    const loop = () => {
      if (
        !videoRef.current ||
        !wsRef.current ||
        wsRef.current.readyState !== WebSocket.OPEN
      ) {
        return
      }

      offscreen.width = videoRef.current.videoWidth
      offscreen.height = videoRef.current.videoHeight
      ctx.drawImage(videoRef.current, 0, 0)

      offscreen.toBlob((blob) => {
        if (blob) wsRef.current!.send(blob)
      }, "image/jpeg", 0.7)

      rafRef.current = requestAnimationFrame(loop)
    }

    loop()
  }

  /* ---------- STOP ---------- */
  const stop = () => {
    rafRef.current && cancelAnimationFrame(rafRef.current)
    wsRef.current?.close()

    const tracks = (videoRef.current?.srcObject as MediaStream)?.getTracks()
    tracks?.forEach((t) => t.stop())

    setActive(false)
  }

  const copyPlate = (plate: string, index: number) => {
    navigator.clipboard.writeText(plate)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 1500)
  }

  useEffect(() => () => stop(), [])

  /* ---------- UI ---------- */
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* HEADER */}
        <h1 className="text-4xl font-bold text-cyan-400 mb-8 flex items-center gap-3">
          <Camera className="w-10 h-10" />
          Live Camera License Plate Recognition
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* CAMERA PANEL */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">
                  Live Camera Feed
                </h2>
                <button
                  onClick={active ? stop : start}
                  className={`px-5 py-2 rounded-lg font-medium flex items-center gap-2 ${
                    active
                      ? "bg-red-600 hover:bg-red-700"
                      : "bg-green-600 hover:bg-green-700"
                  }`}
                >
                  {active ? <Square /> : <Play />}
                  {active ? "Stop" : "Start"}
                </button>
              </div>

              <div className="relative aspect-video bg-black rounded-lg overflow-hidden border-2 border-cyan-500/40">
                {/* Hidden input */}
                <video
  ref={videoRef}
  muted
  playsInline
  className="absolute inset-0 w-full h-full object-cover"
/>

                {/* Annotated output */}
               <canvas
  ref={canvasRef}
  className="absolute inset-0 w-full h-full pointer-events-none"
/>


                {!active && (
                  <div className="absolute inset-0 flex items-center justify-center text-slate-400">
                    Camera Offline
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* DETECTIONS SIDEBAR */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700 sticky top-6">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                Live Detections
              </h2>

              <div className="mb-4 text-sm text-slate-300">
                Total Plates:{" "}
                <span className="font-bold text-cyan-400">
                  {detections.length}
                </span>
              </div>

              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                {detections.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    <Camera className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    Waiting for vehicles…
                  </div>
                ) : (
                  detections.map((d, i) => (
                    <div
                      key={i}
                      className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-cyan-500/50 transition group"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-2 text-xs text-cyan-400 mb-1">
                            <Clock className="w-4 h-4" />
                            {d.timestamp}
                          </div>
                          <p className="font-mono text-xl font-bold text-white">
                            {d.plate}
                          </p>
                        </div>

                        <button
                          onClick={() => copyPlate(d.plate, i)}
                          className="p-2 rounded hover:bg-slate-600"
                        >
                          {copiedIndex === i ? (
                            <CheckCircle2 className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4 text-slate-400 group-hover:text-cyan-400" />
                          )}
                        </button>
                      </div>

                      <div className="mt-3">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-400">Confidence</span>
                          <span className="text-cyan-400 font-semibold">
                            {Math.round(d.confidence * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-600 rounded-full h-1.5">
                          <div
                            className="bg-cyan-500 h-1.5 rounded-full"
                            style={{ width: `${d.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollbar */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(6, 182, 212, 0.5);
          border-radius: 3px;
        }
      `}</style>
    </div>
  )
}
