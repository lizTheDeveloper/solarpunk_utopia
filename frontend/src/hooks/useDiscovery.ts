import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { discoveryApi } from '@/api/discovery';
import type { SearchQuery, IndexEntry } from '@/types/discovery';

export function useSearch(query: SearchQuery) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () => discoveryApi.search(query),
    enabled: !!query.query && query.query.length >= 2,
  });
}

export function useQuickSearch(queryString: string) {
  return useQuery({
    queryKey: ['search', queryString],
    queryFn: () => discoveryApi.quickSearch(queryString),
    enabled: !!queryString && queryString.length >= 2,
  });
}

export function useIndexStats() {
  return useQuery({
    queryKey: ['index-stats'],
    queryFn: () => discoveryApi.getIndexStats(),
  });
}

export function useLocalIndex() {
  return useQuery({
    queryKey: ['local-index'],
    queryFn: () => discoveryApi.getLocalIndex(),
  });
}

export function useAddIndexEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entry: Omit<IndexEntry, 'id' | 'created_at'>) =>
      discoveryApi.addIndexEntry(entry),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['local-index'] });
      queryClient.invalidateQueries({ queryKey: ['index-stats'] });
    },
  });
}

export function useSyncIndexes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => discoveryApi.syncIndexes(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['index-stats'] });
    },
  });
}
