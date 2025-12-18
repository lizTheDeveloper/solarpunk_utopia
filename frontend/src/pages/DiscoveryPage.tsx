import { useState } from 'react';
import { useQuickSearch, useIndexStats } from '@/hooks/useDiscovery';
import { Loading } from '@/components/Loading';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { Search, Database, TrendingUp, MapPin, Tag } from 'lucide-react';
import { formatTimeAgo } from '@/utils/formatters';

export function DiscoveryPage() {
  const [query, setQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isLoading: searchLoading } = useQuickSearch(searchQuery);
  const { data: indexStats } = useIndexStats();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(query);
  };

  const getSourceBadge = (source: string) => {
    switch (source) {
      case 'local':
        return 'bg-green-100 text-green-800';
      case 'cached':
        return 'bg-blue-100 text-blue-800';
      case 'remote':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Discovery & Search</h1>
        <p className="text-gray-600 mt-1">
          Search across the distributed network for offers, needs, and resources
        </p>
      </div>

      {/* Index Stats */}
      {indexStats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-solarpunk-600" />
              <div>
                <p className="text-sm text-gray-600">Local Entries</p>
                <p className="text-2xl font-bold text-gray-900">{indexStats.local_entries}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Cached Indexes</p>
                <p className="text-2xl font-bold text-gray-900">{indexStats.cached_indexes}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <Search className="w-8 h-8 text-purple-600" />
              <div>
                <p className="text-sm text-gray-600">Total Searchable</p>
                <p className="text-2xl font-bold text-gray-900">{indexStats.total_searchable_entries}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Search Form */}
      <Card>
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for offers, needs, resources, or files..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
          </div>
          <Button type="submit" disabled={!query || query.length < 2}>
            Search
          </Button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Searches local index and cached indexes from nearby nodes
        </p>
      </Card>

      {/* Search Results */}
      {searchQuery && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Search Results for "{searchQuery}"
          </h2>

          {searchLoading ? (
            <Loading text="Searching distributed indexes..." />
          ) : searchResults && searchResults.results.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Found {searchResults.total_results} result{searchResults.total_results !== 1 ? 's' : ''} in{' '}
                  {searchResults.search_time_ms}ms
                </p>
                <p className="text-sm text-gray-600">
                  Searched {searchResults.sources_searched.length} source{searchResults.sources_searched.length !== 1 ? 's' : ''}
                </p>
              </div>

              <div className="space-y-3">
                {searchResults.results.map((result, index) => (
                  <Card key={index} hoverable>
                    <div className="flex flex-col gap-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-lg text-gray-900">
                            {result.entry.title}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {result.entry.description}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getSourceBadge(result.source)}`}>
                            {result.source}
                          </span>
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium">
                            {result.entry.type}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        {result.entry.category && (
                          <div className="flex items-center gap-1">
                            <Tag className="w-4 h-4" />
                            <span>{result.entry.category}</span>
                          </div>
                        )}
                        {result.entry.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            <span>{result.entry.location}</span>
                          </div>
                        )}
                      </div>

                      {result.entry.keywords && result.entry.keywords.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap">
                          {result.entry.keywords.map((keyword, i) => (
                            <span
                              key={i}
                              className="px-2 py-1 bg-solarpunk-50 text-solarpunk-700 rounded text-xs"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t">
                        <span>Created {formatTimeAgo(result.entry.created_at)}</span>
                        <div className="flex items-center gap-4">
                          <span>Score: {(result.score * 100).toFixed(0)}%</span>
                          {result.source_node && (
                            <span className="font-mono">{result.source_node.slice(0, 8)}...</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <div className="text-center py-12">
                <p className="text-gray-600">No results found for "{searchQuery}"</p>
                <p className="text-sm text-gray-500 mt-2">
                  Try different search terms or check back later as indexes sync
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Info */}
      {!searchQuery && (
        <Card>
          <div className="text-center py-8">
            <Search className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">
              Distributed Search
            </h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Search across your local index and cached indexes from nearby nodes. Results show
              where the information came from and how recently it was synced.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
