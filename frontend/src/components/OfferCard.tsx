import { Intent } from '@/types/valueflows';
import { Card } from './Card';
import { Button } from './Button';
import { MapPin, Calendar, Package } from 'lucide-react';
import { formatTimeAgo, formatQuantity, formatDate } from '@/utils/formatters';

interface OfferCardProps {
  offer: Intent;
  onAccept?: (offer: Intent) => void;
  showActions?: boolean;
}

export function OfferCard({ offer, onAccept, showActions = true }: OfferCardProps) {
  return (
    <Card hoverable>
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-lg text-gray-900">
              {offer.resource_specification?.name || 'Unknown Resource'}
            </h3>
            <p className="text-sm text-gray-600">
              Offered by {offer.agent?.name || 'Unknown'}
            </p>
          </div>
          <span className="px-3 py-1 bg-solarpunk-100 text-solarpunk-800 rounded-full text-sm font-medium">
            {offer.status}
          </span>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Package className="w-4 h-4" />
            <span>{formatQuantity(offer.quantity, offer.unit)}</span>
          </div>
          {offer.location && (
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              <span>{offer.location}</span>
            </div>
          )}
        </div>

        {(offer.available_from || offer.available_until) && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>
              {offer.available_from && `From ${formatDate(offer.available_from)}`}
              {offer.available_from && offer.available_until && ' - '}
              {offer.available_until && `Until ${formatDate(offer.available_until)}`}
            </span>
          </div>
        )}

        {offer.note && (
          <p className="text-sm text-gray-700 border-l-4 border-solarpunk-300 pl-3 italic">
            {offer.note}
          </p>
        )}

        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-gray-500">
            Posted {formatTimeAgo(offer.created_at)}
          </span>
          {showActions && onAccept && offer.status === 'active' && (
            <Button size="sm" onClick={() => onAccept(offer)}>
              Accept Offer
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
