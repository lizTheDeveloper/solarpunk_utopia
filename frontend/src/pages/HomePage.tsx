import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
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
import { EmptyState } from '@/components/EmptyState';
import { Gift, Heart, ArrowLeftRight, Package, AlertCircle } from 'lucide-react';

export function HomePage() {
  const navigate = useNavigate();
  const location = useLocation();

  // GAP-12: Check if onboarding completed, redirect if not
  useEffect(() => {
    // Don't redirect if already on onboarding page (prevent redirect loop)
    if (location.pathname === '/onboarding') return;

    const onboardingCompleted = localStorage.getItem('onboarding_completed');
    if (!onboardingCompleted) {
      navigate('/onboarding', { replace: true });
    }
  }, [navigate, location.pathname]);
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
      <div className="text-center px-2">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-2">
          Welcome to Solarpunk Mesh
        </h1>
        <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto">
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
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-600 flex-shrink-0" />
              <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900">
                AI Proposals Pending Review
              </h2>
            </div>
            <Link to="/agents" className="self-start sm:self-auto">
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
        <div className="flex items-center justify-between gap-2 mb-4">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Recent Offers</h2>
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
            <EmptyState
              icon={<Package className="w-16 h-16" />}
              title="No Active Offers Yet"
              description="Be the first to share resources with your community! Creating an offer helps neighbors find what they need."
              primaryAction={{
                label: "Create an Offer",
                href: "/offers/create"
              }}
              secondaryAction={{
                label: "Browse All Offers",
                href: "/offers"
              }}
            />
          </Card>
        )}
      </div>

      {/* Recent Needs */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-4">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Recent Needs</h2>
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
            <EmptyState
              icon={<Heart className="w-16 h-16" />}
              title="No Active Needs Yet"
              description="Express what you need and let the community help! Creating a need helps neighbors understand how they can support you."
              primaryAction={{
                label: "Express a Need",
                href: "/needs/create"
              }}
              secondaryAction={{
                label: "Browse All Needs",
                href: "/needs"
              }}
            />
          </Card>
        )}
      </div>
    </div>
  );
}
