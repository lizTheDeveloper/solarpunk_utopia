import { useState } from 'react';
import { useExchanges, useMatches, useCompleteExchange } from '@/hooks/useExchanges';
import { useAuth } from '@/contexts/AuthContext';
import { Loading } from '@/components/Loading';
import { ErrorMessage } from '@/components/ErrorMessage';
import { Card } from '@/components/Card';
import { MatchCard } from '@/components/MatchCard';
import { EmptyState } from '@/components/EmptyState';
import { ArrowRight, CheckCircle, Clock, Check, ArrowLeftRight } from 'lucide-react';
import { formatTimeAgo, formatQuantity, formatStatus } from '@/utils/formatters';

export function ExchangesPage() {
  const { data: exchanges, isLoading: exchangesLoading, error: exchangesError } = useExchanges();
  const { data: matches, isLoading: matchesLoading } = useMatches();
  const { user } = useAuth();
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const completeExchange = useCompleteExchange();

  const currentUserId = user?.id || 'demo-user';

  const handleComplete = async (exchangeId: string, agentId: string) => {
    try {
      await completeExchange.mutateAsync({ exchangeId, agentId });
    } catch (error) {
      console.error('Failed to complete exchange:', error);
    }
  };

  const filteredExchanges = exchanges?.filter(
    (exchange) => selectedStatus === 'all' || exchange.status === selectedStatus
  ) || [];

  const pendingMatches = matches?.filter(m => m.status === 'proposed') || [];

  if (exchangesError) {
    return <ErrorMessage message="Failed to load exchanges. Please try again later." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Exchanges</h1>
        <p className="text-gray-600 mt-1">Track your exchanges and see what's happening in the community</p>
      </div>

      {/* Pending Matches */}
      {!matchesLoading && pendingMatches.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Pending Matches</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {pendingMatches.map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Status:</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-solarpunk-500 focus:border-solarpunk-500"
          >
            <option value="all">All Statuses</option>
            <option value="proposed">Proposed</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </Card>

      {/* Exchanges List */}
      {exchangesLoading ? (
        <Loading text="Loading exchanges..." />
      ) : filteredExchanges.length > 0 ? (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Showing {filteredExchanges.length} exchange{filteredExchanges.length !== 1 ? 's' : ''}
          </p>
          {filteredExchanges.map((exchange) => (
            <Card key={exchange.id}>
              <div className="flex flex-col gap-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900">{exchange.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {exchange.resource_specification?.name}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    exchange.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : exchange.status === 'in_progress'
                      ? 'bg-blue-100 text-blue-800'
                      : exchange.status === 'cancelled'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {formatStatus(exchange.status)}
                  </span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-solarpunk-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 mb-1">Provider</p>
                    <p className="font-medium text-gray-900">{exchange.provider?.name || 'Unknown'}</p>
                  </div>
                  <ArrowRight className="w-6 h-6 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 bg-blue-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 mb-1">Receiver</p>
                    <p className="font-medium text-gray-900">{exchange.receiver?.name || 'Unknown'}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-gray-600">Quantity: </span>
                    <span className="font-medium text-gray-900">
                      {formatQuantity(exchange.quantity, exchange.unit)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Events: </span>
                    <span className="font-medium text-gray-900">{exchange.events?.length || 0}</span>
                  </div>
                </div>

                {exchange.events && exchange.events.length > 0 && (
                  <div className="pt-3 border-t">
                    <p className="text-sm font-medium text-gray-700 mb-2">Recent Events</p>
                    <div className="space-y-2">
                      {exchange.events.slice(0, 3).map((event) => (
                        <div key={event.id} className="flex items-center gap-2 text-sm">
                          {event.action === 'transfer' ? (
                            <CheckCircle className="w-4 h-4 text-green-600" />
                          ) : event.action === 'accept' ? (
                            <CheckCircle className="w-4 h-4 text-blue-600" />
                          ) : (
                            <Clock className="w-4 h-4 text-gray-600" />
                          )}
                          <span className="text-gray-700">
                            {formatStatus(event.action)} - {formatTimeAgo(event.timestamp)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Completion Buttons */}
                {exchange.status !== 'completed' && exchange.status !== 'cancelled' && (
                  <div className="pt-3 border-t">
                    <p className="text-sm font-medium text-gray-700 mb-3">Mark as Complete</p>
                    <div className="flex gap-3">
                      {/* Provider button */}
                      {exchange.provider_id === currentUserId && (
                        <button
                          onClick={() => handleComplete(exchange.id, exchange.provider_id)}
                          disabled={exchange.provider_completed || completeExchange.isPending}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                            exchange.provider_completed
                              ? 'bg-green-100 text-green-800 cursor-not-allowed'
                              : 'bg-solarpunk-600 text-white hover:bg-solarpunk-700'
                          }`}
                        >
                          {exchange.provider_completed ? (
                            <>
                              <Check className="w-4 h-4" />
                              Provider Confirmed
                            </>
                          ) : (
                            <>
                              <Check className="w-4 h-4" />
                              Confirm as Provider
                            </>
                          )}
                        </button>
                      )}

                      {/* Receiver button */}
                      {exchange.receiver_id === currentUserId && (
                        <button
                          onClick={() => handleComplete(exchange.id, exchange.receiver_id)}
                          disabled={exchange.receiver_completed || completeExchange.isPending}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                            exchange.receiver_completed
                              ? 'bg-green-100 text-green-800 cursor-not-allowed'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {exchange.receiver_completed ? (
                            <>
                              <Check className="w-4 h-4" />
                              Receiver Confirmed
                            </>
                          ) : (
                            <>
                              <Check className="w-4 h-4" />
                              Confirm as Receiver
                            </>
                          )}
                        </button>
                      )}
                    </div>
                    {(exchange.provider_completed || exchange.receiver_completed) && (
                      <p className="text-xs text-gray-600 mt-2">
                        {exchange.provider_completed && exchange.receiver_completed
                          ? '🎉 Both parties have confirmed! Exchange complete.'
                          : exchange.provider_completed
                          ? 'Provider confirmed. Waiting for receiver...'
                          : 'Receiver confirmed. Waiting for provider...'}
                      </p>
                    )}
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  Created {formatTimeAgo(exchange.created_at)}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <EmptyState
            icon={<ArrowLeftRight className="w-16 h-16" />}
            title={selectedStatus !== 'all'
              ? `No ${selectedStatus.charAt(0).toUpperCase() + selectedStatus.slice(1)} Exchanges Found`
              : "No Exchanges Yet"}
            description={selectedStatus !== 'all'
              ? "Try selecting a different status filter or browse all exchanges."
              : "Exchanges happen when offers meet needs. Create an offer or express a need to get started!"}
            primaryAction={selectedStatus !== 'all'
              ? { label: "Clear Filters", onClick: () => setSelectedStatus('all') }
              : { label: "Create an Offer", href: "/offers/create" }}
            secondaryAction={selectedStatus === 'all'
              ? { label: "Express a Need", href: "/needs/create" }
              : undefined}
          />
        </Card>
      )}
    </div>
  );
}
