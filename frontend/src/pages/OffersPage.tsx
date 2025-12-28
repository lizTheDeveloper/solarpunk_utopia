import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useOffers, useDeleteOffer } from '@/hooks/useOffers';
import { useAuth } from '@/contexts/AuthContext';
import { useCommunity } from '@/contexts/CommunityContext';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { OfferCard } from '@/components/OfferCard';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Plus, Filter, Users, Gift } from 'lucide-react';
import { RESOURCE_CATEGORIES } from '@/utils/categories';
import type { Intent } from '@/types/valueflows';

export function OffersPage() {
  const { data: offers, isLoading, error } = useOffers();
  const deleteOffer = useDeleteOffer();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { currentCommunity } = useCommunity();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'expiring' | 'nearest'>('newest');
  const [viewMode, setViewMode] = useState<'all' | 'mine'>('all');

  const currentUserId = user?.id || 'demo-user';

  // Utility to calculate urgency score (higher = more urgent)
  const calculateUrgencyScore = (availableUntil?: string): number => {
    if (!availableUntil) return 0;
    const now = new Date();
    const expiryDate = new Date(availableUntil);
    const hoursRemaining = (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60);

    if (hoursRemaining < 0) return 1000; // Expired = highest urgency
    if (hoursRemaining < 24) return 100 - hoursRemaining; // 0-24h = very urgent
    if (hoursRemaining < 168) return 50 - (hoursRemaining / 24); // 0-7 days = medium
    return 0; // >7 days = no urgency
  };

  const handleEdit = (offer: Intent) => {
    // Navigate to edit page (could be same as create with ID param)
    navigate(`/offers/${offer.id}/edit`);
  };

  const handleDelete = async (offer: Intent) => {
    try {
      await deleteOffer.mutateAsync(offer.id);
      toast.success('Offer deleted successfully');
    } catch (error) {
      console.error('Failed to delete offer:', error);
      toast.error('Failed to delete offer. Please try again.');
    }
  };

  // Filter and sort offers
  const filteredOffers = (offers?.filter((offer) => {
    const matchesSearch = !searchTerm ||
      offer.resource_specification?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      offer.note?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = selectedCategory === 'all' ||
      offer.resource_specification?.category === selectedCategory;

    const matchesLocation = selectedLocation === 'all' ||
      offer.location === selectedLocation;

    const matchesViewMode = viewMode === 'all' ||
      (viewMode === 'mine' && offer.agent?.id === currentUserId);

    return matchesSearch && matchesCategory && matchesLocation && matchesViewMode && offer.status === 'active';
  }) || []).sort((a, b) => {
    if (sortBy === 'expiring') {
      // Sort by urgency (most urgent first)
      return calculateUrgencyScore(b.available_until) - calculateUrgencyScore(a.available_until);
    } else if (sortBy === 'newest') {
      // Sort by creation date (newest first)
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
    // 'nearest' would require location data - keeping as fallback to newest
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  // Get unique locations
  const locations = Array.from(new Set(offers?.map(o => o.location).filter(Boolean))) as string[];

  // Show network-wide offers if no community selected
  const showCommunityNotice = !currentCommunity;

  if (error) {
    return <ErrorMessage message="Failed to load offers. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Singleton Mode Notice */}
      {showCommunityNotice && (
        <Card className="bg-blue-50 border-blue-200">
          <div className="flex items-start gap-3">
            <Gift className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">Browsing Network-Wide Offers</h3>
              <p className="text-sm text-blue-800 mb-2">
                You're viewing offers from across the entire network. Join a community to see local offers prioritized.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/communities')}
                  className="text-sm text-blue-700 hover:text-blue-900 underline"
                >
                  Browse communities
                </button>
                <span className="text-blue-400">•</span>
                <button
                  onClick={() => navigate('/communities/create')}
                  className="text-sm text-blue-700 hover:text-blue-900 underline"
                >
                  Create a community
                </button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Offers</h1>
          <p className="text-gray-600 mt-1">Browse what others are offering to share</p>
        </div>
        <Link to="/offers/create">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Create Offer
          </Button>
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setViewMode('all')}
          className={`px-6 py-3 font-medium transition-colors ${
            viewMode === 'all'
              ? 'border-b-2 border-solarpunk-500 text-solarpunk-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          All Offers
        </button>
        <button
          onClick={() => setViewMode('mine')}
          className={`px-6 py-3 font-medium transition-colors ${
            viewMode === 'mine'
              ? 'border-b-2 border-solarpunk-500 text-solarpunk-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          My Offers
        </button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Filters</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search offers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            >
              <option value="all">All Categories</option>
              {RESOURCE_CATEGORIES.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            >
              <option value="all">All Locations</option>
              {locations.map((location) => (
                <option key={location} value={location}>
                  {location}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'newest' | 'expiring' | 'nearest')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            >
              <option value="newest">Newest First</option>
              <option value="expiring">Expiring Soon</option>
              <option value="nearest" disabled>Nearest (coming soon)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Results */}
      {isLoading ? (
        <Loading text="Loading offers..." />
      ) : filteredOffers.length > 0 ? (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Showing {filteredOffers.length} offer{filteredOffers.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredOffers.map((offer) => (
              <OfferCard
                key={offer.id}
                offer={offer}
                onEdit={handleEdit}
                onDelete={handleDelete}
                isOwner={offer.agent?.id === currentUserId}
              />
            ))}
          </div>
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">
              {searchTerm || selectedCategory !== 'all' || selectedLocation !== 'all'
                ? 'No offers match your filters.'
                : 'No active offers yet.'}
            </p>
            <Link to="/offers/create">
              <Button>Create the First Offer</Button>
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}
