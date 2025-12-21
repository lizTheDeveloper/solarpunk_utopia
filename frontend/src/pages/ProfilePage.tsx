/**
 * Profile Page
 *
 * User profile with rest mode settings (GAP-62)
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { RestModeToggle } from '../components/RestModeToggle';
import { UserStatusBadge } from '../components/UserStatusBadge';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [status, setStatus] = useState<'active' | 'resting' | 'sabbatical'>('active');
  const [statusNote, setStatusNote] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadUserStatus();
    }
  }, [user]);

  const loadUserStatus = async () => {
    try {
      const response = await fetch(`http://localhost:8000/vf/agents/${user.id}`);
      const data = await response.json();

      setStatus(data.status || 'active');
      setStatusNote(data.status_note || '');
    } catch (error) {
      console.error('Failed to load user status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus: string, newNote: string) => {
    try {
      const response = await fetch(`http://localhost:8000/vf/agents/${user.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          status_note: newNote,
          status_updated_at: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update status');
      }

      setStatus(newStatus as any);
      setStatusNote(newNote);
    } catch (error) {
      console.error('Failed to update status:', error);
      throw error;
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-12 text-gray-500">
          Loading profile...
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Your Profile
        </h1>
        <p className="text-gray-600">
          Manage your status and settings
        </p>
      </div>

      {/* Current Status Display */}
      <div className="mb-8">
        {status !== 'active' ? (
          <div className="status-badge inline-block px-4 py-2 rounded-full bg-blue-100 text-blue-800 font-medium">
            {status === 'resting' && 'Resting'}
            {status === 'sabbatical' && 'Sabbatical'}
          </div>
        ) : (
          <div className="status-badge inline-block px-4 py-2 rounded-full bg-green-100 text-green-800 font-medium">
            Active
          </div>
        )}
        {statusNote && (
          <p className="mt-2 text-gray-600 italic">"{statusNote}"</p>
        )}
      </div>

      {/* User Info */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>
        <div className="space-y-3">
          <div>
            <span className="text-sm font-medium text-gray-700">Name:</span>
            <span className="ml-2 text-gray-900">{user?.name || 'Anonymous'}</span>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-700">User ID:</span>
            <span className="ml-2 text-gray-600 font-mono text-sm">{user?.id}</span>
          </div>
        </div>
      </div>

      {/* Rest Mode Settings */}
      <RestModeToggle
        currentStatus={status}
        statusNote={statusNote}
        onUpdate={handleStatusUpdate}
      />
    </div>
  );
};
