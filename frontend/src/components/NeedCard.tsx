import { Intent } from '@/types/valueflows';
import { Card } from './Card';
import { Button } from './Button';
import { MapPin, Calendar, Package, Edit, Trash2 } from 'lucide-react';
import { formatTimeAgo, formatQuantity, formatDate } from '@/utils/formatters';

interface NeedCardProps {
  need: Intent;
  onFulfill?: (need: Intent) => void;
  onEdit?: (need: Intent) => void;
  onDelete?: (need: Intent) => void;
  showActions?: boolean;
  isOwner?: boolean;
}

export function NeedCard({ need, onFulfill, onEdit, onDelete, showActions = true, isOwner = false }: NeedCardProps) {
  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this need? This action cannot be undone.')) {
      onDelete?.(need);
    }
  };

  return (
    <Card hoverable>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-base sm:text-lg text-gray-900 break-words">
              {need.resource_specification?.name || 'Unknown Resource'}
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Needed by {need.agent?.name || 'Unknown'}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {need.status}
            </span>
            {isOwner && showActions && (
              <div className="flex gap-1">
                {onEdit && (
                  <button
                    onClick={() => onEdit(need)}
                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Edit need"
                    aria-label={`Edit need: ${need.resource_specification?.name || 'Unknown Resource'}`}
                  >
                    <Edit className="w-4 h-4" aria-hidden="true" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={handleDelete}
                    className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete need"
                    aria-label={`Delete need: ${need.resource_specification?.name || 'Unknown Resource'}`}
                  >
                    <Trash2 className="w-4 h-4" aria-hidden="true" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Package className="w-4 h-4 flex-shrink-0" />
            <span>{formatQuantity(need.quantity, need.unit)}</span>
          </div>
          {need.location && (
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4 flex-shrink-0" />
              <span className="truncate max-w-[150px] sm:max-w-none">{need.location}</span>
            </div>
          )}
        </div>

        {(need.available_from || need.available_until) && (
          <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600">
            <Calendar className="w-4 h-4 flex-shrink-0" />
            <span className="break-words">
              {need.available_from && `From ${formatDate(need.available_from)}`}
              {need.available_from && need.available_until && ' - '}
              {need.available_until && `Until ${formatDate(need.available_until)}`}
            </span>
          </div>
        )}

        {need.note && (
          <p className="text-xs sm:text-sm text-gray-700 border-l-4 border-blue-300 pl-3 italic break-words">
            {need.note}
          </p>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mt-2">
          <span className="text-xs text-gray-500">
            Posted {formatTimeAgo(need.created_at)}
          </span>
          {showActions && onFulfill && need.status === 'active' && (
            <Button size="sm" onClick={() => onFulfill(need)} className="w-full sm:w-auto">
              Fulfill Need
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
