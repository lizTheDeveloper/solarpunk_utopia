import { Users, MapPin, UserCheck } from 'lucide-react';
import { Card } from './Card';
import type { Cell } from '@/types/cell';

interface CellCardProps {
  cell: Cell;
  onClick?: () => void;
  showActions?: boolean;
}

export function CellCard({ cell, onClick, showActions = false }: CellCardProps) {
  const membershipStatus = cell.is_accepting_members
    ? 'Accepting Members'
    : 'Full';

  const membershipColor = cell.is_accepting_members
    ? 'text-green-600'
    : 'text-gray-500';

  return (
    <Card hoverable onClick={onClick} className="relative">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {cell.name}
            </h3>
            {cell.description && (
              <p className="text-sm text-gray-600 line-clamp-2">
                {cell.description}
              </p>
            )}
          </div>
        </div>

        {/* Info Row */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            <span>{cell.member_count}/{cell.max_members}</span>
          </div>

          {cell.location_lat && cell.location_lon && (
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              <span>~{cell.radius_km}km radius</span>
            </div>
          )}
        </div>

        {/* Status */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-200">
          <div className={`flex items-center gap-1 text-sm font-medium ${membershipColor}`}>
            <UserCheck className="w-4 h-4" />
            <span>{membershipStatus}</span>
          </div>

          {showActions && (
            <button
              className="text-sm text-solarpunk-600 hover:text-solarpunk-700 font-medium"
              onClick={(e) => {
                e.stopPropagation();
                onClick?.();
              }}
            >
              View Details
            </button>
          )}
        </div>
      </div>
    </Card>
  );
}
