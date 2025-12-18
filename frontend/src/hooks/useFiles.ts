import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { filesApi } from '@/api/files';

export function useFileManifests() {
  return useQuery({
    queryKey: ['file-manifests'],
    queryFn: () => filesApi.getManifests(),
  });
}

export function useFileManifest(fileId: string) {
  return useQuery({
    queryKey: ['file-manifests', fileId],
    queryFn: () => filesApi.getManifest(fileId),
    enabled: !!fileId,
  });
}

export function useAvailableFiles() {
  return useQuery({
    queryKey: ['available-files'],
    queryFn: () => filesApi.getAvailableFiles(),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: ['file-stats'],
    queryFn: () => filesApi.getFileStats(),
  });
}

export function useUploadFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      metadata,
    }: {
      file: File;
      metadata?: { category?: string; description?: string; keywords?: string[] };
    }) => filesApi.uploadFile(file, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['file-manifests'] });
      queryClient.invalidateQueries({ queryKey: ['file-stats'] });
    },
  });
}

export function useDownloadFile(fileId: string) {
  return useQuery({
    queryKey: ['file-download', fileId],
    queryFn: () => filesApi.downloadFile(fileId),
    enabled: false, // Manual trigger
  });
}

export function useDownloadProgress(fileId: string) {
  return useQuery({
    queryKey: ['download-progress', fileId],
    queryFn: () => filesApi.getDownloadProgress(fileId),
    enabled: !!fileId,
    refetchInterval: 2000, // Poll every 2 seconds
  });
}

export function useStartDownload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (fileId: string) => filesApi.startDownload(fileId),
    onSuccess: (_, fileId) => {
      queryClient.invalidateQueries({ queryKey: ['download-progress', fileId] });
    },
  });
}

export function useSearchFiles(query: string) {
  return useQuery({
    queryKey: ['search-files', query],
    queryFn: () => filesApi.searchFiles(query),
    enabled: !!query && query.length >= 2,
  });
}
