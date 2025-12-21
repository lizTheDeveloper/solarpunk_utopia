/**
 * GAP-64: Power Dynamics Dashboard (Bakunin)
 *
 * Monitors and alerts on power concentration in the network.
 * "Vigilance against centralization" - Mikhail Bakunin
 */

import React, { useState, useEffect } from 'react';

interface PowerAlert {
  id: string;
  type: 'resource_concentration' | 'decision_concentration' | 'knowledge_concentration';
  severity: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  affectedAgent?: string;
  affectedResource?: string;
  suggestions: string[];
  createdAt: string;
}

export const PowerDynamicsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<PowerAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<PowerAlert | null>(null);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/power-dynamics/alerts');
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Failed to load power dynamics alerts:', error);
      // Load mock data for demo
      setAlerts([
        {
          id: '1',
          type: 'resource_concentration',
          severity: 'medium',
          title: 'Battery Warlord Alert',
          description: 'High concentration of battery inventory with limited outflow',
          affectedAgent: 'Solar Sam',
          affectedResource: 'lithium_batteries',
          suggestions: [
            'Encourage battery sharing program',
            'Create decentralized battery storage points',
            'Form a battery collective with multiple custodians'
          ],
          createdAt: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 border-red-500 text-red-800';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'low': return 'bg-blue-100 border-blue-500 text-blue-800';
      default: return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Power Dynamics
        </h1>
        <p className="text-gray-600">
          "The people will feel less hungry if they know that the means of satisfying their needs are in their own hands" - Mikhail Bakunin
        </p>
      </div>

      {/* What is this? */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-6 mb-8 rounded">
        <h2 className="font-semibold text-gray-900 mb-2">Why monitor power dynamics?</h2>
        <p className="text-gray-700 mb-3">
          Even in flat structures, power can accumulate. This dashboard helps us notice patterns
          of centralization before they become entrenched.
        </p>
        <ul className="space-y-1 text-gray-700 text-sm">
          <li>• <strong>Resource concentration</strong> - When one person controls too much of a critical resource</li>
          <li>• <strong>Decision concentration</strong> - When the same people always make decisions</li>
          <li>• <strong>Knowledge concentration</strong> - When only a few people know how things work</li>
        </ul>
      </div>

      {/* Alert categories */}
      <div className="mb-6 flex gap-4">
        <div data-alert-type="resource_concentration" className="flex-1 p-4 bg-white border border-gray-200 rounded-lg">
          <h3 className="font-semibold text-gray-900">Resource Concentration</h3>
          <p className="text-sm text-gray-600 mt-1">
            {alerts.filter(a => a.type === 'resource_concentration').length} alerts
          </p>
        </div>
        <div data-alert-type="decision_concentration" className="flex-1 p-4 bg-white border border-gray-200 rounded-lg">
          <h3 className="font-semibold text-gray-900">Decision Concentration</h3>
          <p className="text-sm text-gray-600 mt-1">
            {alerts.filter(a => a.type === 'decision_concentration').length} alerts
          </p>
        </div>
        <div data-alert-type="knowledge_concentration" className="flex-1 p-4 bg-white border border-gray-200 rounded-lg">
          <h3 className="font-semibold text-gray-900">Knowledge Concentration</h3>
          <p className="text-sm text-gray-600 mt-1">
            {alerts.filter(a => a.type === 'knowledge_concentration').length} alerts
          </p>
        </div>
      </div>

      {/* Alerts list */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Loading power dynamics data...
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-12 text-center">
          <p className="text-green-700 text-lg mb-2">
            ✓ No concerning power concentrations detected
          </p>
          <p className="text-gray-600">
            The network appears well-distributed. Keep up the good work!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map(alert => (
            <div
              key={alert.id}
              className={`power-alert border-l-4 p-6 rounded-lg cursor-pointer hover:shadow-md transition ${
                getSeverityColor(alert.severity)
              }`}
              onClick={() => setSelectedAlert(alert)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {alert.title}
                  </h3>
                  <p className="text-sm text-gray-700 mt-1">
                    {alert.description}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  alert.severity === 'high' ? 'bg-red-200 text-red-900' :
                  alert.severity === 'medium' ? 'bg-yellow-200 text-yellow-900' :
                  'bg-blue-200 text-blue-900'
                }`}>
                  {alert.severity}
                </span>
              </div>

              {alert.affectedAgent && (
                <div className="mb-3 text-sm">
                  <strong>Affected agent:</strong> {alert.affectedAgent}
                  <p className="text-xs text-gray-600 mt-1">
                    Note: This celebrates their contribution while noting the system dependency
                  </p>
                </div>
              )}

              {selectedAlert?.id === alert.id && (
                <div className="suggestions mt-4 pt-4 border-t border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-2">Decentralization suggestions:</h4>
                  <div className="suggestions-container space-y-2">
                    {alert.suggestions.map((suggestion, idx) => (
                      <div key={idx} className="suggestion flex items-start space-x-2 text-sm">
                        <span className="text-green-600 mt-0.5">→</span>
                        <p className="text-gray-700 flex-1">{suggestion}</p>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-4 italic">
                    These are structural suggestions, not individual blame. We're addressing patterns, not people.
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Structural patterns (privacy-preserving) */}
      <div className="mt-8 bg-green-50 border-l-4 border-green-500 p-6 rounded">
        <h3 className="font-semibold text-gray-900 mb-3">Structural patterns detected:</h3>
        <div className="structural-pattern space-y-2 text-sm text-gray-700">
          <p>• Resource distribution is {alerts.length === 0 ? 'balanced' : 'showing concentration'}</p>
          <p>• Decision-making is {alerts.filter(a => a.type === 'decision_concentration').length === 0 ? 'distributed' : 'centralizing'}</p>
          <p>• Knowledge sharing is {alerts.filter(a => a.type === 'knowledge_concentration').length === 0 ? 'healthy' : 'concentrated'}</p>
        </div>
        <p className="text-xs text-gray-500 mt-4 italic">
          This dashboard shows patterns, not individuals. We track flows, not people.
        </p>
      </div>

      {/* Philosophy */}
      <div className="mt-8 bg-purple-50 border-l-4 border-purple-500 p-6 rounded">
        <h3 className="font-semibold text-gray-900 mb-2">Why this matters</h3>
        <div className="space-y-2 text-gray-700 text-sm">
          <p>
            <strong>Prevents hierarchy:</strong> Catch power concentration before it crystallizes
          </p>
          <p>
            <strong>Maintains autonomy:</strong> No one should become indispensable
          </p>
          <p>
            <strong>Enables participation:</strong> Distributed power means distributed voice
          </p>
          <p>
            <strong>Protects freedom:</strong> Authority tends to accumulate - vigilance prevents tyranny
          </p>
        </div>
        <p className="text-gray-600 italic mt-4">
          "Liberty without socialism is privilege and injustice. Socialism without liberty is slavery and brutality." - Mikhail Bakunin
        </p>
      </div>
    </div>
  );
};
