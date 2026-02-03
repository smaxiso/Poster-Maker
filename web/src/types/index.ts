export interface ImageDimensions {
    width: number;
    height: number;
    aspect_ratio: number;
}

export interface ImageMetadata {
    filename: string;
    original_filename: string;
    format: string;
    size_bytes: number;
    dimensions: ImageDimensions;
    url: string;
    preview_url?: string;
}

export type UploadProgressCallback = (progress: number) => void;

export interface TaskResponse {
    task_id: string;
    status: "queued" | "processing" | "completed" | "failed";
    progress: number;
    message: string;
    result?: {
        pdf_path?: string;
        parts_paths?: string[];
    };
}
