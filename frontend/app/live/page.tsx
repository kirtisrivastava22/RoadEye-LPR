"use client";
import { useEffect, useRef, useState } from "react";
import { Camera, Square, Play, CheckCircle2 } from "lucide-react";

interface Detection {
  plate: string;
  confidence: number;
  timestamp: string;
}

export default function LivePage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isActive, setIsActive] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsActive(true);
      startDetection();
    } catch (error) {
      console.error("Camera access denied:", error);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsActive(false);
  };

  const startDetection = () => {
    intervalRef.current = setInterval(() => {
      sendFrameToAPI();
    }, 500);
  };

  const sendFrameToAPI = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      async (blob) => {
        if (!blob) return;

        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
          const res = await fetch("http://localhost:8000/detect/image", {
            method: "POST",
            body: formData,
          });
          const data = await res.json();

          if (data.detections && data.detections.length > 0) {
            const newDetection: Detection = {
              plate: data.detections[0].plate_number,
              confidence: data.detections[0].confidence,
              timestamp: new Date().toLocaleTimeString(),
            };

            setDetections((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.plate === newDetection.plate) {
                return prev;
              }
              return [newDetection, ...prev].slice(0, 20);
            });
          }

          if (data.annotated_image) {
            const img = new Image();
            img.onload = () => {
              if (canvas && ctx) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
              }
            };
            img.src = `data:image/jpeg;base64,${data.annotated_image}`;
          }
        } catch (error) {
          console.error("Detection failed:", error);
        }
      },
      "image/jpeg",
      0.8,
    );
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-cyan-400 mb-8 flex items-center gap-3">
          <Camera className="w-10 h-10" />
          Live Camera Detection
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">
                  Camera Feed
                </h2>
                {!isActive ? (
                  <button
                    onClick={startCamera}
                    className="px-6 py-2.5 bg-green-600 text-white rounded-lg 
                      hover:bg-green-700 font-medium transition-colors flex items-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    Start Camera
                  </button>
                ) : (
                  <button
                    onClick={stopCamera}
                    className="px-6 py-2.5 bg-red-600 text-white rounded-lg 
                      hover:bg-red-700 font-medium transition-colors flex items-center gap-2"
                  >
                    <Square className="w-5 h-5" />
                    Stop Camera
                  </button>
                )}
              </div>

             {/* wrap around the current camera feed */}
<div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700">
  ...
  {/* Replace the current relative container with this */}
  <div className="relative bg-black rounded-lg overflow-hidden w-full" >
    {/* limit the visible area so header & panel remain */}
    <div className="w-full max-w-full mx-auto" style={{ maxHeight: '65vh' }}>
      <div className="aspect-video w-full h-full">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-contain rounded-lg"
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full h-full pointer-events-none rounded-lg"
        />
      </div>
    </div>

    {!isActive && (
      <div className="absolute inset-0 flex items-center justify-center bg-black/80 rounded-lg">
        <p className="text-slate-400 text-lg">Camera not started</p>
      </div>
    )}
  </div>
</div>

            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-slate-700 sticky top-6">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                Live Detections
              </h2>

              <div className="mb-4 p-3 bg-slate-700/50 rounded-lg">
                <p className="text-sm text-slate-300">
                  Plates Detected:{" "}
                  <span className="font-bold text-cyan-400">
                    {detections.length}
                  </span>
                </p>
              </div>

              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {detections.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    <Camera className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No detections yet</p>
                    <p className="text-xs mt-1">
                      Start camera to detect plates
                    </p>
                  </div>
                ) : (
                  detections.map((detection, index) => (
                    <div
                      key={index}
                      className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 animate-fadeIn"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-mono text-xl font-bold text-white">
                          {detection.plate}
                        </p>
                        <span className="text-xs text-slate-400">
                          {detection.timestamp}
                        </span>
                      </div>

                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-slate-400">Confidence</span>
                          <span className="text-cyan-400 font-semibold">
                            {(detection.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-600 rounded-full h-1.5">
                          <div
                            className="bg-cyan-500 h-1.5 rounded-full"
                            style={{ width: `${detection.confidence * 100}%` }}
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

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
