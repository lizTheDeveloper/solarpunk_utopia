// File Chunking System types

export interface FileChunk {
  id: string;
  file_id: string;
  chunk_index: number;
  total_chunks: number;
  data: string; // base64 encoded
  hash: string;
  size_bytes: number;
}

export interface FileManifest {
  id: string;
  filename: string;
  total_size: number;
  total_chunks: number;
  chunk_size: number;
  mime_type: string;
  hash: string;
  created_at: string;
  created_by: string;
  category?: string;
  description?: string;
  keywords?: string[];
  metadata?: Record<string, any>;
}

export interface FileDownload {
  file_id: string;
  manifest: FileManifest;
  chunks_downloaded: number;
  chunks_total: number;
  bytes_downloaded: number;
  bytes_total: number;
  status: 'downloading' | 'completed' | 'failed' | 'paused';
  started_at: string;
  completed_at?: string;
  error?: string;
}

export interface FileUpload {
  file_id: string;
  filename: string;
  total_size: number;
  chunks_uploaded: number;
  chunks_total: number;
  status: 'uploading' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  error?: string;
}

export interface UploadFileRequest {
  file: File;
  category?: string;
  description?: string;
  keywords?: string[];
}

export interface FileStats {
  total_files: number;
  total_chunks: number;
  total_bytes: number;
  files_by_category: Record<string, number>;
}

export interface AvailableFile {
  manifest: FileManifest;
  availability: number; // 0-1, percentage of chunks available
  sources: string[]; // node IDs that have chunks
}
