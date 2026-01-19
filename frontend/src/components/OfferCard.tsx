import { Intent } from '@/types/valueflows';
import { toast } from 'sonner';
import { Card } from './Card';
import { Button } from './Button';
import { MapPin, Calendar, Package, Edit, Trash2, Clock } from 'lucide-react';
import { formatTimeAgo, formatQuantity, formatDate } from '@/utils/formatters';

interface OfferCardProps {
  offer: Intent;
  onAccept?: (offer: Intent) => void;
  onEdit?: (offer: Intent) => void;
  onDelete?: (offer: Intent) => void;
  showActions?: boolean;
  isOwner?: boolean;
}

type UrgencyLevel = 'critical' | 'high' | 'medium' | null;

function calculateUrgency(availableUntil?: string): { level: UrgencyLevel; hoursRemaining: number | null; message: string | null } {
  if (!availableUntil) {
    return { level: null, hoursRemaining: null, message: null };
  }

  const now = new Date();
  const expiryDate = new Date(availableUntil);
  const hoursRemaining = (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60);

  if (hoursRemaining < 0) {
    return { level: 'critical', hoursRemaining: 0, message: 'Expired' };
  } else if (hoursRemaining < 24) {
    return { level: 'critical', hoursRemaining, message: `${Math.floor(hoursRemaining)}h remaining` };
  } else if (hoursRemaining < 72) {
    return { level: 'high', hoursRemaining, message: `${Math.floor(hoursRemaining / 24)}d remaining` };
  } else if (hoursRemaining < 168) { // 7 days
    return { level: 'medium', hoursRemaining, message: `${Math.floor(hoursRemaining / 24)}d remaining` };
  }

  return { level: null, hoursRemaining, message: null };
}

export function OfferCard({ offer, onAccept, onEdit, onDelete, showActions = true, isOwner = false }: OfferCardProps) {
  const handleDelete = () => {
    toast.warning('Are you sure you want to delete this offer?', {
      description: 'This action cannot be undone.',
      action: {
        label: 'Delete',
        onClick: () => onDelete?.(offer),
      },
      cancel: {
        label: 'Cancel',
        onClick: () => {}, // Dismiss toast
      },
    });
  };

  const urgency = calculateUrgency(offer.available_until);

  return (
    <Card hoverable>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-base sm:text-lg text-gray-900 break-words">
              {offer.resource_specification?.name || 'Unknown Resource'}
            </h3>
            <p className="text-xs sm:text-sm text-gray-600">
              Offered by {offer.agent?.name || 'Unknown'}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {urgency.level && (
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1 ${
                  urgency.level === 'critical'
                    ? 'bg-red-100 text-red-800'
                    : urgency.level === 'high'
                    ? 'bg-orange-100 text-orange-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                <Clock className="w-3 h-3" />
                {urgency.message}
              </span>
            )}
            <span className="px-3 py-1 bg-solarpunk-100 text-solarpunk-800 rounded-full text-sm font-medium">
              {offer.status}
            </span>
            {isOwner && showActions && (
              <div className="flex gap-1">
                {onEdit && (
                  <button
                    onClick={() => onEdit(offer)}
                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Edit offer"
                    aria-label={`Edit offer: ${offer.resource_specification?.name || 'Unknown Resource'}`}
                  >
                    <Edit className="w-4 h-4" aria-hidden="true" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={handleDelete}
                    className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete offer"
                    aria-label={`Delete offer: ${offer.resource_specification?.name || 'Unknown Resource'}`}
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
            <span>{formatQuantity(offer.quantity, offer.unit)}</span>
          </div>
          {offer.location && (
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4 flex-shrink-0" />
              <span className="truncate max-w-[150px] sm:max-w-none">{offer.location}</span>
            </div>
          )}
        </div>

        {(offer.available_from || offer.available_until) && (
          <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600">
            <Calendar className="w-4 h-4 flex-shrink-0" />
            <span className="break-words">
              {offer.available_from && `From ${formatDate(offer.available_from)}`}
              {offer.available_from && offer.available_until && ' - '}
              {offer.available_until && `Until ${formatDate(offer.available_until)}`}
            </span>
          </div>
        )}

        {offer.note && (
          <p className="text-xs sm:text-sm text-gray-700 border-l-4 border-solarpunk-300 pl-3 italic break-words">
            {offer.note}
          </p>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mt-2">
          <span className="text-xs text-gray-500">
            Posted {formatTimeAgo(offer.created_at)}
          </span>
          {showActions && onAccept && offer.status === 'active' && (
            <Button size="sm" onClick={() => onAccept(offer)} className="w-full sm:w-auto">
              Accept Offer
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
