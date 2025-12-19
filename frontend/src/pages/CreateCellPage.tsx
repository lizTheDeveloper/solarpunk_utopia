import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateCell } from '@/hooks/useCells';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ArrowLeft } from 'lucide-react';

export function CreateCellPage() {
  const navigate = useNavigate();
  const createCellMutation = useCreateCell();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const formData = new FormData(e.currentTarget);
    const data = {
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      location_lat: formData.get('location_lat')
        ? parseFloat(formData.get('location_lat') as string)
        : undefined,
      location_lon: formData.get('location_lon')
        ? parseFloat(formData.get('location_lon') as string)
        : undefined,
      radius_km: formData.get('radius_km')
        ? parseFloat(formData.get('radius_km') as string)
        : 5.0,
      max_members: formData.get('max_members')
        ? parseInt(formData.get('max_members') as string, 10)
        : 50,
    };

    try {
      const cell = await createCellMutation.mutateAsync(data);
      navigate(`/cells/${cell.id}`);
    } catch (err) {
      setError('Failed to create cell. Please try again.');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate('/cells')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Cells
      </button>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create New Cell</h1>
        <p className="text-gray-600 mt-1">
          Start a local community of 5-50 people who can meet in person
        </p>
      </div>

      {/* Form */}
      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Cell Name *
            </label>
            <input
              id="name"
              name="name"
              type="text"
              required
              placeholder="e.g., Downtown Collective, Riverside Neighbors"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Description
            </label>
            <textarea
              id="description"
              name="description"
              rows={4}
              placeholder="What brings this cell together? What are your values and goals?"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
          </div>

          {/* Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="location_lat"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Latitude
              </label>
              <input
                id="location_lat"
                name="location_lat"
                type="number"
                step="any"
                placeholder="e.g., 47.6062"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Optional: Approximate center of your area
              </p>
            </div>
            <div>
              <label
                htmlFor="location_lon"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Longitude
              </label>
              <input
                id="location_lon"
                name="location_lon"
                type="number"
                step="any"
                placeholder="e.g., -122.3321"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
            </div>
          </div>

          {/* Radius */}
          <div>
            <label
              htmlFor="radius_km"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Area Radius (km)
            </label>
            <input
              id="radius_km"
              name="radius_km"
              type="number"
              step="0.1"
              defaultValue="5.0"
              min="0.1"
              max="50"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              How far can members reasonably travel to meet? (5km = ~30 min walk)
            </p>
          </div>

          {/* Max Members */}
          <div>
            <label
              htmlFor="max_members"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Maximum Members
            </label>
            <input
              id="max_members"
              name="max_members"
              type="number"
              defaultValue="50"
              min="5"
              max="150"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Keep it small enough that everyone can know each other (Dunbar: ~50 max recommended)
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* Submit */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/cells')}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createCellMutation.isPending}>
              {createCellMutation.isPending ? 'Creating...' : 'Create Cell'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
