"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, Image as ImageIcon, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { ImageMetadata } from "@/types";
import { clsx } from "clsx";

interface ImageDropzoneProps {
    onUploadComplete: (metadata: ImageMetadata) => void;
}

export function ImageDropzone({ onUploadComplete }: ImageDropzoneProps) {
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        setIsUploading(true);
        setError(null);

        try {
            const metadata = await api.uploadImage(file);
            onUploadComplete(metadata);
        } catch (err: unknown) {
            console.error("Upload error:", err);
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("Failed to upload image. Please try again.");
            }
        } finally {
            setIsUploading(false);
        }
    }, [onUploadComplete]);

    const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
        onDrop,
        accept: {
            'image/jpeg': [],
            'image/png': [],
            'image/webp': []
        },
        maxFiles: 1,
        multiple: false,
        disabled: isUploading
    });

    return (
        <div className="w-full max-w-xl mx-auto">
            <div
                {...getRootProps()}
                className={clsx(
                    "relative group cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-300 ease-out",
                    // Base styles (Glassmorphism integration)
                    "bg-[rgba(255,255,255,0.03)] hover:bg-[rgba(255,255,255,0.06)]",

                    // Border colors based on state
                    isDragActive ? "border-indigo-500 scale-[1.02] shadow-[0_0_30px_rgba(99,102,241,0.3)]" :
                        isDragReject || error ? "border-red-500/50" :
                            "border-white/10 group-hover:border-white/20",

                    // Layout
                    "flex flex-col items-center justify-center py-16 px-6 text-center"
                )}
            >
                <input {...getInputProps()} />

                {/* State: Uploading */}
                {isUploading ? (
                    <div className="flex flex-col items-center gap-4 animate-in fade-in duration-300">
                        <Loader2 className="w-12 h-12 text-indigo-400 animate-spin" />
                        <div className="space-y-1">
                            <p className="text-lg font-medium text-white">Uploading...</p>
                            <p className="text-sm text-gray-400">Optimizing your image for print</p>
                        </div>
                    </div>
                ) : (
                    /* State: Idle / Dragging */
                    <div className="flex flex-col items-center gap-6">
                        <div className={clsx(
                            "p-4 rounded-full transition-colors duration-300",
                            isDragActive ? "bg-indigo-500/20 text-indigo-400" :
                                error ? "bg-red-500/20 text-red-400" :
                                    "bg-white/5 text-gray-300 group-hover:text-white group-hover:scale-110 group-hover:bg-white/10"
                        )}>
                            {error ? (
                                <AlertCircle className="w-10 h-10" />
                            ) : isDragActive ? (
                                <UploadCloud className="w-10 h-10 animate-bounce" />
                            ) : (
                                <ImageIcon className="w-10 h-10 transition-transform duration-300" />
                            )}
                        </div>

                        <div className="space-y-2">
                            <p className="text-xl font-semibold text-white">
                                {isDragActive ? "Drop to upload" : "Upload your image"}
                            </p>
                            <p className="text-sm text-gray-400 max-w-xs mx-auto leading-relaxed">
                                {error ? (
                                    <span className="text-red-400">{error}</span>
                                ) : (
                                    "Drag & drop or click to browse. Supports JPG, PNG, WEBP high-res images."
                                )}
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
