/**
 * GAP-61: Community Shelf Page
 *
 * Emma Goldman: "Freedom from surveillance, spontaneous mutual aid"
 *
 * Anonymous gifts - pure generosity without expectation of reciprocity,
 * recognition, or social credit. Take what you need, no questions asked.
 */

import React, { useState, useEffect } from 'react';

interface AnonymousGift {
  id: string;
  title?: string;
  description?: string;
  resource_spec_id: string;
  quantity: number;
  unit: string;
  location_id?: string;
  created_at: string;
}

export const CommunityShelfPage: React.FC = () => {
  const [gifts, setGifts] = useState<AnonymousGift[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string | null>(null);

  useEffect(() => {
    loadGifts();
  }, [category]);

  const loadGifts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.append('category', category);

      const response = await fetch(`http://localhost:8001/vf/listings/community-shelf?${params}`);
      const data = await response.json();

      setGifts(data.gifts || []);
    } catch (error) {
      console.error('Failed to load community shelf:', error);
    } finally {
      setLoading(false);
    }
  };

  const takeGift = async (giftId: string) => {
    // Update status to fulfilled (taken)
    try {
      await fetch(`http://localhost:8001/vf/listings/${giftId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'fulfilled' })
      });

      // Reload gifts
      loadGifts();
    } catch (error) {
      console.error('Failed to take gift:', error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          The Community Shelf
        </h1>
        <p className="text-gray-600">
          "Free love means I can love without the state knowing. Free gifts mean I can give without the database knowing." - Emma Goldman
        </p>
      </div>

      {/* What is this? */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-6 mb-8 rounded">
        <h2 className="font-semibold text-gray-900 mb-2">What are anonymous gifts?</h2>
        <p className="text-gray-700 mb-3">
          These gifts were left here by someone in your community. They chose not to be recognized.
          No social credit. No leaderboards. No "you owe me." Just pure generosity.
        </p>
        <ul className="space-y-1 text-gray-700">
          <li>• <strong>Take what you need</strong> - no one will know it's you</li>
          <li>• <strong>No need to reciprocate</strong> - this is a gift, not a transaction</li>
          <li>• <strong>The giver won't know who took it</strong> - that's intentional</li>
          <li>• <strong>Some gifts can't be counted</strong> - and that's beautiful</li>
        </ul>
      </div>

      {/* Category filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by category:
        </label>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setCategory(null)}
            className={`px-4 py-2 rounded-lg transition ${
              category === null
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            All
          </button>
          {['food', 'tools', 'seeds', 'skills', 'materials', 'other'].map(cat => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-4 py-2 rounded-lg transition capitalize ${
                category === cat
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Gifts grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Loading gifts from the community shelf...
        </div>
      ) : gifts.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <p className="text-gray-500 text-lg mb-4">
            The community shelf is empty right now.
          </p>
          <p className="text-gray-600">
            Want to leave something? When creating an offer, check "Make this an anonymous gift"
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {gifts.map(gift => (
            <div
              key={gift.id}
              className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition overflow-hidden"
            >
              {/* Gift content */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {gift.title || 'Anonymous Gift'}
                  </h3>
                  <span className="text-2xl">🎁</span>
                </div>

                {gift.description && (
                  <p className="text-gray-600 mb-4 line-clamp-3">
                    {gift.description}
                  </p>
                )}

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center">
                    <span className="font-medium">Quantity:</span>
                    <span className="ml-2">{gift.quantity} {gift.unit}</span>
                  </div>

                  <div className="flex items-center">
                    <span className="font-medium">From:</span>
                    <span className="ml-2 italic">Someone in your community</span>
                  </div>

                  <div className="flex items-center text-xs">
                    <span className="text-gray-400">
                      Left {new Date(gift.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Take button */}
              <div className="bg-gray-50 px-6 py-4 border-t border-gray-100">
                <button
                  onClick={() => takeGift(gift.id)}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition font-medium"
                >
                  Take this gift
                </button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  No need to say thank you - the gift is thanks enough
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Philosophy */}
      <div className="mt-12 bg-green-50 border-l-4 border-green-500 p-6 rounded">
        <h3 className="font-semibold text-gray-900 mb-2">Why anonymous gifts matter</h3>
        <div className="space-y-2 text-gray-700 text-sm">
          <p>
            <strong>Resists quantification:</strong> Not everything should be measured and tracked
          </p>
          <p>
            <strong>Protects freedom:</strong> Right to give without surveillance or social pressure
          </p>
          <p>
            <strong>Reduces coercion:</strong> No implicit "you should give back" expectation
          </p>
          <p>
            <strong>Enables dignity:</strong> Those who can't give equally aren't exposed
          </p>
          <p>
            <strong>Preserves mystery:</strong> Some acts of kindness should remain unknown
          </p>
        </div>
        <p className="text-gray-600 italic mt-4">
          "The individual is the heart of society. If individual liberty is ground down by
          collective authority, society becomes a prison." - Emma Goldman
        </p>
      </div>
    </div>
  );
};
