// File Chunking API Client
import axios from 'axios';
import type {
  FileManifest,
  FileChunk,
  FileDownload,
  FileStats,
  AvailableFile,
} from '@/types/files';

const api = axios.create({
  baseURL: '/api/files',
});

export const filesApi = {
  // Upload file
  uploadFile: async (
    file: File,
    metadata?: {
      category?: string;
      description?: string;
      keywords?: string[];
    }
  ): Promise<FileManifest> => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata?.category) formData.append('category', metadata.category);
    if (metadata?.description) formData.append('description', metadata.description);
    if (metadata?.keywords) formData.append('keywords', JSON.stringify(metadata.keywords));

    const response = await api.post<FileManifest>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get all file manifests
  getManifests: async (): Promise<FileManifest[]> => {
    const response = await api.get<FileManifest[]>('/manifests');
    return response.data;
  },

  // Get specific manifest
  getManifest: async (fileId: string): Promise<FileManifest> => {
    const response = await api.get<FileManifest>(`/manifests/${fileId}`);
    return response.data;
  },

  // Get available files (files on the network)
  getAvailableFiles: async (): Promise<AvailableFile[]> => {
    const response = await api.get<AvailableFile[]>('/available');
    return response.data;
  },

  // Download file
  downloadFile: async (fileId: string): Promise<Blob> => {
    const response = await api.get(`/download/${fileId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Get download progress
  getDownloadProgress: async (fileId: string): Promise<FileDownload> => {
    const response = await api.get<FileDownload>(`/downloads/${fileId}`);
    return response.data;
  },

  // Start download
  startDownload: async (fileId: string): Promise<FileDownload> => {
    const response = await api.post<FileDownload>(`/downloads/${fileId}/start`);
    return response.data;
  },

  // Get specific chunk
  getChunk: async (fileId: string, chunkIndex: number): Promise<FileChunk> => {
    const response = await api.get<FileChunk>(`/files/${fileId}/chunks/${chunkIndex}`);
    return response.data;
  },

  // Get all chunks for a file
  getChunks: async (fileId: string): Promise<FileChunk[]> => {
    const response = await api.get<FileChunk[]>(`/files/${fileId}/chunks`);
    return response.data;
  },

  // Get file stats
  getFileStats: async (): Promise<FileStats> => {
    const response = await api.get<FileStats>('/stats');
    return response.data;
  },

  // Delete file
  deleteFile: async (fileId: string): Promise<void> => {
    await api.delete(`/files/${fileId}`);
  },

  // Search files
  searchFiles: async (query: string): Promise<FileManifest[]> => {
    const response = await api.get<FileManifest[]>(`/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },
};
