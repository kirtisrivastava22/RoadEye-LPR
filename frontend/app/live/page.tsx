"use client"

import { useEffect, useRef } from "react"

export default function LivePage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    startCamera()
    connectWS()
  }, [])

  async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.current!.srcObject = stream
    videoRef.current!.play()
  }

  function connectWS() {
    wsRef.current = new WebSocket("ws://localhost:8000/ws/video")

    wsRef.current.onopen = () => {
      console.log("WS connected")
      setInterval(sendFrame, 200)
    }

    wsRef.current.onmessage = async (event) => {
  const blob = new Blob([event.data], { type: "image/jpeg" })
  const img = new Image()

  img.src = URL.createObjectURL(blob)

  img.onload = () => {
    const canvas = canvasRef.current!
    const ctx = canvas.getContext("2d")!

    canvas.width = img.width
    canvas.height = img.height

    ctx.drawImage(img, 0, 0)
  }
}

  }

  function sendFrame() {
    if (!videoRef.current || !wsRef.current) return

    const canvas = document.createElement("canvas")
    canvas.width = videoRef.current.videoWidth
    canvas.height = videoRef.current.videoHeight

    const ctx = canvas.getContext("2d")!
    ctx.drawImage(videoRef.current, 0, 0)

    const base64 = canvas.toDataURL("image/jpeg").split(",")[1]
    wsRef.current.send(base64)
  }

  // function drawBoxes(detections: any[]) {
  //   if (!canvasRef.current || !videoRef.current) return

  //   const ctx = canvasRef.current.getContext("2d")!
  //   canvasRef.current.width = videoRef.current.videoWidth
  //   canvasRef.current.height = videoRef.current.videoHeight

  //   ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height)

  //   detections.forEach((det: any) => {
  //     const [x1, y1, x2, y2] = det.bbox
  //     ctx.strokeStyle = "#22D3EE"
  //     ctx.lineWidth = 3
  //     ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

  //     ctx.fillStyle = "#22D3EE"
  //     ctx.fillText(`Conf: ${det.confidence.toFixed(2)}`, x1, y1 - 5)
  //   })
  // }

  return (
    <div className="relative">
      <video ref={videoRef} className="w-full rounded-xl" />
      <canvas ref={canvasRef} className="absolute top-0 left-0" />
    </div>
  )
}
