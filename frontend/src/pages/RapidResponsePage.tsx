/**
 * Rapid Response Page
 *
 * CRITICAL: When ICE shows up. When someone is detained. When we need to mobilize NOW.
 *
 * Features:
 * - BIG RED BUTTON (2-tap trigger)
 * - Active alerts display
 * - Responder status
 * - Coordinator dashboard
 * - Timeline of updates
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Loading } from '../components/Loading';
import { ErrorMessage } from '../components/ErrorMessage';

interface Alert {
  id: string;
  alert_type: string;
  alert_level: 'critical' | 'urgent' | 'watch';
  status: string;
  location_hint: string;
  description: string;
  people_affected?: number;
  coordinator_id?: string;
  confirmed: boolean;
  created_at: string;
  expires_at: string;
}

interface Responder {
  id: string;
  user_id: string;
  status: string;
  role: string;
  eta_minutes?: number;
  notes?: string;
  responded_at: string;
  arrived_at?: string;
}

interface Update {
  id: string;
  posted_by: string;
  update_type: string;
  message: string;
  new_alert_level?: string;
  posted_at: string;
}

const ALERT_LEVELS = ['critical', 'urgent', 'watch'] as const;
const ALERT_TYPES = ['ice_raid', 'checkpoint', 'detention', 'workplace_raid', 'threat', 'other'] as const;

const RapidResponsePage: React.FC = () => {
  const { user, token } = useAuth();
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [responders, setResponders] = useState<Responder[]>([]);
  const [timeline, setTimeline] = useState<Update[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Trigger alert modal state
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [alertType, setAlertType] = useState<typeof ALERT_TYPES[number]>('ice_raid');
  const [alertLevel, setAlertLevel] = useState<typeof ALERT_LEVELS[number]>('critical');
  const [locationHint, setLocationHint] = useState('');
  const [description, setDescription] = useState('');
  const [peopleAffected, setPeopleAffected] = useState<string>('');
  const [includeCoordinates, setIncludeCoordinates] = useState(false);
  const [confirmTrigger, setConfirmTrigger] = useState(false);

  // Respond modal state
  const [showRespondModal, setShowRespondModal] = useState(false);
  const [respondStatus, setRespondStatus] = useState<'responding' | 'available_far' | 'unavailable'>('responding');
  const [respondRole, setRespondRole] = useState<'physical' | 'legal' | 'media' | 'support'>('physical');
  const [etaMinutes, setEtaMinutes] = useState<string>('');
  const [respondNotes, setRespondNotes] = useState('');

  // Load active alerts
  useEffect(() => {
    loadActiveAlerts();
    const interval = setInterval(loadActiveAlerts, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [user]);

  // Load alert details when selected
  useEffect(() => {
    if (selectedAlert) {
      loadAlertDetails(selectedAlert.id);
    }
  }, [selectedAlert]);

  const loadActiveAlerts = async () => {
    if (!user) return;

    try {
      // TODO: Get user's actual cell_id
      const cellId = 'cell-001';

      const response = await fetch(`/api/rapid-response/alerts/active/${cellId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load active alerts');
      }

      const data = await response.json();
      setActiveAlerts(data.alerts || []);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
      setLoading(false);
    }
  };

  const loadAlertDetails = async (alertId: string) => {
    if (!user) return;

    try {
      const response = await fetch(`/api/rapid-response/alerts/${alertId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load alert details');
      }

      const data = await response.json();
      setResponders(data.responders || []);
      setTimeline(data.timeline || []);
    } catch (err) {
      console.error('Failed to load alert details:', err);
    }
  };

  const triggerAlert = async () => {
    if (!user || !confirmTrigger) return;

    try {
      // TODO: Get user's actual cell_id
      const cellId = 'cell-001';

      const response = await fetch('/api/rapid-response/alerts/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          alert_type: alertType,
          alert_level: alertLevel,
          cell_id: cellId,
          location_hint: locationHint,
          description: description,
          people_affected: peopleAffected ? parseInt(peopleAffected) : null,
          include_coordinates: includeCoordinates
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to trigger alert');
      }

      // Close modal and refresh alerts
      setShowTriggerModal(false);
      setConfirmTrigger(false);
      resetTriggerForm();
      await loadActiveAlerts();

      toast.success('Alert triggered! Propagating to nearby members via mesh.');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to trigger alert');
    }
  };

  const respondToAlert = async () => {
    if (!user || !selectedAlert) return;

    try {
      const response = await fetch('/api/rapid-response/responders/respond', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          alert_id: selectedAlert.id,
          status: respondStatus,
          role: respondRole,
          eta_minutes: etaMinutes ? parseInt(etaMinutes) : null,
          notes: respondNotes
        })
      });

      if (!response.ok) {
        throw new Error('Failed to respond to alert');
      }

      // Close modal and refresh details
      setShowRespondModal(false);
      resetRespondForm();
      await loadAlertDetails(selectedAlert.id);

      toast.success('Response recorded!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to respond');
    }
  };

  const confirmAlert = async (alertId: string) => {
    if (!user) return;

    try {
      const response = await fetch(`/api/rapid-response/alerts/${alertId}/confirm`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to confirm alert');
      }

      await loadActiveAlerts();
      if (selectedAlert?.id === alertId) {
        await loadAlertDetails(alertId);
      }

      toast.success('Alert confirmed!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to confirm alert');
    }
  };

  const claimCoordinator = async (alertId: string) => {
    if (!user) return;

    try {
      const response = await fetch(`/api/rapid-response/alerts/${alertId}/claim-coordinator`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to claim coordinator');
      }

      await loadActiveAlerts();
      if (selectedAlert?.id === alertId) {
        await loadAlertDetails(alertId);
      }

      toast.success('You are now coordinating this response!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to claim coordinator');
    }
  };

  const resetTriggerForm = () => {
    setAlertType('ice_raid');
    setAlertLevel('critical');
    setLocationHint('');
    setDescription('');
    setPeopleAffected('');
    setIncludeCoordinates(false);
    setConfirmTrigger(false);
  };

  const resetRespondForm = () => {
    setRespondStatus('responding');
    setRespondRole('physical');
    setEtaMinutes('');
    setRespondNotes('');
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-600';
      case 'urgent':
        return 'bg-orange-500';
      case 'watch':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getAlertTypeLabel = (type: string) => {
    return type.replace(/_/g, ' ').toUpperCase();
  };

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Rapid Response</h1>
        <p className="text-gray-600">
          When ICE shows up. When someone is detained. When we mobilize NOW.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* BIG RED BUTTON */}
      <div className="mb-8 flex justify-center">
        <button
          onClick={() => setShowTriggerModal(true)}
          className="bg-red-600 hover:bg-red-700 text-white font-bold py-8 px-16 rounded-lg text-2xl shadow-2xl transform transition hover:scale-105 active:scale-95 border-4 border-red-800"
        >
          🚨 EMERGENCY ALERT 🚨
        </button>
      </div>

      {/* Active Alerts */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Active Alerts</h2>

        {activeAlerts.length === 0 ? (
          <Card>
            <p className="text-gray-500 text-center py-8">No active alerts. Stay vigilant.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {activeAlerts.map(alert => (
              <Card
                key={alert.id}
                className={`cursor-pointer border-l-4 ${
                  alert.alert_level === 'critical' ? 'border-red-600' :
                  alert.alert_level === 'urgent' ? 'border-orange-500' :
                  'border-yellow-500'
                }`}
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 rounded text-white text-xs font-bold ${getAlertLevelColor(alert.alert_level)}`}>
                        {alert.alert_level.toUpperCase()}
                      </span>
                      <span className="font-semibold">{getAlertTypeLabel(alert.alert_type)}</span>
                      {!alert.confirmed && alert.alert_level === 'critical' && (
                        <span className="text-red-600 text-xs">(NEEDS CONFIRMATION)</span>
                      )}
                    </div>
                    <p className="text-sm mb-1"><strong>Location:</strong> {alert.location_hint}</p>
                    <p className="text-sm mb-2">{alert.description}</p>
                    {alert.people_affected && (
                      <p className="text-sm text-gray-600">People affected: {alert.people_affected}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-2">
                      Triggered: {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="ml-4 flex flex-col gap-2">
                    {!alert.confirmed && alert.alert_level === 'critical' && (
                      <Button
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          confirmAlert(alert.id);
                        }}
                      >
                        Confirm
                      </Button>
                    )}
                    {!alert.coordinator_id && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          claimCoordinator(alert.id);
                        }}
                      >
                        Coordinate
                      </Button>
                    )}
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAlert(alert);
                        setShowRespondModal(true);
                      }}
                    >
                      Respond
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Alert Details (if selected) */}
      {selectedAlert && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Alert Details</h2>

          {/* Responders */}
          <Card className="mb-4">
            <h3 className="font-bold mb-2">Responders ({responders.length})</h3>
            {responders.length === 0 ? (
              <p className="text-gray-500 text-sm">No responders yet. Be the first!</p>
            ) : (
              <div className="space-y-2">
                {responders.map(responder => (
                  <div key={responder.id} className="flex justify-between items-center text-sm border-b pb-2">
                    <div>
                      <span className="font-semibold capitalize">{responder.role}</span>
                      {' - '}
                      <span className="capitalize">{responder.status.replace(/_/g, ' ')}</span>
                      {responder.eta_minutes && (
                        <span className="text-gray-600"> (ETA: {responder.eta_minutes} min)</span>
                      )}
                    </div>
                    {responder.notes && (
                      <span className="text-gray-600 text-xs">{responder.notes}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Timeline */}
          <Card>
            <h3 className="font-bold mb-2">Timeline</h3>
            {timeline.length === 0 ? (
              <p className="text-gray-500 text-sm">No updates yet.</p>
            ) : (
              <div className="space-y-3">
                {timeline.map(update => (
                  <div key={update.id} className="border-l-2 border-gray-300 pl-4">
                    <p className="text-sm font-semibold capitalize">{update.update_type.replace(/_/g, ' ')}</p>
                    <p className="text-sm">{update.message}</p>
                    <p className="text-xs text-gray-500">{new Date(update.posted_at).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Trigger Alert Modal */}
      {showTriggerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-screen overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4 text-red-600">🚨 Trigger Emergency Alert</h2>

            <div className="mb-4">
              <label className="block mb-2 font-semibold">Alert Type</label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value as typeof ALERT_TYPES[number])}
                className="w-full p-2 border rounded"
              >
                {ALERT_TYPES.map(type => (
                  <option key={type} value={type}>{getAlertTypeLabel(type)}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="block mb-2 font-semibold">Alert Level</label>
              <select
                value={alertLevel}
                onChange={(e) => setAlertLevel(e.target.value as typeof ALERT_LEVELS[number])}
                className="w-full p-2 border rounded"
              >
                {ALERT_LEVELS.map(level => (
                  <option key={level} value={level}>{level.toUpperCase()}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="block mb-2 font-semibold">Location (general only)</label>
              <input
                type="text"
                value={locationHint}
                onChange={(e) => setLocationHint(e.target.value)}
                placeholder="e.g., 7th & Main, downtown"
                className="w-full p-2 border rounded"
              />
            </div>

            <div className="mb-4">
              <label className="block mb-2 font-semibold">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of situation"
                rows={3}
                className="w-full p-2 border rounded"
              />
            </div>

            <div className="mb-4">
              <label className="block mb-2 font-semibold">People Affected (optional)</label>
              <input
                type="number"
                value={peopleAffected}
                onChange={(e) => setPeopleAffected(e.target.value)}
                placeholder="Number of people"
                className="w-full p-2 border rounded"
              />
            </div>

            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeCoordinates}
                  onChange={(e) => setIncludeCoordinates(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm">Include GPS coordinates (only if safe)</span>
              </label>
            </div>

            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={confirmTrigger}
                  onChange={(e) => setConfirmTrigger(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm font-semibold">I confirm this is a real emergency</span>
              </label>
              {alertLevel === 'critical' && (
                <p className="text-xs text-gray-600 mt-2">
                  CRITICAL alerts must be confirmed by another member within 5 minutes or will auto-downgrade to WATCH.
                </p>
              )}
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => {
                  setShowTriggerModal(false);
                  resetTriggerForm();
                }}
                variant="secondary"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={triggerAlert}
                disabled={!locationHint || !description || !confirmTrigger}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                TRIGGER ALERT
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Respond Modal */}
      {showRespondModal && selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">Respond to Alert</h2>

            <div className="mb-4">
              <label className="block mb-2 font-semibold">Status</label>
              <select
                value={respondStatus}
                onChange={(e) => setRespondStatus(e.target.value as typeof respondStatus)}
                className="w-full p-2 border rounded"
              >
                <option value="responding">Responding (on my way)</option>
                <option value="available_far">Available but far</option>
                <option value="unavailable">Cannot respond</option>
              </select>
            </div>

            {respondStatus !== 'unavailable' && (
              <>
                <div className="mb-4">
                  <label className="block mb-2 font-semibold">Role</label>
                  <select
                    value={respondRole}
                    onChange={(e) => setRespondRole(e.target.value as typeof respondRole)}
                    className="w-full p-2 border rounded"
                  >
                    <option value="physical">Physical Responder</option>
                    <option value="legal">Legal Observer</option>
                    <option value="media">Media/Documenter</option>
                    <option value="support">Support (supplies/transport)</option>
                  </select>
                </div>

                <div className="mb-4">
                  <label className="block mb-2 font-semibold">ETA (minutes, optional)</label>
                  <input
                    type="number"
                    value={etaMinutes}
                    onChange={(e) => setEtaMinutes(e.target.value)}
                    placeholder="15"
                    className="w-full p-2 border rounded"
                  />
                </div>

                <div className="mb-4">
                  <label className="block mb-2 font-semibold">Notes (optional)</label>
                  <input
                    type="text"
                    value={respondNotes}
                    onChange={(e) => setRespondNotes(e.target.value)}
                    placeholder="e.g., 'bringing camera'"
                    className="w-full p-2 border rounded"
                  />
                </div>
              </>
            )}

            <div className="flex gap-2">
              <Button
                onClick={() => {
                  setShowRespondModal(false);
                  resetRespondForm();
                }}
                variant="secondary"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button onClick={respondToAlert} className="flex-1">
                Submit Response
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RapidResponsePage;
