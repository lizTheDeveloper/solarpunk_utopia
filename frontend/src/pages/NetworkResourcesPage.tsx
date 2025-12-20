import { useState, useEffect } from 'react';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { ErrorMessage } from '@/components/ErrorMessage';
import { discoverResources, DiscoveryResult, DiscoveryFilters } from '@/api/interCommunitySharing';
import { RESOURCE_CATEGORIES } from '@/utils/categories';
import { Globe, Filter, TrendingUp } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function NetworkResourcesPage() {
  const { user, isAuthenticated } = useAuth();
  const [results, setResults] = useState<DiscoveryResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [resourceType, setResourceType] = useState<'offer' | 'need' | ''>('');
  const [category, setCategory] = useState('');
  const [minTrust, setMinTrust] = useState(0.3);
  const [maxDistance, setMaxDistance] = useState(50);
  const [showFilters, setShowFilters] = useState(false);

  const handleDiscover = async () => {
    if (!user?.id) {
      setError('Please log in to discover resources');
      return;
    }

    setLoading(true);
    setError(null);

    const filters: DiscoveryFilters = {
      user_id: user.id,
      resource_type: resourceType || undefined,
      category: category || undefined,
      max_distance_km: maxDistance,
      min_trust: minTrust,
    };

    try {
      const discoveredResources = await discoverResources(filters);
      setResults(discoveredResources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to discover resources');
    } finally {
      setLoading(false);
    }
  };

  // Auto-discover on mount
  useEffect(() => {
    handleDiscover();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Globe className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Network Resources</h1>
          </div>
          <p className="text-gray-600">
            Browse offerings and needs from across communities based on trust and proximity
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2"
        >
          <Filter className="w-4 h-4" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </Button>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Search Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type
              </label>
              <select
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value as 'offer' | 'need' | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="offer">Offers</option>
                <option value="need">Needs</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {RESOURCE_CATEGORIES.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min Trust: {minTrust.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={minTrust}
                onChange={(e) => setMinTrust(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Higher = stronger trust required
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Distance: {maxDistance}km
              </label>
              <input
                type="range"
                min="5"
                max="200"
                step="5"
                value={maxDistance}
                onChange={(e) => setMaxDistance(parseInt(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum distance to show
              </p>
            </div>
          </div>

          <div className="mt-4 flex justify-end">
            <Button onClick={handleDiscover} disabled={loading}>
              {loading ? 'Searching...' : 'Apply Filters'}
            </Button>
          </div>
        </Card>
      )}

      {/* Error */}
      {error && <ErrorMessage message={error} />}

      {/* Results */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {results.length} {results.length === 1 ? 'Result' : 'Results'} Found
          </h2>
        </div>

        {loading && (
          <Card>
            <p className="text-center text-gray-600 py-8">Discovering resources...</p>
          </Card>
        )}

        {!loading && results.length === 0 && (
          <Card>
            <div className="text-center py-8">
              <Globe className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No resources found matching your criteria.</p>
              <p className="text-gray-500 text-sm mt-2">
                Try adjusting your filters or check back later.
              </p>
            </div>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.map((result) => (
            <Card key={result.listing.id} className="hover:shadow-lg transition-shadow">
              <div className="space-y-3">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`inline-block px-2 py-1 text-xs font-medium rounded ${
                          result.listing.listing_type === 'offer'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {result.listing.listing_type === 'offer' ? 'Offer' : 'Need'}
                      </span>
                      {result.is_cross_community && (
                        <span className="inline-block px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                          Cross-Community
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900">
                      {result.listing.title || result.listing.resource_spec_id}
                    </h3>
                  </div>
                </div>

                {/* Details */}
                <div className="space-y-1 text-sm text-gray-600">
                  <p>
                    <span className="font-medium">Quantity:</span> {result.listing.quantity}{' '}
                    {result.listing.unit}
                  </p>
                  {result.listing.description && (
                    <p className="text-gray-700">{result.listing.description}</p>
                  )}
                </div>

                {/* Metadata */}
                <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t">
                  {result.trust_score !== undefined && (
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      <span>Trust: {(result.trust_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {result.distance_km !== undefined && (
                    <span>~{result.distance_km.toFixed(0)}km away</span>
                  )}
                </div>

                {/* Action */}
                <Button
                  size="sm"
                  className="w-full"
                  onClick={() => {
                    // TODO: Navigate to listing detail or initiate exchange
                    console.log('View listing:', result.listing.id);
                  }}
                >
                  View Details
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
