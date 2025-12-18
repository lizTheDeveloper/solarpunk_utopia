import { Link } from 'react-router-dom';
import { useOffers } from '@/hooks/useOffers';
import { useNeeds } from '@/hooks/useNeeds';
import { useExchanges } from '@/hooks/useExchanges';
import { useNetworkStatus } from '@/hooks/useBridge';
import { useBundleStats } from '@/hooks/useBundles';
import { useProposals } from '@/hooks/useAgents';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { Loading } from '@/components/Loading';
import { NetworkStatus } from '@/components/NetworkStatus';
import { OfferCard } from '@/components/OfferCard';
import { NeedCard } from '@/components/NeedCard';
import { ProposalCard } from '@/components/ProposalCard';
import { Gift, Heart, ArrowLeftRight, Package, AlertCircle } from 'lucide-react';

export function HomePage() {
  const { data: offers, isLoading: offersLoading } = useOffers();
  const { data: needs, isLoading: needsLoading } = useNeeds();
  const { data: exchanges, isLoading: exchangesLoading } = useExchanges();
  const { data: networkStatus } = useNetworkStatus();
  const { data: bundleStats } = useBundleStats();
  const { data: proposals } = useProposals('pending');

  const recentOffers = offers?.slice(0, 3) || [];
  const recentNeeds = needs?.slice(0, 3) || [];
  const pendingProposals = proposals?.slice(0, 3) || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Welcome to Solarpunk Mesh
        </h1>
        <p className="text-lg text-gray-600">
          A gift economy network for resilient communities
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/offers/create">
          <Card hoverable className="h-full">
            <div className="flex items-center gap-4">
              <div className="bg-solarpunk-100 rounded-full p-4">
                <Gift className="w-8 h-8 text-solarpunk-700" />
              </div>
              <div>
                <h3 className="font-semibold text-lg text-gray-900">Create an Offer</h3>
                <p className="text-sm text-gray-600">Share what you have to give</p>
              </div>
            </div>
          </Card>
        </Link>
        <Link to="/needs/create">
          <Card hoverable className="h-full">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 rounded-full p-4">
                <Heart className="w-8 h-8 text-blue-700" />
              </div>
              <div>
                <h3 className="font-semibold text-lg text-gray-900">Express a Need</h3>
                <p className="text-sm text-gray-600">Let others know what you need</p>
              </div>
            </div>
          </Card>
        </Link>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <Gift className="w-8 h-8 text-solarpunk-600" />
            <div>
              <p className="text-sm text-gray-600">Active Offers</p>
              <p className="text-2xl font-bold text-gray-900">
                {offersLoading ? '-' : offers?.filter(o => o.status === 'active').length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <Heart className="w-8 h-8 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Active Needs</p>
              <p className="text-2xl font-bold text-gray-900">
                {needsLoading ? '-' : needs?.filter(n => n.status === 'active').length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <ArrowLeftRight className="w-8 h-8 text-purple-600" />
            <div>
              <p className="text-sm text-gray-600">Exchanges</p>
              <p className="text-2xl font-bold text-gray-900">
                {exchangesLoading ? '-' : exchanges?.length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <Package className="w-8 h-8 text-orange-600" />
            <div>
              <p className="text-sm text-gray-600">Bundles Pending</p>
              <p className="text-2xl font-bold text-gray-900">
                {bundleStats?.total_pending || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Network Status */}
      {networkStatus && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Network Status</h2>
          <NetworkStatus status={networkStatus} />
        </div>
      )}

      {/* Pending AI Proposals */}
      {pendingProposals.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-yellow-600" />
              <h2 className="text-2xl font-bold text-gray-900">
                AI Proposals Pending Review
              </h2>
            </div>
            <Link to="/agents">
              <Button variant="ghost" size="sm">View All</Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {pendingProposals.map((proposal) => (
              <ProposalCard key={proposal.id} proposal={proposal} showActions={false} />
            ))}
          </div>
        </div>
      )}

      {/* Recent Offers */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Recent Offers</h2>
          <Link to="/offers">
            <Button variant="ghost" size="sm">View All</Button>
          </Link>
        </div>
        {offersLoading ? (
          <Loading />
        ) : recentOffers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentOffers.map((offer) => (
              <OfferCard key={offer.id} offer={offer} showActions={false} />
            ))}
          </div>
        ) : (
          <Card>
            <p className="text-gray-600 text-center py-8">
              No active offers yet. Be the first to share!
            </p>
          </Card>
        )}
      </div>

      {/* Recent Needs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Recent Needs</h2>
          <Link to="/needs">
            <Button variant="ghost" size="sm">View All</Button>
          </Link>
        </div>
        {needsLoading ? (
          <Loading />
        ) : recentNeeds.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentNeeds.map((need) => (
              <NeedCard key={need.id} need={need} showActions={false} />
            ))}
          </div>
        ) : (
          <Card>
            <p className="text-gray-600 text-center py-8">
              No active needs yet. Express yours to get started!
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
