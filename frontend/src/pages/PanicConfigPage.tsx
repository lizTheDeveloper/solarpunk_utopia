/**
 * Panic Features Configuration Page
 *
 * OPSEC-critical UI for configuring:
 * - Duress PIN (alternate unlock showing decoy)
 * - Quick Wipe (panic gesture destroys data)
 * - Dead Man's Switch (auto-wipe if inactive)
 * - Decoy Mode (app appears as calculator/notes)
 * - Seed Phrase Recovery
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface PanicStatus {
  duress_pin: { enabled: boolean };
  quick_wipe: { enabled: boolean };
  dead_mans_switch: { enabled: boolean; time_remaining?: string };
  decoy_mode: { enabled: boolean };
  burn_notices: { active_count: number; notices: any[] };
  wipe_history: any[];
}

export default function PanicConfigPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<PanicStatus | null>(null);
  const [activeTab, setActiveTab] = useState<'duress' | 'wipe' | 'deadman' | 'decoy' | 'recovery'>('duress');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form states
  const [duressPIN, setDuressPIN] = useState('');
  const [quickWipeGesture, setQuickWipeGesture] = useState('five_tap_logo');
  const [quickWipeConfirmation, setQuickWipeConfirmation] = useState(true);
  const [deadManTimeout, setDeadManTimeout] = useState(72);
  const [decoyType, setDecoyType] = useState('calculator');
  const [secretGesture, setSecretGesture] = useState('31337=');
  const [seedPhrase, setSeedPhrase] = useState('');

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/panic/status');
      if (!res.ok) throw new Error('Failed to fetch panic status');
      const data = await res.json();
      setStatus(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSetDuressPIN = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch('/api/panic/duress-pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duress_pin: duressPIN })
      });

      if (!res.ok) throw new Error('Failed to set duress PIN');

      setSuccess('Duress PIN set successfully. Remember this PIN - it activates decoy mode.');
      setDuressPIN('');
      fetchStatus();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleConfigureQuickWipe = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch('/api/panic/quick-wipe/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: true,
          gesture_type: quickWipeGesture,
          confirmation_required: quickWipeConfirmation
        })
      });

      if (!res.ok) throw new Error('Failed to configure quick wipe');

      setSuccess('Quick wipe configured successfully.');
      fetchStatus();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleConfigureDeadManSwitch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch('/api/panic/dead-mans-switch/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: true,
          timeout_hours: deadManTimeout
        })
      });

      if (!res.ok) throw new Error('Failed to configure dead man\'s switch');

      setSuccess(`Dead man's switch configured: auto-wipe after ${deadManTimeout} hours of inactivity.`);
      fetchStatus();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleConfigureDecoyMode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch('/api/panic/decoy-mode/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: true,
          decoy_type: decoyType,
          secret_gesture: secretGesture
        })
      });

      if (!res.ok) throw new Error('Failed to configure decoy mode');

      setSuccess(`Decoy mode configured: app will appear as ${decoyType}.`);
      fetchStatus();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleGenerateSeedPhrase = async () => {
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch('/api/panic/seed-phrase/generate', {
        method: 'POST'
      });

      if (!res.ok) throw new Error('Failed to generate seed phrase');

      const data = await res.json();
      setSeedPhrase(data.seed_phrase);
      setSuccess('CRITICAL: Write this down and store securely. This is the ONLY way to recover after a wipe.');
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading panic features...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                OPSEC Critical: Panic & Safety Features
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>These features protect you and the network when phones are seized, users detained, or devices inspected.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Status Cards */}
        {status && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className={`p-4 rounded-lg ${status.duress_pin.enabled ? 'bg-green-50 border border-green-200' : 'bg-gray-100 border border-gray-200'}`}>
              <div className="text-sm font-medium text-gray-700">Duress PIN</div>
              <div className={`text-2xl font-bold ${status.duress_pin.enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.duress_pin.enabled ? '✓' : '○'}
              </div>
            </div>

            <div className={`p-4 rounded-lg ${status.quick_wipe.enabled ? 'bg-green-50 border border-green-200' : 'bg-gray-100 border border-gray-200'}`}>
              <div className="text-sm font-medium text-gray-700">Quick Wipe</div>
              <div className={`text-2xl font-bold ${status.quick_wipe.enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.quick_wipe.enabled ? '✓' : '○'}
              </div>
            </div>

            <div className={`p-4 rounded-lg ${status.dead_mans_switch.enabled ? 'bg-green-50 border border-green-200' : 'bg-gray-100 border border-gray-200'}`}>
              <div className="text-sm font-medium text-gray-700">Dead Man's Switch</div>
              <div className={`text-2xl font-bold ${status.dead_mans_switch.enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.dead_mans_switch.enabled ? '✓' : '○'}
              </div>
            </div>

            <div className={`p-4 rounded-lg ${status.decoy_mode.enabled ? 'bg-green-50 border border-green-200' : 'bg-gray-100 border border-gray-200'}`}>
              <div className="text-sm font-medium text-gray-700">Decoy Mode</div>
              <div className={`text-2xl font-bold ${status.decoy_mode.enabled ? 'text-green-600' : 'text-gray-400'}`}>
                {status.decoy_mode.enabled ? '✓' : '○'}
              </div>
            </div>
          </div>
        )}

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md text-green-700">
            {success}
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {[
                { id: 'duress', label: 'Duress PIN' },
                { id: 'wipe', label: 'Quick Wipe' },
                { id: 'deadman', label: 'Dead Man\'s Switch' },
                { id: 'decoy', label: 'Decoy Mode' },
                { id: 'recovery', label: 'Recovery' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 ${
                    activeTab === tab.id
                      ? 'border-red-500 text-red-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Duress PIN Tab */}
            {activeTab === 'duress' && (
              <div>
                <h3 className="text-lg font-medium mb-4">Duress PIN Configuration</h3>
                <p className="text-gray-600 mb-4">
                  Set an alternate PIN that opens the app in decoy mode. When you enter this PIN, the app will show innocuous content and send a silent burn notice to the network.
                </p>

                <form onSubmit={handleSetDuressPIN} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Duress PIN (4-6 digits)
                    </label>
                    <input
                      type="password"
                      value={duressPIN}
                      onChange={(e) => setDuressPIN(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="1234"
                      pattern="[0-9]{4,6}"
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700"
                  >
                    Set Duress PIN
                  </button>
                </form>
              </div>
            )}

            {/* Quick Wipe Tab */}
            {activeTab === 'wipe' && (
              <div>
                <h3 className="text-lg font-medium mb-4">Quick Wipe Configuration</h3>
                <p className="text-gray-600 mb-4">
                  Configure a panic gesture that instantly destroys all sensitive data in under 3 seconds. Cannot be undone (except via seed phrase recovery).
                </p>

                <form onSubmit={handleConfigureQuickWipe} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Panic Gesture
                    </label>
                    <select
                      value={quickWipeGesture}
                      onChange={(e) => setQuickWipeGesture(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="five_tap_logo">Five Taps on Logo</option>
                      <option value="shake_pattern">Shake Pattern</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="confirmation"
                      checked={quickWipeConfirmation}
                      onChange={(e) => setQuickWipeConfirmation(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="confirmation" className="text-sm text-gray-700">
                      Require confirmation (prevents accidents)
                    </label>
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700"
                  >
                    Configure Quick Wipe
                  </button>
                </form>
              </div>
            )}

            {/* Dead Man's Switch Tab */}
            {activeTab === 'deadman' && (
              <div>
                <h3 className="text-lg font-medium mb-4">Dead Man's Switch Configuration</h3>
                <p className="text-gray-600 mb-4">
                  Auto-wipe sensitive data if you don't check in within a specified time. Protects you if you're detained and can't access the app.
                </p>

                <form onSubmit={handleConfigureDeadManSwitch} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timeout (hours of inactivity before wipe)
                    </label>
                    <input
                      type="number"
                      value={deadManTimeout}
                      onChange={(e) => setDeadManTimeout(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      min="1"
                      max="168"
                      required
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      Recommended: 72 hours (3 days)
                    </p>
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700"
                  >
                    Configure Dead Man's Switch
                  </button>
                </form>
              </div>
            )}

            {/* Decoy Mode Tab */}
            {activeTab === 'decoy' && (
              <div>
                <h3 className="text-lg font-medium mb-4">Decoy Mode Configuration</h3>
                <p className="text-gray-600 mb-4">
                  Make the app appear as an innocuous calculator or notes app. A secret gesture reveals the real app.
                </p>

                <form onSubmit={handleConfigureDecoyMode} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Decoy Type
                    </label>
                    <select
                      value={decoyType}
                      onChange={(e) => setDecoyType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="calculator">Calculator</option>
                      <option value="notes">Notes App</option>
                      <option value="weather">Weather App</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Secret Gesture (for calculator: special equation)
                    </label>
                    <input
                      type="text"
                      value={secretGesture}
                      onChange={(e) => setSecretGesture(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="31337="
                      required
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      For calculator: type this and press = to reveal real app
                    </p>
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700"
                  >
                    Configure Decoy Mode
                  </button>
                </form>
              </div>
            )}

            {/* Recovery Tab */}
            {activeTab === 'recovery' && (
              <div>
                <h3 className="text-lg font-medium mb-4">Seed Phrase Recovery</h3>
                <p className="text-gray-600 mb-4">
                  Generate a 12-word seed phrase for identity recovery after a wipe. Write this down and store it securely - it's the ONLY way to recover.
                </p>

                <button
                  onClick={handleGenerateSeedPhrase}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 mb-4"
                >
                  Generate Seed Phrase
                </button>

                {seedPhrase && (
                  <div className="bg-yellow-50 border-2 border-yellow-400 p-4 rounded-md">
                    <p className="text-sm font-medium text-yellow-800 mb-2">
                      CRITICAL: Write this down NOW
                    </p>
                    <div className="font-mono text-sm bg-white p-3 rounded border border-yellow-300">
                      {seedPhrase}
                    </div>
                    <p className="text-xs text-yellow-700 mt-2">
                      Store this in a safe place. Never share it digitally. This cannot be recovered if lost.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Back Button */}
        <div className="mt-6">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-800"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
