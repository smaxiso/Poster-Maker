"use client";

import Image from "next/image";
import { clsx } from "clsx";

interface GridPreviewProps {
    imageUrl: string;
    rows: number;
    cols: number;
    className?: string;
    rotation?: number; // degrees (0, 90, 180, 270)
    flipHorizontal?: boolean;
    flipVertical?: boolean;
    resizeMode?: "maintain" | "crop";
    imageDimensions?: { width: number; height: number };
}

export function GridPreview({
    imageUrl,
    rows,
    cols,
    className,
    rotation = 0,
    flipHorizontal = false,
    flipVertical = false,
    resizeMode = "maintain",
    imageDimensions
}: GridPreviewProps) {
    // Generate vertical lines
    const vLines = Array.from({ length: cols - 1 }, (_, i) => (i + 1) / cols * 100);

    // Generate horizontal lines
    const hLines = Array.from({ length: rows - 1 }, (_, i) => (i + 1) / rows * 100);

    // Generate ticks for rulers
    const rulerTicksX = Array.from({ length: cols * 4 + 1 }, (_, i) => i / (cols * 4) * 100);
    const rulerTicksY = Array.from({ length: rows * 4 + 1 }, (_, i) => i / (rows * 4) * 100);

    // Calculate dimensions for correct fit/fill when rotated
    const getImgStyle = () => {
        const baseTransform = [
            `rotate(${rotation}deg)`,
            `scaleX(${flipHorizontal ? -1 : 1})`,
            `scaleY(${flipVertical ? -1 : 1})`,
        ].join(" ");

        if (!imageDimensions) return { transform: baseTransform, width: '100%', height: '100%' };

        const isRotated = rotation % 180 !== 0;

        // Container Aspect Ratio (A4 Grid)
        // A4 ratio is ~1.414 (210/297) -> But wait, rows/cols logic:
        // Width proportional to Cols * 210, Height proportional to Rows * 297.
        // Aspect = (Cols * 210) / (Rows * 297)
        const containerAspect = (cols * 210) / (rows * 297);

        // Image Aspect Ratio
        const imgAspect = imageDimensions.width / imageDimensions.height;
        // Effective Aspect Ratio after rotation
        const effAspect = isRotated ? (1 / imgAspect) : imgAspect;

        // If we rely on CSS object-fit for non-rotated, it works fine. 
        // But for rotated, we must force dimensions to escape the object-fit constraints on the wrong axis.

        // Actually, let's implement manual calculation for ALL cases to be consistent and safe against the object-fit + rotation bug.

        let targetW, targetH;

        if (resizeMode === "maintain") {
            // FIT behavior
            if (effAspect > containerAspect) {
                // Image is wider than container -> constraint by Width
                // Visual Width = 100%
                // Visual Height = 1/effAspect (relative to width? No relative to container?)
                // Let's work in % of container.
                // Visual Width = 100%
                // Visual Height = 100% / containerAspect / effAspect? No.
                // H_vis = W_vis / effAspect.
                // W_vis = 100% (of container width)
                // H_vis = (100% * container_width) / effAspect
                // H_vis% = 100% * (W_cont/H_cont) / effAspect = 100% * containerAspect / effAspect

                // If rotated 90deg, we assign:
                // img.height = Visual Width = 100%
                // img.width = Visual Height = 100% * containerAspect / effAspect
                if (isRotated) {
                    return {
                        width: `${100 * containerAspect / effAspect}%`,
                        height: '100%',
                        transform: baseTransform,
                        objectFit: "fill" as const // We force size, so fill just stretches to our calculated box (which preserves ratio)
                    };
                } else {
                    return {
                        width: '100%',
                        height: `${100 * containerAspect / effAspect}%`,
                        transform: baseTransform,
                        objectFit: "fill" as const
                    };
                }
            } else {
                // Image is taller -> constraint by Height
                // Visual Height = 100%
                // Visual Width = H_vis * effAspect
                // W_vis% = 100% / containerAspect * effAspect
                if (isRotated) {
                    return {
                        width: '100%',
                        height: `${100 / containerAspect * effAspect}%`,
                        transform: baseTransform,
                        objectFit: "fill" as const
                    };
                } else {
                    return {
                        width: `${100 / containerAspect * effAspect}%`,
                        height: '100%',
                        transform: baseTransform,
                        objectFit: "fill" as const
                    };
                }
            }
        } else {
            // CROP (Fill) behavior
            // Inverse logic of Maintain.
            // If effAspect > containerAspect (Wider): Match Height (100%), Let Width overflow.
            if (effAspect > containerAspect) {
                if (isRotated) {
                    return {
                        width: '100%', // Visual height matches container height
                        height: `${100 / containerAspect * effAspect}%`, // Visual width overflows
                        transform: baseTransform,
                        objectFit: "cover" as const
                    };
                } else {
                    // Standard case, object-cover works fine usually, but let's be explicit
                    // Match Height (100%), Width overflows
                    return {
                        width: 'auto',
                        height: '100%',
                        minWidth: '100%',
                        transform: baseTransform,
                        objectFit: "cover" as const
                    };
                }
            } else {
                // Taller: Match Width (100%), Let Height overflow.
                if (isRotated) {
                    return {
                        width: `${100 * containerAspect / effAspect}%`,
                        height: '100%',
                        transform: baseTransform,
                        objectFit: "cover" as const
                    };
                } else {
                    return {
                        width: '100%',
                        height: 'auto',
                        minHeight: '100%',
                        transform: baseTransform,
                        objectFit: "cover" as const
                    };
                }
            }
        }
    };

    // Simple fallback for object-cover if manual calc is complex or we want standard behavior for non-rotated
    // But consistent manual calc is safer for rotation.

    const imgStyle = getImgStyle();

    return (
        <div className={clsx(
            "relative rounded-lg overflow-hidden shadow-2xl border transition-colors duration-300 flex items-center justify-center", // Added flex center to center the sized image
            resizeMode === "maintain" ? "bg-white border-gray-200" : "bg-[#1a1a1a] border-white/20",
            className
        )}>
            {/* Background Image */}
            <div className="absolute inset-0 flex items-center justify-center m-[1px] overflow-hidden">
                <Image
                    src={imageUrl}
                    alt="Grid Preview"
                    fill={false} // Disable fill, we control size
                    width={imageDimensions?.width || 1000} // Values don't matter much if styles override, but needed for next/image
                    height={imageDimensions?.height || 1000}
                    className="transition-transform duration-300 ease-in-out"
                    style={imgStyle}
                    unoptimized
                />
            </div>

            {/* Grid Overlay */}
            <div className="absolute inset-0 pointer-events-none z-10">
                <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <filter id="text-shadow">
                            <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="black" floodOpacity="0.8" />
                        </filter>
                    </defs>

                    {/* Ruler Ticks (Top) */}
                    {rulerTicksX.map((x, i) => (
                        <line
                            key={`tx-${i}`}
                            x1={`${x}%`} y1="0"
                            x2={`${x}%`} y2={i % 4 === 0 ? "12px" : "6px"}
                            stroke={resizeMode === "maintain" ? "black" : "white"}
                            strokeWidth={i % 4 === 0 ? "2" : "1"}
                            opacity="0.8"
                        />
                    ))}

                    {/* Ruler Ticks (Left) */}
                    {rulerTicksY.map((y, i) => (
                        <line
                            key={`ty-${i}`}
                            x1="0" y1={`${y}%`}
                            x2={i % 4 === 0 ? "12px" : "6px"} y2={`${y}%`}
                            stroke={resizeMode === "maintain" ? "black" : "white"}
                            strokeWidth={i % 4 === 0 ? "2" : "1"}
                            opacity="0.8"
                        />
                    ))}

                    {/* Vertical Lines (Double stroke for awareness) */}
                    {vLines.map((x, i) => (
                        <g key={`v-${i}`}>
                            <line x1={`${x}%`} y1="0%" x2={`${x}%`} y2="100%" stroke="black" strokeWidth="3" opacity="0.5" />
                            <line x1={`${x}%`} y1="0%" x2={`${x}%`} y2="100%" stroke="#FFD700" strokeWidth="1.5" strokeDasharray="5,5" />
                        </g>
                    ))}

                    {/* Horizontal Lines */}
                    {hLines.map((y, i) => (
                        <g key={`h-${i}`}>
                            <line x1="0%" y1={`${y}%`} x2="100%" y2={`${y}%`} stroke="black" strokeWidth="3" opacity="0.5" />
                            <line x1="0%" y1={`${y}%`} x2="100%" y2={`${y}%`} stroke="#FFD700" strokeWidth="1.5" strokeDasharray="5,5" />
                        </g>
                    ))}
                </svg>

                {/* Page Labels */}
                <div
                    className="absolute inset-0 grid"
                    style={{
                        gridTemplateColumns: `repeat(${cols}, 1fr)`,
                        gridTemplateRows: `repeat(${rows}, 1fr)`
                    }}
                >
                    {Array.from({ length: rows * cols }).map((_, i) => (
                        <div key={i} className="relative flex items-center justify-center border border-white/5">
                            <div className="flex flex-col items-center justify-center">
                                <span className="text-2xl md:text-4xl font-black text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]" style={{ textShadow: "0 0 10px rgba(0,0,0,0.5)" }}>
                                    {i + 1}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
