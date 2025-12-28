/**
 * GAP-62: Loafer's Rights (Rest Mode Toggle)
 *
 * Emma Goldman + Peter Kropotkin: "The right to be lazy"
 *
 * Allows users to signal they're in rest mode - taking a break from contributing.
 * No guilt trips, no judgment, just space to rest and recover.
 */

import React, { useState } from 'react';
import { toast } from 'sonner';

interface RestModeToggleProps {
  currentStatus: 'active' | 'resting' | 'sabbatical';
  statusNote?: string;
  onUpdate: (status: string, note: string) => Promise<void>;
}

export const RestModeToggle: React.FC<RestModeToggleProps> = ({
  currentStatus,
  statusNote = '',
  onUpdate
}) => {
  const [status, setStatus] = useState(currentStatus);
  const [note, setNote] = useState(statusNote);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onUpdate(status, note);
      setIsEditing(false);
      toast.success('Status updated successfully');
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Rest Mode
      </h3>
      <p className="text-sm text-gray-600 mb-4">
        "The right to be lazy is sacred." - Emma Goldman
      </p>

      {!isEditing ? (
        <>
          {/* Current status display */}
          <div className="mb-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Current status:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                status === 'resting' || status === 'sabbatical'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-green-100 text-green-800'
              }`}>
                {status === 'active' && '🌱 Active'}
                {status === 'resting' && '🌙 Resting'}
                {status === 'sabbatical' && '✨ Sabbatical'}
              </span>
            </div>

            {note && (
              <p className="text-sm text-gray-600 mt-2 italic">
                "{note}"
              </p>
            )}
          </div>

          <button
            data-testid="status-selector"
            onClick={() => setIsEditing(true)}
            className="text-green-600 hover:text-green-700 text-sm font-medium"
          >
            Change status
          </button>
        </>
      ) : (
        <>
          {/* Status selector */}
          <div className="space-y-3 mb-4">
            <button
              type="button"
              onClick={() => setStatus('active')}
              className={`w-full flex items-start space-x-3 p-3 border rounded-lg text-left ${
                status === 'active'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0 mt-1">
                {status === 'active' ? '●' : '○'}
              </div>
              <div>
                <div className="font-medium text-gray-900">🌱 Active</div>
                <div className="text-sm text-gray-600">Participating normally</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setStatus('resting')}
              className={`w-full flex items-start space-x-3 p-3 border rounded-lg text-left ${
                status === 'resting'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0 mt-1">
                {status === 'resting' ? '●' : '○'}
              </div>
              <div>
                <div className="font-medium text-gray-900">🌙 Resting</div>
                <div className="text-sm text-gray-600">
                  Taking a break - no notifications, no pressure
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setStatus('sabbatical')}
              className={`w-full flex items-start space-x-3 p-3 border rounded-lg text-left ${
                status === 'sabbatical'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0 mt-1">
                {status === 'sabbatical' ? '●' : '○'}
              </div>
              <div>
                <div className="font-medium text-gray-900">✨ Sabbatical</div>
                <div className="text-sm text-gray-600">
                  Extended break - will return when ready
                </div>
              </div>
            </button>
          </div>

          {/* Optional note */}
          {(status === 'resting' || status === 'sabbatical') && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Optional note (visible to community):
              </label>
              <textarea
                name="status_note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="e.g., 'Recovering from burnout', 'Caring for sick parent', or just 'Need rest'"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 resize-none"
                rows={3}
              />
              <p className="text-xs text-gray-500 mt-1">
                You can leave this blank. No explanation needed.
              </p>
            </div>
          )}

          {/* Explanation */}
          <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4 rounded">
            <p className="text-sm text-gray-700">
              <strong>What rest mode means:</strong>
            </p>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• No notifications about matches or proposals</li>
              <li>• Profile shows "Taking time to rest"</li>
              <li>• You can still receive gifts if needed</li>
              <li>• No judgment, no timeline to return</li>
              <li>• Rest is resistance to productivity culture</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={() => {
                setStatus(currentStatus);
                setNote(statusNote);
                setIsEditing(false);
              }}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </>
      )}

      {/* Philosophy */}
      {!isEditing && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 italic">
            "Somebody has said that dust is matter in the wrong place. The same can be said
            about persons who are supposed to be wrong people in the right place. There's no
            'wrong' amount to contribute. Rest is not laziness. Needing help is not failure."
            - Emma Goldman
          </p>
        </div>
      )}
    </div>
  );
};
