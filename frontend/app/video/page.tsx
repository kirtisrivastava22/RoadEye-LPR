"use client";
import { useRef, useState } from "react";
import { Copy, CheckCircle2, Clock, Shield, Video } from "lucide-react";

interface DetectionResult {
  plate: string;
  confidence: number;
  videoTimestamp: string; // Video time like "00:05.23"
  frameTime: number; // Raw seconds for deduplication
}

export default function LiveVideoUpload() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [plate, setPlate] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [detections, setDetections] = useState<DetectionResult[]>([]);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [currentVideoTime, setCurrentVideoTime] = useState<string>("00:00.00");

  const formatVideoTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`;
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const exportDetections = () => {
    const csv = [
      "Video Time,License Plate,Confidence",
      ...detections.map(
        (d) =>
          `${d.videoTimestamp},${d.plate},${(d.confidence * 100).toFixed(1)}%`,
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `detections_${new Date().getTime()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const connectWebSocket = () => {
    if (ws) return;
    const socket = new WebSocket("ws://localhost:8000/ws/video");
    socket.binaryType = "arraybuffer";

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Update current plate display
      setPlate(data.plate);

      // Use timestamp from server (which came from our frame metadata)
      const currentTime = data.timestamp || 0;
      setCurrentVideoTime(formatVideoTime(currentTime));

      // If new plate detected, add to detections list
      if (data.plate && data.plate.trim()) {
        const videoTimestamp = formatVideoTime(currentTime);

        setDetections((prev) => {
          // Check if this exact plate was detected within the last 2 seconds
          // This prevents duplicate entries for the same plate in quick succession
          const lastDetection = prev[prev.length - 1];
          if (
            lastDetection &&
            lastDetection.plate === data.plate &&
            currentTime - lastDetection.frameTime < 2
          ) {
            return prev;
          }

          return [
            ...prev,
            {
              plate: data.plate,
              confidence: data.confidence || 0,
              videoTimestamp: videoTimestamp,
              frameTime: currentTime,
            },
          ];
        });
      }

      // Update canvas with annotated frame
      const img = new Image();
      img.src = `data:image/jpeg;base64,${data.frame}`;
      img.onload = () => {
        const ctx = canvasRef.current?.getContext("2d");
        if (ctx && canvasRef.current) {
          ctx.clearRect(
            0,
            0,
            canvasRef.current.width,
            canvasRef.current.height,
          );
          ctx.drawImage(
            img,
            0,
            0,
            canvasRef.current.width,
            canvasRef.current.height,
          );
        }
      };
    };

    socket.onclose = () => {
      setWs(null);
      setProcessing(false);
    };

    setWs(socket);
  };

  const handleStart = () => {
    if (!file || !ws || processing) return;

    // Clear previous detections
    setDetections([]);
    setProcessing(true);

    const video = videoRef.current;
    if (!video) return;

    video.src = URL.createObjectURL(file);
    video.load();
    video.play();

    video.onplay = () => {
      const sendFrame = () => {
        if (!ws || video.paused || video.ended) {
          setProcessing(false);
          return;
        }

        // Capture current video time BEFORE sending
        const currentTime = video.currentTime;
        setCurrentVideoTime(formatVideoTime(currentTime));

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
          if (blob && ws.readyState === WebSocket.OPEN) {
            blob.arrayBuffer().then((buffer) => {
              // Send frame with timestamp metadata
              const metadata = JSON.stringify({ timestamp: currentTime });
              const metadataBytes = new TextEncoder().encode(metadata + "\n");
              const combined = new Uint8Array(
                metadataBytes.length + buffer.byteLength,
              );
              combined.set(metadataBytes, 0);
              combined.set(new Uint8Array(buffer), metadataBytes.length);
              ws.send(combined);
            });
          }
        }, "image/jpeg");

        requestAnimationFrame(sendFrame);
      };
      sendFrame();
    };
  };

  const handleReset = () => {
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
    setDetections([]);
    setPlate(null);
    setProcessing(false);
    setCurrentVideoTime("00:00.00");
  };

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold text-cyan-400 mb-8 flex items-center gap-3">
            <Video className="w-10 h-10" />
            Video License Plate Recognition
          </h1>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Video Section */}
            <div className="lg:col-span-2 space-y-4">
              {/* Controls */}
              <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
                <h2 className="text-xl font-semibold text-white mb-4">
                  Upload & Process
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Select Video File
                    </label>
                    <input
                      type="file"
                      accept="video/*"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className={
  "block w-full text-sm text-slate-300 " +
  "file:mr-4 file:py-2 file:px-4 " +
  "file:rounded-lg file:border-0 " +
  "file:text-sm file:font-semibold " +
  "file:bg-cyan-600 file:text-white " +
  "hover:file:bg-cyan-700 " +
  "file:cursor-pointer cursor-pointer " +
  "bg-slate-700/50 rounded-lg border border-slate-600"
}
                    />
                    {file && (
                      <p className="mt-2 text-sm text-slate-400">
                        Selected: {file.name}
                      </p>
                    )}
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={connectWebSocket}
                      disabled={!!ws}
                      className="px-6 py-2.5 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:bg-slate-600 disabled:cursor-not-allowed font-medium transition-colors">
                      {ws ? "Connected ✓" : "Connect"}
                    </button>

                    <button
                      onClick={handleStart}
                      disabled={!file || !ws || processing}
                      className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed font-medium transition-colors flex items-center gap-2" >
                      {processing ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Processing...
                        </>
                      ) : (
                        "Start Detection"
                      )}
                    </button>

                    <button
                      onClick={handleReset}
                      disabled={!processing && detections.length === 0}
                      className="px-6 py-2.5 bg-slate-600 text-white rounded-lg  hover:bg-slate-700 disabled:bg-slate-700 disabled:cursor-not-allowed font-medium transition-colors" >
                      Reset
                    </button>

                    {detections.length > 0 && (
                      <button
                        onClick={exportDetections}
                        className="px-6 py-2.5 bg-purple-600 text-white rounded-lg  hover:bg-purple-700 font-medium transition-colors"
                        title="Export to CSV"
                      >
                        Export CSV
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Video Display */}
              <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">
                    Live Feed
                  </h2>
                  <div className="flex items-center gap-2 text-cyan-400 font-mono text-sm">
                    <Clock className="w-4 h-4" />
                    <span>{currentVideoTime}</span>
                  </div>
                </div>

                <video ref={videoRef} className="hidden" />
                <canvas
                  ref={canvasRef}
                  width={640}
                  height={480}
                  className="w-full rounded-lg border-2 border-cyan-500/50 bg-slate-900"
                />

                {plate && (
                  <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-green-400 font-semibold text-lg">
                      Current Detection:{" "}
                      <span className="font-mono">{plate}</span>
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Detection Results Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700 sticky top-6">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                  Detection Results
                </h2>

                <div className="mb-4 p-3 bg-slate-700/50 rounded-lg">
                  <p className="text-sm text-slate-300">
                    Total Detections:{" "}
                    <span className="font-bold text-cyan-400">
                      {detections.length}
                    </span>
                  </p>
                </div>

                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                  {detections.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">
                      <Video className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No detections yet</p>
                      <p className="text-xs mt-1">
                        Start processing to see results
                      </p>
                    </div>
                  ) : (
                    detections.map((detection, index) => (
                      <div
                        key={index}
                        className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-cyan-500/50 transition-colors group"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Clock className="w-4 h-4 text-cyan-400" />
                              <span className="font-mono text-sm font-semibold text-cyan-400">
                                {detection.videoTimestamp}
                              </span>
                            </div>
                            <p className="font-mono text-xl font-bold text-white">
                              {detection.plate}
                            </p>
                          </div>

                          <button
                            onClick={() =>
                              copyToClipboard(detection.plate, index)
                            }
                            className="p-2 hover:bg-slate-600 rounded-lg transition-colors"
                            title="Copy to clipboard"
                          >
                            {copiedIndex === index ? (
                              <CheckCircle2 className="w-4 h-4 text-green-400" />
                            ) : (
                              <Copy className="w-4 h-4 text-slate-400 group-hover:text-cyan-400" />
                            )}
                          </button>
                        </div>

                        {detection.confidence > 0 && (
                          <div className="mt-3">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-slate-400">Confidence</span>
                              <span className="text-cyan-400 font-semibold">
                                {(detection.confidence * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-600 rounded-full h-1.5">
                              <div
                                className="bg-cyan-500 h-1.5 rounded-full transition-all"
                                style={{
                                  width: `${detection.confidence * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
