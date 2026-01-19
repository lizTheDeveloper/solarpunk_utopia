import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateOffer } from '@/hooks/useOffers';
import { useCommunity } from '@/contexts/CommunityContext';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { ErrorMessage } from '@/components/ErrorMessage';
import { VisibilitySelector } from '@/components/VisibilitySelector';
import { COMMON_UNITS, COMMON_LOCATIONS } from '@/utils/categories';
import { ArrowLeft, Gift } from 'lucide-react';

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
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string>('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [location, setLocation] = useState('');
  const [availableFrom, setAvailableFrom] = useState('');
  const [availableUntil, setAvailableUntil] = useState('');
  const [visibility, setVisibility] = useState<'my_cell' | 'my_community' | 'trusted_network' | 'anyone_local' | 'network_wide'>('trusted_network');
  const [anonymous, setAnonymous] = useState(false);  // GAP-61: Emma Goldman
  const [errors, setErrors] = useState<string[]>([]);
  const [success, setSuccess] = useState(false);

  // Optional community notice (not blocking)
  const showCommunityNotice = !currentCommunity;

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPhoto(file);
      // Create preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    // Validate form (simple validation - just need title and quantity)
    if (!title.trim()) {
      setErrors(['Please provide a title']);
      return;
    }

    if (!quantity || parseFloat(quantity) <= 0) {
      setErrors(['Please provide a valid quantity']);
      return;
    }

    // Validate date range
    if (availableFrom && availableUntil) {
      const fromDate = new Date(availableFrom);
      const untilDate = new Date(availableUntil);

      if (untilDate <= fromDate) {
        setErrors(['"Available Until" must be after "Available From"']);
        return;
      }
    }

    try {
      // TODO: Handle photo upload - for now we'll store the base64 in description
      // In production, this should upload to storage service and store URL
      const photoData = photoPreview ? `\n\n[Photo: ${photoPreview.slice(0, 100)}...]` : '';

      await createOffer.mutateAsync({
        listing_type: 'offer',
        agent_id: anonymous ? undefined : user.id, // No agent for anonymous gifts (GAP-61); user exists due to auth check
        anonymous,  // GAP-61: Emma Goldman - anonymous gifts
        title: title,
        resource_spec_id: title, // Use title as resource spec
        quantity: parseFloat(quantity),
        unit,
        location_id: location || undefined,
        available_from: availableFrom || undefined,
        available_until: availableUntil || undefined,
        description: description + photoData,
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
          {showCommunityNotice && (
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
              <div className="flex items-start gap-3">
                <Gift className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-blue-900 mb-1">Posting as a Singleton</h3>
                  <p className="text-sm text-blue-800 mb-2">
                    You're not in a community yet. Your offer will be visible to everyone on the network.
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => navigate('/communities')}
                      className="text-sm text-blue-700 hover:text-blue-900 underline"
                    >
                      Browse communities
                    </button>
                    <span className="text-blue-400">•</span>
                    <button
                      type="button"
                      onClick={() => navigate('/communities/create')}
                      className="text-sm text-blue-700 hover:text-blue-900 underline"
                    >
                      Create a community
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

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
                placeholder="e.g., Fresh Tomatoes, Bicycle Repair Skills, Spare Couch"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Tell us more about what you're offering... condition, how to use it, why you're giving it away..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Photo (optional)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
              {photoPreview && (
                <div className="mt-3">
                  <img
                    src={photoPreview}
                    alt="Preview"
                    className="max-w-xs rounded-lg border-2 border-solarpunk-300"
                  />
                </div>
              )}
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
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
              <p className="text-xs text-gray-500 mt-1">When will this be available?</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Available Until
              </label>
              <input
                type="date"
                value={availableUntil}
                onChange={(e) => setAvailableUntil(e.target.value)}
                min={availableFrom || new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
              />
              <p className="text-xs text-gray-500 mt-1">When does this expire?</p>
            </div>
          </div>

          {/* Visibility */}
          <VisibilitySelector
            value={visibility}
            onChange={(val) => setVisibility(val as any)}
          />

          {/* GAP-61: Anonymous Gift Toggle */}
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded">
            <div className="mb-3 pb-3 border-b border-amber-200">
              <h3 className="font-semibold text-gray-900 mb-1">🎁 What is an Anonymous Gift?</h3>
              <p className="text-sm text-gray-700">
                Anonymous gifts are placed on the community shelf with no tracking. Anyone can take them freely - no names, no records, no social credit. Pure giving.
              </p>
            </div>
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
                  Check this box to give freely without being identified
                </p>
                <p className="text-xs text-gray-500 mt-2 italic">
                  "Free gifts mean I can give without the database knowing." - Emma Goldman
                </p>
                {anonymous && (
                  <>
                    <div className="anonymous-badge mt-3 px-4 py-2 bg-amber-100 border border-amber-300 rounded text-amber-900 font-medium inline-block">
                      🎁 Anonymous Gift
                    </div>
                    <div className="mt-3 space-y-2">
                      <div className="text-sm text-gray-700 space-y-1">
                        <p className="font-medium">How it works:</p>
                        <p>✓ Your name will not appear on the listing</p>
                        <p>✓ Recipients can claim without knowing who you are</p>
                        <p>✓ No record of who takes it</p>
                        <p>✓ Doesn't count toward your stats or reputation</p>
                        <p>✓ You can still manage and cancel your anonymous gifts</p>
                      </div>
                      <div className="text-xs text-gray-600 bg-white bg-opacity-50 p-2 rounded mt-2">
                        <p className="font-medium mb-1">Privacy & Safety:</p>
                        <p>• Community stewards can see your identity for safety and moderation purposes</p>
                        <p>• Anonymous gifts are always visible to your community</p>
                        <p>• Use for giving without recognition or when you want privacy for sensitive items</p>
                      </div>
                    </div>
                  </>
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
