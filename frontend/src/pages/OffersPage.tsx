import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useOffers } from '@/hooks/useOffers';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { OfferCard } from '@/components/OfferCard';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Plus, Filter } from 'lucide-react';
import { RESOURCE_CATEGORIES } from '@/utils/categories';

export function OffersPage() {
  const { data: offers, isLoading, error } = useOffers();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');

  // Filter offers
  const filteredOffers = offers?.filter((offer) => {
    const matchesSearch = !searchTerm ||
      offer.resource_specification?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      offer.note?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = selectedCategory === 'all' ||
      offer.resource_specification?.category === selectedCategory;

    const matchesLocation = selectedLocation === 'all' ||
      offer.location === selectedLocation;

    return matchesSearch && matchesCategory && matchesLocation && offer.status === 'active';
  }) || [];

  // Get unique locations
  const locations = Array.from(new Set(offers?.map(o => o.location).filter(Boolean))) as string[];

  if (error) {
    return <ErrorMessage message="Failed to load offers. Please try again later." />;
  }

  return (
    <div className="space-y-6">
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

      {/* Filters */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Filters</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <OfferCard key={offer.id} offer={offer} />
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
