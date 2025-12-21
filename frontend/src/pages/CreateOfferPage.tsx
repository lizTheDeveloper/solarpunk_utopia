import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateOffer } from '@/hooks/useOffers';
import { useCommunity } from '@/contexts/CommunityContext';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { ErrorMessage } from '@/components/ErrorMessage';
import { VisibilitySelector } from '@/components/VisibilitySelector';
import { RESOURCE_CATEGORIES, COMMON_UNITS, COMMON_LOCATIONS } from '@/utils/categories';
import { validateIntentForm } from '@/utils/validation';
import { ArrowLeft } from 'lucide-react';

export function CreateOfferPage() {
  const navigate = useNavigate();
  const createOffer = useCreateOffer();
  const { currentCommunity } = useCommunity();
  const { user, isAuthenticated, loading } = useAuth();

  // Redirect to login if not authenticated (unless anonymous gift)
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/login?redirect=/create-offer');
    }
  }, [loading, isAuthenticated, navigate]);

  // Don't render form if not authenticated
  if (loading) {
    return <div className="max-w-2xl mx-auto p-8 text-center">Loading...</div>;
  }

  if (!isAuthenticated || !user) {
    return null; // Redirect will handle this
  }

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [subcategory, setSubcategory] = useState('');
  const [item, setItem] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [location, setLocation] = useState('');
  const [availableFrom, setAvailableFrom] = useState('');
  const [availableUntil, setAvailableUntil] = useState('');
  const [note, setNote] = useState('');
  const [visibility, setVisibility] = useState<'my_cell' | 'my_community' | 'trusted_network' | 'anyone_local' | 'network_wide'>('trusted_network');
  const [anonymous, setAnonymous] = useState(false);  // GAP-61: Emma Goldman
  const [errors, setErrors] = useState<string[]>([]);
  const [success, setSuccess] = useState(false);

  const selectedCategory = RESOURCE_CATEGORIES.find(cat => cat.id === category);
  const subcategories = selectedCategory?.subcategories || [];
  const selectedSubcategory = subcategories.find(sub => sub.id === subcategory);
  const items = selectedSubcategory?.items || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    // Create resource specification name - prefer item, then title, fallback to category path
    const resourceName = item || title || `${category}/${subcategory}`;

    // Validate form
    if (!resourceName || !quantity) {
      setErrors(['Please provide a resource name and quantity']);
      return;
    }

    try {
      await createOffer.mutateAsync({
        listing_type: 'offer',
        agent_id: anonymous ? undefined : user.id, // No agent for anonymous gifts (GAP-61); user exists due to auth check
        anonymous,  // GAP-61: Emma Goldman - anonymous gifts
        title: title || item,
        resource_spec_id: resourceName,
        quantity: parseFloat(quantity),
        unit,
        location_id: location || undefined,
        available_from: availableFrom || undefined,
        available_until: availableUntil || undefined,
        description: description || note || undefined,
        community_id: currentCommunity?.id,
        visibility,
      });

      // Show success message
      setSuccess(true);

      // Navigate after brief delay
      setTimeout(() => {
        if (anonymous) {
          navigate('/community-shelf');
        } else {
          navigate('/offers');
        }
      }, 1500);
    } catch (error) {
      setErrors(['Failed to create offer. Please try again.']);
    }
  };

  // Show success screen
  if (success) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="confirmation success-message bg-green-50 border-l-4 border-green-500 p-6 rounded-lg">
          <h2 className="text-2xl font-bold text-green-900 mb-2">
            {anonymous ? '🎁 Posted to Community Shelf' : '✓ Offer Created!'}
          </h2>
          <p className="text-green-700 mb-4">
            {anonymous
              ? 'Your anonymous gift has been placed on the community shelf. Anyone can take it, no questions asked.'
              : 'Your offer has been posted successfully!'
            }
          </p>
          {anonymous && (
            <div className="text-sm text-green-600 space-y-1">
              <p>• No one will know it's from you</p>
              <p>• No record of who takes it</p>
              <p>• Pure gift, no social credit</p>
            </div>
          )}
          <p className="text-sm text-gray-600 mt-4">
            Redirecting...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Create an Offer</h1>
        <p className="text-gray-600 mt-1">Share what you have to give with the community</p>
      </div>

      {/* Form */}
      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {errors.length > 0 && (
            <ErrorMessage message={errors.join(', ')} />
          )}

          {/* Simple Resource Entry */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">What are you offering?</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Fresh Tomatoes, Bicycle Repair Skills"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resource Type
              </label>
              <select
                name="resource_spec"
                value={item}
                onChange={(e) => setItem(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              >
                <option value="">Select type (optional)...</option>
                <option value="Tomatoes">Tomatoes</option>
                <option value="Tools">Tools</option>
                <option value="Skills">Skills</option>
                <option value="Seeds">Seeds</option>
                <option value="Materials">Materials</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Tell us more about what you're offering..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
            </div>

          </div>

          {/* Quantity */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quantity *
              </label>
              <input
                type="number"
                name="quantity"
                step="0.01"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Unit *
              </label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
                required
              >
                {COMMON_UNITS.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
            >
              <option value="">No specific location</option>
              {COMMON_LOCATIONS.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          {/* Availability */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Available From
              </label>
              <input
                type="date"
                value={availableFrom}
                onChange={(e) => setAvailableFrom(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Available Until
              </label>
              <input
                type="date"
                value={availableUntil}
                onChange={(e) => setAvailableUntil(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
            </div>
          </div>

          {/* Visibility */}
          <VisibilitySelector
            value={visibility}
            onChange={(val) => setVisibility(val as any)}
          />

          {/* GAP-61: Anonymous Gift Toggle */}
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                name="anonymous"
                checked={anonymous}
                onChange={(e) => setAnonymous(e.target.checked)}
                className="mt-1 h-5 w-5 text-green-600 rounded focus:ring-green-500"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">Make this an anonymous gift</div>
                <p className="text-sm text-gray-600 mt-1">
                  Leave it on the community shelf. No one will know it's from you.
                </p>
                <p className="text-xs text-gray-500 mt-2 italic">
                  "Free gifts mean I can give without the database knowing." - Emma Goldman
                </p>
                {anonymous && (
                  <div className="anonymous-badge mt-3 px-4 py-2 bg-amber-100 border border-amber-300 rounded text-amber-900 font-medium inline-block">
                    🎁 Anonymous Gift
                  </div>
                )}
                {anonymous && (
                  <div className="mt-3 space-y-1 text-sm text-gray-700">
                    <p>✓ Anyone can take it</p>
                    <p>✓ No record of who took it</p>
                    <p>✓ Doesn't count toward your "stats"</p>
                    <p>✓ Pure gift, no social credit</p>
                  </div>
                )}
              </div>
            </label>
          </div>


          {/* Actions */}
          <div className="flex gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate(-1)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createOffer.isPending}
              className="flex-1"
            >
              {createOffer.isPending ? 'Creating...' : 'Create Offer'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
