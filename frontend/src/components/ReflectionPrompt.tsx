/**
 * GAP-59: Reflection Prompt Modal
 *
 * Paulo Freire's conscientization - critical consciousness through reflection
 *
 * This component shows prompts that invite users to think about WHY they're
 * participating in the gift economy, not just transact mechanically.
 */

import React, { useState } from 'react';
import { ConscientizationPrompt, UserReflection } from '../types/conscientization';

interface ReflectionPromptProps {
  prompt: ConscientizationPrompt;
  onSubmit: (reflection: Partial<UserReflection>) => void;
  onSkip: () => void;
  userId: string;
}

export const ReflectionPrompt: React.FC<ReflectionPromptProps> = ({
  prompt,
  onSubmit,
  onSkip,
  userId
}) => {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [freeText, setFreeText] = useState('');
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [anonymous, setAnonymous] = useState(false);

  const handleOptionToggle = (option: string) => {
    if (selectedOptions.includes(option)) {
      setSelectedOptions(selectedOptions.filter(o => o !== option));
    } else {
      setSelectedOptions([...selectedOptions, option]);
    }
  };

  const handleSubmit = () => {
    const reflection: Partial<UserReflection> = {
      user_id: userId,
      prompt_id: prompt.id,
      response: prompt.options ? selectedOptions : freeText,
      free_text: freeText || undefined,
      anonymous,
      created_at: new Date().toISOString()
    };

    onSubmit(reflection);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6 rounded-t-lg">
          <h2 className="text-2xl font-bold mb-2">Take a Moment to Reflect</h2>
          <p className="text-sm opacity-90">
            "The oppressed must not become oppressors, but restorers of humanity." - Paulo Freire
          </p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Main Question */}
          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">
              {prompt.question}
            </h3>

            {/* Options (if present) */}
            {prompt.options && !showFollowUp && (
              <div className="space-y-2">
                {prompt.options.map((option, index) => (
                  <label
                    key={index}
                    className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-gray-200 transition"
                  >
                    <input
                      type="checkbox"
                      checked={selectedOptions.includes(option)}
                      onChange={() => handleOptionToggle(option)}
                      className="mt-1 h-4 w-4 text-green-600 rounded focus:ring-green-500"
                    />
                    <span className="text-gray-700">{option}</span>
                  </label>
                ))}
              </div>
            )}

            {/* Sub-questions (if present) */}
            {prompt.subQuestions && (
              <div className="space-y-3 mt-4">
                {prompt.subQuestions.map((question, index) => (
                  <div key={index} className="pl-4 border-l-2 border-green-500">
                    <p className="text-gray-700 italic">• {question}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Free text area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {showFollowUp && prompt.followUp ? prompt.followUp : "Your reflection (optional):"}
            </label>
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder="Share your thoughts, feelings, or questions..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              rows={4}
            />
          </div>

          {/* Philosophy explanation */}
          <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
            <p className="text-sm text-gray-700">
              <strong>Why this matters:</strong> {prompt.philosophy}
            </p>
          </div>

          {/* Anonymous option */}
          <label className="flex items-center space-x-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={anonymous}
              onChange={(e) => setAnonymous(e.target.checked)}
              className="h-4 w-4 text-green-600 rounded focus:ring-green-500"
            />
            <span>Share my reflection anonymously with the community</span>
          </label>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 flex justify-between items-center rounded-b-lg border-t">
          <button
            onClick={onSkip}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium transition"
          >
            Skip (that's okay!)
          </button>

          <div className="space-x-3">
            {!showFollowUp && prompt.followUp && (selectedOptions.length > 0 || freeText) && (
              <button
                onClick={() => setShowFollowUp(true)}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
              >
                Continue Reflecting
              </button>
            )}

            <button
              onClick={handleSubmit}
              disabled={!selectedOptions.length && !freeText}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {anonymous ? 'Share Anonymously' : 'Save Reflection'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
