"use client"
import { useEffect, useRef, useState } from "react"

type Detection = {
  plate: string
  confidence: number
  bbox: [number, number, number, number] // [x1, y1, x2, y2]
  timestamp: string
}

export default function LiveCameraPage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
      }
    })
  }, [])

  useEffect(() => {
    wsRef.current = new WebSocket("ws://localhost:8000/ws/video")

    wsRef.current.onmessage = (event) => {
      const data: Detection = JSON.parse(event.data)
      setDetections((prev) => [...prev, data])
    }

    return () => wsRef.current?.close()
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      detections.forEach((det) => {
        const [x1, y1, x2, y2] = det.bbox

        ctx.strokeStyle = "#22D3EE"
        ctx.lineWidth = 3
        ctx.shadowColor = "#22D3EE"
        ctx.shadowBlur = 15
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

        ctx.fillStyle = "#22D3EE"
        ctx.shadowBlur = 10
        ctx.font = "20px monospace"
        ctx.fillText(`${det.plate} (${(det.confidence * 100).toFixed(1)}%)`, x1, y1 - 5)
      })

      requestAnimationFrame(render)
    }

    render()
  }, [detections])

  return (
    <div className="relative w-full h-full flex justify-center items-center">
      <video
        ref={videoRef}
        className="w-full max-w-4xl rounded-lg"
        autoPlay
        muted
      />
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full pointer-events-none"
      />
    </div>
  )
}
