import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCell, useCellMembers, useInviteToCell } from '@/hooks/useCells';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import {
  Users,
  MapPin,
  UserPlus,
  Settings,
  ArrowLeft,
  Shield,
  Calendar,
} from 'lucide-react';

export function CellDetailPage() {
  const { cellId } = useParams<{ cellId: string }>();
  const navigate = useNavigate();
  const [showInviteModal, setShowInviteModal] = useState(false);

  const { data: cell, isLoading, error } = useCell(cellId!);
  const {
    data: members,
    isLoading: loadingMembers,
    error: errorMembers,
  } = useCellMembers(cellId!);

  const inviteMutation = useInviteToCell(cellId!);

  if (error || errorMembers) {
    return <ErrorMessage message="Failed to load cell details. Please try again later." />;
  }

  if (isLoading || loadingMembers) {
    return <Loading />;
  }

  if (!cell) {
    return <ErrorMessage message="Cell not found." />;
  }

  const stewards = members?.filter((m) => m.role === 'steward') || [];
  const regularMembers = members?.filter((m) => m.role === 'member') || [];

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/cells')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Cells
      </button>

      {/* Header */}
      <Card>
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{cell.name}</h1>
            {cell.description && (
              <p className="text-gray-600">{cell.description}</p>
            )}
          </div>
          <Button variant="secondary">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-start gap-3">
            <Users className="w-5 h-5 text-solarpunk-600 mt-1" />
            <div>
              <p className="text-sm text-gray-600">Members</p>
              <p className="text-lg font-semibold text-gray-900">
                {cell.member_count}/{cell.max_members}
              </p>
            </div>
          </div>

          {cell.location_lat && cell.location_lon && (
            <div className="flex items-start gap-3">
              <MapPin className="w-5 h-5 text-solarpunk-600 mt-1" />
              <div>
                <p className="text-sm text-gray-600">Area</p>
                <p className="text-lg font-semibold text-gray-900">
                  {cell.radius_km}km radius
                </p>
              </div>
            </div>
          )}

          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-solarpunk-600 mt-1" />
            <div>
              <p className="text-sm text-gray-600">Created</p>
              <p className="text-lg font-semibold text-gray-900">
                {new Date(cell.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Stewards Section */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Shield className="w-5 h-5 text-solarpunk-600" />
            Stewards
          </h2>
        </div>
        <div className="space-y-2">
          {stewards.length > 0 ? (
            stewards.map((steward) => (
              <div
                key={steward.id}
                className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">User {steward.user_id.slice(0, 8)}</p>
                  <p className="text-sm text-gray-600">
                    Joined {new Date(steward.joined_at).toLocaleDateString()}
                  </p>
                </div>
                <span className="px-3 py-1 bg-solarpunk-100 text-solarpunk-700 rounded-full text-sm font-medium">
                  Steward
                </span>
              </div>
            ))
          ) : (
            <p className="text-gray-600">No stewards yet</p>
          )}
        </div>
      </Card>

      {/* Members Section */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-solarpunk-600" />
            Members ({regularMembers.length})
          </h2>
          {cell.is_accepting_members && (
            <Button onClick={() => setShowInviteModal(true)}>
              <UserPlus className="w-4 h-4 mr-2" />
              Invite Member
            </Button>
          )}
        </div>
        <div className="space-y-2">
          {regularMembers.length > 0 ? (
            regularMembers.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between py-2 px-3 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-900">User {member.user_id.slice(0, 8)}</p>
                  <p className="text-sm text-gray-600">
                    Joined {new Date(member.joined_at).toLocaleDateString()}
                    {member.vouched_by && ` • Vouched by ${member.vouched_by.slice(0, 8)}`}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-600">No members yet</p>
          )}
        </div>
      </Card>

      {/* Invite Modal - Simple version */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Invite Member
            </h2>
            <p className="text-gray-600 mb-4">
              Enter the user ID of the person you want to invite to this cell.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const inviteeId = formData.get('inviteeId') as string;
                inviteMutation.mutate(inviteeId, {
                  onSuccess: () => {
                    setShowInviteModal(false);
                  },
                });
              }}
            >
              <input
                name="inviteeId"
                type="text"
                placeholder="User ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4"
                required
              />
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowInviteModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={inviteMutation.isPending}>
                  {inviteMutation.isPending ? 'Sending...' : 'Send Invite'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
