/**
 * Network Impact Widget
 *
 * Shows network-wide aliveness - exchanges happening, people participating.
 * Anti-Reputation Capitalism: No dollar values. The exchange IS the value.
 */

import React, { useState, useEffect } from 'react';

interface NetworkMetrics {
  transaction_count: number;
  active_communities: number;
  active_members: number;
  period_type: string;
  period_start: string;
  period_end: string;
}

interface NetworkImpactWidgetProps {
  periodType?: 'day' | 'week' | 'month' | 'year';
}

export const NetworkImpactWidget: React.FC<NetworkImpactWidgetProps> = ({
  periodType = 'month',
}) => {
  const [metrics, setMetrics] = useState<NetworkMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
  }, [periodType]);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch exchange counts from the exchanges API
      const response = await fetch('/vf/exchanges');
      const data = await response.json();

      if (data.exchanges) {
        // Count exchanges and active participants
        const exchanges = data.exchanges;
        const uniqueAgents = new Set<string>();

        exchanges.forEach((ex: any) => {
          if (ex.provider_id) uniqueAgents.add(ex.provider_id);
          if (ex.receiver_id) uniqueAgents.add(ex.receiver_id);
        });

        setMetrics({
          transaction_count: exchanges.length,
          active_members: uniqueAgents.size,
          active_communities: 1, // TODO: Count actual communities
          period_type: periodType,
          period_start: '',
          period_end: '',
        });
      } else {
        setMetrics(null);
      }
    } catch (err) {
      setError('Failed to load network metrics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="network-impact-widget loading">
        <div className="spinner"></div>
        <p>Loading network impact...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="network-impact-widget error">
        <p>{error}</p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="network-impact-widget no-data">
        <h3>Network Aliveness</h3>
        <p>No exchanges yet. Start sharing!</p>
      </div>
    );
  }

  const formatLargeNumber = (num: number) => {
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`;
    } else if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`;
    }
    return num.toString();
  };

  return (
    <div className="network-impact-widget">
      <div className="header">
        <h3>Network Aliveness</h3>
        <p className="subtitle">
          The exchange IS the celebration. No counting needed.
        </p>
      </div>

      <div className="hero-stat">
        <div className="big-number">
          {formatLargeNumber(metrics.transaction_count)}
        </div>
        <div className="label">
          Exchanges this {periodType}
        </div>
      </div>

      <div className="network-stats">
        <div className="stat-grid">
          <div className="stat-item">
            <div className="icon">🤝</div>
            <div className="value">{formatLargeNumber(metrics.transaction_count)}</div>
            <div className="label">Exchanges</div>
          </div>

          <div className="stat-item">
            <div className="icon">👥</div>
            <div className="value">{formatLargeNumber(metrics.active_members)}</div>
            <div className="label">Active Members</div>
          </div>

          <div className="stat-item">
            <div className="icon">🌱</div>
            <div className="value">{metrics.active_communities}</div>
            <div className="label">Communities</div>
          </div>
        </div>
      </div>

      <div className="impact-message">
        <h4>Is the Network Alive?</h4>
        <div className="impact-facts">
          <div className="fact">
            <span className="bullet">•</span>
            <span className="text">
              {metrics.transaction_count > 0 ? 'Yes - exchanges happening!' : 'Quiet - start sharing!'}
            </span>
          </div>
          <div className="fact">
            <span className="bullet">•</span>
            <span className="text">
              {formatLargeNumber(metrics.active_members)} people participating
            </span>
          </div>
          <div className="fact">
            <span className="bullet">•</span>
            <span className="text">
              Community is {metrics.transaction_count > 10 ? 'thriving' : metrics.transaction_count > 0 ? 'growing' : 'just starting'}
            </span>
          </div>
        </div>
      </div>

      <div className="vision-statement">
        <p>
          Every exchange is a prefiguration of the world we're building. A
          world where we take care of each other, not because there's profit in
          it, but because we're all we've got.
        </p>
        <p className="philosophy-note">
          We don't track dollar values. The gift is the point. Carol doesn't need
          celebration - she was there, she got the joy of sharing.
        </p>
      </div>
    </div>
  );
};

export default NetworkImpactWidget;
