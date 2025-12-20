/**
 * GAP-59: Collective Reflections Page
 *
 * Freire's "problem-posing education" - a space for community dialogue,
 * not individual reflection in isolation.
 *
 * This is NOT a forum - it's a problem-posing space where tensions and
 * contradictions become opportunities for collective learning.
 */

import React, { useState, useEffect } from 'react';
import { DialogueProblem, UserReflection } from '../types/conscientization';

export const CollectiveReflectionsPage: React.FC = () => {
  const [problems, setProblems] = useState<DialogueProblem[]>([]);
  const [reflections, setReflections] = useState<UserReflection[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<string | null>(null);
  const [newVoice, setNewVoice] = useState('');

  useEffect(() => {
    // Load from localStorage (in future: API)
    const allReflections = localStorage.getItem('freire_reflections_all') || '[]';
    setReflections(JSON.parse(allReflections));

    // Mock problems for demo
    setProblems([
      {
        id: 'problem-1',
        problem: "Some people offer a lot, others rarely. Why?",
        voices: [
          {
            id: 'v1',
            author: 'anonymous',
            text: "Maybe they have more free time? I work 60 hours/week and barely have energy to cook, let alone garden.",
            created_at: new Date().toISOString()
          },
          {
            id: 'v2',
            author: 'anonymous',
            text: "Or more privilege/resources to start with. My family has land - that's not my 'generosity', it's inherited wealth.",
            created_at: new Date().toISOString()
          },
          {
            id: 'v3',
            author: 'anonymous',
            text: "I feel guilty when I can't contribute equally. The app doesn't judge, but I judge myself.",
            created_at: new Date().toISOString()
          }
        ],
        created_at: new Date().toISOString()
      },
      {
        id: 'problem-2',
        problem: "Is receiving a gift the same as getting charity? How is it different?",
        voices: [
          {
            id: 'v4',
            author: 'anonymous',
            text: "Charity feels like pity. Gift feels like... relationship? Like we're in this together.",
            created_at: new Date().toISOString()
          },
          {
            id: 'v5',
            author: 'anonymous',
            text: "But sometimes it DOES feel like charity. Especially when there's clear imbalance in who has what.",
            created_at: new Date().toISOString()
          }
        ],
        created_at: new Date().toISOString()
      }
    ]);
  }, []);

  const addVoice = (problemId: string) => {
    if (!newVoice.trim()) return;

    setProblems(problems.map(p => {
      if (p.id === problemId) {
        return {
          ...p,
          voices: [
            ...p.voices,
            {
              id: `v${Date.now()}`,
              author: 'anonymous',
              text: newVoice,
              created_at: new Date().toISOString()
            }
          ]
        };
      }
      return p;
    }));

    setNewVoice('');
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Collective Reflections
        </h1>
        <p className="text-gray-600">
          "No one educates anyone, no one educates themselves alone. People educate each other through dialogue." - Paulo Freire
        </p>
      </div>

      {/* What is this? */}
      <div className="bg-green-50 border-l-4 border-green-500 p-6 mb-8 rounded">
        <h2 className="font-semibold text-gray-900 mb-2">What is this space?</h2>
        <p className="text-gray-700 mb-2">
          This is a <strong>problem-posing space</strong>, not a forum. When tensions, contradictions,
          or questions emerge in our gift economy, we bring them here for collective reflection.
        </p>
        <p className="text-gray-700">
          We don't hide uncomfortable truths - we use them as opportunities to learn together.
          There are no "right answers," only deeper understanding.
        </p>
      </div>

      {/* Problems/Tensions */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Active Dialogues</h2>

        {problems.map(problem => (
          <div key={problem.id} className="bg-white border border-gray-200 rounded-lg shadow-sm">
            {/* Problem statement */}
            <div className="bg-amber-50 p-4 border-b border-amber-100 rounded-t-lg">
              <h3 className="text-lg font-semibold text-gray-900">
                🤔 {problem.problem}
              </h3>
            </div>

            {/* Voices */}
            <div className="p-4 space-y-4">
              {problem.voices.map(voice => (
                <div key={voice.id} className="pl-4 border-l-2 border-green-500">
                  <p className="text-gray-700 italic">"{voice.text}"</p>
                  <p className="text-xs text-gray-500 mt-1">
                    - {voice.author} • {new Date(voice.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}

              {/* Add voice */}
              {selectedProblem === problem.id ? (
                <div className="mt-4 space-y-2">
                  <textarea
                    value={newVoice}
                    onChange={(e) => setNewVoice(e.target.value)}
                    placeholder="Add your voice to this dialogue..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 resize-none"
                    rows={3}
                  />
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => setSelectedProblem(null)}
                      className="px-4 py-2 text-gray-600 hover:text-gray-800"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => addVoice(problem.id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Add Voice
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setSelectedProblem(problem.id)}
                  className="text-green-600 hover:text-green-700 text-sm font-medium"
                >
                  + Add your voice
                </button>
              )}
            </div>

            {/* Synthesis (if exists) */}
            {problem.synthesis && (
              <div className="bg-green-50 p-4 border-t border-green-100 rounded-b-lg">
                <p className="text-sm font-semibold text-gray-700 mb-1">
                  Emergent Understanding:
                </p>
                <p className="text-gray-700">{problem.synthesis}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Personal Reflections (private) */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Private Reflections</h2>
        <p className="text-gray-600 mb-6">
          These are your personal reflections - not shared unless you choose to.
        </p>

        {reflections.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">
              You haven't written any reflections yet. They'll appear here as you engage with the app.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {reflections.map((reflection) => (
              <div key={reflection.id} className="bg-white border border-gray-200 rounded-lg p-4">
                <p className="text-sm text-gray-500 mb-2">
                  {new Date(reflection.created_at).toLocaleDateString()}
                </p>
                <p className="text-gray-700">
                  {Array.isArray(reflection.response)
                    ? reflection.response.join(', ')
                    : reflection.response}
                </p>
                {reflection.free_text && (
                  <p className="text-gray-600 italic mt-2">"{reflection.free_text}"</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
