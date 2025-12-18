import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateNeed } from '@/hooks/useNeeds';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { ErrorMessage } from '@/components/ErrorMessage';
import { RESOURCE_CATEGORIES, COMMON_UNITS, COMMON_LOCATIONS } from '@/utils/categories';
import { validateIntentForm } from '@/utils/validation';
import { ArrowLeft } from 'lucide-react';

export function CreateNeedPage() {
  const navigate = useNavigate();
  const createNeed = useCreateNeed();

  const [category, setCategory] = useState('');
  const [subcategory, setSubcategory] = useState('');
  const [item, setItem] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('kg');
  const [location, setLocation] = useState('');
  const [availableFrom, setAvailableFrom] = useState('');
  const [availableUntil, setAvailableUntil] = useState('');
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

  const selectedCategory = RESOURCE_CATEGORIES.find(cat => cat.id === category);
  const subcategories = selectedCategory?.subcategories || [];
  const selectedSubcategory = subcategories.find(sub => sub.id === subcategory);
  const items = selectedSubcategory?.items || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);

    // Create resource specification name
    const resourceName = item || `${category}/${subcategory}`;

    // Validate form
    const validation = validateIntentForm({
      resourceSpecificationId: resourceName,
      quantity: parseFloat(quantity),
      unit,
      location,
    });

    if (!validation.valid) {
      setErrors(validation.errors);
      return;
    }

    try {
      await createNeed.mutateAsync({
        type: 'need',
        agent_id: 'current-user', // Would come from auth context
        resource_specification_id: resourceName,
        quantity: parseFloat(quantity),
        unit,
        location: location || undefined,
        available_from: availableFrom || undefined,
        available_until: availableUntil || undefined,
        note: note || undefined,
      });

      navigate('/needs');
    } catch (error) {
      setErrors(['Failed to create need. Please try again.']);
    }
  };

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
        <h1 className="text-3xl font-bold text-gray-900">Express a Need</h1>
        <p className="text-gray-600 mt-1">Let the community know what you need</p>
      </div>

      {/* Form */}
      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {errors.length > 0 && (
            <ErrorMessage message={errors.join(', ')} />
          )}

          {/* Resource Selection */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">What do you need?</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setSubcategory('');
                  setItem('');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select a category...</option>
                {RESOURCE_CATEGORIES.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            {category && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subcategory *
                </label>
                <select
                  value={subcategory}
                  onChange={(e) => {
                    setSubcategory(e.target.value);
                    setItem('');
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select a subcategory...</option>
                  {subcategories.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {subcategory && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Item *
                </label>
                <select
                  value={item}
                  onChange={(e) => setItem(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select an item...</option>
                  {items.map((itm) => (
                    <option key={itm} value={itm}>
                      {itm}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Quantity */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quantity *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                Needed From
              </label>
              <input
                type="date"
                value={availableFrom}
                onChange={(e) => setAvailableFrom(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Needed Until
              </label>
              <input
                type="date"
                value={availableUntil}
                onChange={(e) => setAvailableUntil(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Any additional details about this need..."
            />
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
              disabled={createNeed.isPending}
              className="flex-1"
            >
              {createNeed.isPending ? 'Creating...' : 'Express Need'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
