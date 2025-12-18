import { Bundle } from '@/types/bundles';
import { Package, ArrowRight, Clock, CheckCircle, XCircle } from 'lucide-react';
import { formatTimeAgo, formatBundleId } from '@/utils/formatters';
import { clsx } from 'clsx';

interface BundleStatusProps {
  bundle: Bundle;
  compact?: boolean;
}

export function BundleStatus({ bundle, compact = false }: BundleStatusProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
      case 'expired':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'in_transit':
        return <ArrowRight className="w-4 h-4 text-blue-600 animate-pulse" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'expired':
        return 'bg-red-100 text-red-800';
      case 'in_transit':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm">
        {getStatusIcon(bundle.status)}
        <span className="font-mono text-gray-600">{formatBundleId(bundle.id)}</span>
        <span className={clsx('px-2 py-0.5 rounded text-xs font-medium', getStatusColor(bundle.status))}>
          {bundle.status}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-gray-600" />
          <span className="font-mono text-sm text-gray-900">{formatBundleId(bundle.id)}</span>
        </div>
        <span className={clsx('px-3 py-1 rounded-full text-sm font-medium', getStatusColor(bundle.status))}>
          {bundle.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-600">From</p>
          <p className="font-medium text-gray-900">{bundle.source}</p>
        </div>
        <div>
          <p className="text-gray-600">To</p>
          <p className="font-medium text-gray-900">{bundle.destination}</p>
        </div>
        <div>
          <p className="text-gray-600">Type</p>
          <p className="font-medium text-gray-900">{bundle.payload_type}</p>
        </div>
        <div>
          <p className="text-gray-600">Hops</p>
          <p className="font-medium text-gray-900">{bundle.hop_count || 0}</p>
        </div>
      </div>

      {bundle.route && bundle.route.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs text-gray-600 mb-2">Route</p>
          <div className="flex items-center gap-1 flex-wrap">
            {bundle.route.map((hop, index) => (
              <div key={index} className="flex items-center gap-1">
                <span className="text-xs bg-gray-100 px-2 py-1 rounded">{hop}</span>
                {index < bundle.route!.length - 1 && (
                  <ArrowRight className="w-3 h-3 text-gray-400" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-3 pt-3 border-t text-xs text-gray-500">
        Created {formatTimeAgo(bundle.created_at)}
      </div>
    </div>
  );
}
