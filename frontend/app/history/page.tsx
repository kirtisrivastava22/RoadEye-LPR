"use client"

import { useEffect, useState } from "react"

type DetectionHistory = {
  plate_number: string
  confidence: number
  timestamp: string
  source: string
  image_path: string
}

export default function HistoryPage() {
  const [history, setHistory] = useState<DetectionHistory[]>([])

  useEffect(() => {
    fetch("http://localhost:8000/history")
      .then((res) => res.json())
      .then((data) => setHistory(data))
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-cyan-400 mb-4">Detection History</h1>

      <div className="space-y-2">
        {history.length === 0 && <p>No detections yet.</p>}
        {history.map((det, idx) => (
          <div
            key={idx}
            className="p-3 bg-[#111827] rounded-lg border border-cyan-500/20"
          >
            <p>
              <strong>Plate:</strong> {det.plate_number} —{" "}
              <strong>Confidence:</strong> {(det.confidence * 100).toFixed(1)}%
            </p>
            <p>
              <strong>Source:</strong> {det.source} —{" "}
              <strong>Time:</strong> {new Date(det.timestamp).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
