"use client"

import { useState } from "react"

export default function VideoPage() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<any>(null)

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append("file", file)

    const res = await fetch("http://localhost:8000/detect/video", {
      method: "POST",
      body: formData,
    })

    const data = await res.json()
    setResult(data)
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold text-cyan-400">Video Detection</h1>

      <input
        type="file"
        accept="video/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="text-gray-200"
      />

      <button
        onClick={handleUpload}
        className="px-4 py-2 bg-cyan-500 rounded-lg hover:bg-cyan-400 transition"
      >
        Upload & Detect
      </button>

      {result && (
        <pre className="bg-[#111827] p-4 rounded-lg text-sm overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  )
}
