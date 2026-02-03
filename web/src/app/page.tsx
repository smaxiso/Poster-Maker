"use client";

import { useState } from "react";
import { ImageDropzone } from "@/components/ImageDropzone";
import { GridPreview } from "@/components/GridPreview";
import { ImageMetadata } from "@/types";
import { api } from "@/lib/api";
import { Sparkles, RefreshCw, Printer, RotateCcw, RotateCw, FlipHorizontal, FlipVertical, Maximize, Minimize } from "lucide-react";
import { clsx } from "clsx";

export default function Home() {
  const [uploadedImage, setUploadedImage] = useState<ImageMetadata | null>(null);
  const [rows, setRows] = useState(3);
  const [cols, setCols] = useState(2);
  const [rotation, setRotation] = useState(0);
  const [flipHorizontal, setFlipHorizontal] = useState(false);
  const [flipVertical, setFlipVertical] = useState(false);
  const [resizeMode, setResizeMode] = useState<"maintain" | "crop">("maintain");

  const [isProcessing, setIsProcessing] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [taskStatus, setTaskStatus] = useState<"queued" | "processing" | "completed" | "failed" | null>(null);
  const [taskMessage, setTaskMessage] = useState("");

  const totalPages = rows * cols;

  const handleGenerate = async () => {
    if (!uploadedImage) return;

    setIsProcessing(true);
    setTaskStatus("queued");
    setProgress(0);

    try {
      // Pass rotation and flip params
      const task = await api.createTask(
        uploadedImage.filename,
        rows,
        cols,
        rotation,
        flipHorizontal,
        flipVertical,
        resizeMode
      );
      setTaskId(task.task_id);

      // Start polling
      const interval = setInterval(async () => {
        try {
          const status = await api.getTask(task.task_id);
          setTaskStatus(status.status);
          setProgress(status.progress);
          setTaskMessage(status.message);

          if (status.status === "completed" || status.status === "failed") {
            clearInterval(interval);
            setIsProcessing(false);
          }
        } catch (e) {
          console.error("Polling error", e);
          clearInterval(interval);
          setIsProcessing(false);
        }
      }, 1000);

    } catch (e) {
      console.error("Generation failed", e);
      setTaskStatus("failed");
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (taskId) {
      window.open(api.getPdfDownloadUrl(taskId), "_blank");
    }
  };

  const rotateLeft = () => setRotation(r => (r - 90) % 360);
  const rotateRight = () => setRotation(r => (r + 90) % 360);
  const toggleFlipH = () => setFlipHorizontal(f => !f);
  const toggleFlipV = () => setFlipVertical(f => !f);
  const toggleResizeMode = () => setResizeMode(m => m === "maintain" ? "crop" : "maintain");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 text-center relative z-10">

      {!uploadedImage ? (
        <main className="w-full max-w-4xl flex flex-col items-center gap-12 animate-fade-in">

          <div className="space-y-6">
            <h1 className="text-6xl md:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-[var(--gradient-primary)] drop-shadow-sm pb-2">
              Poster Maker
            </h1>
            <p className="text-xl text-gray-300 max-w-xl mx-auto leading-relaxed font-light">
              Turn your digital memories into massive wall art.
              <br />
              <span className="text-white/60 text-base">Split. Print. Assemble.</span>
            </p>
          </div>

          <ImageDropzone onUploadComplete={setUploadedImage} />

        </main>
      ) : (
        <main className="glass-card w-full max-w-6xl flex flex-col lg:flex-row gap-8 animate-fade-in p-8">

          {/* LEFT: Preview Panel */}
          <div className="flex-1 flex flex-col gap-4 min-w-0">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-400" /> Preview
              </h2>
              <div className="flex items-center gap-3">
                {/* Image Manipulation Controls */}
                {!taskId && (
                  <div className="flex items-center gap-2 bg-black/40 rounded-lg p-1.5 border border-white/10 backdrop-blur-sm shadow-inner">
                    <div className="flex gap-0.5">
                      <button onClick={rotateLeft} className="p-2 hover:bg-white/10 rounded-md transition-all active:scale-95 text-gray-300 hover:text-white" title="Rotate Left">
                        <RotateCcw className="w-4 h-4" />
                      </button>
                      <button onClick={rotateRight} className="p-2 hover:bg-white/10 rounded-md transition-all active:scale-95 text-gray-300 hover:text-white" title="Rotate Right">
                        <RotateCw className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="w-px h-5 bg-white/10 mx-1"></div>

                    <div className="flex gap-0.5">
                      <button onClick={toggleFlipH} className={clsx("p-2 rounded-md transition-all active:scale-95", flipHorizontal ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30" : "hover:bg-white/10 text-gray-300 hover:text-white")} title="Flip Horizontal">
                        <FlipHorizontal className="w-4 h-4" />
                      </button>
                      <button onClick={toggleFlipV} className={clsx("p-2 rounded-md transition-all active:scale-95", flipVertical ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30" : "hover:bg-white/10 text-gray-300 hover:text-white")} title="Flip Vertical">
                        <FlipVertical className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="w-px h-5 bg-white/10 mx-1"></div>

                    <button
                      onClick={toggleResizeMode}
                      className={clsx("p-2 rounded-md transition-all active:scale-95 flex items-center gap-2 text-xs font-medium", resizeMode === "crop" ? "bg-pink-500/20 text-pink-300 border border-pink-500/30" : "hover:bg-white/10 text-gray-300 hover:text-white")}
                      title={resizeMode === "crop" ? "Mode: Fill (Crop)" : "Mode: Fit (Maintain)"}
                    >
                      {resizeMode === "crop" ? <Maximize className="w-4 h-4" /> : <Minimize className="w-4 h-4" />}
                      {resizeMode === "crop" ? "FILL" : "FIT"}
                    </button>
                  </div>
                )}
                <div className="text-xs font-mono bg-white/5 px-2 py-1 rounded text-gray-400">
                  {uploadedImage.dimensions.width} x {uploadedImage.dimensions.height} px
                </div>
              </div>
            </div>

            {/* Dynamic Aspect Ratio Container */}
            <div
              className="relative w-full bg-black/40 rounded-xl overflow-hidden border border-white/5 group transition-all duration-500 ease-in-out"
              style={{
                aspectRatio: `${(cols * 210) / (rows * 297)}` // A4 ratio is 210/297 (approx 1:1.414)
              }}
            >
              <GridPreview
                imageUrl={api.getFileUrl(uploadedImage.preview_url || uploadedImage.url)}
                rows={rows}
                cols={cols}
                className="w-full h-full"
                rotation={rotation}
                flipHorizontal={flipHorizontal}
                flipVertical={flipVertical}
                resizeMode={resizeMode}
                imageDimensions={uploadedImage.dimensions}
              />
            </div>
          </div>

          {/* RIGHT: Configuration Panel */}
          <div className="lg:w-96 flex flex-col gap-8">

            {/* Stats Card */}
            <div className="bg-white/5 rounded-xl p-6 border border-white/5 space-y-4">
              <div className="flex justify-between items-center pb-4 border-b border-white/5">
                <span className="text-gray-400">Total Pages</span>
                <span className="text-3xl font-bold text-indigo-400">{totalPages}</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/20 p-3 rounded-lg text-center">
                  <div className="text-xs text-gray-500 uppercase">Input Size</div>
                  <div className="font-mono text-sm">{(uploadedImage.size_bytes / 1024 / 1024).toFixed(1)} MB</div>
                </div>
                <div className="bg-black/20 p-3 rounded-lg text-center">
                  <div className="text-xs text-gray-500 uppercase">Format</div>
                  <div className="font-mono text-sm">{uploadedImage.format}</div>
                </div>
              </div>
            </div>

            {/* Grid Controls (State: Configuring) */}
            {!taskId ? (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Printer className="w-5 h-5" /> Layout
                </h3>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Rows (Vertical)</span>
                      <span className="font-mono text-indigo-400">{rows}</span>
                    </div>
                    <input
                      type="range" min="1" max="10"
                      value={rows} onChange={(e) => setRows(Number(e.target.value))}
                      className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-400 disabled:opacity-50"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Columns (Horizontal)</span>
                      <span className="font-mono text-pink-400">{cols}</span>
                    </div>
                    <input
                      type="range" min="1" max="10"
                      value={cols} onChange={(e) => setCols(Number(e.target.value))}
                      className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-pink-500 hover:accent-pink-400 disabled:opacity-50"
                    />
                  </div>
                </div>
              </div>
            ) : (
              /* State: Processing / Complete */
              <div className="space-y-6 flex-1 flex flex-col justify-center">
                <div className="space-y-2 text-left">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">
                      {taskStatus === "completed" ? "Ready to Print!" : "Generating..."}
                    </h3>
                    <span className="text-xs text-gray-400 font-mono">{progress}%</span>
                  </div>

                  <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-pink-500 transition-all duration-300 ease-out"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-400 animate-pulse">{taskMessage}</p>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="mt-auto space-y-3">
              {!taskId ? (
                <button
                  onClick={handleGenerate}
                  disabled={isProcessing}
                  className="btn-primary w-full flex items-center justify-center gap-2 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? "Starting..." : "Generate Poster"}
                </button>
              ) : taskStatus === "completed" ? (
                <button
                  onClick={handleDownload}
                  className="btn-primary w-full flex items-center justify-center gap-2 text-lg bg-green-500 hover:bg-green-600 shadow-[0_0_20px_rgba(34,197,94,0.3)] animate-pulse"
                >
                  Download PDF
                </button>
              ) : null}

              <button
                onClick={() => {
                  setUploadedImage(null);
                  setRows(3);
                  setCols(2);
                  setTaskId(null);
                  setTaskStatus(null);
                }}
                className="w-full py-3 rounded-xl font-medium border border-white/10 hover:bg-white/5 transition-colors text-gray-400 flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" /> Start Over
              </button>
            </div>
          </div>

        </main>
      )}

      <footer className="fixed bottom-6 text-xs text-gray-600 font-medium tracking-wide">
        POSTER MAKER 2026
      </footer>
    </div>
  );
}
