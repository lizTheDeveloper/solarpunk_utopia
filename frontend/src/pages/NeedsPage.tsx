import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useNeeds, useDeleteNeed } from '@/hooks/useNeeds';
import { useAuth } from '@/contexts/AuthContext';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { NeedCard } from '@/components/NeedCard';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Plus, Filter } from 'lucide-react';
import { RESOURCE_CATEGORIES } from '@/utils/categories';
import type { Intent } from '@/types/valueflows';

export function NeedsPage() {
  const { data: needs, isLoading, error } = useNeeds();
  const deleteNeed = useDeleteNeed();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');

  const currentUserId = user?.id || 'demo-user';

  const handleEdit = (need: Intent) => {
    navigate(`/needs/${need.id}/edit`);
  };

  const handleDelete = async (need: Intent) => {
    try {
      await deleteNeed.mutateAsync(need.id);
    } catch (error) {
      console.error('Failed to delete need:', error);
      alert('Failed to delete need. Please try again.');
    }
  };

  // Filter needs
  const filteredNeeds = needs?.filter((need) => {
    const matchesSearch = !searchTerm ||
      need.resource_specification?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      need.note?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = selectedCategory === 'all' ||
      need.resource_specification?.category === selectedCategory;

    const matchesLocation = selectedLocation === 'all' ||
      need.location === selectedLocation;

    return matchesSearch && matchesCategory && matchesLocation && need.status === 'active';
  }) || [];

  // Get unique locations
  const locations = Array.from(new Set(needs?.map(n => n.location).filter(Boolean))) as string[];

  if (error) {
    return <ErrorMessage message="Failed to load needs. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Needs</h1>
          <p className="text-gray-600 mt-1">See what others need and how you can help</p>
        </div>
        <Link to="/needs/create">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Express a Need
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
              placeholder="Search needs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
        <Loading text="Loading needs..." />
      ) : filteredNeeds.length > 0 ? (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Showing {filteredNeeds.length} need{filteredNeeds.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredNeeds.map((need) => (
              <NeedCard
                key={need.id}
                need={need}
                onEdit={handleEdit}
                onDelete={handleDelete}
                isOwner={need.agent?.id === currentUserId}
              />
            ))}
          </div>
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">
              {searchTerm || selectedCategory !== 'all' || selectedLocation !== 'all'
                ? 'No needs match your filters.'
                : 'No active needs yet.'}
            </p>
            <Link to="/needs/create">
              <Button>Express the First Need</Button>
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}
